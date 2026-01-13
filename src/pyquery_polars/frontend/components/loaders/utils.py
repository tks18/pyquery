import re
import uuid
import streamlit as st
from typing import List, Dict
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.params import CleanCastParams, CastChange
from pyquery_polars.core.models import RecipeStep


def filter_list_by_regex(items: List[str], pattern: str) -> List[str]:
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        return [i for i in items if regex.search(i)]
    except re.error:
        # Fallback to simple substring match if regex is invalid
        pat_lower = pattern.lower()
        return [i for i in items if pat_lower in i.lower()]


def handle_auto_inference(engine: PyQueryEngine, alias_val: str):
    """Runs type inference and adds a clean_cast step if needed."""
    try:
        with st.spinner("Auto-detecting types..."):
            inferred = engine.infer_types(alias_val, [], sample_size=1000)
            if inferred:

                TYPE_ACTION_MAP = {
                    "Int64": "To Int",
                    "Float64": "To Float",
                    "Date": "To Date",
                    "Datetime": "To Datetime",
                    "Boolean": "To Boolean"
                }

                p = CleanCastParams()
                count = 0
                for col, dtype in inferred.items():
                    action = TYPE_ACTION_MAP.get(dtype)
                    if action:
                        p.changes.append(CastChange(col=col, action=action))
                        count += 1

                if count > 0:
                    new_step = RecipeStep(
                        id=str(uuid.uuid4()),
                        type="clean_cast",
                        label="Auto Clean Types",
                        params=p.model_dump()
                    )
                    st.session_state.all_recipes[alias_val].append(new_step)
                    st.toast(
                        f"✨ Auto-added cleaning step for {count} columns!", icon="🪄")
    except Exception as e:
        print(f"Auto infer error: {e}")
