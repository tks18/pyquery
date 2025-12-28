import streamlit as st
import polars as pl
from typing import Optional, cast, Literal
from pyquery_polars.core.params import JoinDatasetParams, AggregateParams, WindowFuncParams, ReshapeParams, AggDef, ConcatParams
from pyquery_polars.frontend.state_manager import update_step_params, get_active_recipe


def render_join_dataset(step_id: str, params: JoinDatasetParams, schema: Optional[pl.Schema]) -> JoinDatasetParams:
    # Access datasets from Engine
    engine = st.session_state.get('engine')
    dataset_names = []
    if engine:
        # Or public method if available
        dataset_names = list(engine._datasets.keys())

    # Select dataset to join
    default_idx = 0
    if params.alias in dataset_names:
        default_idx = dataset_names.index(params.alias)
    elif dataset_names:
        default_idx = 0

    join_alias = st.selectbox(
        "Join With", dataset_names, index=default_idx, key=f"ja_{step_id}")

    params.alias = join_alias if join_alias else ""

    if engine and join_alias in engine._datasets:
        current_cols = schema.names() if schema else []

        # Get recipe for the other dataset
        other_recipe = st.session_state.all_recipes.get(join_alias, [])
        # Get schema of the transformed other dataset
        other_schema = engine.get_transformed_schema(join_alias, other_recipe)
        other_cols = other_schema.names() if other_schema else []

        c1, c2, c3 = st.columns(3)
        # Filter defaults to prevent StreamlitAPIException if columns changed
        valid_left = [c for c in params.left_on if c in current_cols]
        valid_right = [c for c in params.right_on if c in other_cols]

        left_on = c1.multiselect(
            "Left On", current_cols, default=valid_left, key=f"jlo_{step_id}")
        right_on = c2.multiselect(
            "Right On", other_cols, default=valid_right, key=f"jro_{step_id}")

        # safely handle how index
        how_opts = ["left", "inner", "outer", "cross", "anti", "semi"]
        try:
            h_idx = how_opts.index(params.how)
        except:
            h_idx = 0

        how = c3.selectbox("Type", how_opts, index=h_idx, key=f"jh_{step_id}")

        params.left_on = left_on
        params.right_on = right_on
        # Fix: Cast to Literal
        params.how = cast(
            Literal["left", "inner", "outer", "cross", "anti", "semi"], how)
            
        # --- VISUAL JOIN ANALYSIS ---
        st.markdown("---")
        if st.header("📊 Analyze Overlap (Preview)"): 
             # Use header/subheader or just a button? The user clicked a button?
             # No, the previous code had `if st.button(...)`. 
             # I should keep the button but make the output persistent?
             # Streamlit buttons reset on rerun.
             # If I want it persistent, I need session state.
             # For now, I'll stick to the button and just fix the logic.
             pass
             
        if st.button("📊 Analyze Overlap", key=f"btn_venn_{step_id}"):
            if not (params.left_on and params.right_on):
                st.error("Please select join columns first.")
            else:
                try:
                    with st.spinner("Sampling & Analyzing..."):
                        active_ds = st.session_state.active_base_dataset
                        
                        all_steps = get_active_recipe()
                        curr_idx = next((i for i, s in enumerate(all_steps) if s.id == step_id), -1)
                        
                        left_recipe = all_steps[:curr_idx] if curr_idx != -1 else []
                        right_recipe = st.session_state.all_recipes.get(join_alias, [])
                        
                        # Call Backend to perform analysis
                        results = engine.analyze_join_overlap(
                            left_dataset=active_ds,
                            left_recipe=left_recipe,
                            right_dataset=join_alias,
                            right_recipe=right_recipe,
                            left_on=params.left_on,
                            right_on=params.right_on,
                            limit=5000
                        )
                        
                        if "error" in results:
                            st.error(results["error"])
                        else:
                            l_count = results["l_count"]
                            r_count = results["r_count"]
                            match_count = results["match_count"]
                            
                            st.caption(f"⚠️ **Approximation:** Based on top 5000 rows of each dataset.")
                            
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Left (Sample)", l_count, delta=f"-{l_count - match_count}", delta_color="inverse")
                            m2.metric("Matches", match_count)
                            m3.metric("Right (Sample)", r_count, delta=f"-{r_count - match_count}", delta_color="inverse")
                            
                            # Safe Percentages (Capped at 1.0)
                            l_pct = min((match_count / l_count), 1.0) if l_count > 0 else 0.0
                            r_pct = min((match_count / r_count), 1.0) if r_count > 0 else 0.0
                            
                            c_bar1, c_bar2 = st.columns(2)
                            c_bar1.progress(l_pct, text=f"Left Retention: {l_pct:.1%}")
                            c_bar2.progress(r_pct, text=f"Right Retention: {r_pct:.1%}")

                except Exception as e:
                    st.error(f"Analysis Failed: {e}")

    else:
        st.error("Select a valid dataset to join.")

    return params


