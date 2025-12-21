from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Union, cast
from pydantic import BaseModel
from pyquery.backend.engine import PyQueryEngine
from pyquery.api.dependencies import get_engine
from pyquery.core.models import RecipeStep

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
        from pyquery.core.models import RecipeStep

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
def start_export(req: ExportRequest, engine: PyQueryEngine = Depends(get_engine)):
    """Start an asynchronous export job."""
    try:
        steps = cast(List[Union[Dict[str, Any], RecipeStep]], req.steps)
        job_id = engine.start_export_job(
            dataset_name=req.dataset,
            recipe=steps,
            exporter_name=req.exporter,
            params=req.params
        )
        return {"job_id": job_id, "status": "RUNNING"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, engine: PyQueryEngine = Depends(get_engine)):
    """Check the status of a background job."""
    info = engine.get_job_status(job_id)
    if not info:
        raise HTTPException(status_code=404, detail="Job not found")

    return info
