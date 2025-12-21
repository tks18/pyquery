from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from pyquery.backend.engine import PyQueryEngine
from pyquery.api.dependencies import get_engine
from pyquery.core.registry import StepRegistry

router = APIRouter()


@router.get("/transforms")
def list_transforms(engine: PyQueryEngine = Depends(get_engine)):
    """
    List all available transformation steps and their schema.
    """
    steps = StepRegistry.get_all()
    result = []

    for step_type, def_obj in steps.items():
        # Generate JSON Schema for the Pydantic params model
        schema = def_obj.params_model.model_json_schema() if def_obj.params_model else {}

        result.append({
            "type": step_type,
            "label": def_obj.metadata.label,
            "group": def_obj.metadata.group,
            "schema": schema
        })

    return result


@router.get("/loaders")
def list_loaders(engine: PyQueryEngine = Depends(get_engine)):
    """
    List available data loaders.
    """
    loaders = engine.get_loaders()
    result = []

    for l in loaders:
        # We don't have ui_schema anymore, but we have params_model
        schema = l.params_model.model_json_schema() if l.params_model else {}
        result.append({
            "name": l.name,
            "schema": schema
        })
    return result


@router.get("/exporters")
def list_exporters(engine: PyQueryEngine = Depends(get_engine)):
    """
    List available data exporters.
    """
    exporters = engine.get_exporters()
    result = []

    for e in exporters:
        schema = e.params_model.model_json_schema() if e.params_model else {}
        result.append({
            "name": e.name,
            "schema": schema
        })
    return result
