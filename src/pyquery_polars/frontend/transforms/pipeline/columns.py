"""
Column operation step renderers - Class-based UI components for column operations.

Each class represents a single step type and inherits from BaseStepRenderer.
"""

from typing import Optional

import streamlit as st
import polars as pl

from pyquery_polars.frontend.transforms.base import BaseStepRenderer
from pyquery_polars.core.params import (
    CastChange, SelectColsParams, DropColsParams, RenameColParams,
    KeepColsParams, AddColParams, CleanCastParams, PromoteHeaderParams,
    SplitColParams, CombineColsParams, AddRowNumberParams,
    ExplodeParams, CoalesceParams, OneHotEncodeParams, SanitizeColsParams
)
from pyquery_polars.frontend.utils.completions import (
    generate_module_completions, get_common_completions
)
from pyquery_polars.frontend.elements import python_editor


class SanitizeColsStep(BaseStepRenderer[SanitizeColsParams]):
    """Renderer for the sanitize_cols step - standardizes header names."""

    def render(self, step_id: str, params: SanitizeColsParams,
               schema: Optional[pl.Schema]) -> SanitizeColsParams:
        current_cols = schema.names() if schema else []
        default = [c for c in params.cols if c in current_cols]

        st.caption(
            "Standardizes header names by trimming whitespace and replacing multiple spaces with single space.")
        selected = st.multiselect(
            "Select columns to sanitize:", current_cols, default=default, key=f"sntz_{step_id}")
        params.cols = selected
        return params


class SelectColsStep(BaseStepRenderer[SelectColsParams]):
    """Renderer for the select_cols step - selects specific columns."""

    def render(self, step_id: str, params: SelectColsParams,
               schema: Optional[pl.Schema]) -> SelectColsParams:
        current_cols = schema.names() if schema else []
        default = [c for c in params.cols if c in current_cols]
        selected = st.multiselect(
            "Select columns:", current_cols, default=default, key=f"sel_{step_id}")
        params.cols = selected
        return params


class DropColsStep(BaseStepRenderer[DropColsParams]):
    """Renderer for the drop_cols step - removes specified columns."""

    def render(self, step_id: str, params: DropColsParams,
               schema: Optional[pl.Schema]) -> DropColsParams:
        current_cols = schema.names() if schema else []
        default = [c for c in params.cols if c in current_cols]
        dropped = st.multiselect(
            "Select columns to remove:", current_cols, default=default, key=f"drp_{step_id}")
        params.cols = dropped
        return params


class KeepColsStep(BaseStepRenderer[KeepColsParams]):
    """Renderer for the keep_cols step - keeps only specified columns."""

    def render(self, step_id: str, params: KeepColsParams,
               schema: Optional[pl.Schema]) -> KeepColsParams:
        current_cols = schema.names() if schema else []
        default = [c for c in params.cols if c in current_cols]
        kept = st.multiselect(
            "Keep ONLY these columns:", current_cols, default=default, key=f"kp_{step_id}")
        params.cols = kept
        return params


class RenameColStep(BaseStepRenderer[RenameColParams]):
    """Renderer for the rename_col step - renames a column."""

    def render(self, step_id: str, params: RenameColParams,
               schema: Optional[pl.Schema]) -> RenameColParams:
        current_cols = schema.names() if schema else []
        c1, c2 = st.columns(2)

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


class AddColStep(BaseStepRenderer[AddColParams]):
    """Renderer for the add_col step - adds a computed column."""

    def render(self, step_id: str, params: AddColParams,
               schema: Optional[pl.Schema]) -> AddColParams:
        c1, c2 = st.columns([1, 2])

        def _update_cb():
            new_name = self.state.get_value(f"fe_n_{step_id}", "")
            new_expr = self.state.get_value(f"fe_e_{step_id}", "1")

            ctx = self.ctx
            p_dict = {"name": new_name, "expr": new_expr}
            ctx.state_manager.update_step_params(step_id, p_dict)

        new_col = c1.text_input(
            "New Col Name", value=params.name, key=f"fe_n_{step_id}", on_change=_update_cb)

        @st.cache_data
        def get_all_completions():
            all_comps = get_common_completions()
            all_comps.extend(generate_module_completions(pl, "pl"))
            return all_comps

        completions = get_all_completions()

        expr_code = python_editor(
            code=params.expr,
            key=f"fe_e_{step_id}",
            height=[10, 20],
            completions=completions,
            state=self.state
        )

        if expr_code is not None and expr_code != params.expr:
            params.expr = expr_code
            ctx = self.ctx
            p_dict = {"name": new_col, "expr": expr_code}
            ctx.state_manager.update_step_params(step_id, p_dict)
            st.rerun()

        params.name = new_col if new_col else ""
        return params


