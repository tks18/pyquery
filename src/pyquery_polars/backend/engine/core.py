from typing import Any, Dict, List, Optional, Union, Sequence, Tuple
import polars as pl
import os
from pydantic import BaseModel

# Import Utils
from pyquery_polars.backend.io.plugins import ALL_LOADERS, ALL_EXPORTERS
from pyquery_polars.core.models import JobInfo, PluginDef, RecipeStep, DatasetMetadata
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.backend.io.files import get_staging_dir, get_excel_sheet_names, cleanup_staging_files, resolve_file_paths, batch_detect_encodings, convert_file_to_utf8
from pyquery_polars.core.io_params import FileFilter

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
                    metadata: Optional[Dict[str, Any]] = None):
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
            file_count=metadata.get("file_count", 1)
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

        # Register with SQL context
        try:
            self._sql_context.register(name, concat_lf)
        except Exception as e:
            print(f"SQL Registration Warning: {e}")

    def remove_dataset(self, name: str):
        if name in self._datasets:
            del self._datasets[name]
            try:
                self._sql_context.unregister(name)
            except:
                pass

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
        return {
            "source_path": meta.source_path,
            "input_type": meta.input_type,
            "input_format": meta.input_format,
            "process_individual": meta.process_individual,
            "file_list": meta.file_list,
            "file_count": meta.file_count
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
