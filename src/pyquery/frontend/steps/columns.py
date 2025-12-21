import streamlit as st
import polars as pl
from typing import Optional
from pyquery.core.params import (
    CastChange, SelectColsParams, DropColsParams, RenameColParams,
    KeepColsParams, AddColParams, CleanCastParams
)


def render_select_cols(step_id: str, params: SelectColsParams, schema: Optional[pl.Schema]) -> SelectColsParams:
    current_cols = schema.names() if schema else []
    default = [c for c in params.cols if c in current_cols]
    selected = st.multiselect(
        "Select columns:", current_cols, default=default, key=f"sel_{step_id}")
    params.cols = selected
    return params


def render_drop_cols(step_id: str, params: DropColsParams, schema: Optional[pl.Schema]) -> DropColsParams:
    current_cols = schema.names() if schema else []
    default = [c for c in params.cols if c in current_cols]
    dropped = st.multiselect(
        "Select columns to remove:", current_cols, default=default, key=f"drp_{step_id}")
    params.cols = dropped
    return params


def render_keep_cols(step_id: str, params: KeepColsParams, schema: Optional[pl.Schema]) -> KeepColsParams:
    current_cols = schema.names() if schema else []
    default = [c for c in params.cols if c in current_cols]
    kept = st.multiselect(
        "Keep ONLY these columns:", current_cols, default=default, key=f"kp_{step_id}")
    params.cols = kept
    return params


def render_rename_col(step_id: str, params: RenameColParams, schema: Optional[pl.Schema]) -> RenameColParams:
    current_cols = schema.names() if schema else []
    c1, c2 = st.columns(2)

    # params.old is a string
    old_col_val = params.old if params.old in current_cols else (
        current_cols[0] if current_cols else None)

    try:
        idx = current_cols.index(old_col_val) if old_col_val else 0
    except ValueError:
        idx = 0

    target = c1.selectbox("Old Name", current_cols,
                          index=idx, key=f"rn_o_{step_id}")
    new_name = c2.text_input(
        "New Name", value=params.new, key=f"rn_n_{step_id}")

    params.old = target
    params.new = new_name
    return params


def render_add_col(step_id: str, params: AddColParams, schema: Optional[pl.Schema]) -> AddColParams:
    c1, c2 = st.columns([1, 2])

    def _update_cb():
        # Fetch current values from widget state
        new_name = st.session_state.get(f"fe_n_{step_id}", "")
        new_expr = st.session_state.get(f"fe_e_{step_id}", "1")

        # Update param model
        from pyquery.frontend.state_manager import update_step_params
        # Create fresh dict
        p_dict = {"name": new_name, "expr": new_expr}
        update_step_params(step_id, p_dict)

    new_col = c1.text_input(
        "New Col Name", value=params.name, key=f"fe_n_{step_id}", on_change=_update_cb)
    expr_str = c2.text_input(
        "Polars Expression", value=params.expr, key=f"fe_e_{step_id}", on_change=_update_cb)

    params.name = new_col if new_col else ""
    params.expr = expr_str if expr_str else "1"
    return params


def render_clean_cast(step_id: str, params: CleanCastParams, schema: Optional[pl.Schema]) -> CleanCastParams:
    current_cols = schema.names() if schema else []

    # Params initialized with default_factory list, so params.changes exists

    # Render active changes
    if params.changes:
        for idx, change in enumerate(params.changes):
            c_txt, c_btn = st.columns([0.9, 0.1])
            with c_txt:
                st.text(f"• {change.col} ➝ {change.action}")
            with c_btn:
                def _del_cc_cb(idx_to_remove=idx):
                    from pyquery.frontend.state_manager import get_active_recipe, update_step_params
                    steps = get_active_recipe()
                    target = next((s for s in steps if s.id == step_id), None)
                    if target:
                        try:
                            p = CleanCastParams(**target.params)
                            if 0 <= idx_to_remove < len(p.changes):
                                p.changes.pop(idx_to_remove)
                                update_step_params(step_id, p.model_dump())
                        except:
                            pass

                st.button("x", key=f"del_{step_id}_{idx}", on_click=_del_cc_cb)

    c1, c2, c3 = st.columns([2, 2, 1])
    target_cols = c1.multiselect(
        "Columns", current_cols, key=f"cc_c_{step_id}")
    action = c2.selectbox("Action", [
        "To String",
        "To Int", "To Int (Robust)",
        "To Float", "To Float (Robust)",
        "To Boolean",
        "To Date", "To Date (Robust)",
        "To Datetime", "To Datetime (Robust)",
        "To Time", "To Time (Robust)",
        "To Duration",
        "Trim Whitespace", "Standardize NULLs",
        "Fix Excel Serial Date", "Fix Excel Serial Datetime", "Fix Excel Serial Time"
    ], key=f"cc_a_{step_id}")

    def _add_cc_cb():
        t_cols = st.session_state.get(f"cc_c_{step_id}")
        act = st.session_state.get(f"cc_a_{step_id}")

        if t_cols and act:
            from pyquery.frontend.state_manager import get_active_recipe, update_step_params
            steps = get_active_recipe()
            target = next((s for s in steps if s.id == step_id), None)
            if target:
                try:
                    p = CleanCastParams(**target.params)
                except:
                    p = CleanCastParams()

                for col in t_cols:
                    p.changes.append(CastChange(col=col, action=act))

                update_step_params(step_id, p.model_dump())

    c3.button("Add", key=f"add_{step_id}", on_click=_add_cc_cb)

    return params
