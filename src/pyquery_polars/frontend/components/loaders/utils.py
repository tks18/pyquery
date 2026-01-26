from typing import List

import re
import streamlit as st
import fnmatch

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.core.io import ItemFilter, FilterType
from pyquery_polars.frontend.base.state import StateManager


def filter_list_by_regex(items: List[str], pattern: str) -> List[str]:
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        return [i for i in items if regex.search(i)]
    except re.error:
        # Fallback to simple substring match if regex is invalid
        pat_lower = pattern.lower()
        return [i for i in items if pat_lower in i.lower()]


# Reserved label for system-managed auto-infer steps
AUTO_INFER_LABEL = "[System] Auto-Infer Types"


def handle_auto_inference(engine: PyQueryEngine, alias_val: str, state: 'StateManager'):
    """Runs type inference and adds/replaces the system auto-infer step at position 0."""
    try:
        # 1. First, remove any existing system-managed step to ensure a clean refresh
        remove_auto_inference_step(engine, alias_val, state=state)

        # 2. Get fresh data from backend
        lf = engine.datasets.get(alias_val)
        if lf is None:
            return

        with st.spinner("Auto-detecting types..."):
            inferred = engine.analytics.infer_types(lf, [], sample_size=1000)

            if inferred:
                # 3. Apply via backend as a NEW step at the START (prepend=True)
                # Since we just removed any old one, this will always be at position 0
                engine.recipes.apply_inferred_types(
                    alias_val,
                    inferred,
                    merge_step_id=None,  # Fresh start
                    prepend=True,
                    label=AUTO_INFER_LABEL
                )

                # Sync frontend state
                state.sync_all_from_backend()

                st.toast(f"✨ Auto-infer refreshed!", icon="🪄")

    except Exception as e:
        st.warning(f"Auto infer error: {e}")


def remove_auto_inference_step(engine: PyQueryEngine, alias_val: str, state: 'StateManager'):
    """
    Removes system-managed auto-infer steps.
    Surgical: Targets strictly system label, or legacy labels ONLY if they are the first step.
    """
    try:
        current_recipe = engine.recipes.get(alias_val)
        to_remove = []

        # Legacy labels used by older versions of the auto-infer logic
        LEGACY_LABELS = ["Auto Clean Types",
                         "Auto-Clean Types", "Auto Infer Types"]

        steps = getattr(current_recipe, "steps", current_recipe)

        for idx, s in enumerate(steps):
            label = getattr(s, "label", "")
            step_type = getattr(s, "type", "")

            if step_type == "clean_cast":
                # 1. Always remove strictly tagged system steps
                if label == AUTO_INFER_LABEL:
                    to_remove.append(s.id)
                # 2. Remove legacy steps ONLY if they are at position 0 (where system adds them)
                # This ensures we don't accidentally wipe user-added Clean Cast steps later in the recipe.
                elif idx == 0 and label in LEGACY_LABELS:
                    to_remove.append(s.id)

        if to_remove:
            for step_id in to_remove:
                engine.recipes.remove_step(alias_val, step_id)

            # Sync frontend state
            state.sync_all_from_backend()
    except Exception as e:
        pass


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
