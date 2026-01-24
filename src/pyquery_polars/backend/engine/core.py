from typing import Any, Dict, List, Literal, Optional, Union, Sequence, Tuple
import polars as pl
import os
import uuid
from pydantic import BaseModel

# Import Utils
from pyquery_polars.backend.io.plugins import ALL_LOADERS, ALL_EXPORTERS
from pyquery_polars.core.models import JobInfo, PluginDef, RecipeStep, DatasetMetadata
from pyquery_polars.core.params import CleanCastParams, CastChange
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.backend.io.files import get_excel_sheet_names, get_excel_table_names, cleanup_staging_files, resolve_file_paths, batch_detect_encodings, convert_file_to_utf8
from pyquery_polars.core.io import FileFilter
from pyquery_polars.core.project import (
    ProjectFile, ProjectMeta, PathConfig, DatasetProject, ProjectImportResult
)
from pyquery_polars.backend.project.serializer import (
    save_project, load_project, resolve_paths, convert_paths_to_relative,
    validate_dataset_files
)

# Modules
from .registry import register_all_steps
from .jobs import JobManager
from ..processing import executor as execution
from ..processing.materializer import StorageManager
from ..analysis import AnalysisEngine
from ..analysis.inference import TypeInferenceEngine
from ..analysis.joins import JoinAnalyzer


