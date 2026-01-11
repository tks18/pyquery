import streamlit as st
import os
import re
import glob
import pandas as pd
import uuid
from typing import List
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.utils.file_picker import pick_file, pick_folder
from pyquery_polars.core.params import CleanCastParams, CastChange
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io_params import FileFilter, FilterType

# Helper: Filter List by Regex


def filter_list_by_regex(items: List[str], pattern: str) -> List[str]:
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        return [i for i in items if regex.search(i)]
    except re.error:
        # Fallback to simple substring match if regex is invalid
        # This helps users who type '*' or other non-regex chars expecting matches
        pat_lower = pattern.lower()
        return [i for i in items if pat_lower in i.lower()]

# Helper: Auto Inference Logic


def handle_auto_inference(engine: PyQueryEngine, alias_val: str):
    """Runs type inference and adds a clean_cast step if needed."""
    try:
        with st.spinner("Auto-detecting types..."):
            inferred = engine.infer_types(alias_val, [], sample_size=1000)
            if inferred:

                TYPE_ACTION_MAP = {
                    "Int64": "To Int",
                    "Float64": "To Float",
                    "Date": "To Date",
                    "Datetime": "To Datetime",
                    "Boolean": "To Boolean"
                }

                p = CleanCastParams()
                count = 0
                for col, dtype in inferred.items():
                    action = TYPE_ACTION_MAP.get(dtype)
                    if action:
                        p.changes.append(CastChange(col=col, action=action))
                        count += 1

                if count > 0:
                    new_step = RecipeStep(
                        id=str(uuid.uuid4()),
                        type="clean_cast",
                        label="Auto Clean Types",
                        params=p.model_dump()
                    )
                    st.session_state.all_recipes[alias_val].append(new_step)
                    st.toast(
                        f"✨ Auto-added cleaning step for {count} columns!", icon="🪄")
    except Exception as e:
        print(f"Auto infer error: {e}")


