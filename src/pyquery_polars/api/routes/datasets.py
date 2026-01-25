from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.api.dependencies import get_engine

router = APIRouter()


class LoadRequest(BaseModel):
    loader: str
    alias: str
    params: Dict[str, Any]


class DatasetSummary(BaseModel):
    name: str
    rows: Optional[int] = None
    cols: Optional[int] = None
    dtypes: Dict[str, str]


@router.get("/", response_model=List[str])
def get_datasets(engine: PyQueryEngine = Depends(get_engine)):
    """List all active dataset names."""
    return engine.datasets.list_names()


@router.post("/load")
def load_dataset(req: LoadRequest, engine: PyQueryEngine = Depends(get_engine)):
    """Load a dataset using a specific loader."""
    # Run the loader
    result = engine.io.run_loader(req.loader, req.params)

    if result is None:
        raise HTTPException(
            status_code=400, detail="Failed to load dataset. Check params.")

    # Extract LazyFrame and metadata
    lf, metadata = result if isinstance(result, tuple) else (result, {})

    # Register in engine
    engine.datasets.add(req.alias, lf, metadata=metadata)
    return {"status": "loaded", "name": req.alias}


@router.get("/{name}", response_model=DatasetSummary)
def get_dataset_info(name: str, engine: PyQueryEngine = Depends(get_engine)):
    """Get schema and basic info for a dataset."""
    lf = engine.datasets.get(name)
    if lf is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        # We need to collect schema (lightweight)
        schema = lf.collect_schema()

        # Renamed to avoid pydantic conflict
        dtypes_map = {k: str(v) for k, v in schema.items()}

        return DatasetSummary(
            name=name,
            dtypes=dtypes_map
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}")
def unload_dataset(name: str, engine: PyQueryEngine = Depends(get_engine)):
    """Unload a dataset from memory."""
    if engine.datasets.get(name) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    engine.datasets.remove(name)
    return {"status": "removed", "name": name}