class PyQueryEngine:
    def __init__(self):
        self._datasets: Dict[str, DatasetMetadata] = {}  # Metadata storage
        # Recipe storage (backend-centric)
        self._recipes: Dict[str, List[RecipeStep]] = {}
        self._sql_context = pl.SQLContext()

        # Analysis Engine
        self.analysis = AnalysisEngine()

        # IO Plugins
        self._loaders: Dict[str, PluginDef] = {}
        self._exporters: Dict[str, PluginDef] = {}

        # Init Registry
        register_all_steps()
        self._register_io_defaults()

        def apply_recipe_wrapper(lf, recipe, project_recipes=None):
            # Get dict of LazyFrames for execution context
            datasets_dict = self._get_datasets_dict_for_execution()
            return execution.apply_recipe(lf, recipe, datasets_dict, project_recipes)

        # Job Manager
        self._job_manager = JobManager(
            get_dataset_func=self.get_dataset,
            apply_recipe_func=apply_recipe_wrapper,
            exporters=self._exporters
        )

    def _register_io_defaults(self):
        for l in ALL_LOADERS:
            self._loaders[l.name] = l
        for e in ALL_EXPORTERS:
            self._exporters[e.name] = e

    def get_supported_steps(self) -> List[str]:
        return StepRegistry.get_supported_steps()

    # ==========================
    # DATASET MANAGEMENT
    # ==========================
    def add_dataset(self, name: str, lf_or_lfs: Union[pl.LazyFrame, List[pl.LazyFrame]],
                    metadata: Optional[Dict[str, Any]] = None,
                    loader_type: Optional[Literal["File",
                                                  "SQL", "API"]] = None,
                    loader_params: Optional[Dict[str, Any]] = None):
        """Add a dataset with comprehensive metadata."""
        if metadata is None:
            metadata = {}

        # Create DatasetMetadata object
        ds_meta = DatasetMetadata(
            source_path=metadata.get("source_path"),
            input_type=metadata.get("input_type", "file"),
            input_format=metadata.get("input_format"),
            process_individual=metadata.get("process_individual", False),
            file_list=metadata.get("file_list"),
            file_count=metadata.get("file_count", 1),
            loader_type=loader_type,
            loader_params=loader_params
        )

        # Handle LazyFrame vs List[LazyFrame]
        if isinstance(lf_or_lfs, list):
            ds_meta.base_lfs = lf_or_lfs
            # For SQL context, register concatenated view
            concat_lf = pl.concat(lf_or_lfs, how="diagonal")
            ds_meta.base_lf = None  # Don't store twice
        else:
            ds_meta.base_lf = lf_or_lfs
            ds_meta.base_lfs = None
            concat_lf = lf_or_lfs

        self._datasets[name] = ds_meta

        # Initialize empty recipe if not exists
        if name not in self._recipes:
            self._recipes[name] = []

        # Register with SQL context
        try:
            self._sql_context.register(name, concat_lf)
        except Exception as e:
            print(f"SQL Registration Warning: {e}")

    def remove_dataset(self, name: str):
        if name in self._datasets:
            del self._datasets[name]
            # Also remove associated recipe
            if name in self._recipes:
                del self._recipes[name]
            try:
                self._sql_context.unregister(name)
            except:
                pass

    def rename_dataset(self, old_name: str, new_name: str) -> bool:
        """Rename a dataset, updating all references."""
        if old_name not in self._datasets or new_name in self._datasets:
            return False

        # Move metadata to new key
        self._datasets[new_name] = self._datasets.pop(old_name)

        # Move recipe to new key
        if old_name in self._recipes:
            self._recipes[new_name] = self._recipes.pop(old_name)

        # Update SQL context
        try:
            # Get the LazyFrame for re-registration
            meta = self._datasets[new_name]
            if meta.base_lf is not None:
                lf = meta.base_lf
            elif meta.base_lfs:
                lf = pl.concat(meta.base_lfs, how="diagonal")
            else:
                lf = None

            self._sql_context.unregister(old_name)
            if lf is not None:
                self._sql_context.register(new_name, lf)
        except Exception as e:
            print(f"SQL Context Rename Warning: {e}")

        return True

    def get_dataset(self, name: str) -> Optional[pl.LazyFrame]:
        """Get LazyFrame for preview (returns first file if process_individual)."""
        meta = self._datasets.get(name)
        if meta is None:
            return None

        # Return appropriate LazyFrame
        if meta.base_lf is not None:
            return meta.base_lf
        elif meta.base_lfs is not None and len(meta.base_lfs) > 0:
            # For preview with process_individual, return first file only
            return meta.base_lfs[0]

        return None

    def get_dataset_metadata(self, name: str) -> Dict[str, Any]:
        """Get dataset metadata as dict."""
        meta = self._datasets.get(name)
        if meta is None:
            return {}

        # Convert to dict, excluding LazyFrames
        # Calculate LF count
        lf_count = 0
        if meta.base_lfs:
            lf_count = len(meta.base_lfs)
        elif meta.base_lf is not None:
            lf_count = 1

        return {
            "source_path": meta.source_path,
            "input_type": meta.input_type,
            "input_format": meta.input_format,
            "process_individual": meta.process_individual,
            "file_list": meta.file_list,
            "file_count": meta.file_count,
            "lazyframe_count": lf_count,
            "loader_type": meta.loader_type,
            "loader_params": meta.loader_params
        }

    def _get_datasets_dict_for_execution(self) -> Dict[str, pl.LazyFrame]:
        """Get dict of dataset names to LazyFrames for execution context."""
        result = {}
        for name, meta in self._datasets.items():
            if meta.base_lf is not None:
                result[name] = meta.base_lf
            elif meta.base_lfs is not None and len(meta.base_lfs) > 0:
                # Use concatenated view
                result[name] = pl.concat(meta.base_lfs, how="diagonal")
        return result

    # ==========================
    # RECIPE MANAGEMENT (Backend-Centric)
    # ==========================
    def add_recipe(self, dataset_name: str, recipe: List[RecipeStep]) -> None:
        """Add or replace recipe for a dataset."""
        self._recipes[dataset_name] = recipe

    def get_recipe(self, dataset_name: str) -> List[RecipeStep]:
        """Get recipe for a dataset. Returns empty list if none."""
        return self._recipes.get(dataset_name, [])

    def update_recipe(self, dataset_name: str, recipe: List[RecipeStep]) -> None:
        """Update (replace) recipe for a dataset."""
        self._recipes[dataset_name] = recipe

    def add_recipe_step(self, dataset_name: str, step: RecipeStep) -> None:
        """Add a single step to a dataset's recipe."""
        if dataset_name not in self._recipes:
            self._recipes[dataset_name] = []
        self._recipes[dataset_name].append(step)

    def clear_recipe(self, dataset_name: str) -> None:
        """Clear all recipe steps for a dataset."""
        self._recipes[dataset_name] = []

    def get_all_recipes(self) -> Dict[str, List[RecipeStep]]:
        """Get all recipes as a dict (for project export and frontend sync)."""
        return self._recipes.copy()

    def set_all_recipes(self, recipes: Dict[str, List[RecipeStep]]) -> None:
        """Set all recipes at once (for project import)."""
        self._recipes = recipes.copy()

    # ==========================
    # PROJECT MANAGEMENT
    # ==========================
    def export_project(
        self,
        path_mode: Literal["absolute", "relative"] = "absolute",
        base_dir: Optional[str] = None,
        description: Optional[str] = None
    ) -> ProjectFile:
        """
        Export complete project state to a ProjectFile object.

        Args:
            path_mode: 'absolute' or 'relative' for file paths
            base_dir: Required if path_mode='relative'
            description: Optional project description

        Returns:
            ProjectFile object ready for serialization
        """
        datasets = []

        for name, meta in self._datasets.items():
            # Get loader params (stored in metadata)
            loader_params = meta.loader_params or {}
            loader_type = meta.loader_type or "File"

            # Get recipe for this dataset
            recipe = self._recipes.get(name, [])

            ds = DatasetProject(
                alias=name,
                loader_type=loader_type,
                loader_params=loader_params,
                recipe=recipe
            )
            datasets.append(ds)

        # Build project file
        project = ProjectFile(
            meta=ProjectMeta(description=description),
            path_config=PathConfig(mode="absolute"),
            datasets=datasets
        )

        # Convert paths if relative mode requested
        if path_mode == "relative" and base_dir:
            project = convert_paths_to_relative(project, base_dir)

        return project

    def save_project_to_file(
        self,
        file_path: str,
        path_mode: Literal["absolute", "relative"] = "absolute",
        base_dir: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Export and save project to a .pyquery file.

        Returns:
            Path to saved file
        """
        project = self.export_project(path_mode, base_dir, description)
        save_project(project, file_path)
        return file_path

    def import_project(
        self,
        project: ProjectFile,
        mode: Literal["replace", "merge"] = "replace",
        base_dir_override: Optional[str] = None
    ) -> ProjectImportResult:
        """
        Import a project, loading datasets and recipes.

        Args:
            project: ProjectFile to import
            mode: 'replace' clears existing, 'merge' adds non-conflicting
            base_dir_override: Override base_dir for relative path resolution

        Returns:
            ProjectImportResult with success status and warnings
        """
        result = ProjectImportResult()

        # Resolve paths to absolute if needed
        resolved = resolve_paths(project, base_dir_override)

        # Check for missing files
        missing = validate_dataset_files(resolved)

        # Clear existing if replace mode
        if mode == "replace":
            self.clear_all()

        for ds in resolved.datasets:
            # Skip if dataset exists in merge mode
            if mode == "merge" and ds.alias in self._datasets:
                result.datasets_skipped.append(ds.alias)
                result.warnings.append(f"Skipped '{ds.alias}': already exists")
                continue

            # Skip if files are missing
            if ds.alias in missing:
                result.datasets_skipped.append(ds.alias)
                result.warnings.append(
                    f"Skipped '{ds.alias}': missing files: {missing[ds.alias][:3]}"
                )
                continue

            # Attempt to load dataset
            try:
                loader_result = self.run_loader(
                    ds.loader_type, ds.loader_params)

                if loader_result:
                    lf, metadata = loader_result
                    self.add_dataset(
                        ds.alias, lf, metadata,
                        loader_type=ds.loader_type,
                        loader_params=ds.loader_params
                    )

                    # Load recipe
                    if ds.recipe:
                        self._recipes[ds.alias] = ds.recipe

                    result.datasets_loaded.append(ds.alias)
                else:
                    result.datasets_skipped.append(ds.alias)
                    result.warnings.append(
                        f"Failed to load '{ds.alias}': loader returned None")

            except Exception as e:
                result.datasets_skipped.append(ds.alias)
                result.errors.append(f"Error loading '{ds.alias}': {str(e)}")

        result.success = len(result.errors) == 0
        return result

    def load_project_from_file(
        self,
        file_path: str,
        mode: Literal["replace", "merge"] = "replace"
    ) -> ProjectImportResult:
        """
        Load a project from a .pyquery file.

        Args:
            file_path: Path to .pyquery file
            mode: 'replace' or 'merge'

        Returns:
            ProjectImportResult
        """
        project = load_project(file_path)

        # Use file's directory as base for relative path resolution
        file_dir = os.path.dirname(os.path.abspath(file_path))

        return self.import_project(project, mode, base_dir_override=file_dir)

    def clear_all(self) -> None:
        """Clear all datasets and recipes."""
        dataset_names = list(self._datasets.keys())
        for name in dataset_names:
            self.remove_dataset(name)
        self._recipes.clear()

    def get_dataset_for_export(self, name: str, recipe: Sequence[Union[dict, RecipeStep]],
                               project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> Optional[pl.LazyFrame]:
        """
        Get LazyFrame for export with recipe applied.
        Delegates to execution engine.
        """
        meta = self._datasets.get(name)
        if meta is None:
            return None

        ctx = self._get_datasets_dict_for_execution()

        # Use unified preparation logic in FULL mode
        return execution.prepare_view(
            meta, recipe, ctx, project_recipes, mode="full"
        )

    def materialize_dataset(self, dataset_name: str, new_name: str,
                            recipe: Optional[Sequence[Union[dict,
                                                            RecipeStep]]] = None,
                            project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> bool:
        """
        Materialize a dataset with optional recipe to a new dataset.
        Delegates to StorageManager.
        """
        return StorageManager.materialize_dataset(
            get_lf_func=self.get_dataset_for_export,
            add_dataset_func=self.add_dataset,
            dataset_name=dataset_name,
            new_name=new_name,
            recipe=recipe or [],
            project_recipes=project_recipes
        )

    def cleanup_staging(self, max_age_hours: int = 24):
        """Clean up stale staging files."""
        cleanup_staging_files(max_age_hours)

    def get_file_sheet_names(self, file_path: str) -> List[str]:
        """Get sheet names from an Excel file."""
        return get_excel_sheet_names(file_path)

    def get_file_table_names(self, file_path: str) -> List[str]:
        """Get table names from an Excel file."""
        return get_excel_table_names(file_path)

    def scan_encodings(self, files: List[str]) -> Dict[str, str]:
        """Detect non-utf8 encodings in list of files."""
        return batch_detect_encodings(files)

    def convert_encoding(self, file_path: str, source_encoding: str) -> str:
        """Convert a file to UTF-8."""
        return convert_file_to_utf8(file_path, source_encoding)

    def resolve_files(self, path: str, filters: Optional[List[FileFilter]] = None, limit: Optional[int] = None) -> List[str]:
        """Resolve a file path with filters."""
        return resolve_file_paths(path, filters, limit)

    def get_eda_view(self,
                     dataset_name: str,
                     recipe: Sequence[Union[dict, RecipeStep]],
                     project_recipes: Optional[Dict[str,
                                                    List[RecipeStep]]] = None,
                     strategy: str = "preview",
                     limit: int = 5000) -> Optional[pl.LazyFrame]:
        """
        Get a view for EDA with specific strategy.
        Strategies:
        - "preview": First file only (if individual), Limit N (Fastest).
        - "full_head": Full dataset, Limit N.
        - "full_sample": Full dataset, Sample N (Random).
        """
        # Hard cap for browser safety
        limit = min(limit, 100000)

        meta = self._datasets.get(dataset_name)
        if meta is None:
            return None

        datasets_dict = self._get_datasets_dict_for_execution()

        if strategy == "preview":
            return execution.prepare_view(
                meta, recipe, datasets_dict, project_recipes,
                mode="preview", preview_limit=limit)

        elif strategy == "full_head":
            # Get full processed view with collection limit
            return execution.prepare_view(
                meta, recipe, datasets_dict, project_recipes,
                mode="full", collection_limit=limit)

        elif strategy == "full_sample":
            # Get view limited to HARD_LIMIT at source
            HARD_LIMIT = 100000
            lf = execution.prepare_view(
                meta, recipe, datasets_dict, project_recipes,
                mode="full", collection_limit=HARD_LIMIT)

            if lf is not None:
                df = lf.collect()
                if len(df) <= limit:
                    return df.lazy()
                return df.sample(n=limit, seed=42).lazy()

        return None

    def get_dataset_names(self) -> List[str]:
        return list(self._datasets.keys())

    def infer_types(self, dataset_name: str, recipe: Sequence[Any], project_recipes: Optional[Dict[str, List[Any]]] = None, columns: Optional[List[str]] = None, sample_size: int = 1000) -> Dict[str, str]:
        """
        Infer data types for specific columns based on a sample of the transformed data.
        Delegates to TypeInferenceEngine.
        """
        base_lf = self.get_dataset(dataset_name)
        datasets_dict = self._get_datasets_dict_for_execution()

        return TypeInferenceEngine.infer_types(
            base_lf=base_lf,
            recipe=recipe,
            datasets_dict=datasets_dict,
            project_recipes=project_recipes,
            columns=columns,
            sample_size=sample_size
        )

    def auto_infer_dataset(self, dataset_name: str) -> Optional[RecipeStep]:
        """
        [NEW] Centralized Auto-Inference Logic.
        Detects type improvements and automatically updates the dataset's recipe 
        with a 'clean_cast' step at the beginning.
        """
        try:
            # 1. Run Inference
            # We run it on the raw dataset (empty recipe)
            raw_recipe = []
            inferred = self.infer_types(
                dataset_name, raw_recipe, sample_size=1000)

            if not inferred:
                return None

            # 2. Map to Actions
            TYPE_ACTION_MAP = {
                "Int64": "To Int",
                "Float64": "To Float",
                "Date": "To Date",
                "Datetime": "To Datetime",
                "Boolean": "To Boolean"
            }

            p = CleanCastParams()
            count = 0
            for col, dtype in inferred.items():
                action = TYPE_ACTION_MAP.get(dtype)
                if action:
                    p.changes.append(CastChange(col=col, action=action))
                    count += 1

            if count == 0:
                return None

            # 3. Create Step
            new_step = RecipeStep(
                id=str(uuid.uuid4()),
                type="clean_cast",
                label="Auto Clean Types",
                params=p.model_dump()
            )

            # 4. Update Recipe (Idempotent Insert/Replace)
            current_recipe = self.get_recipe(dataset_name)

            # Check for existing Auto Clean Types step
            existing_idx = None
            for i, step in enumerate(current_recipe):
                if isinstance(step, dict):  # Handle dict steps if any
                    if step.get("type") == "clean_cast" and step.get("label") == "Auto Clean Types":
                        existing_idx = i
                        break
                elif step.type == "clean_cast" and step.label == "Auto Clean Types":
                    existing_idx = i
                    break

            if existing_idx is not None:
                # Replace
                current_recipe[existing_idx] = new_step
            else:
                # Insert at Start
                current_recipe.insert(0, new_step)

            self.update_recipe(dataset_name, current_recipe)
            return new_step

        except Exception as e:
            print(f"Auto-Infer Logic Error: {e}")
            return None

    def get_dataset_schema(self, name: str, project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> Optional[pl.Schema]:
        lf = self.get_dataset(name)
        if lf is None:
            return None

        # Apply recipe if context provided
        if project_recipes and name in project_recipes:
            try:
                lf = self.apply_recipe(
                    lf, project_recipes[name], project_recipes)
            except:
                # Fallback to base schema
                pass

        try:
            return lf.collect_schema()
        except:
            return None

    def get_transformed_schema(self, name: str, recipe: Sequence[Union[dict, RecipeStep]]) -> Optional[pl.Schema]:
        base_lf = self.get_dataset(name)
        if base_lf is None:
            return None
        try:
            datasets_dict = self._get_datasets_dict_for_execution()
            transformed_lf = execution.apply_recipe(
                base_lf, recipe, datasets_dict)
            return transformed_lf.collect_schema()
        except:
            return None

    # ==========================
    # EXPORT JOBS
    # ==========================
    def get_loaders(self) -> List[PluginDef]:
        return list(self._loaders.values())

    def get_exporters(self) -> List[PluginDef]:
        return list(self._exporters.values())

    def run_loader(self, loader_name: str, params: Union[Dict[str, Any], BaseModel]) -> Optional[Tuple[pl.LazyFrame, Dict[str, Any]]]:
        loader = self._loaders.get(loader_name)
        if not loader:
            return None
        if not loader.func:
            return None
        try:
            if loader.params_model:
                if isinstance(params, BaseModel):
                    validated_params = params
                else:
                    validated_params = loader.params_model.model_validate(
                        params)
                result = loader.func(validated_params)
            else:
                result = loader.func(params)

            # Handle Legacy (LF only) vs New (LF, Metadata)
            if isinstance(result, tuple):
                return result
            else:
                return result, {}  # Default empty metadata

        except Exception as e:
            print(f"Loader Error: {e}")
            return None

    def start_export_job(self, dataset_name: str, recipe: Sequence[Union[dict, RecipeStep]],
                         exporter_name: str, params: Union[Dict[str, Any], BaseModel],
                         project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> str:

        # Check for Individual Export Mode
        export_individual = False
        if isinstance(params, dict):
            export_individual = params.get("export_individual", False)
        else:
            export_individual = getattr(params, "export_individual", False)

        precomputed: Any = None

        if export_individual:
            # 1. Get Base LFs List
            meta = self._datasets.get(dataset_name)
            if meta and meta.base_lfs:
                # 2. Apply Recipe to EACH
                ctx = self._get_datasets_dict_for_execution()
                lfs_list = []
                for lf in meta.base_lfs:
                    # Apply recipe to individual file LF
                    # Note: We share the same context (joined datasets are full)
                    processed = execution.apply_recipe(
                        lf, recipe, ctx, project_recipes)
                    lfs_list.append(processed)
                precomputed = lfs_list
            else:
                # Fallback if no list available
                precomputed = self.get_dataset_for_export(
                    dataset_name, recipe, project_recipes)
        else:
            # Standard Single Export
            precomputed = self.get_dataset_for_export(
                dataset_name, recipe, project_recipes)

        return self._job_manager.start_export_job(
            dataset_name,
            [],  # Empty recipe since we've already applied it
            exporter_name,
            params,
            project_recipes=None,
            precomputed_lf=precomputed
        )

    def get_job_status(self, job_id: str) -> Optional[JobInfo]:
        return self._job_manager.get_job_status(job_id)

    # ==========================
    # SQL ENGINE
    # ==========================
    def execute_sql(self, query: str, project_recipes: Optional[Dict[str, List[RecipeStep]]] = None,
                    preview: bool = False, preview_limit: int = 1000,
                    collection_limit: Optional[int] = None) -> pl.LazyFrame:
        """
        Executes a SQL query against loaded datasets.
        Delegates to execution engine.
        """
        # 1. Prepare all datasets views
        final_datasets = {}
        raw_context = self._get_datasets_dict_for_execution()
        mode = "preview" if preview else "full"

        for name, meta in self._datasets.items():
            recipe = project_recipes.get(name, []) if project_recipes else []

            # Use unified preparation logic
            view = execution.prepare_view(
                meta, recipe, raw_context, project_recipes,
                mode=mode, preview_limit=preview_limit,
                collection_limit=collection_limit
            )

            if view is not None:
                final_datasets[name] = view

        # 2. Execute SQL
        return execution.execute_sql(query, final_datasets, project_recipes=None)

    def execute_sql_preview(self, query: str, limit: int = 1000,
                            project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.DataFrame:
        """
        Executes SQL query on a sampled subset of data (Top N rows) for fast preview.
        Returns an eager DataFrame.
        """
        # Reuse execute_sql with preview=True (uses first file + input limit)
        lf = self.execute_sql(query, project_recipes,
                              preview=True, preview_limit=limit)
        return lf.limit(limit).collect()

    def start_sql_export_job(self, query: str, exporter_name: str,
                             params: Union[Dict[str, Any], BaseModel],
                             project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> str:
        """Starts an export job based on a SQL query."""
        try:
            # Create Context with Recipes Applied using FULL mode (preview=False)
            lf = self.execute_sql(query, project_recipes, preview=False)

            # We pass empty recipe/dataset_name effectively, as precomputed_lf overrides them
            return self._job_manager.start_export_job(
                dataset_name="SQL_RESULT",
                recipe=[],
                exporter_name=exporter_name,
                params=params,
                project_recipes=None,
                precomputed_lf=lf
            )
        except Exception as e:
            raise ValueError(f"SQL Error: {e}")

    # ==========================
    # TRANSFORMATION ENGINE
    # ==========================
    def apply_step(self, lf: pl.LazyFrame, step: RecipeStep,
                   project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
        datasets_dict = self._get_datasets_dict_for_execution()
        return execution.apply_step(lf, step, datasets_dict, project_recipes)

    def apply_recipe(self, lf: pl.LazyFrame, recipe: Sequence[Union[dict, RecipeStep]],
                     project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
        datasets_dict = self._get_datasets_dict_for_execution()
        return execution.apply_recipe(lf, recipe, datasets_dict, project_recipes)

    def get_preview(self, dataset_name: str, recipe: Sequence[Union[dict, RecipeStep]],
                    limit: int = 1000, project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> Optional[pl.DataFrame]:
        meta = self._datasets.get(dataset_name)
        if meta is None:
            return None

        ctx = self._get_datasets_dict_for_execution()

        # Use unified preparation logic in PREVIEW mode
        lf = execution.prepare_view(
            meta, recipe, ctx, project_recipes,
            mode="preview", preview_limit=limit
        )

        if lf is None:
            return None

        return lf.collect()

    def get_profile(self, dataset_name: str, recipe: Sequence[Union[dict, RecipeStep]]) -> Optional[Dict[str, Any]]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None:
            return None
        try:
            datasets_dict = self._get_datasets_dict_for_execution()
            return execution.get_profile(base_lf, recipe, datasets_dict)
        except Exception as e:
            return {"error": str(e)}

    def analyze_join_overlap(self,
                             left_dataset: str,
                             left_recipe: Sequence[Union[dict, RecipeStep]],
                             right_dataset: str,
                             right_recipe: Sequence[Union[dict, RecipeStep]],
                             left_on: List[str],
                             right_on: List[str]) -> Dict[str, Any]:
        """
        Analyzes join overlap using standardized get_preview logic.
        Delegates to JoinAnalyzer.
        """
        # 1. Get Previews (Eager DataFrames)
        l_df = self.get_preview(left_dataset, left_recipe)
        r_df = self.get_preview(right_dataset, right_recipe)

        return JoinAnalyzer.analyze_overlap(
            l_df, r_df, left_on, right_on
        )