class CleanCastStep(BaseStepRenderer[CleanCastParams]):
    """Renderer for the clean_cast step - cleans and casts column types."""

    def render(self, step_id: str, params: CleanCastParams,
               schema: Optional[pl.Schema]) -> CleanCastParams:
        current_cols = schema.names() if schema else []

        res_key = f"ad_res_{step_id}"

        with st.expander("✨ Auto Detect Types", expanded=self.state.has_value(res_key)):
            TYPE_ACTION_MAP = {
                "Int64": "To Int",
                "Float64": "To Float",
                "Date": "To Date",
                "Datetime": "To Datetime",
                "Boolean": "To Boolean"
            }

            if not self.state.has_value(res_key):
                c_ad1, c_ad2 = st.columns([0.7, 0.3])
                ad_cols = c_ad1.multiselect(
                    "Inspect Columns", current_cols, default=[], key=f"ad_c_{step_id}")
                sample_sz = c_ad2.number_input(
                    "Sample Size", 100, 1000, 500, step=50, key=f"ad_sz_{step_id}")

                if st.button("🔍 Analyze", key=f"btn_ad_{step_id}", help="Infer types from sample data"):
                    from pyquery_polars.backend import PyQueryEngine
                    engine = self.engine
                    active_ds = self.ctx.state_manager.active_dataset
                    steps = self.ctx.state_manager.get_active_recipe()

                    partial_recipe = []
                    for s in steps:
                        if s.id == step_id:
                            break
                        partial_recipe.append(s)

                    if engine and active_ds:
                        with st.spinner("Analyzing..."):
                            lf = engine.datasets.get(active_ds)
                            if lf is not None:
                                inferred = engine.analytics.infer_types(
                                    base_lf=lf,
                                    recipe=partial_recipe,
                                    project_recipes=self.ctx.state_manager.all_recipes,
                                    columns=ad_cols,
                                    sample_size=sample_sz
                                )
                            else:
                                inferred = None

                        if inferred:
                            self.state.set_value(res_key, inferred)
                            st.rerun()
                        else:
                            st.warning("No new types detected.")
            else:
                inferred = self.state.get_value(res_key)
                st.info(
                    f"⚡ Detected **{len(inferred)}** potential changes. Review and edit before applying:")

                ALL_CAST_ACTIONS = [
                    "To String",
                    "To Int", "To Int (Robust)",
                    "To Float", "To Float (Robust)",
                    "To Boolean",
                    "To Date", "To Date (Robust)", "To Date (Format)",
                    "To Datetime", "To Datetime (Robust)", "To Datetime (Format)",
                    "To Time", "To Time (Robust)", "To Time (Format)",
                    "To Duration",
                    "Trim Whitespace", "Standardize NULLs",
                    "Fix Excel Serial Date", "Fix Excel Serial Datetime", "Fix Excel Serial Time"
                ]

                preview_data = []
                for col, dtype in inferred.items():
                    action = TYPE_ACTION_MAP.get(dtype, "Unknown")
                    preview_data.append(
                        {"Column": col, "Detected": dtype, "Proposed Action": action})

                edited_data = st.data_editor(
                    preview_data,
                    column_config={
                        "Column": st.column_config.TextColumn("Column", disabled=True),
                        "Detected": st.column_config.TextColumn("Detected Type", disabled=True),
                        "Proposed Action": st.column_config.SelectboxColumn(
                            "Action", options=ALL_CAST_ACTIONS, required=True, width="large")
                    },
                    width="stretch", hide_index=True, key=f"ad_editor_{step_id}"
                )

                c_yes, c_no = st.columns([1, 1])

                if c_yes.button("✅ Confirm & Apply", type="primary", key=f"ad_y_{step_id}"):
                    new_changes = []
                    rows = edited_data if isinstance(
                        edited_data, list) else edited_data.to_dict('records')

                    for row in rows:
                        col = row.get("Column")
                        action = row.get("Proposed Action")
                        if col and action and action != "Unknown":
                            new_changes.append(
                                CastChange(col=col, action=action))

                    if new_changes:
                        from pyquery_polars.backend import PyQueryEngine
                        engine = self.engine
                        active_ds = self.ctx.state_manager.active_dataset

                        if engine and active_ds:
                            engine.recipes.apply_cast_changes(
                                active_ds, new_changes, merge_step_id=step_id)

                            ctx = self.ctx
                            ctx.state_manager.sync_all_from_backend()

                            self.state.delete_value(res_key)
                            st.rerun()

                if c_no.button("❌ Discard", key=f"ad_n_{step_id}"):
                    self.state.delete_value(res_key)
                    st.rerun()

        if params.changes:
            for idx, change in enumerate(params.changes):
                c_txt, c_btn = st.columns([0.9, 0.1])
                with c_txt:
                    st.text(f"• {change.col} ➝ {change.action}")
                with c_btn:
                    def _del_cc_cb(idx_to_remove=idx):
                        ctx = self.ctx
                        steps = ctx.state_manager.get_active_recipe()
                        target = next(
                            (s for s in steps if s.id == step_id), None)
                        if target:
                            try:
                                p = CleanCastParams(**target.params)
                                if 0 <= idx_to_remove < len(p.changes):
                                    p.changes.pop(idx_to_remove)
                                    ctx.state_manager.update_step_params(
                                        step_id, p.model_dump())
                            except:
                                pass
                    st.button(
                        "x", key=f"del_{step_id}_{idx}", on_click=_del_cc_cb)

        c1, c2, c3 = st.columns([2, 2, 1])
        target_cols = c1.multiselect(
            "Columns", current_cols, key=f"cc_c_{step_id}")
        action = c2.selectbox("Action", [
            "To String",
            "To Int", "To Int (Robust)",
            "To Float", "To Float (Robust)",
            "To Boolean",
            "To Date", "To Date (Robust)", "To Date (Format)",
            "To Datetime", "To Datetime (Robust)", "To Datetime (Format)",
            "To Time", "To Time (Robust)", "To Time (Format)",
            "To Duration",
            "Trim Whitespace", "Standardize NULLs",
            "Fix Excel Serial Date", "Fix Excel Serial Datetime", "Fix Excel Serial Time"
        ], key=f"cc_a_{step_id}")

        custom_fmt = None
        if action and "(Format)" in action:
            custom_fmt = st.text_input(
                "Format String (e.g. %d/%m/%Y)", key=f"cc_f_{step_id}")

        def _add_cc_cb():
            t_cols = self.state.get_value(f"cc_c_{step_id}")
            act = self.state.get_value(f"cc_a_{step_id}")
            fmt = self.state.get_value(f"cc_f_{step_id}")

            if t_cols and act:
                ctx = self.ctx
                steps = ctx.state_manager.get_active_recipe()
                target = next((s for s in steps if s.id == step_id), None)
                if target:
                    try:
                        p = CleanCastParams(**target.params)
                    except:
                        p = CleanCastParams()

                    for col in t_cols:
                        p.changes.append(CastChange(
                            col=col, action=act, fmt=fmt if fmt else None))
                    ctx.state_manager.update_step_params(
                        step_id, p.model_dump())

        c3.button(
            "Add", key=f"add_{step_id}", on_click=_add_cc_cb)
        return params


