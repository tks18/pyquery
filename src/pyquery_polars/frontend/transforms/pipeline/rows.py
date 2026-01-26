"""
Row operation step renderers - Class-based UI components for row operations.

Each class represents a single step type and inherits from BaseStepRenderer.
"""

from typing import Any, Optional, cast, Literal

import streamlit as st
import polars as pl

from pyquery_polars.frontend.transforms.base import BaseStepRenderer
from pyquery_polars.core.params import (
    FilterCondition, FilterRowsParams, SortRowsParams,
    DeduplicateParams, SampleParams, SliceRowsParams,
    ShiftParams, DropEmptyRowsParams, RemoveOutliersParams
)


class FilterRowsStep(BaseStepRenderer[FilterRowsParams]):
    """Renderer for the filter_rows step - filters rows based on conditions."""

    def render(self, step_id: str, params: FilterRowsParams,
               schema: Optional[pl.Schema]) -> FilterRowsParams:
        current_cols = schema.names() if schema else []

        st.markdown("Combine conditions with:")
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
                        ctx = self.ctx
                        steps = ctx.state_manager.get_active_recipe()
                        target = next(
                            (s for s in steps if s.id == step_id), None)
                        if target:
                            try:
                                p_model = FilterRowsParams(**target.params)
                                if 0 <= idx_to_remove < len(p_model.conditions):
                                    p_model.conditions.pop(idx_to_remove)
                                    ctx.state_manager.update_step_params(
                                        step_id, p_model.model_dump())
                            except Exception:
                                pass
                    st.button("x", key=f"fd_{step_id}_{idx}", on_click=_del_cb)

        st.markdown("---")

        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        f_col = c1.selectbox("Col", current_cols, key=f"fc_{step_id}")

        col_dtype = schema.get(f_col, pl.Utf8) if schema else pl.Utf8
        valid_ops = ["==", "!=", ">", "<", ">=",
                     "<=", "is_not_null", "is_null"]
        if col_dtype == pl.Utf8:
            valid_ops.append("contains")

        f_op = c2.selectbox("Op", valid_ops, key=f"fo_{step_id}")
        f_val = c3.text_input("Value", key=f"fv_{step_id}", disabled=f_op in [
                              "is_null", "is_not_null"])

        def _add_filter_cb():
            col = self.state.get_value(f"fc_{step_id}")
            op = self.state.get_value(f"fo_{step_id}")
            val = self.state.get_value(f"fv_{step_id}")

            if col and op:
                ctx = self.ctx
                steps = ctx.state_manager.get_active_recipe()
                target_step = next((s for s in steps if s.id == step_id), None)

                if target_step:
                    try:
                        p_model = FilterRowsParams(**target_step.params)
                    except:
                        p_model = FilterRowsParams()

                    p_model.conditions.append(
                        FilterCondition(col=col, op=op, val=val))
                    ctx.state_manager.update_step_params(
                        step_id, p_model.model_dump())

        c4.button("Add", key=f"fa_{step_id}", on_click=_add_filter_cb)
        return params


class SortRowsStep(BaseStepRenderer[SortRowsParams]):
    """Renderer for the sort_rows step - sorts rows by columns."""

    def render(self, step_id: str, params: SortRowsParams,
               schema: Optional[pl.Schema]) -> SortRowsParams:
        current_cols = schema.names() if schema else []
        cols = st.multiselect("Columns", current_cols,
                              default=params.cols, key=f"srt_{step_id}")
        desc = st.checkbox("Descending", value=params.desc,
                           key=f"srt_d_{step_id}")

        params.cols = cols
        params.desc = desc
        return params


class DeduplicateStep(BaseStepRenderer[DeduplicateParams]):
    """Renderer for the deduplicate step - removes duplicate rows."""

    def render(self, step_id: str, params: DeduplicateParams,
               schema: Optional[pl.Schema]) -> DeduplicateParams:
        current_cols = schema.names() if schema else []
        subset = st.multiselect("Subset Columns (Empty=All)", current_cols,
                                default=params.subset, key=f"dd_{step_id}")
        params.subset = subset
        return params


