"""
Combine operation step renderers - Class-based UI components for joining/aggregating.

Each class represents a single step type and inherits from BaseStepRenderer.
"""

from typing import Optional, cast, Literal

import streamlit as st
import polars as pl

from pyquery_polars.frontend.transforms.base import BaseStepRenderer
from pyquery_polars.core.params import (
    JoinDatasetParams, AggregateParams, WindowFuncParams,
    ReshapeParams, AggDef, ConcatParams
)


class JoinDatasetStep(BaseStepRenderer[JoinDatasetParams]):
    """Renderer for the join_dataset step - joins with another dataset."""

    def render(self, step_id: str, params: JoinDatasetParams,
               schema: Optional[pl.Schema]) -> JoinDatasetParams:
        engine = self.engine
        dataset_names = []
        if engine:
            dataset_names = engine.datasets.list_names()

        default_idx = 0
        if params.alias in dataset_names:
            default_idx = dataset_names.index(params.alias)
        elif dataset_names:
            default_idx = 0

        join_alias = st.selectbox(
            "Join With", dataset_names, index=default_idx, key=f"ja_{step_id}")
        params.alias = join_alias if join_alias else ""

        if engine and engine.datasets.exists(join_alias):
            current_cols = schema.names() if schema else []

            other_recipe = self.ctx.state_manager.all_recipes.get(
                join_alias, [])
            lf_other = engine.datasets.get(join_alias)
            if lf_other is not None:
                other_schema = engine.processing.get_transformed_schema(
                    lf_other, other_recipe)
                other_cols = other_schema.names() if other_schema else []
            else:
                other_cols = []

            c1, c2, c3 = st.columns(3)
            valid_left = [c for c in params.left_on if c in current_cols]
            valid_right = [c for c in params.right_on if c in other_cols]

            left_on = c1.multiselect(
                "Left On", current_cols, default=valid_left, key=f"jlo_{step_id}")
            right_on = c2.multiselect(
                "Right On", other_cols, default=valid_right, key=f"jro_{step_id}")

            how_opts = ["left", "inner", "outer", "cross", "anti", "semi"]
            try:
                h_idx = how_opts.index(params.how)
            except:
                h_idx = 0

            how = c3.selectbox("Type", how_opts, index=h_idx,
                               key=f"jh_{step_id}")

            params.left_on = left_on
            params.right_on = right_on
            params.how = cast(
                Literal["left", "inner", "outer", "cross", "anti", "semi"], how)

            st.markdown("---")
            if st.header("📊 Analyze Overlap (Preview)"):
                pass

            if st.button("📊 Analyze Overlap", key=f"btn_venn_{step_id}"):
                if not (params.left_on and params.right_on):
                    st.error("Please select join columns first.")
                else:
                    try:
                        with st.spinner("Sampling & Analyzing..."):
                            active_ds = self.ctx.state_manager.active_dataset

                            ctx = self.ctx
                            all_steps = ctx.state_manager.get_active_recipe()
                            curr_idx = next((i for i, s in enumerate(
                                all_steps) if s.id == step_id), -1)

                            left_recipe = all_steps[:curr_idx] if curr_idx != -1 else []
                            right_recipe = self.ctx.state_manager.all_recipes.get(
                                join_alias, [])

                            if not active_ds:
                                st.error("No active dataset selected.")
                                return params

                            left_meta = engine.datasets.get_metadata(active_ds)
                            if not left_meta:
                                st.error(f"Metadata not found for {active_ds}")
                                return params

                            left_view = engine.processing.prepare_view(
                                left_meta, left_recipe)

                            right_meta = engine.datasets.get_metadata(
                                join_alias)
                            if not right_meta:
                                st.error(
                                    f"Metadata not found for {join_alias}")
                                return params

                            right_view = engine.processing.prepare_view(
                                right_meta, right_recipe)

                            if left_view is not None and right_view is not None:
                                results = engine.analytics.analyze_join_overlap(
                                    left_df=left_view.limit(5000).collect(),
                                    right_df=right_view.limit(5000).collect(),
                                    left_on=params.left_on,
                                    right_on=params.right_on)
                            else:
                                results = {
                                    "error": "Failed to prepare views for analysis."}

                            if "error" in results:
                                st.error(results["error"])
                            else:
                                l_count = cast(int, results["l_count"])
                                r_count = cast(int, results["r_count"])
                                match_count = cast(
                                    int, results["match_count"])

                                st.caption(
                                    "⚠️ **Approximation:** Based on top 5000 rows of each dataset.")

                                m1, m2, m3 = st.columns(3)
                                m1.metric(
                                    "Left (Sample)", l_count, delta=f"-{l_count - match_count}", delta_color="inverse")
                                m2.metric("Matches", match_count)
                                m3.metric(
                                    "Right (Sample)", r_count, delta=f"-{r_count - match_count}", delta_color="inverse")

                                l_pct = min((match_count / l_count),
                                            1.0) if l_count > 0 else 0.0
                                r_pct = min((match_count / r_count),
                                            1.0) if r_count > 0 else 0.0

                                c_bar1, c_bar2 = st.columns(2)
                                c_bar1.progress(
                                    l_pct, text=f"Left Retention: {l_pct:.1%}")
                                c_bar2.progress(
                                    r_pct, text=f"Right Retention: {r_pct:.1%}")

                    except Exception as e:
                        st.error(f"Analysis Failed: {e}")
        else:
            st.error("Select a valid dataset to join.")

        return params