class PromoteHeaderStep(BaseStepRenderer[PromoteHeaderParams]):
    """Renderer for the promote_header step - uses first row as headers."""

    def render(self, step_id: str, params: PromoteHeaderParams,
               schema: Optional[pl.Schema]) -> PromoteHeaderParams:
        st.info(
            "ℹ️ Uses the **first row** as headers and removes it. Use options below to limit which columns get renamed.")

        current_cols = schema.names() if schema else []
        c1, c2 = st.columns(2)

        default_inc = [c for c in params.include_cols if c in current_cols]
        inc = c1.multiselect("Include Cols (Only rename these)",
                             current_cols, default=default_inc, key=f"ph_inc_{step_id}")

        avail_exc = [c for c in current_cols if c not in inc]
        default_exc = [c for c in params.exclude_cols if c in avail_exc]
        exc = c2.multiselect("Exclude Cols (Rename all except)",
                             avail_exc, default=default_exc, key=f"ph_exc_{step_id}")

        params.include_cols = inc
        params.exclude_cols = exc
        return params


class SplitColStep(BaseStepRenderer[SplitColParams]):
    """Renderer for the split_col step - splits column by delimiter."""

    def render(self, step_id: str, params: SplitColParams,
               schema: Optional[pl.Schema]) -> SplitColParams:
        current_cols = schema.names() if schema else []

        col_idx = 0
        if params.col in current_cols:
            col_idx = current_cols.index(params.col)

        c1, c2, c3 = st.columns(3)
        col = c1.selectbox("Column", current_cols,
                           index=col_idx, key=f"sp_c_{step_id}")
        pat = c2.text_input("Delimiter", value=params.pat,
                            key=f"sp_p_{step_id}")
        n = c3.number_input("Max Splits", min_value=1,
                            value=params.n, key=f"sp_n_{step_id}")

        params.col = col
        params.pat = pat
        params.n = int(n)
        return params


class CombineColsStep(BaseStepRenderer[CombineColsParams]):
    """Renderer for the combine_cols step - combines columns with separator."""

    def render(self, step_id: str, params: CombineColsParams,
               schema: Optional[pl.Schema]) -> CombineColsParams:
        current_cols = schema.names() if schema else []
        default_cols = [c for c in params.cols if c in current_cols]

        cols = st.multiselect("Columns", current_cols,
                              default=default_cols, key=f"cb_c_{step_id}")

        c1, c2 = st.columns(2)
        sep = c1.text_input(
            "Separator", value=params.separator, key=f"cb_s_{step_id}")
        name = c2.text_input(
            "New Name", value=params.new_name, key=f"cb_n_{step_id}")

        params.cols = cols
        params.separator = sep
        params.new_name = name
        return params