class SampleStep(BaseStepRenderer[SampleParams]):
    """Renderer for the sample step - samples rows from dataset."""

    def render(self, step_id: str, params: SampleParams,
               schema: Optional[pl.Schema]) -> SampleParams:
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
            curr_val = params.val if 0.01 <= params.val <= 1.0 else 0.1
            val = st.slider("Fraction", 0.01, 1.0, value=float(
                curr_val), key=f"sv_{step_id}")
        else:
            curr_val = int(params.val) if params.val >= 1 else 100
            val = st.number_input("Count", min_value=1,
                                  value=curr_val, key=f"sn_{step_id}")

        params.val = float(val)
        return params


class SliceRowsStep(BaseStepRenderer[SliceRowsParams]):
    """Renderer for the slice_rows step - keeps/removes top/bottom N rows."""

    def render(self, step_id: str, params: SliceRowsParams,
               schema: Optional[pl.Schema]) -> SliceRowsParams:
        modes = ["Keep Top", "Keep Bottom", "Remove Top", "Remove Bottom"]
        try:
            idx = modes.index(params.mode)
        except ValueError:
            idx = 0

        c1, c2 = st.columns(2)
        mode = c1.selectbox("Operation", modes, index=idx,
                            key=f"sl_m_{step_id}")
        n = c2.number_input("N Rows", min_value=1, value=params.n,
                            step=1, key=f"sl_n_{step_id}")

        params.mode = cast(Any, mode)
        params.n = int(n)
        return params


class ShiftStep(BaseStepRenderer[ShiftParams]):
    """Renderer for the shift step - shifts column values (lag/lead)."""

    def render(self, step_id: str, params: ShiftParams,
               schema: Optional[pl.Schema]) -> ShiftParams:
        current_cols = schema.names() if schema else []

        col_idx = 0
        if params.col in current_cols:
            col_idx = current_cols.index(params.col)

        c1, c2 = st.columns(2)
        col = c1.selectbox("Column", current_cols,
                           index=col_idx, key=f"sh_c_{step_id}")
        periods = c2.number_input("Periods (Negative for Lead)",
                                  value=params.periods, step=1, key=f"sh_p_{step_id}")

        fill_v = st.text_input("Fill Value (Optional)", value=str(
            params.fill_value) if params.fill_value is not None else "", key=f"sh_f_{step_id}")

        final_fill = None
        if fill_v:
            try:
                final_fill = float(fill_v)
                if final_fill.is_integer():
                    final_fill = int(final_fill)
            except:
                final_fill = fill_v

        params.col = col
        params.periods = int(periods)
        params.fill_value = final_fill
        return params


class DropEmptyRowsStep(BaseStepRenderer[DropEmptyRowsParams]):
    """Renderer for the drop_empty_rows step - removes rows with empty/null values."""

    def render(self, step_id: str, params: DropEmptyRowsParams,
               schema: Optional[pl.Schema]) -> DropEmptyRowsParams:
        current_cols = schema.names() if schema else []

        c1, c2 = st.columns([0.3, 0.7])
        how = c1.selectbox("Mode", ["any", "all"],
                           index=0 if params.how == "any" else 1, key=f"de_h_{step_id}")

        default_sub = [c for c in params.subset if c in current_cols]
        subset = st.multiselect("Subset Columns (Empty=Check All)",
                                current_cols, default=default_sub, key=f"de_s_{step_id}")

        params.how = cast(Any, how)
        params.subset = subset
        return params


class RemoveOutliersStep(BaseStepRenderer[RemoveOutliersParams]):
    """Renderer for the remove_outliers step - removes rows with outlier values."""

    def render(self, step_id: str, params: RemoveOutliersParams,
               schema: Optional[pl.Schema]) -> RemoveOutliersParams:
        c1, c2 = st.columns(2)
        current_cols = schema.names() if schema else []

        col_idx = 0
        if params.col in current_cols:
            col_idx = current_cols.index(params.col)

        col = c1.selectbox("Numeric Column", current_cols,
                           index=col_idx, key=f"ro_c_{step_id}")

        factor = c2.number_input("IQR Factor (1.5 = Standard, 3.0 = Extreme)",
                                 value=params.factor, step=0.1, key=f"ro_f_{step_id}")

        st.caption(
            f"Removes rows where value is outside [Q1 - {factor}*IQR, Q3 + {factor}*IQR]")

        params.col = col if col else ""
        params.factor = float(factor)
        return params
