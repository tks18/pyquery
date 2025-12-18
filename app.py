import streamlit as st
import polars as pl
import os
import glob
import json
import io
import requests
import threading
import time
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="Shan's PyQuery | Enterprise ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Project State
if 'datasets' not in st.session_state:
    st.session_state.datasets = {}
if 'recipe_steps' not in st.session_state:
    st.session_state.recipe_steps = []
if 'last_added_id' not in st.session_state:
    st.session_state.last_added_id = None
if 'active_base_dataset' not in st.session_state:
    st.session_state.active_base_dataset = None
# Inputs
if 'file_path_buffer' not in st.session_state:
    st.session_state.file_path_buffer = ""

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================


def get_files_from_path(path_input):
    path_input = path_input.strip('"').strip("'")
    if os.path.isdir(path_input):
        return os.path.join(path_input, "*")
    return path_input

def load_from_sql(connection_string, query):
    try:
        # Requires connectorx
        return pl.read_database_uri(query=query, uri=connection_string).lazy()
    except Exception as e:
        st.error(f"SQL Load Error: {e}")
        return None

def load_from_api(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        content = r.content
        # Try JSON first
        try:
            return pl.read_json(io.BytesIO(content)).lazy()
        except:
            pass
        # Try CSV
        try:
            return pl.read_csv(io.BytesIO(content)).lazy()
        except:
            st.error("Could not parse API response as JSON or CSV.")
            return None
    except Exception as e:
        st.error(f"API Request Error: {e}")
        return None


def load_lazy_frame(source_path, sheet_name="Sheet1"):
    if not source_path:
        return None
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
            is_glob = "*" in source_path
            files = glob.glob(source_path) if is_glob else [source_path]
            if not files:
                return None
            lazy_frames = []
            for f in files:
                try:
                    df = pl.read_excel(
                        f, sheet_name=sheet_name, infer_schema_length=0)
                    df = df.select(pl.all().cast(pl.Utf8))
                    lazy_frames.append(df.lazy())
                except:
                    pass
            return pl.concat(lazy_frames) if lazy_frames else None
        else:
            return pl.scan_csv(source_path, infer_schema_length=0)
    except:
        return None

# --- ROBUST PARSERS ---


def robust_numeric_cleaner(col_name, dtype=pl.Float64):
    return (pl.col(col_name).str.strip_chars().str.replace_all(",", "").str.replace_all(r"[^\d\.\-]", "").cast(dtype, strict=False))


def robust_date_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_date(strict=False),
        c.str.to_date("%d/%m/%Y", strict=False),
        c.str.to_date("%m/%d/%Y", strict=False),
        c.str.to_date("%d-%m-%Y", strict=False),
        c.str.to_date("%Y/%m/%d", strict=False),
        c.str.to_date("%d-%b-%Y", strict=False),
    ])


def robust_datetime_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_datetime(strict=False),
        c.str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False),
        c.str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False),
        c.str.to_datetime("%m/%d/%Y %H:%M:%S", strict=False),
        c.str.to_datetime("%d-%m-%Y %H:%M:%S", strict=False),
    ])


def robust_time_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_time(strict=False),
        c.str.to_time("%H:%M", strict=False),
        c.str.to_time("%I:%M %p", strict=False),
        c.str.to_time("%I:%M:%S %p", strict=False)
    ])


def robust_excel_date_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False))).cast(pl.Date)


def robust_excel_datetime_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False)))


def robust_excel_time_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False))).dt.time()


