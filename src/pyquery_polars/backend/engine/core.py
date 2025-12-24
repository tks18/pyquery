from typing import Any, Dict, List, Optional, Union
import polars as pl
import os
from pydantic import BaseModel

# Import Utils
from pyquery_polars.backend.io_plugins.standard import ALL_LOADERS, ALL_EXPORTERS
from pyquery_polars.core.models import JobInfo, PluginDef, RecipeStep
from pyquery_polars.core.registry import StepRegistry

# Modules
from .registry import register_all_steps
from .jobs import JobManager
from . import execution


class PyQueryEngine:
    def __init__(self):
        self._datasets: Dict[str, pl.LazyFrame] = {}  # In-memory storage

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
        if source_path:
            if not hasattr(self, '_dataset_metadata'):
                self._dataset_metadata = {}
            self._dataset_metadata[name] = {"source_path": source_path}

    def remove_dataset(self, name: str):
        if name in self._datasets:
            del self._datasets[name]
        if hasattr(self, '_dataset_metadata') and name in self._dataset_metadata:
            del self._dataset_metadata[name]

    def get_dataset(self, name: str) -> Optional[pl.LazyFrame]:
        return self._datasets.get(name)

    def get_dataset_metadata(self, name: str) -> Dict[str, Any]:
        if not hasattr(self, '_dataset_metadata'):
            return {}
        return self._dataset_metadata.get(name, {})

    def get_file_sheet_names(self, file_path: str) -> List[str]:
        """Get sheet names from an Excel file."""
        from pyquery_polars.backend.utils.io import get_excel_sheet_names
        return get_excel_sheet_names(file_path)

    def get_dataset_names(self) -> List[str]:
        return list(self._datasets.keys())

    def get_dataset_schema(self, name: str) -> Optional[pl.Schema]:
        lf = self.get_dataset(name)
        if lf is None:
            return None
        try:
            return lf.collect_schema()
        except:
            return None

    def get_transformed_schema(self, name: str, recipe: List[Union[dict, RecipeStep]]) -> Optional[pl.Schema]:
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

    def run_loader(self, loader_name: str, params: Union[Dict[str, Any], BaseModel]) -> Union[Optional[pl.LazyFrame], tuple]:
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

    def start_export_job(self, dataset_name: str, recipe: List[Union[dict, RecipeStep]],
                         exporter_name: str, params: Union[Dict[str, Any], BaseModel],
                         project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> str:
        return self._job_manager.start_export_job(dataset_name, recipe, exporter_name, params, project_recipes)

    def get_job_status(self, job_id: str) -> Optional[JobInfo]:
        return self._job_manager.get_job_status(job_id)

    # ==========================
    # TRANSFORMATION ENGINE
    # ==========================
    def apply_step(self, lf: pl.LazyFrame, step: RecipeStep,
                   project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
        return execution.apply_step(lf, step, self._datasets, project_recipes)

    def apply_recipe(self, lf: pl.LazyFrame, recipe: List[Union[dict, RecipeStep]],
                     project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
        return execution.apply_recipe(lf, recipe, self._datasets, project_recipes)

    def get_preview(self, dataset_name: str, recipe: List[Union[dict, RecipeStep]],
                    limit: int = 50, project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> Optional[pl.DataFrame]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None:
            return None
        return execution.get_preview(base_lf, recipe, self._datasets, project_recipes)

    def get_profile(self, dataset_name: str, recipe: List[Union[dict, RecipeStep]]) -> Optional[Dict[str, Any]]:
        base_lf = self.get_dataset(dataset_name)
        if base_lf is None:
            return None
        try:
            return execution.get_profile(base_lf, recipe, self._datasets)
        except Exception as e:
            return {"error": str(e)}