@st.dialog("Import File", width="large")
def show_file_loader(engine: PyQueryEngine):
    st.caption("Load data from local files (CSV, Excel, Parquet, JSON, IPC)")

    loader_name = "File"

    # --- 0. DATASET ALIAS (Top) ---
    # State Keys
    mode_key = f"dlg_{loader_name}_mode"
    path_key = f"dlg_{loader_name}_path"
    folder_key = f"dlg_{loader_name}_folder"

    # Defaults
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "Single File"
    if path_key not in st.session_state:
        st.session_state[path_key] = ""
    if folder_key not in st.session_state:
        st.session_state[folder_key] = ""

    alias_default = f"data_{len(st.session_state.all_recipes) + 1}"

    # Row 1: Alias + Mode
    c_alias, c_mode = st.columns([0.65, 0.35])
    alias_val = c_alias.text_input(
        "Dataset Alias", value=alias_default, help="Unique name for this dataset")
    # Use selectbox for cleaner "one row" look or horizontal radio
    # User said "type - file / folder". Horizontal radio is good.
    mode = c_mode.radio(
        "Import Mode", ["Single File", "Folder Pattern"], horizontal=True, key=mode_key)

    # --- 1. SOURCE CONFIGURATION ---

    effective_path = ""
    folder_input = None
    # Path Input Block
    if mode == "Single File":
        col_path, col_btn = st.columns([0.85, 0.15])
        path_input = col_path.text_input("File Path", key=path_key)

        def callback_pick_file():
            picked = pick_file("Select File")
            if picked:
                st.session_state[path_key] = picked
        col_btn.button("📂", on_click=callback_pick_file,
                       key="btn_pick_file", help="Browse Files")
        effective_path = path_input

    else:  # Folder Pattern
        col_dir, col_btn = st.columns([0.85, 0.15])
        folder_input = col_dir.text_input("Base Folder", key=folder_key)

        def callback_pick_folder():
            picked = pick_folder("Select Folder")
            if picked:
                st.session_state[folder_key] = picked
        col_btn.button("📂", on_click=callback_pick_folder,
                       key="btn_pick_folder", help="Browse Folder")

        # Pattern Config
        c1, c2 = st.columns(2)
        PATTERNS = {
            "CSV (*.csv)": "*.csv",
            "Excel (*.xlsx)": "*.xlsx",
            "Parquet (*.parquet)": "*.parquet",
            "JSON (*.json)": "*.json",
            "Recursive CSV (**/*.csv)": "**/*.csv",
            "All Supported Files (*)": "*",
            "Custom": "custom"
        }

        pat_key = f"dlg_{loader_name}_pat_type"
        sel_pat_label = c1.selectbox(
            "Pattern Type", list(PATTERNS.keys()), key=pat_key)

        final_pattern = PATTERNS[sel_pat_label]
        if final_pattern == "custom":
            final_pattern = c2.text_input(
                "Custom Pattern", value="*.csv", key=f"dlg_{loader_name}_pat_custom")
        else:
            c2.text_input("Pattern Preview",
                          value=final_pattern, disabled=True)

        if folder_input and final_pattern:
            effective_path = os.path.join(folder_input, final_pattern)

    # --- 1.1 ADVANCED PATH FILTERS ---
    filter_key = f"dlg_{loader_name}_filters"
    if filter_key not in st.session_state:
        st.session_state[filter_key] = []

    # Only show if not Single File (Single file doesn't need path filtering usually, but maybe for consistency?)
    # Actually, user might want to check if single file matches regex?
    # But usually this is for "Pattern" mode.
    # Let's show for Folder Pattern mode mainly.
    effective_filters = []

    if mode == "Folder Pattern":
        with st.expander("Advanced Path Filters", expanded=False):
            st.caption("Apply additional filters to file paths.")

            # Callback for deletion
            def delete_filter(idx):
                if 0 <= idx < len(st.session_state[filter_key]):
                    st.session_state[filter_key].pop(idx)

            # Show existing
            for i, f in enumerate(st.session_state[filter_key]):
                c1, c2, c3, c4 = st.columns([0.25, 0.25, 0.4, 0.1])
                c1.markdown(f"**{f['type']}**")
                c2.caption(f"Apply to: {f.get('target', 'filename')}")
                c3.text(f['value'])
                c4.button(
                    "✕", key=f"btn_del_filt_{i}", on_click=delete_filter, args=(i,))

            # Add New
            st.divider()
            c_add_1, c_add_2, c_add_3, c_add_4 = st.columns(
                [0.25, 0.25, 0.4, 0.1])
            new_f_type = c_add_1.selectbox("Type", [
                                           "contains", "not_contains", "regex", "exact", "is_not", "glob"], key="new_filt_type")
            new_f_target = c_add_2.selectbox(
                "Target", ["filename", "path"], key="new_filt_target")
            new_f_val = c_add_3.text_input("Value", key="new_filt_val")

            def add_filter():
                if st.session_state.new_filt_val:
                    st.session_state[filter_key].append({
                        "type": st.session_state.new_filt_type,
                        "value": st.session_state.new_filt_val,
                        "target": st.session_state.new_filt_target
                    })
                    st.session_state.new_filt_val = ""  # Clear

            c_add_4.button("➕", on_click=add_filter, key="btn_add_filt")

        # Convert to FileFilter objects
        if st.session_state[filter_key]:
            # Map string types to Enum
            type_map = {
                "contains": FilterType.CONTAINS,
                "not_contains": FilterType.NOT_CONTAINS,
                "regex": FilterType.REGEX,
                "exact": FilterType.EXACT,
                "is_not": FilterType.IS_NOT,
                "glob": FilterType.GLOB
            }

            for f in st.session_state[filter_key]:
                effective_filters.append(FileFilter(
                    type=type_map[f['type']],
                    value=f['value'],
                    target=f.get('target', 'filename')
                ))

    # --- determine excel status & Base File ---
    is_excel = False
    sheet_source_file = effective_path

    if effective_path:
        lower_path = effective_path.lower()
        if lower_path.endswith(".xlsx") or lower_path.endswith(".xls") or lower_path.endswith(".xlsm"):
            is_excel = True
        elif "*" in effective_path:  # Glob heuristic
            if ".xls" in lower_path:
                is_excel = True

    # --- 2. EXCEL SHEETS (Conditional) ---
    selected_sheets = ["Sheet1"]

    # Show sheet selection prominently if Excel
    if is_excel and effective_path:
        st.write("###### Excel Sheets")
        with st.container(border=True):
            try:
                # Handle Glob Base Selection
                if "*" in effective_path:
                    # Quick scan for potential base files (limit 20 for UI)
                    matches = []
                    try:
                        is_rec = "**" in effective_path
                        # Iterate to find first few excel files
                        # We use glob.iglob to avoid full list load if massive
                        cnt = 0
                        for f in glob.iglob(effective_path, recursive=is_rec):
                            if f.lower().endswith(('.xlsx', '.xls', '.xlsm')):
                                matches.append(f)
                                cnt += 1
                                if cnt >= 50:
                                    break
                    except:
                        pass

                    if matches:
                        # Helper for display
                        def format_match(path_val):
                            try:
                                # Try relative to user input folder first
                                if folder_input and os.path.exists(folder_input):
                                    return os.path.relpath(path_val, folder_input)
                                # Fallback to relative to CWD or just basename
                                return os.path.relpath(path_val)
                            except:
                                return os.path.basename(path_val)

                        # Select Box with formatter
                        base_selection = st.selectbox(
                            "Select Base File (Template)",
                            matches,
                            format_func=format_match,
                            help="Choose a file to populate the sheet list from."
                        )
                        sheet_source_file = base_selection
                    else:
                        st.warning("No Excel files found matching pattern.")
                        sheet_source_file = None

                if sheet_source_file:
                    # Get sheets from file
                    sheets = engine.get_file_sheet_names(sheet_source_file)

                    col_filter, col_act = st.columns([0.7, 0.3])
                    sheet_filter = col_filter.text_input(
                        "Filter Sheets (Name/Regex)", "", key="sheet_regex_filter", placeholder="e.g. Sheet.*")

                    filtered_sheets = sheets
                    if sheet_filter:
                        filtered_sheets = filter_list_by_regex(
                            sheets, sheet_filter)

                    all_sheets = col_act.checkbox(
                        "Select All Filtered", value=False)

                    if all_sheets:
                        selected_sheets = filtered_sheets
                    else:
                        selected_sheets = st.multiselect(
                            "Select Sheets",
                            filtered_sheets,
                            default=["Sheet1"] if "Sheet1" in filtered_sheets else (
                                [filtered_sheets[0]] if filtered_sheets else [])
                        )
            except Exception as e:
                st.warning(f"Could not read sheets: {e}")

    # --- 3. ADVANCED CONFIG (Conditional) ---
    # Legacy section removed in favor of "Advanced Path Filters" above.
    pass

    # --- 4. PREVIEW & REVIEW (Dynamic Tabs) ---
    with st.expander("🔎 Preview & Review", expanded=True):
        tabs_labels = ["📂 Matched Files"]
        if is_excel:
            tabs_labels.append("📑 Selected Sheets")

        tabs = st.tabs(tabs_labels)

    # TAB 1: Files
    with tabs[0]:
        if effective_path:
            try:
                # Use resolve_files via Engine
                found_files = []
                try:
                    found_files = engine.resolve_files(
                        effective_path, effective_filters, limit=1000)
                except Exception as e:
                    st.error(f"Error resolving paths: {e}")

                scan_limit = 1000
                count = len(found_files)

                display_files = found_files[:scan_limit]
                data = []
                for f in display_files:
                    try:
                        size = os.path.getsize(f)
                        h_size = f"{size / 1024:.1f} KB" if size < 1024 * \
                            1024 else f"{size / (1024 * 1024):.1f} MB"
                    except:
                        h_size = "Unknown"
                    data.append({
                        "File Name": os.path.basename(f),
                        "Size": h_size,
                        "Path": f
                    })

                if found_files:
                    st.success(
                        f"Found {len(found_files)}{'+' if count >= scan_limit else ''} files.")
                    df_files = pd.DataFrame(data)
                    # Add S.No
                    df_files.insert(0, "S.No", range(1, len(df_files) + 1))

                    st.dataframe(
                        df_files,
                        width="stretch",
                        height="auto",
                        hide_index=True,
                        column_config={
                            "S.No": st.column_config.NumberColumn(width="small"),
                            "Size": st.column_config.TextColumn(width="small"),
                            "Path": st.column_config.TextColumn(width="large")
                        }
                    )
                else:
                    st.warning("No files found matching the pattern.")
            except Exception as e:
                st.error(f"Error previewing files: {e}")
        else:
            st.info("Select a path to preview files.")

    # TAB 2: Sheets (if Excel)
    if is_excel:
        with tabs[1]:
            if selected_sheets:
                # Show File Name context (basename of base file or pattern)
                # Use sheet_source_file if available (Template), else effective_path
                target_f = sheet_source_file if sheet_source_file else effective_path
                fname_ctx = os.path.basename(target_f) if target_f else ""

                df_sheets = pd.DataFrame({
                    "File Name": [fname_ctx] * len(selected_sheets),
                    "Sheet Name": selected_sheets
                })
                df_sheets.insert(0, "S.No", range(1, len(df_sheets) + 1))

                st.dataframe(
                    df_sheets,
                    width="stretch",
                    height=200,
                    hide_index=True,
                    column_config={
                        "S.No": st.column_config.NumberColumn(width="small"),
                        "File Name": st.column_config.TextColumn(width="medium"),
                        "Sheet Name": st.column_config.TextColumn(width="large")
                    }
                )
            else:
                st.warning("No sheets selected.")

    # --- 5. SETTINGS (Expander) ---
    with st.expander("⚙️ Loading Settings", expanded=False):
        c_opts_1, c_opts_2 = st.columns(2)

        process_individual = c_opts_1.checkbox(
            "Process Individually", value=(mode == "Folder Pattern"))
        include_src = c_opts_2.checkbox("Include Source Info", value=False)
        auto_infer = st.checkbox("✨ Auto Detect Types", value=False,
                                 help="Automatically scan and add a cleaning step.")

    # --- 6. ACTION ---
    st.divider()
    if st.button("Load Data", type="primary", use_container_width=True):
        if not alias_val:
            st.error("Alias is required.")
            return
        if not effective_path:
            st.error("Invalid path.")
            return

        params = {
            "path": effective_path,
            "filters": effective_filters,
            "sheet": selected_sheets,
            "alias": alias_val,
            "process_individual": process_individual,
            "include_source_info": include_src,
        }

        result = engine.run_loader("File", params)
        if result:
            lf, meta = result
            engine.add_dataset(alias_val, lf, meta)

            if alias_val not in st.session_state.all_recipes:
                st.session_state.all_recipes[alias_val] = []

            # Run Auto Inference
            if auto_infer:
                handle_auto_inference(engine, alias_val)

            st.rerun()
        else:
            st.error("Failed to load.")