def render_aggregate(step_id: str, params: AggregateParams, schema: Optional[pl.Schema]) -> AggregateParams:
    current_cols = schema.names() if schema else []

    valid_keys = [c for c in params.keys if c in current_cols]
    group_keys = st.multiselect(
        "Group By", current_cols, default=valid_keys, key=f"gb_{step_id}")
    params.keys = group_keys

    # Display existing aggregations
    if params.aggs:
        for idx, agg in enumerate(params.aggs):
            c_txt, c_btn = st.columns([0.9, 0.1])
            with c_txt:
                st.text(f"• {agg.col} ➝ {agg.op}")  # Dot access

            def _del_agg_cb(idx=idx):
                # Need to fetch fresh state to modify
                steps = get_active_recipe()
                target = next((s for s in steps if s.id == step_id), None)
                if target:
                    try:
                        p = AggregateParams(**target.params)
                        if 0 <= idx < len(p.aggs):
                            p.aggs.pop(idx)
                            update_step_params(step_id, p.model_dump())
                    except:
                        pass

            c_btn.button(
                "x", key=f"ag_d_{step_id}_{idx}", on_click=_del_agg_cb)

    c1, c2, c3 = st.columns([2, 2, 1])

    # Store widget state in session keys directly handled by callback
    st.selectbox("Column", current_cols, key=f"ag_c_{step_id}")
    st.selectbox("Op", ["sum", "mean", "min", "max", "count",
                        "n_unique", "first", "last", "median"], key=f"ag_o_{step_id}")

    def _add_agg_cb():
        col = st.session_state.get(f"ag_c_{step_id}")
        op = st.session_state.get(f"ag_o_{step_id}")

        if col and op:
            steps = get_active_recipe()
            target = next((s for s in steps if s.id == step_id), None)
            if target:
                try:
                    p = AggregateParams(**target.params)
                except:
                    p = AggregateParams()

                p.aggs.append(AggDef(col=col, op=op))
                update_step_params(step_id, p.model_dump())

    c3.button("Add", key=f"ag_a_{step_id}", on_click=_add_agg_cb)

    return params


def render_window_func(step_id: str, params: WindowFuncParams, schema: Optional[pl.Schema]) -> WindowFuncParams:
    current_cols = schema.names() if schema else []
    st.caption("Calculate Ranking, Rolling Stats, Lag/Lead over partitions.")

    c1, c2 = st.columns(2)
    # Safe index finding
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

    win_op = c2.selectbox("Operation", ops, index=o_idx, key=f"wf_o_{step_id}")

    c3, c4 = st.columns(2)
    valid_over = [c for c in params.over if c in current_cols]
    over_cols = c3.multiselect(
        "Partition By (Over)", current_cols, default=valid_over, key=f"wf_p_{step_id}")
    valid_sort = [c for c in params.sort if c in current_cols]
    sort_cols = c4.multiselect(
        "Sort By (Order)", current_cols, default=valid_sort, key=f"wf_s_{step_id}")

    # Generate default name if missing
    default_name = f"{target_col}_{win_op}" if target_col else ""
    # Use params.name if set, else default
    curr_name = params.name if params.name else default_name

    new_col_name = st.text_input(
        "New Column Name", value=curr_name, key=f"wf_n_{step_id}")

    params.target = target_col if target_col else ""
    params.op = win_op
    params.over = over_cols
    params.sort = sort_cols
    params.name = new_col_name
    return params


def render_reshape(step_id: str, params: ReshapeParams, schema: Optional[pl.Schema]) -> ReshapeParams:
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
        # logic: if val_vars has cols that are now id_vars, drop them from default
        
        val_vars = c2.multiselect("Value Variables (To Rows)", remaining_cols, default=valid_vals, key=f"rs_v_{step_id}")
        params.id_vars = id_vars
        params.val_vars = val_vars

    else:  # Pivot
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
        val_col = c3.selectbox("Values", current_cols,
                               index=v_idx, key=f"rs_pv_{step_id}")

        aggs = ["sum", "mean", "min", "max", "first", "count"]
        a_idx = aggs.index(params.agg) if params.agg in aggs else 0
        agg = st.selectbox("Aggregation", aggs, index=a_idx,
                           key=f"rs_pa_{step_id}")

        params.idx = index_cols
        params.col = col_col if col_col else ""
        params.val = val_col if val_col else ""
        params.agg = agg

    return params


def render_concat_datasets(step_id: str, params: ConcatParams, schema: Optional[pl.Schema]) -> ConcatParams:
    # Access datasets from Engine
    engine = st.session_state.get('engine')
    dataset_names = []
    if engine:
        dataset_names = list(engine._datasets.keys())

    st.info("ℹ️ Vertically stacks another dataset below this one (Union). Columns are matched by name.")

    default_idx = 0
    if params.other_dataset in dataset_names:
        default_idx = dataset_names.index(params.other_dataset)

    other = st.selectbox("Stack Dataset (Bottom)", dataset_names,
                         index=default_idx, key=f"cn_d_{step_id}")

    params.other_dataset = other if other else ""
    return params
