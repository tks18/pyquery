import threading
import uuid
import time
import os
from typing import Dict, Optional, List, Union, Callable, Any
from pydantic import BaseModel
import polars as pl

from pyquery_polars.core.models import JobInfo, RecipeStep, PluginDef


class JobManager:
    def __init__(self,
                 get_dataset_func: Callable[[str], Optional[pl.LazyFrame]],
                 apply_recipe_func: Callable[[pl.LazyFrame, List[Any], Optional[Dict]], pl.LazyFrame],
                 exporters: Dict[str, PluginDef]):
        self._jobs: Dict[str, JobInfo] = {}
        self._get_dataset = get_dataset_func
        self._apply_recipe = apply_recipe_func
        self._exporters = exporters

    def start_export_job(self, dataset_name: str, recipe: List[Union[dict, RecipeStep]],
                         exporter_name: str, params: Union[Dict[str, Any], BaseModel],
                         project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> str:
        job_id = str(uuid.uuid4())
        exporter = self._exporters.get(exporter_name)
        if not exporter:
            raise ValueError(f"Unknown exporter: {exporter_name}")

        if not exporter.func:
            raise ValueError(f"Exporter {exporter_name} has no function")

        validated_params = params
        if exporter.params_model:
            try:
                if not isinstance(params, BaseModel):
                    validated_params = exporter.params_model.model_validate(
                        params)
            except Exception as e:
                raise ValueError(f"Invalid export configuration: {e}")

        # Safe Path extraction
        path = "unknown"
        if hasattr(validated_params, 'path'):
            path = getattr(validated_params, 'path')
        elif isinstance(params, dict):
            path = params.get('path', 'unknown')

        job_info = JobInfo(
            job_id=job_id,
            status="RUNNING",
            file=path
        )
        self._jobs[job_id] = job_info

        t = threading.Thread(target=self._internal_export_worker, args=(
            job_id, dataset_name, recipe, exporter_name, validated_params, project_recipes))
        t.start()
        return job_id

    def _internal_export_worker(self, job_id, dataset_name, recipe, exporter_name, params, project_recipes=None):
        start_time = time.time()
        try:
            base_lf = self._get_dataset(dataset_name)
            if base_lf is None:
                raise ValueError("Dataset not found")

            final_lf = self._apply_recipe(
                base_lf, recipe, project_recipes)

            exporter = self._exporters.get(exporter_name)
            if exporter and exporter.func:
                exporter.func(final_lf, params)

            end_time = time.time()
            duration = end_time - start_time

            info = self._jobs[job_id]
            info.duration = duration
            info.status = "COMPLETED"

            # Size check
            path = None
            if hasattr(params, 'path'):
                path = getattr(params, 'path')
            elif isinstance(params, dict):
                path = params.get('path')

            if path and os.path.exists(path):
                size_bytes = os.path.getsize(path)
                info.size_str = f"{size_bytes / 1024 / 1024:.2f} MB"

        except Exception as e:
            if job_id in self._jobs:
                self._jobs[job_id].duration = time.time() - start_time
                self._jobs[job_id].status = "FAILED"
                self._jobs[job_id].error = str(e)

    def get_job_status(self, job_id: str) -> Optional[JobInfo]:
        return self._jobs.get(job_id)
