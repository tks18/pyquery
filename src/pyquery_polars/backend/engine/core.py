from typing import Any, Dict, List, Optional, Union, Sequence, Tuple
import polars as pl
import os
from pydantic import BaseModel

# Import Utils
from pyquery_polars.backend.io_plugins.standard import ALL_LOADERS, ALL_EXPORTERS
from pyquery_polars.core.models import JobInfo, PluginDef, RecipeStep
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.backend.utils.io import get_staging_dir, get_excel_sheet_names

# Modules
from .registry import register_all_steps
from .jobs import JobManager
from . import execution
from ..analysis import AnalysisEngine


class PyQueryEngine:
    def __init__(self):
        self._datasets: Dict[str, pl.LazyFrame] = {}  # In-memory storage
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
            return execution.apply_recipe(lf, recipe, self._datasets, project_recipes)

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
    def add_dataset(self, name: str, lf: pl.LazyFrame, source_path: Optional[str] = None):
        self._datasets[name] = lf
        try:
            self._sql_context.register(name, lf)
        except Exception as e:
            print(f"SQL Registration Warning: {e}")
        if source_path:
            if not hasattr(self, '_dataset_metadata'):
                self._dataset_metadata = {}
            self._dataset_metadata[name] = {"source_path": source_path}

    def remove_dataset(self, name: str):
        if name in self._datasets:
            del self._datasets[name]
            try:
                self._sql_context.unregister(name)
            except:
                pass
        if hasattr(self, '_dataset_metadata') and name in self._dataset_metadata:
            del self._dataset_metadata[name]

    def get_dataset(self, name: str) -> Optional[pl.LazyFrame]:
        return self._datasets.get(name)

    def get_dataset_metadata(self, name: str) -> Dict[str, Any]:
        if not hasattr(self, '_dataset_metadata'):
            return {}
        return self._dataset_metadata.get(name, {})

    def materialize_dataset(self, name: str, lf_or_df: Union[pl.LazyFrame, pl.DataFrame], reference_name: Optional[str] = None) -> bool:
        """
        Materializes a DataFrame to the centralized staging folder and registers it as a new dataset.
        """
        try:
            # 1. Get Centralized Staging Dir
            staging_dir = get_staging_dir()

            # 2. Sanitize Name (Basic)
            safe_name = "".join(
                x for x in name if x.isalnum() or x in " _-").strip()
            if not safe_name:
                raise ValueError("Invalid dataset name")

            file_path = os.path.join(staging_dir, f"{safe_name}.parquet")

            # 3. Write
            if isinstance(lf_or_df, pl.LazyFrame):
                lf_or_df.sink_parquet(file_path)
            else:
                lf_or_df.write_parquet(file_path)

            # 4. Register
            new_lf = pl.scan_parquet(file_path)
            self.add_dataset(safe_name, new_lf, source_path=file_path)
            return True
        except Exception as e:
            print(f"Materialization Error: {e}")
            return False

    def get_file_sheet_names(self, file_path: str) -> List[str]:
        """Get sheet names from an Excel file."""
        return get_excel_sheet_names(file_path)

    def get_dataset_names(self) -> List[str]:
        return list(self._datasets.keys())

    def infer_types(self, dataset_name: str, recipe: Sequence[Any], project_recipes: Optional[Dict[str, List[Any]]] = None, columns: Optional[List[str]] = None, sample_size: int = 1000) -> Dict[str, str]:
        """
        Infer data types for specific columns based on a sample of the transformed data.
        Returns a dictionary mapping column names to suggested PyQuery types (e.g. 'Int64', 'Date').
        """
        # 1. Get base dataset
        lf = self.get_dataset(dataset_name)
        if lf is None:
            return {}
            
        # 2. Apply current recipe to get state
        try:
             transformed_lf = execution.apply_recipe(lf, recipe, self._datasets, project_recipes)
        except Exception as e:
             # If pipeline breaks, fall back to base
             transformed_lf = lf

        # 3. Slice Sample
        try:
            sample_df = transformed_lf.slice(0, sample_size).collect()
        except Exception as e:
            return {}

        # 4. Determine columns to check
        if not columns:
            # Default: Inspect all String columns
            columns = [c for c, t in sample_df.schema.items() if t == pl.String]
        
        inferred = {}
        
        for col in columns:
            if col not in sample_df.columns:
                continue
                
            s = sample_df[col]
            # Skip if empty
            if s.len() == 0:
                continue
                
            # Only infer for strings (safest for now)
            if s.dtype != pl.String:
                continue
            
            # Check non-null values only
            # If a column is mixed (valid ints + garbage), strict=False will nullify garbage.
            # INFERENCE RULE: If > 90% of non-nulls can be cast, suggest it?
            # Or STRICT: All non-nulls must be castable.
            # Let's go with STRICT for safety, or High Confidence (>99%).
            
            non_null_s = s.drop_nulls()
            if non_null_s.len() == 0:
                continue
            
            count = non_null_s.len()

            # Helper to check success rate
            def check_cast(dtype):
                try:
                    casted = non_null_s.cast(dtype, strict=False)
                    # Count nulls that weren't null before (failure to cast)
                    new_nulls = casted.null_count()
                    return new_nulls == 0 # Strict success
                except:
                    return False

            # 1. Boolean (common strings)
            # Custom check because 'True'/'False' might be case insensitive
            try:
                upper = non_null_s.str.to_uppercase()
                is_bool = upper.is_in(["TRUE", "FALSE", "T", "F", "1", "0", "YES", "NO"]).all()
                if is_bool:
                    inferred[col] = "Boolean"
                    continue
            except:
                pass

            # 2. Int64
            if check_cast(pl.Int64):
                inferred[col] = "Int64"
                continue

            # 3. Float64
            if check_cast(pl.Float64):
                inferred[col] = "Float64"
                continue
                
            # 4. Date (ISO)
            if check_cast(pl.Date):
                inferred[col] = "Date"
                continue

             # 5. Datetime (ISO)
            if check_cast(pl.Datetime):
                inferred[col] = "Datetime"
                continue
                
        return inferred

    def get_dataset_schema(self, name: str, project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> Optional[pl.Schema]:
        lf = self.get_dataset(name)
        if lf is None:
            return None
            
        # Apply recipe if context provided
        if project_recipes and name in project_recipes:
            try:
                lf = self.apply_recipe(lf, project_recipes[name], project_recipes)
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
            transformed_lf = execution.apply_recipe(
                base_lf, recipe, self._datasets)
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
        return self._job_manager.start_export_job(dataset_name, recipe, exporter_name, params, project_recipes)

    def get_job_status(self, job_id: str) -> Optional[JobInfo]:
        return self._job_manager.get_job_status(job_id)

    # ==========================
    # SQL ENGINE
    # ==========================
    def execute_sql(self, query: str, project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
        """Executes a SQL query against loaded datasets."""
        # If recipes provided, build temp context
        if project_recipes:
             ctx = pl.SQLContext()
             for name, lf in self._datasets.items():
                 target_lf = lf
                 if name in project_recipes:
                     try:
                        target_lf = self.apply_recipe(lf, project_recipes[name], project_recipes)
                     except:
                        pass
                 ctx.register(name, target_lf)
             return ctx.execute(query, eager=False)
        
        # Default global context
        return self._sql_context.execute(query, eager=False)

    def execute_sql_preview(self, query: str, limit: int = 1000, 
                            project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.DataFrame:
        """
        Executes SQL query on a sampled subset of data (Top N rows) for fast preview.
        Returns an eager DataFrame.
        """
        temp_ctx = pl.SQLContext()
        for name, lf in self._datasets.items():
            try:
                # Apply Recipe
                target_lf = lf
                if project_recipes and name in project_recipes:
                    target_lf = self.apply_recipe(lf, project_recipes[name], project_recipes)
                
                temp_ctx.register(name, target_lf.limit(limit))
            except:
                pass
        return temp_ctx.execute(query, eager=True)

    def start_sql_export_job(self, query: str, exporter_name: str,
                             params: Union[Dict[str, Any], BaseModel],
                             project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> str:
        """Starts an export job based on a SQL query."""
        try:
            # Create Context with Recipes Applied
            ctx = pl.SQLContext()
            for name, lf in self._datasets.items():
                 target_lf = lf
                 if project_recipes and name in project_recipes:
                     target_lf = self.apply_recipe(lf, project_recipes[name], project_recipes)
                 ctx.register(name, target_lf)
            
            lf = ctx.execute(query, eager=False)
            
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
        return execution.apply_step(lf, step, self._datasets, project_recipes)

    def apply_recipe(self, lf: pl.LazyFrame, recipe: Sequence[Union[dict, RecipeStep]],
                     project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
        return execution.apply_recipe(lf, recipe, self._datasets, project_recipes)

    def get_preview(self, dataset_name: str, recipe: Sequence[Union[dict, RecipeStep]],
                    limit: int = 50, project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> Optional[pl.DataFrame]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None:
            return None
        return execution.get_preview(base_lf, recipe, self._datasets, project_recipes)

    def get_profile(self, dataset_name: str, recipe: Sequence[Union[dict, RecipeStep]]) -> Optional[Dict[str, Any]]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None:
            return None
        try:
            return execution.get_profile(base_lf, recipe, self._datasets)
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
        """
        # 1. Get Previews (Eager DataFrames)
        # We reuse the robust get_preview method for consistency
        l_df = self.get_preview(left_dataset, left_recipe)
        r_df = self.get_preview(right_dataset, right_recipe)
        
        if l_df is None:
             return {"error": f"Left dataset {left_dataset} preview failed."}
        if r_df is None:
             return {"error": f"Right dataset {right_dataset} preview failed."}

        # 2. Compute Counts
        try:
            l_count = len(l_df)
            r_count = len(r_df)
            
            if l_count == 0 or r_count == 0:
                 return {"l_count": l_count, "r_count": r_count, "match_count": 0}

            # 3. Join (Eager)
            match_count = len(l_df.join(r_df, left_on=left_on, right_on=right_on, how="inner"))
            
            return {
                "l_count": l_count,
                "r_count": r_count,
                "match_count": match_count
            }
        except Exception as e:
            return {"error": str(e)}
