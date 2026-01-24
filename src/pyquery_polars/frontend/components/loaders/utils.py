import re
import uuid
import streamlit as st
from typing import List, Dict
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.params import CleanCastParams, CastChange
from pyquery_polars.core.io import FileFilter, ItemFilter, FilterType
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
            # Use centralized backend logic
            new_step = engine.auto_infer_dataset(alias_val)

            if new_step:
                # Sync frontend state
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
                    st.toast(f"✨ Updated cleaning step!", icon="🔄")
                else:
                    # Insert at the beginning (position 0)
                    recipe.insert(0, new_step)
                    st.toast(f"✨ Auto-added cleaning step!", icon="🪄")

                # Update Session State
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
