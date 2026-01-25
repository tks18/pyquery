from typing import Any, Optional

import polars as pl

from pyquery_polars.core.registry import StepRegistry


def render_step_ui(step_type: str, step_id: str, params: Any, schema: Optional[pl.Schema]) -> Any:
    """
    Generic dispatcher for step UI rendering.
    Looks up the registered frontend function.
    """
    definition = StepRegistry.get(step_type)
    if not definition:
        return params

    if definition.frontend_func:
        # print(f"DEBUG: Rendering {step_type} with params: {params}")

        # 1. Convert Dict -> Model
        if definition.params_model and isinstance(params, dict):
            try:
                model_instance = definition.params_model.model_validate(params)
            except Exception as e:
                import streamlit as st
                st.error(f"Params Validation Error ({step_type}): {e}")
                model_instance = definition.params_model()
        else:
            model_instance = params

        # 2. Render
        updated_model = definition.frontend_func(
            step_id, model_instance, schema)

        # 3. Return
        if hasattr(updated_model, "model_dump"):
            dumped = updated_model.model_dump()
            # if dumped != params:
            #     print(f"DEBUG: Change detected in {step_type}! {params} -> {dumped}")
            return dumped
        return updated_model

    return params