def build_filter_expr(col_name, op, val_str, schema):
    if op == "is_null":
        return pl.col(col_name).is_null()
    if op == "is_not_null":
        return pl.col(col_name).is_not_null()
    if not val_str:
        return None
    dtype = schema.get(col_name, pl.Utf8)
    try:
        rhs = None
        if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]:
            clean_val = val_str.strip()
            rhs = pl.lit(int(float(clean_val))
                         ) if "." in clean_val else pl.lit(int(clean_val))
        elif dtype in [pl.Float32, pl.Float64]:
            rhs = pl.lit(float(val_str.strip()))
        elif dtype == pl.Date:
            rhs = pl.lit(val_str.strip()).str.to_date()
        elif dtype == pl.Datetime:
            rhs = pl.lit(val_str.strip()).str.to_datetime()
        elif dtype == pl.Time:
            rhs = pl.lit(val_str.strip()).str.to_time()
        elif dtype == pl.Boolean:
            rhs = pl.lit(val_str.lower() in ['true', '1', 'yes'])
        else:
            rhs = pl.lit(val_str)

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
            return pl.col(col_name).str.contains(val_str)
    except:
        return None
    return None


def export_worker(lazy_frame, path, fmt, compression, result_container):
    try:
        start_time = datetime.now()
        os.makedirs(os.path.dirname(os.path.abspath(path))
                    or ".", exist_ok=True)
        if fmt == "Parquet":
            lazy_frame.sink_parquet(
                path, compression=compression)
        elif fmt == "CSV":
            lazy_frame.sink_csv(path)
        elif fmt == "Excel":
            lazy_frame.collect().write_excel(path)
        elif fmt == "SQL":
            # path here acts as table name, we need connection string from somewhere?
            # We will pass connection string as 'compression' arg hack or a new struct?
            # Let's refactor export_worker signature or use a result_container to pass args?
            # For simplicity, we assume 'path' is table name and 'compression' is connection URI
            # This is a bit hacky but keeps signature same.
            table_name = path
            conn_uri = compression
            lazy_frame.collect().write_database(table_name=table_name, connection=conn_uri, if_table_exists="append")
        result_container['status'] = 'success'
        result_container['message'] = f"Success! Time: {datetime.now() - start_time}"
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
    st.session_state.recipe_steps.append(
        {"type": step_type, "label": default_label, "id": new_id, "params": {}})
    st.session_state.last_added_id = new_id


