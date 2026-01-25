"""
JobManager

Manages background export jobs (async file exports with progress tracking).
"""
from typing import Dict, Optional, List, Union, Callable, Any, Sequence, TYPE_CHECKING
from pydantic import BaseModel

import threading
import uuid
import time
import os
import polars as pl

from pyquery_polars.core.models import JobInfo, RecipeStep
from pyquery_polars.backend.processing import ProcessingManager
from pyquery_polars.backend.io import IOManager


class JobManager:
    """
    Manages export jobs.

    Dependencies:
    - ProcessingManager: To prepare datasets/views
    - IOManager: To get exporters

    This class handles:
    - Starting background export jobs
    - Tracking job status (RUNNING, COMPLETED, FAILED)
    - Reporting job progress and results
    """

    def __init__(
        self,
        processing_manager: "ProcessingManager",
        io_manager: "IOManager"
    ):
        self._jobs: Dict[str, JobInfo] = {}
        self._processing = processing_manager
        self._io = io_manager

    def start_export_job(
        self,
        dataset_name: str,
        recipe: Sequence[Union[dict, RecipeStep]],
        exporter_name: str,
        params: Union[Dict[str, Any], BaseModel],
        project_recipes: Optional[Dict[str, List[RecipeStep]]] = None,
        precomputed_lf: Optional[Union[pl.LazyFrame,
                                       List[pl.LazyFrame]]] = None
    ) -> str:
        """Start a background export job. Returns job_id."""
        job_id = str(uuid.uuid4())

        # Resolve exporter via IOManager
        exporter = self._io.get_exporter(exporter_name)
        if not exporter:
            raise ValueError(f"Unknown exporter: {exporter_name}")

        if not exporter.func:
            raise ValueError(f"Exporter {exporter_name} has no function")

        validated_params = params
        if exporter.params_model:
            try:
                if not isinstance(params, BaseModel):
                    # Try validation if model available
                    if isinstance(params, dict):
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

        t = threading.Thread(
            target=self._internal_export_worker,
            args=(job_id, dataset_name, recipe, exporter_name,
                  validated_params, project_recipes, precomputed_lf)
        )
        t.start()
        return job_id

    def _internal_export_worker(
        self,
        job_id,
        dataset_name,
        recipe,
        exporter_name,
        params,
        project_recipes=None,
        precomputed_lf=None
    ):
        """Internal worker thread for export jobs."""
        start_time = time.time()
        try:
            if precomputed_lf is not None:
                final_lf = precomputed_lf
            else:
                # Use ProcessingManager to get view
                meta = self._processing._datasets.get_metadata(dataset_name)
                if not meta:
                    raise ValueError("Dataset not found")

                final_lf = self._processing.prepare_view(
                    meta, recipe, mode="full"
                )

            # Re-fetch exporter in worker (safe)
            exporter = self._io.get_exporter(exporter_name)
            export_result = {}
            if exporter and exporter.func:
                # Exporter returns Dict with status/size_str
                res = exporter.func(final_lf, params)
                if isinstance(res, dict):
                    export_result = res

            end_time = time.time()
            duration = end_time - start_time

            info = self._jobs[job_id]
            info.duration = duration

            # Status handling
            if export_result.get('status') == 'Done':
                info.status = "COMPLETED"
            elif str(export_result.get('status', '')).startswith('Error'):
                info.status = "FAILED"
                info.error = export_result.get('status')
            else:
                info.status = "COMPLETED"

            # Size check
            if export_result.get('size_str'):
                info.size_str = str(export_result.get('size_str'))
            else:
                # Fallback to single file check
                path = None
                if hasattr(params, 'path'):
                    path = getattr(params, 'path')
                elif isinstance(params, dict):
                    path = params.get('path')

                if path and os.path.exists(path):
                    size_bytes = os.path.getsize(path)
                    info.size_str = f"{size_bytes / 1024 / 1024:.2f} MB"

            # File Details
            if export_result.get('file_details'):
                info.file_details = export_result.get('file_details')

        except Exception as e:
            if job_id in self._jobs:
                self._jobs[job_id].duration = time.time() - start_time
                self._jobs[job_id].status = "FAILED"
                self._jobs[job_id].error = str(e)

    def get_job_status(self, job_id: str) -> Optional[JobInfo]:
        """Get the status of a job by its ID."""
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> Dict[str, JobInfo]:
        """Get all jobs (for monitoring)."""
        return self._jobs.copy()
