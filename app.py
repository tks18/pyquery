import streamlit as st
import polars as pl
import os
import glob
import json
import threading
import time
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="Shan's PyQuery | ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'raw_lf' not in st.session_state:
    st.session_state.raw_lf = None
if 'recipe_steps' not in st.session_state:
    st.session_state.recipe_steps = []
if 'file_path' not in st.session_state:
    st.session_state.file_path = ""
if 'sheet_name' not in st.session_state:
    st.session_state.sheet_name = "Sheet1"
if 'last_added_id' not in st.session_state:
    st.session_state.last_added_id = None
if 'export_result' not in st.session_state:
    st.session_state.export_result = None

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================


def get_files_from_path(path_input):
    path_input = path_input.strip('"').strip("'")
    if os.path.isdir(path_input):
        return os.path.join(path_input, "*")
    return path_input


def load_lazy_frame(source_path, sheet_name="Sheet1"):
    file_ext = source_path.split(
        '.')[-1].lower() if "." in source_path else "csv"
    try:
        if "csv" in file_ext:
            return pl.scan_csv(source_path, infer_schema_length=0, ignore_errors=True)
        elif "parquet" in file_ext:
            return pl.scan_parquet(source_path)
        elif "json" in file_ext:
            return pl.scan_ndjson(source_path, infer_schema_length=0)
        elif "xlsx" in file_ext or "xls" in file_ext:
            st.warning("⚠️ Excel files require initial RAM load.")
            is_glob = "*" in source_path
            files = glob.glob(source_path) if is_glob else [source_path]
            if not files:
                raise FileNotFoundError("No files found.")
            lazy_frames = []
            prog_bar = st.progress(0)
            for idx, f in enumerate(files):
                try:
                    df = pl.read_excel(
                        f, sheet_name=sheet_name, infer_schema_length=0)
                    df = df.select(pl.all().cast(pl.Utf8))
                    lazy_frames.append(df.lazy())
                except Exception as exc:
                    st.error(f"Failed to read {f}: {exc}")
                prog_bar.progress((idx + 1) / len(files))
            prog_bar.empty()
            return pl.concat(lazy_frames) if lazy_frames else None
        else:
            return pl.scan_csv(source_path, infer_schema_length=0)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def excel_date_to_datetime(col_name):
    return (
        pl.datetime(1899, 12, 30) +
        pl.duration(days=pl.col(col_name).cast(pl.Float64, strict=False))
    )


def build_filter_expr(col_name, op, val_str, schema):
    """
    Constructs a Polars expression with TYPE-AWARE casting.
    """
    # 1. Handle Unary Operators (No value needed)
    if op == "is_null":
        return pl.col(col_name).is_null()
    if op == "is_not_null":
        return pl.col(col_name).is_not_null()

    # 2. Require Value for other ops
    if not val_str:
        return None

    # 3. Detect Column Type from Schema
    dtype = schema.get(col_name, pl.Utf8)

    # 4. Prepare the RHS (Right Hand Side) value with correct type
    try:
        rhs = None

        # --- Numeric Handling ---
        if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]:
            # Clean string (handle decimals in ints)
            clean_val = val_str.strip()
            if "." in clean_val:
                rhs = pl.lit(int(float(clean_val)))  # cast 10.0 -> 10
            else:
                rhs = pl.lit(int(clean_val))

        elif dtype in [pl.Float32, pl.Float64]:
            rhs = pl.lit(float(val_str.strip()))

        # --- Date Handling ---
        elif dtype == pl.Date:
            # Expecting YYYY-MM-DD. Let Polars parse it.
            rhs = pl.lit(val_str.strip()).str.to_date()

        elif dtype == pl.Datetime:
            rhs = pl.lit(val_str.strip()).str.to_datetime()

        # --- Boolean Handling ---
        elif dtype == pl.Boolean:
            if val_str.lower() in ['true', '1', 'yes']:
                rhs = pl.lit(True)
            elif val_str.lower() in ['false', '0', 'no']:
                rhs = pl.lit(False)

        # --- Default (String) ---
        else:
            rhs = pl.lit(val_str)

        # 5. Build Expression
        if op == "==":
            return pl.col(col_name) == rhs
        elif op == "!=":
            return pl.col(col_name) != rhs
        elif op == ">":
            return pl.col(col_name) > rhs
        elif op == "<":
            return pl.col(col_name) < rhs
        elif op == ">=":
            return pl.col(col_name) >= rhs
        elif op == "<=":
            return pl.col(col_name) <= rhs
        elif op == "contains":
            # Contains is strict string op
            return pl.col(col_name).str.contains(val_str)

    except Exception:
        # If casting fails (e.g. text in int col), return None to avoid crash
        return None

    return None


