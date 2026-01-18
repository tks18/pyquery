import re
import uuid
import streamlit as st
from typing import List, Dict
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.params import CleanCastParams, CastChange
from pyquery_polars.core.io_params import FileFilter, ItemFilter, FilterType
from pyquery_polars.core.models import RecipeStep
import fnmatch


def filter_list_by_regex(items: List[str], pattern: str) -> List[str]:
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        return [i for i in items if regex.search(i)]
    except re.error:
        # Fallback to simple substring match if regex is invalid
        pat_lower = pattern.lower()
        return [i for i in items if pat_lower in i.lower()]


def handle_auto_inference(engine: PyQueryEngine, alias_val: str):
    """Runs type inference and adds/replaces a clean_cast step if needed."""
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
                    
                    recipe = st.session_state.all_recipes.get(alias_val, [])
                    
                    # Check for existing Auto Clean Types step
                    existing_idx = None
                    for i, step in enumerate(recipe):
                        if step.label == "Auto Clean Types" and step.type == "clean_cast":
                            existing_idx = i
                            break
                    
                    if existing_idx is not None:
                        # Replace existing step at the same position
                        recipe[existing_idx] = new_step
                        st.toast(f"✨ Updated cleaning step for {count} columns!", icon="🔄")
                    else:
                        # Insert at the beginning (position 0) since it's a source-level step
                        recipe.insert(0, new_step)
                        st.toast(f"✨ Auto-added cleaning step for {count} columns!", icon="🪄")
                    
                    st.session_state.all_recipes[alias_val] = recipe
    except Exception as e:
        print(f"Auto infer error: {e}")


def _check_item_match(name: str, f: ItemFilter) -> bool:
    """Evaluates if a sheet name satisfies a filter (Frontend Mirror)."""
    val = f.value
    check_val = name
    check_lower = check_val.lower()
    val_lower = val.lower()

    if f.type == FilterType.EXACT:
        return val == check_val
    if f.type == FilterType.IS_NOT:
        return val != check_val
    if f.type == FilterType.CONTAINS:
        return val_lower in check_lower
    if f.type == FilterType.NOT_CONTAINS:
        return val_lower not in check_lower
    if f.type == FilterType.GLOB:
        return fnmatch.fnmatch(check_lower, val_lower)
    if f.type == FilterType.REGEX:
        try:
            return bool(re.search(val, check_val, re.IGNORECASE))
        except re.error:
            return False
    return False


def filter_sheet_names(names: List[str], filters: List[ItemFilter]) -> List[str]:
    return [n for n in names if all(_check_item_match(n, f) for f in filters)]