def load_recipe_from_json(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state.recipe_steps = data
        st.success("Recipe loaded!")
    except Exception as e:
        st.error(f"Invalid JSON: {e}")


# ==========================================
# 3. SIDEBAR (PROJECT MANAGER)
# ==========================================
with st.sidebar:
    st.title("⚡ Shan's PyQuery")

    st.header("1. Project Datasets")
    with st.expander("Import Dataset", expanded=True):
        tab_file, tab_sql, tab_api = st.tabs(["File", "SQL", "API"])
        
        with tab_file:
            f_path = st.text_input(
                "Path / Glob", placeholder="data/sales.csv", key="fp_input")
            f_name_file = st.text_input(
                "Dataset Alias", placeholder="e.g. Sales", key="fn_input_file")
            f_sheet = st.text_input("Sheet (Excel Only)", "Sheet1", key="fs_input")
            if st.button("Add File", type="primary"):
                if f_path and f_name_file:
                    resolved = get_files_from_path(f_path)
                    lf = load_lazy_frame(resolved, f_sheet)
                    if lf is not None:
                        st.session_state.datasets[f_name_file] = lf
                        if len(st.session_state.datasets) == 1:
                            st.session_state.active_base_dataset = f_name_file
                        st.success(f"Added '{f_name_file}'")
                        st.rerun()
                    else:
                        st.error("Could not load file.")

        with tab_sql:
            s_conn = st.text_input("Connection URI", placeholder="postgresql://user:pass@localhost:5432/db", key="sql_conn")
            s_query = st.text_area("SQL Query / Table", placeholder="SELECT * FROM sales", key="sql_query")
            f_name_sql = st.text_input("Dataset Alias", placeholder="e.g. Sales_SQL", key="fn_input_sql")
            if st.button("Add SQL", type="primary"):
                if s_conn and s_query and f_name_sql:
                    lf = load_from_sql(s_conn, s_query)
                    if lf is not None:
                        st.session_state.datasets[f_name_sql] = lf
                        if len(st.session_state.datasets) == 1:
                            st.session_state.active_base_dataset = f_name_sql
                        st.success(f"Added '{f_name_sql}'")
                        st.rerun()

        with tab_api:
            a_url = st.text_input("API URL", placeholder="https://api.example.com/data.json", key="api_url")
            f_name_api = st.text_input("Dataset Alias", placeholder="e.g. API_Data", key="fn_input_api")
            if st.button("Add API", type="primary"):
                if a_url and f_name_api:
                    lf = load_from_api(a_url)
                    if lf is not None:
                        st.session_state.datasets[f_name_api] = lf
                        if len(st.session_state.datasets) == 1:
                            st.session_state.active_base_dataset = f_name_api
                        st.success(f"Added '{f_name_api}'")
                        st.rerun()

    if st.session_state.datasets:
        st.markdown("**Loaded Datasets:**")
        for name in list(st.session_state.datasets.keys()):
            c1, c2 = st.columns([0.8, 0.2])
            c1.caption(f"📄 {name}")
            if c2.button("🗑️", key=f"del_ds_{name}"):
                del st.session_state.datasets[name]
                if st.session_state.active_base_dataset == name:
                    st.session_state.active_base_dataset = None
                st.rerun()

    st.divider()

    st.header("2. Transform")
    
    # Transformation Map: Display Name -> (Step Type, Default Label)
    transform_options = {
        "Select Columns": ("select_cols", "Select Columns"),
        "Drop Columns": ("drop_cols", "Remove Columns"),
        "Rename Column": ("rename_col", "Rename Column"),
        "Keep Specific (Finalize)": ("keep_cols", "Keep Specific Columns"),
        "Filter Rows": ("filter_rows", "Filter Group"),
        "Sort Rows": ("sort_rows", "Sort Order"),
        "Deduplicate": ("deduplicate", "Remove Duplicates"),
        "Sample Data": ("sample", "Random Sample"),
        "Clean / Cast Types": ("clean_cast", "Multi-Col Types"),
        "Add New Column": ("add_col", "Feature Eng."),
        "Join Dataset": ("join_dataset", "Merge Dataset"),
        "Group By (Aggregate)": ("aggregate", "Summarize Data"),
        "Window Function": ("window_func", "Rolling/Rank"),
        "Reshape (Pivot/Melt)": ("reshape", "Pivot/Unpivot")
    }
    
    selected_transform = st.selectbox("Choose Transformation", list(transform_options.keys()), key="transform_selector")
    
    if st.button("➕ Add Step", type="primary", use_container_width=True):
        step_type, default_label = transform_options[selected_transform]
        add_step(step_type, default_label)

    st.divider()
    st.header("3. Recipe")
    recipe_json = json.dumps(st.session_state.recipe_steps, indent=2)
    st.download_button("💾 Save", recipe_json,
                       "recipe.json", "application/json")
    uploaded_recipe = st.file_uploader("📂 Load", type=["json"])
    if uploaded_recipe and st.button("Apply"):
        load_recipe_from_json(uploaded_recipe)
        st.rerun()
    if st.button("🗑️ Reset"):
        st.session_state.recipe_steps = []
        st.rerun()

# ==========================================
# 4. MAIN PIPELINE
# ==========================================

if not st.session_state.datasets:
    st.info("👈 Start by importing a dataset in the 'Project Datasets' sidebar.")
    st.stop()

dataset_names = list(st.session_state.datasets.keys())
index_base = 0
if st.session_state.active_base_dataset in dataset_names:
    index_base = dataset_names.index(st.session_state.active_base_dataset)

selected_base = st.selectbox(
    "Pipeline Source (Base Dataset)", dataset_names, index=index_base)
st.session_state.active_base_dataset = selected_base
current_lf = st.session_state.datasets[selected_base]

# ----------------------------------------------------
# TAB LAYOUT: RECIPE EDITOR VS DATA PROFILE
# ----------------------------------------------------
tab_recipe, tab_profile = st.tabs(["🛠️ Recipe Editor", "🔍 Data Profile"])

with tab_recipe:
    if st.session_state.recipe_steps:
        with st.expander("🗺️ Recipe Overview", expanded=False):
            st.markdown(" ➝ ".join(
                [f"**{i+1}.** {s['label']}" for i, s in enumerate(st.session_state.recipe_steps)]))

    # --- RECIPE LOOP ---
    for i, step in enumerate(st.session_state.recipe_steps):
        step_type = step['type']
        params = step['params']

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

            # ==================== LOGIC ====================

            if step_type == "join_dataset":
                available_joins = [d for d in dataset_names]
                join_alias = st.selectbox("Join With", available_joins, index=available_joins.index(
                    params['alias']) if 'alias' in params and params['alias'] in available_joins else 0, key=f"ja_{step['id']}")
                step['params']['alias'] = join_alias
                if join_alias in st.session_state.datasets:
                    other_lf = st.session_state.datasets[join_alias]
                    try:
                        other_cols = other_lf.collect_schema().names()
                    except:
                        other_cols = []
                    c1, c2, c3 = st.columns(3)
                    left_on = c1.multiselect("Left On", current_cols, default=params.get(
                        'left_on', []), key=f"jlo_{step['id']}")
                    right_on = c2.multiselect("Right On", other_cols, default=params.get(
                        'right_on', []), key=f"jro_{step['id']}")
                    how = c3.selectbox("Type", [
                                       "left", "inner", "outer", "cross", "anti", "semi"], index=0, key=f"jh_{step['id']}")
                    step['params']['left_on'] = left_on
                    step['params']['right_on'] = right_on
                    step['params']['how'] = how
                    if left_on and right_on:
                        try:
                            current_lf = current_lf.join(
                                other_lf, left_on=left_on, right_on=right_on, how=how)
                        except Exception as e:
                            st.error(f"Join Error: {e}")
                else:
                    st.error("Dataset not loaded.")

            elif step_type == "aggregate":
                group_keys = st.multiselect("Group By", current_cols, default=params.get(
                    'keys', []), key=f"gb_{step['id']}")
                step['params']['keys'] = group_keys
                if 'aggs' not in params:
                    step['params']['aggs'] = []
                if params['aggs']:
                    for idx, agg in enumerate(params['aggs']):
                        c_txt, c_btn = st.columns([0.9, 0.1])
                        with c_txt:
                            st.text(f"• {agg['col']} ➝ {agg['op']}")
                        with c_btn:
                            if st.button("x", key=f"ag_d_{step['id']}_{idx}"):
                                del params['aggs'][idx]
                                st.rerun()
                c1, c2, c3 = st.columns([2, 2, 1])
                agg_col = c1.selectbox(
                    "Column", current_cols, key=f"ag_c_{step['id']}")
                agg_op = c2.selectbox("Op", ["sum", "mean", "min", "max", "count",
                                      "n_unique", "first", "last", "median"], key=f"ag_o_{step['id']}")
                if c3.button("Add", key=f"ag_a_{step['id']}"):
                    step['params']['aggs'].append(
                        {'col': agg_col, 'op': agg_op})
                    st.rerun()
                if group_keys and params['aggs']:
                    agg_exprs = []
                    for agg in params['aggs']:
                        col_expr = pl.col(agg['col'])
                        op = agg['op']
                        if op == "sum":
                            agg_exprs.append(col_expr.sum())
                        elif op == "mean":
                            agg_exprs.append(col_expr.mean())
                        elif op == "min":
                            agg_exprs.append(col_expr.min())
                        elif op == "max":
                            agg_exprs.append(col_expr.max())
                        elif op == "count":
                            agg_exprs.append(col_expr.count())
                        elif op == "n_unique":
                            agg_exprs.append(col_expr.n_unique())
                        elif op == "first":
                            agg_exprs.append(col_expr.first())
                        elif op == "last":
                            agg_exprs.append(col_expr.last())
                        elif op == "median":
                            agg_exprs.append(col_expr.median())
                    try:
                        current_lf = current_lf.group_by(
                            group_keys).agg(agg_exprs)
                    except Exception as e:
                        st.error(f"Error: {e}")

            elif step_type == "window_func":
                st.caption(
                    "Calculate Ranking, Rolling Stats, Lag/Lead over partitions.")
                c1, c2 = st.columns(2)
                target_col = c1.selectbox(
                    "Target Column", current_cols, key=f"wf_t_{step['id']}")
                win_op = c2.selectbox("Operation", ["sum", "mean", "min", "max", "count", "cum_sum",
                                      "rank_dense", "rank_ordinal", "lag", "lead"], key=f"wf_o_{step['id']}")

                c3, c4 = st.columns(2)
                over_cols = c3.multiselect("Partition By (Over)", current_cols, default=params.get(
                    'over', []), key=f"wf_p_{step['id']}")
                # Sort is crucial for cum_sum, lag, lead, rank
                sort_cols = c4.multiselect("Sort By (Order)", current_cols, default=params.get(
                    'sort', []), key=f"wf_s_{step['id']}")

                new_col_name = st.text_input("New Column Name", value=params.get(
                    'name', f"{target_col}_{win_op}"), key=f"wf_n_{step['id']}")

                step['params']['target'] = target_col
                step['params']['op'] = win_op
                step['params']['over'] = over_cols
                step['params']['sort'] = sort_cols
                step['params']['name'] = new_col_name

                if target_col and new_col_name:
                    expr = pl.col(target_col)
                    if win_op == "sum":
                        expr = expr.sum()
                    elif win_op == "mean":
                        expr = expr.mean()
                    elif win_op == "min":
                        expr = expr.min()
                    elif win_op == "max":
                        expr = expr.max()
                    elif win_op == "count":
                        expr = expr.count()
                    elif win_op == "cum_sum":
                        expr = expr.cum_sum()
                    elif win_op == "rank_dense":
                        expr = expr.rank("dense")
                    elif win_op == "rank_ordinal":
                        expr = expr.rank("ordinal")
                    elif win_op == "lag":
                        expr = expr.shift(1)
                    elif win_op == "lead":
                        expr = expr.shift(-1)
                    if over_cols:
                        expr = expr.over(over_cols)
                    if sort_cols:
                        current_lf = current_lf.sort(sort_cols)
                    current_lf = current_lf.with_columns(
                        expr.alias(new_col_name))

            elif step_type == "reshape":
                mode = st.radio("Mode", ["Unpivot (Melt)", "Pivot (Spread)"], index=0 if params.get(
                    'mode') == "Unpivot" else 1, horizontal=True, key=f"rs_m_{step['id']}")
                step['params']['mode'] = mode.split(" ")[0]

                if step['params']['mode'] == "Unpivot":
                    c1, c2 = st.columns(2)
                    id_vars = c1.multiselect("ID Variables (Keep)", current_cols, default=params.get(
                        'id_vars', []), key=f"rs_i_{step['id']}")
                    val_vars = c2.multiselect("Value Variables (To Rows)", [
                                              c for c in current_cols if c not in id_vars], default=params.get('val_vars', []), key=f"rs_v_{step['id']}")
                    step['params']['id_vars'] = id_vars
                    step['params']['val_vars'] = val_vars
                    if id_vars and val_vars:
                        current_lf = current_lf.melt(
                            id_vars=id_vars, value_vars=val_vars)

                else:  # Pivot
                    st.warning(
                        "⚠️ Pivot requires eager execution (RAM intensive). It breaks streaming.")
                    c1, c2, c3 = st.columns(3)
                    index_cols = c1.multiselect("Index (Rows)", current_cols, default=params.get(
                        'idx', []), key=f"rs_px_{step['id']}")
                    col_col = c2.selectbox(
                        "Columns (Headers)", current_cols, key=f"rs_pc_{step['id']}")
                    val_col = c3.selectbox(
                        "Values", current_cols, key=f"rs_pv_{step['id']}")
                    agg = st.selectbox("Aggregation", [
                                       "sum", "mean", "min", "max", "first", "count"], key=f"rs_pa_{step['id']}")

                    step['params']['idx'] = index_cols
                    step['params']['col'] = col_col
                    step['params']['val'] = val_col
                    step['params']['agg'] = agg

                    if index_cols and col_col and val_col:
                        try:
                            # PIVOT TRICK: Collect -> Pivot -> Lazy
                            current_lf = current_lf.collect().pivot(
                                index=index_cols, on=col_col, values=val_col, aggregate_function=agg
                            ).lazy()
                        except Exception as e:
                            st.error(f"Pivot Error: {e}")

            elif step_type == "sort_rows":
                cols = st.multiselect("Columns", current_cols, default=params.get(
                    'cols', []), key=f"srt_{step['id']}")
                desc = st.checkbox("Descending", value=params.get(
                    'desc', False), key=f"srt_d_{step['id']}")
                step['params']['cols'] = cols
                step['params']['desc'] = desc
                if cols:
                    current_lf = current_lf.sort(cols, descending=desc)

            elif step_type == "select_cols":
                default = [c for c in params.get(
                    'cols', []) if c in current_cols]
                selected = st.multiselect(
                    "Select columns:", current_cols, default=default, key=f"sel_{step['id']}")
                step['params']['cols'] = selected
                if selected:
                    current_lf = current_lf.select(selected)

            elif step_type == "drop_cols":
                default = [c for c in params.get(
                    'cols', []) if c in current_cols]
                dropped = st.multiselect(
                    "Select columns to remove:", current_cols, default=default, key=f"drp_{step['id']}")
                step['params']['cols'] = dropped
                if dropped:
                    current_lf = current_lf.drop(dropped)

            elif step_type == "keep_cols":
                default = [c for c in params.get(
                    'cols', []) if c in current_cols]
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

            elif step_type == "filter_rows":
                if 'conditions' not in step['params']:
                    step['params']['conditions'] = []
                if 'logic' not in step['params']:
                    step['params']['logic'] = "AND"
                st.markdown("Combine conditions with:")
                logic_choice = st.radio("Logic", ["AND (Match All)", "OR (Match Any)"], index=0 if step['params']
                                        ['logic'] == "AND" else 1, horizontal=True, key=f"lg_{step['id']}")
                step['params']['logic'] = "AND" if "AND" in logic_choice else "OR"
                if step['params']['conditions']:
                    st.markdown("**Active Filters:**")
                    for idx, cond in enumerate(step['params']['conditions']):
                        c_txt, c_btn = st.columns([0.9, 0.1])
                        with c_txt:
                            st.text(
                                f"• {cond['col']} {cond['op']} {cond['val']}")
                        with c_btn:
                            if st.button("x", key=f"fd_{step['id']}_{idx}"):
                                del step['params']['conditions'][idx]
                                st.rerun()
                st.markdown("---")
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                f_col = c1.selectbox("Col", current_cols,
                                     key=f"fc_{step['id']}")
                col_dtype = current_schema.get(f_col, pl.Utf8)
                valid_ops = ["==", "!=", ">", "<", ">=",
                             "<=", "is_not_null", "is_null"]
                if col_dtype == pl.Utf8:
                    valid_ops.append("contains")
                f_op = c2.selectbox("Op", valid_ops, key=f"fo_{step['id']}")
                f_val = c3.text_input("Value", key=f"fv_{step['id']}", disabled=f_op in [
                                      "is_null", "is_not_null"])
                if c4.button("Add", key=f"fa_{step['id']}"):
                    step['params']['conditions'].append(
                        {'col': f_col, 'op': f_op, 'val': f_val})
                    st.rerun()
                conditions = step['params']['conditions']
                if conditions:
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

                # --- UPDATED ACTION LIST ---
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

                        # --- STANDARD CASTING ---
                        if act == "To String":
                            exprs.append(pl.col(t_col).cast(pl.Utf8))
                        elif act == "To Int":
                            exprs.append(pl.col(t_col).cast(
                                pl.Int64, strict=False))
                        elif act == "To Float":
                            exprs.append(pl.col(t_col).cast(
                                pl.Float64, strict=False))
                        elif act == "To Boolean":
                            exprs.append(pl.col(t_col).cast(
                                pl.Boolean, strict=False))
                        elif act == "To Date":
                            exprs.append(pl.col(t_col).cast(
                                pl.Date, strict=False))
                        elif act == "To Datetime":
                            exprs.append(pl.col(t_col).cast(
                                pl.Datetime, strict=False))
                        elif act == "To Time":
                            exprs.append(pl.col(t_col).cast(
                                pl.Time, strict=False))
                        elif act == "To Duration":
                            exprs.append(pl.col(t_col).cast(
                                pl.Duration, strict=False))

                        # --- ROBUST CASTING ---
                        elif act == "To Int (Robust)":
                            exprs.append(
                                robust_numeric_cleaner(t_col, pl.Int64))
                        elif act == "To Float (Robust)":
                            exprs.append(
                                robust_numeric_cleaner(t_col, pl.Float64))
                        elif act == "To Date (Robust)":
                            exprs.append(robust_date_parser(t_col))
                        elif act == "To Datetime (Robust)":
                            exprs.append(robust_datetime_parser(t_col))
                        elif act == "To Time (Robust)":
                            exprs.append(robust_time_parser(t_col))

                        # --- CLEANING ---
                        elif act == "Trim Whitespace":
                            exprs.append(pl.col(t_col).str.strip_chars())
                        elif act == "Standardize NULLs":
                            null_vals = ["NA", "na", "nan", "NULL", "null", ""]
                            exprs.append(pl.when(pl.col(t_col).is_in(null_vals)).then(
                                None).otherwise(pl.col(t_col)).alias(t_col))

                        # --- EXCEL FIXES ---
                        elif act == "Fix Excel Serial Date":
                            exprs.append(robust_excel_date_parser(t_col))
                        elif act == "Fix Excel Serial Datetime":
                            exprs.append(robust_excel_datetime_parser(t_col))
                        elif act == "Fix Excel Serial Time":
                            exprs.append(robust_excel_time_parser(t_col))

                    if exprs:
                        current_lf = current_lf.with_columns(exprs)

            elif step_type == "add_col":
                c1, c2 = st.columns([1, 2])
                new_col = c1.text_input("New Col Name", value=params.get(
                    'name', ''), key=f"fe_n_{step['id']}")
                expr_str = c2.text_input("Polars Expression", value=params.get(
                    'expr', ''), key=f"fe_e_{step['id']}")
                step['params'] = {'name': new_col, 'expr': expr_str}
                if new_col and expr_str:
                    try:
                            current_lf = current_lf.with_columns(
                            computed_expr.alias(new_col))
                    except Exception as e:
                        st.error(f"Expression Error: {e}")

            elif step_type == "deduplicate":
                subset = st.multiselect("Subset Columns (Empty=All)", current_cols, default=params.get('subset', []), key=f"dd_{step['id']}")
                step['params']['subset'] = subset
                if subset:
                    current_lf = current_lf.unique(subset=subset)
                else:
                    current_lf = current_lf.unique()

            elif step_type == "sample":
                method = st.radio("Method", ["Fraction", "N Rows (Head)"], index=0 if params.get('method') == "Fraction" else 1, key=f"sm_{step['id']}")
                val = 0
                if method == "Fraction":
                    val = st.slider("Fraction", 0.01, 1.0, value=params.get('val', 0.1), key=f"sv_{step['id']}")
                    step['params'] = {'method': method, 'val': val}
                    # Polars lazy sample requires 'seed' usually or might not be supported in older versions?
                    # default to collect sample lazy if needed, but try lazy first.
                    try:
                        current_lf = current_lf.collect().sample(fraction=val, shuffle=True).lazy()
                    except:
                         # Fallback for pure lazy which might not support shuffle well
                         current_lf = current_lf.filter(pl.int_range(0, pl.count()) < (pl.count() * val))
                else:
                    val = st.number_input("N Rows", min_value=1, value=int(params.get('val', 100)), key=f"sn_{step['id']}")
                    step['params'] = {'method': method, 'val': val}
                    current_lf = current_lf.limit(val)

    # --- RESULT AREA ---
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
    # Move Format selector OUTSIDE the form so it triggers a re-run on change
    out_fmt = st.selectbox("Format", ["Parquet", "CSV", "Excel", "SQL"], key="export_fmt_global")

    with st.form("export_form"):
        c1, c2 = st.columns(2)
        
        # Dynamic inputs based on format
        out_path = ""
        comp = "" # acts as Compression OR Connection URI
        
        if out_fmt == "SQL":
            out_path = c1.text_input("Table Name", "output_table")
            comp = c2.text_input("DB Connection URI", "postgresql://...")
        else:
            out_path = c1.text_input("Output Path", f"output.{out_fmt.lower()}")
            if out_fmt == "Parquet":
                comp = c2.selectbox("Compression", ["zstd", "snappy", "gzip"])
            else:
                 c2.text("(No Options)")
        
        submitted = st.form_submit_button("Start Background Export")
        
    if submitted:
        if out_fmt == "Excel":
            st.warning("⚠️ Excel export requires RAM.")
        if out_fmt == "SQL" and (not out_path or not comp):
            st.error("Table Name and URI required for SQL export.")
        else:
            result_container = {}
            t = threading.Thread(target=export_worker, args=(
                current_lf, out_path, out_fmt, comp, result_container))
            t.start()
            with st.spinner(f"Exporting..."):
                while t.is_alive():
                    time.sleep(1)
            if result_container.get('status') == 'success':
                st.success(result_container['message'])
            else:
                st.error(f"Export Failed: {result_container.get('message')}")

with tab_profile:
    st.header("🔍 Dataset Health Check")

    # Analyze the CURRENT transformed state
    if st.button("Generate Profile (Takes time for large data)"):
        with st.spinner("Profiling..."):
            try:
                # We only take a sample for profiling to be fast
                sample_df = current_lf.limit(10000).collect()

                # Metrics
                st.markdown(
                    f"**Rows:** {sample_df.height} (Sampled) | **Columns:** {sample_df.width}")

                # Column Details
                for col in sample_df.columns:
                    with st.expander(f"Column: **{col}** ({sample_df[col].dtype})"):
                        c1, c2, c3, c4 = st.columns(4)
                        n_null = sample_df[col].null_count()
                        pct_null = (n_null / sample_df.height) * 100
                        n_unique = sample_df[col].n_unique()

                        c1.metric("Nulls", f"{n_null} ({pct_null:.1f}%)")
                        c2.metric("Unique", n_unique)

                        # Type specific stats
                        if sample_df[col].dtype in [pl.Float64, pl.Int64]:
                            c3.metric("Min", f"{sample_df[col].min()}")
                            c4.metric("Max", f"{sample_df[col].max()}")
                            st.bar_chart(sample_df[col].value_counts().sort(
                                "count", descending=True).limit(20))
                        elif sample_df[col].dtype == pl.Utf8:
                            st.write("Top Values:")
                            st.dataframe(sample_df[col].value_counts().sort(
                                "count", descending=True).limit(5))

            except Exception as e:
                st.error(f"Profiling Failed: {e}")