def export_worker(lazy_frame, path, fmt, compression, result_container):
    try:
        start_time = datetime.now()
        os.makedirs(os.path.dirname(os.path.abspath(path))
                    or ".", exist_ok=True)
        if fmt == "Parquet":
            lazy_frame.sink_parquet(
                path, compression=compression, engine="streaming")
        elif fmt == "CSV":
            lazy_frame.sink_csv(path, engine="streaming")
        elif fmt == "Excel":
            lazy_frame.collect().write_excel(path)
        duration = datetime.now() - start_time
        result_container['status'] = 'success'
        result_container['message'] = f"Export successful! Time taken: {duration}"
    except Exception as e:
        result_container['status'] = 'error'
        result_container['message'] = str(e)


def move_step(index, direction):
    steps = st.session_state.recipe_steps
    if direction == -1 and index > 0:
        steps[index], steps[index-1] = steps[index-1], steps[index]
    elif direction == 1 and index < len(steps) - 1:
        steps[index], steps[index+1] = steps[index+1], steps[index]
    st.session_state.last_added_id = steps[index if direction == -
                                           1 else index+1]['id']


def delete_step(index):
    st.session_state.recipe_steps.pop(index)


def add_step(step_type, default_label):
    new_id = datetime.now().timestamp()
    st.session_state.recipe_steps.append({
        "type": step_type,
        "label": default_label,
        "id": new_id,
        "params": {}
    })
    st.session_state.last_added_id = new_id