class AddRowNumberStep(BaseStepRenderer[AddRowNumberParams]):
    """Renderer for the add_row_number step - adds row number column."""

    def render(self, step_id: str, params: AddRowNumberParams,
               schema: Optional[pl.Schema]) -> AddRowNumberParams:
        def _update_cb():
            name = self.state.get_value(f"rn_n_{step_id}", "row_nr")
            mode = self.state.get_value(f"rn_m_{step_id}", "Simple")

            p = {"name": name, "mode": mode,
                 "start": 1, "step": 1, "options": ""}

            if mode == "Custom":
                p["start"] = self.state.get_value(f"rn_s_{step_id}", 1)
                p["step"] = self.state.get_value(f"rn_st_{step_id}", 1)
            elif mode == "Alternating":
                p["options"] = self.state.get_value(f"rn_o_{step_id}", "")

            ctx = self.ctx
            ctx.state_manager.update_step_params(step_id, p)

        c1, c2 = st.columns(2)
        name = c1.text_input("Index Column Name",
                             value=params.name, key=f"rn_n_{step_id}", on_change=_update_cb)

        mode = c2.selectbox("Mode", ["Simple", "Custom", "Alternating"],
                            index=["Simple", "Custom", "Alternating"].index(params.mode) if params.mode in [
                                "Simple", "Custom", "Alternating"] else 0,
                            key=f"rn_m_{step_id}", on_change=_update_cb)

        if mode == "Custom":
            c_i1, c_i2 = st.columns(2)
            start = c_i1.number_input("Start", value=int(
                params.start), key=f"rn_s_{step_id}", on_change=_update_cb)
            step = c_i2.number_input("Step", value=int(
                params.step), key=f"rn_st_{step_id}", on_change=_update_cb)
            params.start = start
            params.step = step
        elif mode == "Alternating":
            opts = st.text_input("Values (comma separated)", value=params.options,
                                 key=f"rn_o_{step_id}", on_change=_update_cb, placeholder="Option A, Option B")
            params.options = opts

        params.name = name
        params.mode = mode  # type: ignore
        return params


class ExplodeStep(BaseStepRenderer[ExplodeParams]):
    """Renderer for the explode step - explodes list columns into rows."""

    def render(self, step_id: str, params: ExplodeParams,
               schema: Optional[pl.Schema]) -> ExplodeParams:
        current_cols = schema.names() if schema else []

        default_cols = [c for c in params.cols if c in current_cols]
        cols = st.multiselect("Columns to Explode (List)", current_cols,
                              default=default_cols, key=f"ex_c_{step_id}")

        params.cols = cols
        return params


class CoalesceStep(BaseStepRenderer[CoalesceParams]):
    """Renderer for the coalesce step - takes first non-null value."""

    def render(self, step_id: str, params: CoalesceParams,
               schema: Optional[pl.Schema]) -> CoalesceParams:
        current_cols = schema.names() if schema else []
        default_cols = [c for c in params.cols if c in current_cols]

        st.caption(
            "Select columns in priority order (first non-null value is taken).")
        cols = st.multiselect("Columns", current_cols,
                              default=default_cols, key=f"cl_c_{step_id}")
        new_name = st.text_input(
            "New Name", value=params.new_name, key=f"cl_n_{step_id}")

        params.cols = cols
        params.new_name = new_name
        return params


class OneHotEncodeStep(BaseStepRenderer[OneHotEncodeParams]):
    """Renderer for the one_hot_encode step - one-hot encoding for categorical columns."""

    def render(self, step_id: str, params: OneHotEncodeParams,
               schema: Optional[pl.Schema]) -> OneHotEncodeParams:
        st.info("ℹ️ Converts categorical column into multiple binary columns (0/1). Uses unique values found in data.")
        current_cols = schema.names() if schema else []

        col_idx = 0
        if params.col in current_cols:
            col_idx = current_cols.index(params.col)

        c1, c2, c3 = st.columns(3)
        col = c1.selectbox("Column", current_cols,
                           index=col_idx, key=f"ohe_c_{step_id}")
        prefix = c2.text_input("Prefix (Optional)", value=params.prefix,
                               placeholder=col, key=f"ohe_p_{step_id}")
        sep = c3.text_input(
            "Separator", value=params.separator, key=f"ohe_s_{step_id}")

        params.col = col if col else ""
        params.prefix = prefix
        params.separator = sep
        return params
