from typing import List

import re
import streamlit as st
import fnmatch

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.core.io import ItemFilter, FilterType


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
            # Use analytics manager directly
            lf = engine.datasets.get(alias_val)
            if lf is None:
                return

            inferred = engine.analytics.infer_types(lf, [], sample_size=1000)

            if inferred:
                # Find existing step to update
                target_id = None
                try:
                    current_recipe = engine.recipes.get(alias_val)
                    for s in current_recipe:
                        if s.type == "clean_cast" and s.label in ["Auto Clean Types", "Auto-Clean Types"]:
                            target_id = s.id
                            break
                except:
                    pass

                # Apply via backend
                # prepend=True ensures if new step created, it is first
                engine.recipes.apply_inferred_types(
                    alias_val,
                    inferred,
                    merge_step_id=target_id,
                    prepend=True
                )

                # Sync frontend state
                from pyquery_polars.frontend.state_manager import sync_all_from_backend
                sync_all_from_backend()

                st.toast(f"✨ Auto-cleaning updated!", icon="🪄")

    except Exception as e:
        st.warning(f"Auto infer error: {e}")
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
