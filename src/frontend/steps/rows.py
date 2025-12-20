import streamlit as st
import polars as pl
from typing import Optional, cast, Literal
from src.core.params import (
    FilterCondition, FilterRowsParams, SortRowsParams,
    DeduplicateParams, SampleParams
)


def render_filter_rows(step_id: str, params: FilterRowsParams, schema: Optional[pl.Schema]) -> FilterRowsParams:
    current_cols = schema.names() if schema else []

    # params is FilterRowsParams (has conditions, logic)

    st.markdown("Combine conditions with:")
    # params.logic is "AND" or "OR"
    logic_idx = 0 if params.logic == "AND" else 1
    logic_choice = st.radio("Logic", ["AND (Match All)", "OR (Match Any)"],
                            index=logic_idx,
                            horizontal=True, key=f"lg_{step_id}")
    params.logic = "AND" if "AND" in logic_choice else "OR"

    if params.conditions:
        st.markdown("**Active Filters:**")
        for idx, cond in enumerate(params.conditions):
            c_txt, c_btn = st.columns([0.9, 0.1])
            with c_txt:
                st.text(f"• {cond.col} {cond.op} {cond.val}")
            with c_btn:
                def _del_cb(idx_to_remove=idx):
                    from src.frontend.state_manager import get_active_recipe, update_step_params
                    steps = get_active_recipe()
                    target = next((s for s in steps if s.id == step_id), None)
                    if target:
                        try:
                            p_model = FilterRowsParams(**target.params)
                            if 0 <= idx_to_remove < len(p_model.conditions):
                                p_model.conditions.pop(idx_to_remove)
                                update_step_params(
                                    step_id, p_model.model_dump())
                        except Exception as e:
                            pass

                st.button("x", key=f"fd_{step_id}_{idx}", on_click=_del_cb)

    st.markdown("---")

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    f_col = c1.selectbox("Col", current_cols, key=f"fc_{step_id}")

    # Determine valid ops based on type
    col_dtype = schema.get(f_col, pl.Utf8) if schema else pl.Utf8
    valid_ops = ["==", "!=", ">", "<", ">=", "<=", "is_not_null", "is_null"]
    if col_dtype == pl.Utf8:
        valid_ops.append("contains")

    f_op = c2.selectbox("Op", valid_ops, key=f"fo_{step_id}")
    f_val = c3.text_input("Value", key=f"fv_{step_id}", disabled=f_op in [
                          "is_null", "is_not_null"])

    def _add_filter_cb():
        # Callback to handle Add
        col = st.session_state.get(f"fc_{step_id}")
        op = st.session_state.get(f"fo_{step_id}")
        val = st.session_state.get(f"fv_{step_id}")

        if col and op:
            from src.frontend.state_manager import get_active_recipe, update_step_params
            steps = get_active_recipe()
            # Find step
            target_step = next((s for s in steps if s.id == step_id), None)

            if target_step:
                # Parse current params safely
                try:
                    # target_step.params is Dict
                    p_model = FilterRowsParams(**target_step.params)
                except:
                    p_model = FilterRowsParams()

                # Update
                p_model.conditions.append(
                    FilterCondition(col=col, op=op, val=val))
                # Save
                update_step_params(step_id, p_model.model_dump())

    # Button with Callback
    c4.button("Add", key=f"fa_{step_id}", on_click=_add_filter_cb)

    return params


def render_sort_rows(step_id: str, params: SortRowsParams, schema: Optional[pl.Schema]) -> SortRowsParams:
    current_cols = schema.names() if schema else []
    cols = st.multiselect("Columns", current_cols,
                          default=params.cols, key=f"srt_{step_id}")
    desc = st.checkbox("Descending", value=params.desc, key=f"srt_d_{step_id}")

    params.cols = cols
    params.desc = desc
    return params


def render_deduplicate(step_id: str, params: DeduplicateParams, schema: Optional[pl.Schema]) -> DeduplicateParams:
    current_cols = schema.names() if schema else []
    subset = st.multiselect("Subset Columns (Empty=All)", current_cols,
                            default=params.subset, key=f"dd_{step_id}")
    params.subset = subset
    return params


def render_sample(step_id: str, params: SampleParams, schema: Optional[pl.Schema]) -> SampleParams:
    # Model uses Literal["Fraction", "N"]
    options = ["Fraction", "N"]
    try:
        idx = options.index(params.method)
    except ValueError:
        idx = 0

    def format_func(opt):
        return "N Rows" if opt == "N" else opt

    method_val = st.radio("Method", options, index=idx,
                          format_func=format_func, key=f"sm_{step_id}")

    params.method = cast(Literal["Fraction", "N"], method_val)

    val = 0.0
    if params.method == "Fraction":
        # Ensure value matches slider range
        curr_val = params.val if 0.01 <= params.val <= 1.0 else 0.1
        val = st.slider("Fraction", 0.01, 1.0, value=float(
            curr_val), key=f"sv_{step_id}")
    else:
        # Check defaults
        curr_val = int(params.val) if params.val >= 1 else 100
        val = st.number_input("Count", min_value=1,
                              value=curr_val, key=f"sn_{step_id}")

    params.val = float(val)  # Model expects float
    return params
