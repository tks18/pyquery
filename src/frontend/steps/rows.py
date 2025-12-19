import streamlit as st
import polars as pl

def render_filter_rows(step_id, params, schema):
    current_cols = schema.names() if schema else []
    
    if 'conditions' not in params:
        params['conditions'] = []
    if 'logic' not in params:
        params['logic'] = "AND"
        
    st.markdown("Combine conditions with:")
    logic_choice = st.radio("Logic", ["AND (Match All)", "OR (Match Any)"], 
                            index=0 if params['logic'] == "AND" else 1, 
                            horizontal=True, key=f"lg_{step_id}")
    params['logic'] = "AND" if "AND" in logic_choice else "OR"
    
    if params['conditions']:
        st.markdown("**Active Filters:**")
        for idx, cond in enumerate(params['conditions']):
            c_txt, c_btn = st.columns([0.9, 0.1])
            with c_txt:
                st.text(f"• {cond['col']} {cond['op']} {cond['val']}")
            with c_btn:
                if st.button("x", key=f"fd_{step_id}_{idx}"):
                    del params['conditions'][idx]
                    st.rerun()
    
    st.markdown("---")
    
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    f_col = c1.selectbox("Col", current_cols, key=f"fc_{step_id}")
    
    # Determine valid ops based on type
    col_dtype = schema.get(f_col, pl.Utf8) if schema else pl.Utf8
    valid_ops = ["==", "!=", ">", "<", ">=", "<=", "is_not_null", "is_null"]
    if col_dtype == pl.Utf8:
        valid_ops.append("contains")
        
    f_op = c2.selectbox("Op", valid_ops, key=f"fo_{step_id}")
    f_val = c3.text_input("Value", key=f"fv_{step_id}", disabled=f_op in ["is_null", "is_not_null"])
    
    if c4.button("Add", key=f"fa_{step_id}"):
        params['conditions'].append({'col': f_col, 'op': f_op, 'val': f_val})
        st.rerun()
        
    return params

def render_sort_rows(step_id, params, schema):
    current_cols = schema.names() if schema else []
    cols = st.multiselect("Columns", current_cols, default=params.get('cols', []), key=f"srt_{step_id}")
    desc = st.checkbox("Descending", value=params.get('desc', False), key=f"srt_d_{step_id}")
    
    params['cols'] = cols
    params['desc'] = desc
    return params

def render_deduplicate(step_id, params, schema):
    current_cols = schema.names() if schema else []
    subset = st.multiselect("Subset Columns (Empty=All)", current_cols, default=params.get('subset', []), key=f"dd_{step_id}")
    params['subset'] = subset
    return params

def render_sample(step_id, params, schema):
    method = st.radio("Method", ["Fraction", "N Rows (Head)"], 
                      index=0 if params.get('method') == "Fraction" else 1, 
                      key=f"sm_{step_id}")
    
    val = 0
    if method == "Fraction":
        val = st.slider("Fraction", 0.01, 1.0, value=float(params.get('val', 0.1)), key=f"sv_{step_id}")
    else:
        val = st.number_input("N Rows", min_value=1, value=int(params.get('val', 100)), key=f"sn_{step_id}")
        
    params['method'] = method
    params['val'] = val
    return params
