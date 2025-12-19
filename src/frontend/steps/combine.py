import streamlit as st
import polars as pl

def render_join_dataset(step_id, params, schema):
    dataset_names = list(st.session_state.datasets.keys())
    
    # Select dataset to join
    default_idx = 0
    if params.get('alias') in dataset_names:
        default_idx = dataset_names.index(params['alias'])
        
    join_alias = st.selectbox("Join With", dataset_names, index=default_idx, key=f"ja_{step_id}")
    params['alias'] = join_alias
    
    if join_alias in st.session_state.datasets:
        current_cols = schema.names() if schema else []
        other_lf = st.session_state.datasets[join_alias]
        try:
            other_cols = other_lf.collect_schema().names()
        except:
            other_cols = []
            
        c1, c2, c3 = st.columns(3)
        left_on = c1.multiselect("Left On", current_cols, default=params.get('left_on', []), key=f"jlo_{step_id}")
        right_on = c2.multiselect("Right On", other_cols, default=params.get('right_on', []), key=f"jro_{step_id}")
        how = c3.selectbox("Type", ["left", "inner", "outer", "cross", "anti", "semi"], index=0, key=f"jh_{step_id}")
        
        params['left_on'] = left_on
        params['right_on'] = right_on
        params['how'] = how
    else:
        st.error("Dataset not loaded.")
        
    return params

def render_aggregate(step_id, params, schema):
    current_cols = schema.names() if schema else []
    
    group_keys = st.multiselect("Group By", current_cols, default=params.get('keys', []), key=f"gb_{step_id}")
    params['keys'] = group_keys
    
    if 'aggs' not in params:
        params['aggs'] = []
        
    if params['aggs']:
        for idx, agg in enumerate(params['aggs']):
            c_txt, c_btn = st.columns([0.9, 0.1])
            with c_txt:
                st.text(f"• {agg['col']} ➝ {agg['op']}")
            with c_btn:
                if st.button("x", key=f"ag_d_{step_id}_{idx}"):
                    del params['aggs'][idx]
                    st.rerun()
                    
    c1, c2, c3 = st.columns([2, 2, 1])
    agg_col = c1.selectbox("Column", current_cols, key=f"ag_c_{step_id}")
    agg_op = c2.selectbox("Op", ["sum", "mean", "min", "max", "count",
                          "n_unique", "first", "last", "median"], key=f"ag_o_{step_id}")
                          
    if c3.button("Add", key=f"ag_a_{step_id}"):
        params['aggs'].append({'col': agg_col, 'op': agg_op})
        st.rerun()
        
    return params

def render_window_func(step_id, params, schema):
    current_cols = schema.names() if schema else []
    st.caption("Calculate Ranking, Rolling Stats, Lag/Lead over partitions.")
    
    c1, c2 = st.columns(2)
    target_col = c1.selectbox("Target Column", current_cols, key=f"wf_t_{step_id}")
    win_op = c2.selectbox("Operation", ["sum", "mean", "min", "max", "count", "cum_sum",
                          "rank_dense", "rank_ordinal", "lag", "lead"], key=f"wf_o_{step_id}")

    c3, c4 = st.columns(2)
    over_cols = c3.multiselect("Partition By (Over)", current_cols, default=params.get('over', []), key=f"wf_p_{step_id}")
    sort_cols = c4.multiselect("Sort By (Order)", current_cols, default=params.get('sort', []), key=f"wf_s_{step_id}")

    # Generate default name if missing
    default_name = f"{target_col}_{win_op}" if target_col else ""
    new_col_name = st.text_input("New Column Name", value=params.get('name', default_name), key=f"wf_n_{step_id}")

    params['target'] = target_col
    params['op'] = win_op
    params['over'] = over_cols
    params['sort'] = sort_cols
    params['name'] = new_col_name
    return params

def render_reshape(step_id, params, schema):
    current_cols = schema.names() if schema else []
    
    mode_idx = 0 if params.get('mode') == "Unpivot" else 1
    mode_sel = st.radio("Mode", ["Unpivot (Melt)", "Pivot (Spread)"], index=mode_idx, horizontal=True, key=f"rs_m_{step_id}")
    mode = mode_sel.split(" ")[0]
    params['mode'] = mode

    if mode == "Unpivot":
        c1, c2 = st.columns(2)
        id_vars = c1.multiselect("ID Variables (Keep)", current_cols, default=params.get('id_vars', []), key=f"rs_i_{step_id}")
        val_vars = c2.multiselect("Value Variables (To Rows)", [
                                  c for c in current_cols if c not in id_vars], default=params.get('val_vars', []), key=f"rs_v_{step_id}")
        params['id_vars'] = id_vars
        params['val_vars'] = val_vars

    else:  # Pivot
        st.warning("⚠️ Pivot requires eager execution (RAM intensive). It breaks streaming.")
        c1, c2, c3 = st.columns(3)
        index_cols = c1.multiselect("Index (Rows)", current_cols, default=params.get('idx', []), key=f"rs_px_{step_id}")
        col_col = c2.selectbox("Columns (Headers)", current_cols, key=f"rs_pc_{step_id}")
        val_col = c3.selectbox("Values", current_cols, key=f"rs_pv_{step_id}")
        agg = st.selectbox("Aggregation", ["sum", "mean", "min", "max", "first", "count"], key=f"rs_pa_{step_id}")

        params['idx'] = index_cols
        params['col'] = col_col
        params['val'] = val_col
        params['agg'] = agg
        
    return params
