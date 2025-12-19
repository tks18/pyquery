import streamlit as st

def render_select_cols(step_id, params, schema):
    current_cols = schema.names() if schema else []
    default = [c for c in params.get('cols', []) if c in current_cols]
    selected = st.multiselect(
        "Select columns:", current_cols, default=default, key=f"sel_{step_id}")
    params['cols'] = selected
    return params

def render_drop_cols(step_id, params, schema):
    current_cols = schema.names() if schema else []
    default = [c for c in params.get('cols', []) if c in current_cols]
    dropped = st.multiselect(
        "Select columns to remove:", current_cols, default=default, key=f"drp_{step_id}")
    params['cols'] = dropped
    return params

def render_keep_cols(step_id, params, schema):
    current_cols = schema.names() if schema else []
    default = [c for c in params.get('cols', []) if c in current_cols]
    kept = st.multiselect(
        "Keep ONLY these columns:", current_cols, default=default, key=f"kp_{step_id}")
    params['cols'] = kept
    return params

def render_rename_col(step_id, params, schema):
    current_cols = schema.names() if schema else []
    c1, c2 = st.columns(2)
    old_col = params.get('old') if params.get('old') in current_cols else (
        current_cols[0] if current_cols else None)
    
    # Safely handle index helper
    try:
        idx = current_cols.index(old_col) if old_col else 0
    except ValueError:
        idx = 0
        
    target = c1.selectbox("Old Name", current_cols, index=idx, key=f"rn_o_{step_id}")
    new_name = c2.text_input("New Name", value=params.get('new', ''), key=f"rn_n_{step_id}")
    
    params['old'] = target
    params['new'] = new_name
    return params

def render_add_col(step_id, params, schema):
    c1, c2 = st.columns([1, 2])
    new_col = c1.text_input("New Col Name", value=params.get('name', ''), key=f"fe_n_{step_id}")
    expr_str = c2.text_input("Polars Expression", value=params.get('expr', ''), key=f"fe_e_{step_id}")
    
    params['name'] = new_col
    params['expr'] = expr_str
    return params

def render_clean_cast(step_id, params, schema):
    current_cols = schema.names() if schema else []
    
    if 'changes' not in params:
        params['changes'] = []
        
    # Render active changes
    if params['changes']:
        for idx, change in enumerate(params['changes']):
            c_txt, c_btn = st.columns([0.9, 0.1])
            with c_txt:
                st.text(f"• {change['col']} ➝ {change['action']}")
            with c_btn:
                if st.button("x", key=f"del_{step_id}_{idx}"):
                    del params['changes'][idx]
                    st.rerun()

    c1, c2, c3 = st.columns([2, 2, 1])
    target_cols = c1.multiselect("Columns", current_cols, key=f"cc_c_{step_id}")
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

    if c3.button("Add", key=f"add_{step_id}"):
        if target_cols:
            for col in target_cols:
                params['changes'].append({'col': col, 'action': action})
            st.rerun()
            
    return params
