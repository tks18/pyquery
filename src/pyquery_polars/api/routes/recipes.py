from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Union, cast
from pydantic import BaseModel
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.api.dependencies import get_engine
from pyquery_polars.core.models import RecipeStep
import pyquery_polars.api.db as db

router = APIRouter()


class PreviewRequest(BaseModel):
    dataset: str
    steps: List[Dict[str, Any]]  # Raw dicts that map to RecipeStep
    limit: int = 50


class ExportRequest(BaseModel):
    dataset: str
    steps: List[Dict[str, Any]]
    exporter: str
    params: Dict[str, Any]


@router.post("/preview")
def preview_recipe(req: PreviewRequest, engine: PyQueryEngine = Depends(get_engine)):
    """Apply a recipe and return the first N rows."""
    try:
        # validate steps
        # Engine.apply_recipe handles dict->RecipeStep conversion,
        # but passing dicts is risky if keys mismatch.
        # Let's trust the engine's parsing logic for now to keep API thin.

        # Cast to satisfy list invariance
        from typing import cast, Union
        from pyquery_polars.core.models import RecipeStep

        steps = cast(List[Union[Dict[str, Any], RecipeStep]], req.steps)
        df = engine.get_preview(req.dataset, steps, req.limit)
        if df is None:
            raise HTTPException(
                status_code=404, detail="Dataset not found or error")

        # serialize to json-friendly dict
        return df.to_dicts()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export")
def start_export(req: ExportRequest,
                 background_tasks: BackgroundTasks,
                 engine: PyQueryEngine = Depends(get_engine)):
    """Start an asynchronous export job with persistence."""
    try:
        steps = cast(List[Union[Dict[str, Any], RecipeStep]], req.steps)

        # 1. Start on Engine
        job_id = engine.start_export_job(
            dataset_name=req.dataset,
            recipe=steps,
            exporter_name=req.exporter,
            params=req.params
        )

        # 2. Extract path for DB
        path = "unknown"
        if isinstance(req.params, dict):
            path = req.params.get('path', 'unknown')
        # Pydantic case handled by engine call, but here req.params is dict usually

        # 3. Create Persistent Record in API DB
        db.create_job(job_id, req.dataset, req.exporter, path)

        # 4. Spawn Background Monitor
        background_tasks.add_task(monitor_job, job_id, engine)

        return {"job_id": job_id, "status": "RUNNING"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def monitor_job(job_id: str, engine: PyQueryEngine):
    """Poll engine job status and update API DB on completion."""
    import time
    while True:
        info = engine.get_job_status(job_id)
        if not info:
            # Job vanished from engine? Mark failed or unknown
            # If engine restarted, this loop wouldn't be running anyway.
            # This means engine deleted it or logic error.
            db.update_job_status(
                job_id, "FAILED", error="Lost contact with engine job")
            break

        if info.status in ["COMPLETED", "FAILED", "CANCELLED"]:
            # Sync final state
            db.update_job_status(job_id, info.status,
                                 info.duration, info.error, info.size_str)
            break

        # Still RUNNING
        time.sleep(1.0)


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, engine: PyQueryEngine = Depends(get_engine)):
    """
    Check status using Engine (Real-time) + DB (History).
    """
    # 1. Ask Engine (Real-time truth)
    eng_info = engine.get_job_status(job_id)

    if eng_info:
        # Sync latest generic status to DB (optional optimization to keep DB fresh)
        # We rely on monitor usually, but this doesn't hurt.
        return eng_info

    # 2. Fallback to API DB (History / Persistence)
    db_job = db.get_job(job_id)
    if db_job:
        # Convert dict to JobInfo compatible response
        return {
            "job_id": db_job['job_id'],
            "status": db_job['status'],
            "duration": db_job['duration'],
            "error": db_job['error'],
            "file": db_job['file_path'],
            "size_str": db_job['file_size']
        }

    raise HTTPException(status_code=404, detail="Job not found")


@router.get("/jobs")
def list_jobs(limit: int = 50):
    """List historical jobs from API DB."""
    return db.list_jobs(limit)


@router.post("/validate")
def validate_recipe(req: PreviewRequest, engine: PyQueryEngine = Depends(get_engine)):
    """
    Validate a recipe structure and parameters.
    """
    try:
        from typing import cast, Union
        from pyquery_polars.core.models import RecipeStep

        steps = cast(List[Union[Dict[str, Any], RecipeStep]], req.steps)
        # We rely on Pydantic models in StepRegistry for validation
        # Since Preview/Apply already does this implicitly, we can simulation it
        # or just return "valid" if Pydantic didn't error during request parsing?
        # Actually Pydantic validates the 'PreviewRequest' body, but 'steps' is Any/Dict.
        # We need to manually validate each step against its registry model.

        from pyquery_polars.core.registry import StepRegistry

        errors = []
        for i, s in enumerate(steps):
            step_dict = s if isinstance(s, dict) else s.model_dump()
            step_type = step_dict.get("type")
            if not step_type:
                errors.append(f"Step {i}: Missing 'type'")
                continue

            def_obj = StepRegistry.get(step_type)
            if not def_obj:
                errors.append(f"Step {i}: Unknown step type '{step_type}'")
                continue

            if def_obj.params_model:
                try:
                    def_obj.params_model.model_validate(
                        step_dict.get("params", {}))
                except Exception as e:
                    errors.append(f"Step {i} ({step_type}): {str(e)}")

        if errors:
            return {"valid": False, "errors": errors}

        return {"valid": True, "errors": []}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/schema")
def get_schema(req: PreviewRequest, engine: PyQueryEngine = Depends(get_engine)):
    """
    Predict the output schema of a recipe.
    """
    try:
        from typing import cast, Union
        from pyquery_polars.core.models import RecipeStep

        steps = cast(List[Union[Dict[str, Any], RecipeStep]], req.steps)
        schema = engine.get_transformed_schema(req.dataset, steps)

        if schema is None:
            raise HTTPException(
                status_code=404, detail="Dataset not found or Schema inference failed")

        # Convert schema to friendly dict
        return {k: str(v) for k, v in schema.items()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