class AggregateStep(BaseStepRenderer[AggregateParams]):
    """Renderer for the aggregate step - groups and aggregates data."""

    def render(self, step_id: str, params: AggregateParams,
               schema: Optional[pl.Schema]) -> AggregateParams:
        current_cols = schema.names() if schema else []

        valid_keys = [c for c in params.keys if c in current_cols]
        group_keys = st.multiselect(
            "Group By", current_cols, default=valid_keys, key=f"gb_{step_id}")
        params.keys = group_keys

        if params.aggs:
            for idx, agg in enumerate(params.aggs):
                c_txt, c_btn = st.columns([0.9, 0.1])
                with c_txt:
                    st.text(f"• {agg.col} ➝ {agg.op}")

                def _del_agg_cb(idx=idx):
                    ctx = self.ctx
                    steps = ctx.state_manager.get_active_recipe()
                    target = next((s for s in steps if s.id == step_id), None)
                    if target:
                        try:
                            p = AggregateParams(**target.params)
                            if 0 <= idx < len(p.aggs):
                                p.aggs.pop(idx)
                                ctx.state_manager.update_step_params(
                                    step_id, p.model_dump())
                        except:
                            pass

                c_btn.button(
                    "x", key=f"ag_d_{step_id}_{idx}", on_click=_del_agg_cb)

        c1, c2, c3 = st.columns([2, 2, 1])
        st.selectbox("Column", current_cols, key=f"ag_c_{step_id}")
        st.selectbox("Op", ["sum", "mean", "min", "max", "count",
                            "n_unique", "first", "last", "median"], key=f"ag_o_{step_id}")

        def _add_agg_cb():
            col = self.state.get_value(f"ag_c_{step_id}")
            op = self.state.get_value(f"ag_o_{step_id}")

            if col and op:
                ctx = self.ctx
                steps = ctx.state_manager.get_active_recipe()
                target = next((s for s in steps if s.id == step_id), None)
                if target:
                    try:
                        p = AggregateParams(**target.params)
                    except:
                        p = AggregateParams()

                    p.aggs.append(AggDef(col=col, op=op))
                    ctx.state_manager.update_step_params(
                        step_id, p.model_dump())

        c3.button("Add", key=f"ag_a_{step_id}", on_click=_add_agg_cb)
        return params