def load_recipe_from_json(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state.recipe_steps = data
        st.success("Recipe loaded!")
    except Exception as e:
        st.error(f"Invalid JSON: {e}")


# ==========================================
# 3. SIDEBAR: CONTROLS
# ==========================================
with st.sidebar:
    st.title("⚡ Shan's PyQuery")
    st.header("1. Ingest Data")
    path_input = st.text_input(
        "Path / Glob", value=st.session_state.file_path, placeholder="data/*.csv")
    sheet_input = st.text_input(
        "Sheet (Excel)", value=st.session_state.sheet_name)
    if st.button("Load Source", type="primary"):
        st.session_state.file_path = path_input
        st.session_state.sheet_name = sheet_input
        resolved = get_files_from_path(path_input)
        lf = load_lazy_frame(resolved, sheet_input)
        if lf is not None:
            st.session_state.raw_lf = lf
            st.success("Data Loaded!")
            st.rerun()
    st.divider()
    st.header("2. Add Step")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Select Cols"):
            add_step("select_cols", "Select Columns")
        if st.button("➕ Filter Rows"):
            add_step("filter_rows", "Filter Group")
        if st.button("➕ Clean/Cast"):
            add_step("clean_cast", "Multi-Col Types")
    with c2:
        if st.button("➕ Drop Cols"):
            add_step("drop_cols", "Remove Columns")
        if st.button("➕ Rename Col"):
            add_step("rename_col", "Rename Column")
        if st.button("➕ New Column"):
            add_step("add_col", "Feature Eng.")
    if st.button("➕ Keep Cols (Finalize)"):
        add_step("keep_cols", "Keep Specific Columns")
    st.divider()
    st.header("3. Manage Recipe")
    recipe_json = json.dumps(st.session_state.recipe_steps, indent=2)
    st.download_button("💾 Save Recipe", recipe_json,
                       "recipe.json", "application/json")
    uploaded_recipe = st.file_uploader("📂 Load Recipe", type=["json"])
    if uploaded_recipe and st.button("Apply Recipe"):
        load_recipe_from_json(uploaded_recipe)
        st.rerun()
    if st.button("🗑️ Clear All"):
        st.session_state.recipe_steps = []
        st.rerun()

# ==========================================
# 4. MAIN PIPELINE LOGIC
# ==========================================
if st.session_state.raw_lf is None:
    st.info("👈 Please load a dataset from the sidebar to begin.")
    st.stop()

if st.session_state.recipe_steps:
    with st.expander("🗺️ Recipe Overview (Click to see flow)", expanded=False):
        steps_summary = [f"**{i+1}.** {s['label']}" for i,
                         s in enumerate(st.session_state.recipe_steps)]
        st.markdown(" ➝ ".join(steps_summary))

st.subheader("🛠️ Recipe Editor")

current_lf = st.session_state.raw_lf

# --- MAIN LOOP ---
for i, step in enumerate(st.session_state.recipe_steps):
    step_type = step['type']

    # 1. Fetch Schema for current step (Needed for Type-Aware Filtering)
    try:
        current_schema = current_lf.collect_schema()
        current_cols = current_schema.names()
    except:
        current_cols = []
        current_schema = {}

    is_expanded = (step['id'] == st.session_state.last_added_id)
    label_display = f"#{i+1}: {step['label']} ({step_type.replace('_', ' ').title()})"

    with st.expander(label_display, expanded=is_expanded):
        c_head, c_act = st.columns([0.7, 0.3])
        with c_head:
            new_lbl = st.text_input(
                "Step Label", value=step['label'], key=f"lbl_{step['id']}")
            step['label'] = new_lbl
        with c_act:
            st.write("Actions:")
            b1, b2, b3 = st.columns(3)
            if b1.button("⬆️", key=f"u{i}"):
                move_step(i, -1)
                st.rerun()
            if b2.button("⬇️", key=f"d{i}"):
                move_step(i, 1)
                st.rerun()
            if b3.button("❌", key=f"x{i}"):
                delete_step(i)
                st.rerun()
        st.divider()

        params = step['params']

        if step_type == "select_cols":
            default = [c for c in params.get('cols', []) if c in current_cols]
            selected = st.multiselect(
                "Select columns:", current_cols, default=default, key=f"sel_{step['id']}")
            step['params']['cols'] = selected
            if selected:
                current_lf = current_lf.select(selected)

        elif step_type == "drop_cols":
            default = [c for c in params.get('cols', []) if c in current_cols]
            dropped = st.multiselect(
                "Select columns to remove:", current_cols, default=default, key=f"drp_{step['id']}")
            step['params']['cols'] = dropped
            if dropped:
                current_lf = current_lf.drop(dropped)

        elif step_type == "keep_cols":
            default = [c for c in params.get('cols', []) if c in current_cols]
            kept = st.multiselect(
                "Keep ONLY these columns:", current_cols, default=default, key=f"kp_{step['id']}")
            step['params']['cols'] = kept
            if kept:
                current_lf = current_lf.select(kept)

        elif step_type == "rename_col":
            c1, c2 = st.columns(2)
            old_col = params.get('old') if params.get('old') in current_cols else (
                current_cols[0] if current_cols else None)
            target = c1.selectbox("Old Name", current_cols, index=current_cols.index(
                old_col) if old_col else 0, key=f"rn_o_{step['id']}")
            new_name = c2.text_input("New Name", value=params.get(
                'new', ''), key=f"rn_n_{step['id']}")
            step['params'] = {'old': target, 'new': new_name}
            if target and new_name:
                current_lf = current_lf.rename({target: new_name})

        # --- UPDATED FILTER ROW (With Type Awareness) ---
        elif step_type == "filter_rows":
            if 'conditions' not in step['params']:
                step['params']['conditions'] = []
            if 'logic' not in step['params']:
                step['params']['logic'] = "AND"

            st.markdown("Combine conditions with:")
            logic_choice = st.radio("Logic", ["AND (Match All)", "OR (Match Any)"],
                                    index=0 if step['params']['logic'] == "AND" else 1,
                                    horizontal=True, key=f"lg_{step['id']}")
            step['params']['logic'] = "AND" if "AND" in logic_choice else "OR"

            if step['params']['conditions']:
                st.markdown("**Active Filters:**")
                for idx, cond in enumerate(step['params']['conditions']):
                    c_txt, c_btn = st.columns([0.9, 0.1])
                    with c_txt:
                        st.text(f"• {cond['col']} {cond['op']} {cond['val']}")
                    with c_btn:
                        if st.button("x", key=f"fd_{step['id']}_{idx}"):
                            del step['params']['conditions'][idx]
                            st.rerun()
            st.markdown("---")
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            f_col = c1.selectbox("Col", current_cols, key=f"fc_{step['id']}")

            # Smart Operator Filtering
            col_dtype = current_schema.get(f_col, pl.Utf8)
            valid_ops = ["==", "!=", ">", "<", ">=",
                         "<=", "is_not_null", "is_null"]
            if col_dtype == pl.Utf8:
                valid_ops.append("contains")

            f_op = c2.selectbox("Op", valid_ops, key=f"fo_{step['id']}")

            # Helper text for Dates
            help_txt = "Value"
            if col_dtype == pl.Date:
                help_txt = "YYYY-MM-DD"

            f_val = c3.text_input(help_txt, key=f"fv_{step['id']}", disabled=f_op in [
                                  "is_null", "is_not_null"])

            if c4.button("Add", key=f"fa_{step['id']}"):
                step['params']['conditions'].append(
                    {'col': f_col, 'op': f_op, 'val': f_val})
                st.rerun()

            conditions = step['params']['conditions']
            if conditions:
                # PASS SCHEMA TO FILTER BUILDER
                exprs = [build_filter_expr(
                    c['col'], c['op'], c['val'], current_schema) for c in conditions]
                exprs = [e for e in exprs if e is not None]
                if exprs:
                    if step['params']['logic'] == "AND":
                        final_expr = exprs[0]
                        for e in exprs[1:]:
                            final_expr = final_expr & e
                    else:
                        final_expr = exprs[0]
                        for e in exprs[1:]:
                            final_expr = final_expr | e
                    current_lf = current_lf.filter(final_expr)

        elif step_type == "clean_cast":
            if 'changes' not in step['params']:
                step['params']['changes'] = []
            if step['params']['changes']:
                for idx, change in enumerate(step['params']['changes']):
                    c_txt, c_btn = st.columns([0.9, 0.1])
                    with c_txt:
                        st.text(f"• {change['col']} ➝ {change['action']}")
                    with c_btn:
                        if st.button("x", key=f"del_{step['id']}_{idx}"):
                            del step['params']['changes'][idx]
                            st.rerun()
            c1, c2, c3 = st.columns([2, 2, 1])
            target_cols = c1.multiselect(
                "Columns", current_cols, key=f"cc_c_{step['id']}")
            action = c2.selectbox("Action", [
                "To String", "To Int", "To Float", "To Date", "To Datetime", "To Boolean",
                "Trim Whitespace", "Standardize NULLs",
                "Fix Excel Serial Date", "Fix Excel Serial Datetime"
            ], key=f"cc_a_{step['id']}")
            if c3.button("Add", key=f"add_{step['id']}"):
                if target_cols:
                    for col in target_cols:
                        step['params']['changes'].append(
                            {'col': col, 'action': action})
                    st.rerun()

            if step['params']['changes']:
                exprs = []
                for change in step['params']['changes']:
                    t_col = change['col']
                    act = change['action']
                    if t_col not in current_cols:
                        continue
                    if act == "To String":
                        exprs.append(pl.col(t_col).cast(pl.Utf8))
                    elif act == "To Int":
                        exprs.append(pl.col(t_col).cast(
                            pl.Int64, strict=False))
                    elif act == "To Float":
                        exprs.append(pl.col(t_col).cast(
                            pl.Float64, strict=False))
                    elif act == "To Date":
                        exprs.append(pl.col(t_col).cast(pl.Date, strict=False))
                    elif act == "To Datetime":
                        exprs.append(pl.col(t_col).cast(
                            pl.Datetime, strict=False))
                    elif act == "To Boolean":
                        exprs.append(pl.col(t_col).cast(
                            pl.Boolean, strict=False))
                    elif act == "Trim Whitespace":
                        exprs.append(pl.col(t_col).str.strip_chars())
                    elif act == "Standardize NULLs":
                        null_vals = ["NA", "na", "nan", "NULL", "null", ""]
                        exprs.append(pl.when(pl.col(t_col).is_in(null_vals)).then(
                            None).otherwise(pl.col(t_col)).alias(t_col))
                    elif act == "Fix Excel Serial Date":
                        exprs.append(excel_date_to_datetime(
                            t_col).cast(pl.Date).alias(t_col))
                    elif act == "Fix Excel Serial Datetime":
                        exprs.append(excel_date_to_datetime(
                            t_col).alias(t_col))
                if exprs:
                    current_lf = current_lf.with_columns(exprs)

        elif step_type == "add_col":
            c1, c2 = st.columns([1, 2])
            new_col = c1.text_input("New Col Name", value=params.get(
                'name', ''), key=f"fe_n_{step['id']}")
            expr_str = c2.text_input("Polars Expression (pl.col...)", value=params.get(
                'expr', ''), key=f"fe_e_{step['id']}")
            step['params'] = {'name': new_col, 'expr': expr_str}
            if new_col and expr_str:
                try:
                    computed_expr = eval(expr_str)
                    current_lf = current_lf.with_columns(
                        computed_expr.alias(new_col))
                except Exception as e:
                    st.error(f"Expression Error: {e}")

st.divider()
st.subheader("📊 Live Preview (Top 50)")
try:
    preview_df = current_lf.limit(50).collect()
    st.dataframe(preview_df, width="stretch")
    st.caption(f"Shape: {preview_df.shape} (Rows shown are limited)")
except Exception as e:
    st.error(f"Pipeline Error: {e}")

st.divider()
st.subheader("🚀 Export Data (Threaded)")
with st.form("export_form"):
    c1, c2, c3 = st.columns(3)
    out_path = c1.text_input("Output Path", "output.parquet")
    out_fmt = c2.selectbox("Format", ["Parquet", "CSV", "Excel"])
    comp = c3.selectbox("Compression (Parquet)", ["snappy", "zstd", "gzip"])
    submitted = st.form_submit_button("Start Background Export")

if submitted:
    if out_fmt == "Excel":
        st.warning("⚠️ Excel export requires loading all data to RAM.")
    result_container = {}
    t = threading.Thread(target=export_worker, args=(
        current_lf, out_path, out_fmt, comp, result_container))
    t.start()
    with st.spinner(f"Exporting to {out_path}..."):
        while t.is_alive():
            time.sleep(1)
    if result_container.get('status') == 'success':
        st.success(result_container['message'])
    else:
        st.error(f"Export Failed: {result_container.get('message')}")