@st.dialog("SQL Connection", width="large")
def show_sql_loader(engine: PyQueryEngine):
    st.caption("Connect to SQL Databases via SQLAlchemy")

    conn = st.text_input("Connection String",
                         placeholder="postgresql://user:pass@host:port/dbname")
    query = st.text_area("SQL Query", height=150,
                         placeholder="SELECT * FROM table_name LIMIT 1000")

    alias_val = st.text_input(
        "Dataset Alias", value=f"sql_data_{len(st.session_state.all_recipes) + 1}")
    auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False)

    if st.button("Execute Query", type="primary", use_container_width=True):
        if not conn or not query:
            st.error("Connection string and query are required.")
            return

        params = {"conn": conn, "query": query, "alias": alias_val}

        res = engine.run_loader("SQL", params)
        if res:
            lf_or_lfs, meta = res
            engine.add_dataset(alias_val, lf_or_lfs, meta)
            st.session_state.all_recipes[alias_val] = []
            st.session_state.active_base_dataset = alias_val
            st.session_state.recipe_steps = []

            if auto_infer:
                handle_auto_inference(engine, alias_val)

            st.rerun()
        else:
            st.error("SQL Load Failed.")


@st.dialog("API Import", width="large")
def show_api_loader(engine: PyQueryEngine):
    st.caption("Import JSON/Data from REST API")
    url = st.text_input("API Endpoint URL")
    alias_val = st.text_input(
        "Dataset Alias", value=f"api_data_{len(st.session_state.all_recipes) + 1}")
    auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False)

    if st.button("Fetch Data", type="primary", use_container_width=True):
        params = {"url": url, "alias": alias_val}
        res = engine.run_loader("API", params)
        if res:
            lf_or_lfs, meta = res
            engine.add_dataset(alias_val, lf_or_lfs, meta)
            st.session_state.all_recipes[alias_val] = []
            st.session_state.active_base_dataset = alias_val
            st.session_state.recipe_steps = []

            if auto_infer:
                handle_auto_inference(engine, alias_val)

            st.rerun()
        else:
            st.error("API Load Failed.")