class WindowFuncStep(BaseStepRenderer[WindowFuncParams]):
    """Renderer for the window_func step - window/ranking functions."""

    def render(self, step_id: str, params: WindowFuncParams,
               schema: Optional[pl.Schema]) -> WindowFuncParams:
        current_cols = schema.names() if schema else []
        st.caption("Calculate Ranking, Rolling Stats, Lag/Lead over partitions.")

        c1, c2 = st.columns(2)
        try:
            t_idx = current_cols.index(
                params.target) if params.target in current_cols else 0
        except:
            t_idx = 0

        target_col = c1.selectbox(
            "Target Column", current_cols, index=t_idx, key=f"wf_t_{step_id}")

        ops = ["sum", "mean", "min", "max", "count", "cum_sum",
               "rank_dense", "rank_ordinal", "lag", "lead"]
        try:
            o_idx = ops.index(params.op)
        except:
            o_idx = 0

        win_op = c2.selectbox(
            "Operation", ops, index=o_idx, key=f"wf_o_{step_id}")

        c3, c4 = st.columns(2)
        valid_over = [c for c in params.over if c in current_cols]
        over_cols = c3.multiselect(
            "Partition By (Over)", current_cols, default=valid_over, key=f"wf_p_{step_id}")
        valid_sort = [c for c in params.sort if c in current_cols]
        sort_cols = c4.multiselect(
            "Sort By (Order)", current_cols, default=valid_sort, key=f"wf_s_{step_id}")

        default_name = f"{target_col}_{win_op}" if target_col else ""
        curr_name = params.name if params.name else default_name
        new_col_name = st.text_input(
            "New Column Name", value=curr_name, key=f"wf_n_{step_id}")

        params.target = target_col if target_col else ""
        params.op = win_op
        params.over = over_cols
        params.sort = sort_cols
        params.name = new_col_name
        return params


class ReshapeStep(BaseStepRenderer[ReshapeParams]):
    """Renderer for the reshape step - pivot/unpivot operations."""

    def render(self, step_id: str, params: ReshapeParams,
               schema: Optional[pl.Schema]) -> ReshapeParams:
        current_cols = schema.names() if schema else []

        mode_idx = 0 if params.mode == "Unpivot" else 1
        mode_sel = st.radio("Mode", ["Unpivot (Melt)", "Pivot (Spread)"],
                            index=mode_idx, horizontal=True, key=f"rs_m_{step_id}")
        mode = mode_sel.split(" ")[0]

        params.mode = cast(Literal["Unpivot", "Pivot"], mode)

        if mode == "Unpivot":
            c1, c2 = st.columns(2)
            valid_ids = [c for c in params.id_vars if c in current_cols]
            id_vars = c1.multiselect(
                "ID Variables (Keep)", current_cols, default=valid_ids, key=f"rs_i_{step_id}")

            remaining_cols = [c for c in current_cols if c not in id_vars]
            valid_vals = [c for c in params.val_vars if c in remaining_cols]
            val_vars = c2.multiselect(
                "Value Variables (To Rows)", remaining_cols, default=valid_vals, key=f"rs_v_{step_id}")
            params.id_vars = id_vars
            params.val_vars = val_vars
        else:
            st.warning(
                "⚠️ Pivot requires eager execution (RAM intensive). It breaks streaming.")
            c1, c2, c3 = st.columns(3)
            valid_idx = [c for c in params.idx if c in current_cols]
            index_cols = c1.multiselect(
                "Index (Rows)", current_cols, default=valid_idx, key=f"rs_px_{step_id}")

            c_idx = current_cols.index(
                params.col) if params.col in current_cols else 0
            col_col = c2.selectbox(
                "Columns (Headers)", current_cols, index=c_idx, key=f"rs_pc_{step_id}")

            v_idx = current_cols.index(
                params.val) if params.val in current_cols else 0
            val_col = c3.selectbox(
                "Values", current_cols, index=v_idx, key=f"rs_pv_{step_id}")

            aggs = ["sum", "mean", "min", "max", "first", "count"]
            a_idx = aggs.index(params.agg) if params.agg in aggs else 0
            agg = st.selectbox("Aggregation", aggs,
                               index=a_idx, key=f"rs_pa_{step_id}")

            params.idx = index_cols
            params.col = col_col if col_col else ""
            params.val = val_col if val_col else ""
            params.agg = agg

        return params


class ConcatDatasetsStep(BaseStepRenderer[ConcatParams]):
    """Renderer for the concat_datasets step - vertically stacks datasets."""

    def render(self, step_id: str, params: ConcatParams,
               schema: Optional[pl.Schema]) -> ConcatParams:
        engine = self.engine
        dataset_names = []
        if engine:
            dataset_names = engine.datasets.list_names()

        st.info(
            "ℹ️ Vertically stacks another dataset below this one (Union). Columns are matched by name.")

        default_idx = 0
        if params.other_dataset in dataset_names:
            default_idx = dataset_names.index(params.other_dataset)

        other = st.selectbox("Stack Dataset (Bottom)", dataset_names,
                             index=default_idx, key=f"cn_d_{step_id}")

        params.other_dataset = other if other else ""
        return params
