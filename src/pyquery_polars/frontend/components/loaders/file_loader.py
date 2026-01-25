from typing import Optional

import streamlit as st
import os
import re
import glob
import pandas as pd

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.core.io import FileFilter, FilterType, ItemFilter
from pyquery_polars.frontend.utils.file_picker import pick_file, pick_folder
from pyquery_polars.frontend.utils.cache_utils import get_cached_sheet_names, get_cached_resolved_files, get_cached_encoding_scan, get_cached_table_names
from pyquery_polars.frontend.components.loaders.utils import filter_list_by_regex, handle_auto_inference, filter_sheet_names


# Constant Map for Filter Types
FILTER_TYPE_MAP = {
    "contains": FilterType.CONTAINS,
    "regex": FilterType.REGEX,
    "exact": FilterType.EXACT,
    "glob": FilterType.GLOB,
    "not_contains": FilterType.NOT_CONTAINS,
    "is_not": FilterType.IS_NOT
}


@st.dialog("Import File", width="large")
def show_file_loader(engine: PyQueryEngine, edit_mode: bool = False, edit_dataset_name: Optional[str] = None):
    """
    File Loader Dialog.

    Args:
        engine: PyQueryEngine instance
        edit_mode: If True, pre-fill inputs from existing dataset metadata
        edit_dataset_name: Name of dataset to edit (required if edit_mode=True)
    """
    dialog_title = "Edit Dataset" if edit_mode else "Import File"
    st.caption(f"{'Modify settings for existing dataset' if edit_mode else 'Load data from local files (CSV, Excel, Parquet, JSON, IPC)'}")

    loader_name = "File"

    # --- STATE MANAGEMENT ---
    busy_key = f"dlg_{loader_name}_busy"
    action_key = f"dlg_{loader_name}_action"
    job_params_key = f"dlg_{loader_name}_job_params"

    # State for visibility
    if "show_loader_file" not in st.session_state:
        st.session_state.show_loader_file = False

    if busy_key not in st.session_state:
        st.session_state[busy_key] = False
    if action_key not in st.session_state:
        st.session_state[action_key] = None
    if job_params_key not in st.session_state:
        st.session_state[job_params_key] = {}

    is_busy = st.session_state[busy_key]

    # --- INPUT FORM ---

    # State Keys
    mode_key = f"dlg_{loader_name}_mode"
    path_key = f"dlg_{loader_name}_path"
    folder_key = f"dlg_{loader_name}_folder"
    recent_paths_key = f"dlg_{loader_name}_recent_paths"

    # --- PRE-FILL LOGIC FOR EDIT MODE ---
    edit_init_key = f"dlg_{loader_name}_edit_initialized"
    if edit_mode and edit_dataset_name and not st.session_state.get(edit_init_key):
        meta = engine.datasets.get_metadata(edit_dataset_name)
        if meta:
            params = meta.loader_params or {}
        else:
            params = {}

        if params:
            original_path = params.get("path", "")

            # Pre-fill alias
            st.session_state[f"dlg_{loader_name}_alias"] = edit_dataset_name

            # Determine mode and set paths correctly
            has_filters = params.get("filters") and len(
                params.get("filters", [])) > 0
            is_folder_mode = params.get(
                "process_individual") or has_filters or os.path.isdir(original_path) or glob.has_magic(original_path)

            if is_folder_mode:
                st.session_state[mode_key] = "Folder Pattern"
                # Extract just the folder path (if path contains wildcards or is a folder)
                if os.path.isdir(original_path):
                    st.session_state[folder_key] = original_path
                else:
                    # Path might be a glob pattern - extract directory and pattern
                    folder_part = os.path.dirname(original_path)
                    pattern_part = os.path.basename(original_path)

                    # Handle recursive patterns like **/*.csv
                    if folder_part.endswith("**") or "**" in pattern_part:
                        # Recursive pattern detected
                        st.session_state[f"dlg_{loader_name}_recursive"] = True
                        # Extract actual folder (remove **/)
                        if folder_part.endswith("**"):
                            folder_part = folder_part[:-3] if folder_part.endswith(
                                "/**") else folder_part[:-2]
                        # Clean pattern (remove **/ prefix if present)
                        if pattern_part.startswith("**/"):
                            pattern_part = pattern_part[3:]
                    else:
                        st.session_state[f"dlg_{loader_name}_recursive"] = False

                    # Set folder
                    if folder_part and os.path.isdir(folder_part):
                        st.session_state[folder_key] = folder_part
                    else:
                        st.session_state[folder_key] = original_path

                    # Detect pattern type from extension
                    PATTERN_REVERSE_MAP = {
                        "*.csv": "CSV (*.csv)",
                        "*.xlsx": "Excel (*.xlsx)",
                        "*.parquet": "Parquet (*.parquet)",
                        "*.json": "JSON (*.json)",
                        "*": "All Supported Files (*)",
                    }
                    if pattern_part in PATTERN_REVERSE_MAP:
                        st.session_state[f"dlg_{loader_name}_pat_type"] = PATTERN_REVERSE_MAP[pattern_part]
                    else:
                        # Custom pattern
                        st.session_state[f"dlg_{loader_name}_pat_type"] = "Custom"
                        st.session_state[f"dlg_{loader_name}_pat_custom"] = pattern_part
            else:
                st.session_state[mode_key] = "Single File"
                st.session_state[path_key] = original_path

            # Excel settings - PRE-FILL THE WIDGET KEYS
            # Check for Table Mode (either explicit selection or dynamic filters)
            if params.get("table") or params.get("table_filters"):
                st.session_state[f"dlg_{loader_name}_excel_target"] = "Table"
                # For table mode, the widget key is `dlg_{loader_name}_table_mode`
                if params.get("table_filters"):
                    st.session_state[f"dlg_{loader_name}_table_mode"] = "Dynamic Filter"
                else:
                    st.session_state[f"dlg_{loader_name}_table_mode"] = "Manual Selection"

            # Check for Sheet Mode (either explicit selection or dynamic filters)
            elif params.get("sheet") or params.get("sheet_filters"):
                st.session_state[f"dlg_{loader_name}_excel_target"] = "Sheet"

                if params.get("sheet_filters"):
                    st.session_state[f"dlg_{loader_name}_sheet_mode"] = "Dynamic Filter"
                else:
                    st.session_state[f"dlg_{loader_name}_sheet_mode"] = "Manual Selection"

            # Options - use session state keys
            st.session_state[f"dlg_{loader_name}_process_individual"] = params.get(
                "process_individual", False)
            st.session_state[f"dlg_{loader_name}_include_src"] = params.get(
                "include_source_info", False)
            st.session_state[f"dlg_{loader_name}_clean_headers"] = params.get(
                "clean_headers", False)
            st.session_state[f"dlg_{loader_name}_auto_infer"] = params.get(
                "auto_infer", False)
            if edit_mode:
                st.session_state[f"dlg_{loader_name}_split_sheets"] = False
                st.session_state[f"dlg_{loader_name}_split_files"] = False
            else:
                st.session_state[f"dlg_{loader_name}_split_sheets"] = params.get(
                    "split_sheets", False)
                if "split_files" in params:
                    st.session_state[f"dlg_{loader_name}_split_files"] = params.get(
                        "split_files", False)

            # --- PRE-FILL FILTERS ---
            # Helper to convert ItemFilter objects (Pydantic) or dicts to display format
            def convert_filters_for_display(filter_list):
                result = []
                if filter_list:
                    for f in filter_list:
                        if hasattr(f, 'type') and hasattr(f, 'value'):
                            # Pydantic model
                            f_type = f.type.value if hasattr(
                                f.type, 'value') else str(f.type)
                            result.append(
                                {"type": f_type, "value": f.value, "target": getattr(f, 'target', 'name')})
                        elif isinstance(f, dict):
                            f_type = f.get('type', '')
                            if hasattr(f_type, 'value'):
                                f_type = f_type.value
                            result.append({"type": str(f_type), "value": f.get(
                                'value', ''), "target": f.get('target', 'name')})
                return result

            # Path filters
            if params.get("filters"):
                st.session_state[f"dlg_{loader_name}_filters"] = convert_filters_for_display(
                    params["filters"])

            # Sheet filters
            if params.get("sheet_filters"):
                st.session_state[f"dlg_{loader_name}_sheet_filters"] = convert_filters_for_display(
                    params["sheet_filters"])

            # Table filters
            if params.get("table_filters"):
                st.session_state[f"dlg_{loader_name}_table_filters"] = convert_filters_for_display(
                    params["table_filters"])

            # Pre-fill selected sheets if manually selected
            if params.get("sheet"):
                if params["sheet"] == "__ALL_SHEETS__":
                    st.session_state[f"dlg_{loader_name}_sht_all_g"] = True
                elif isinstance(params["sheet"], list):
                    # For manual selection, we default to the list.
                    # NOTE: This key is used in multiselect `default` param, BUT multiselect uses `key` for state
                    st.session_state[f"dlg_{loader_name}_sel_sheet"] = params["sheet"]

            # Pre-fill selected tables if manually selected
            if params.get("table"):
                if params["table"] == "__ALL_TABLES__":
                    st.session_state[f"dlg_{loader_name}_tbl_all_g"] = True
                elif isinstance(params["table"], list):
                    st.session_state[f"dlg_{loader_name}_sel_table"] = params["table"]
                    st.session_state[f"dlg_{loader_name}_final_table"] = params["table"]

        # Mark as initialized to avoid re-running
        st.session_state[edit_init_key] = True

    # Defaults
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "Single File"
    if path_key not in st.session_state:
        st.session_state[path_key] = ""
    if folder_key not in st.session_state:
        st.session_state[folder_key] = ""
    if recent_paths_key not in st.session_state:
        st.session_state[recent_paths_key] = []

    # Callback to Trigger Load check
    def trigger_check_load():
        if st.session_state[path_key]:  # Only if path exists
            p = st.session_state[path_key]
            if os.path.exists(p):
                st.session_state[f"dlg_{loader_name}_trigger"] = True
            else:
                st.toast("Path does not exist", icon="❌")

    alias_default = f"data_{len(st.session_state.all_recipes) + 1}"
    # Set alias default if not already in session state
    alias_key = f"dlg_{loader_name}_alias"
    if alias_key not in st.session_state:
        st.session_state[alias_key] = alias_default

    # 1. CORE IDENTITY (Always Visible)
    c_alias, c_mode = st.columns([0.65, 0.35])
    alias_val = c_alias.text_input(
        "Dataset Alias", key=alias_key, help="Unique name for this dataset", disabled=is_busy)
    mode = c_mode.radio(
        "Import Mode", ["Single File", "Folder Pattern"], horizontal=True, key=mode_key, disabled=is_busy)

    # 2. CONFIGURATION EXPANDER
    # Collapsed when busy to focus on status
    with st.expander("📂 Source & Settings", expanded=not is_busy):

        # --- SOURCE CONFIGURATION ---
        effective_path = ""
        folder_input = None

        # Path Input Block
        if mode == "Single File":
            # RECENT PATHS
            recents = st.session_state[recent_paths_key]
            if recents:
                def on_recent_change():
                    sel = st.session_state[f"{loader_name}_recent_sel"]
                    if sel != "Select recent...":
                        st.session_state[path_key] = sel

                c_rec, c_clr = st.columns([0.85, 0.15])
                c_rec.selectbox("Recent Paths", [
                                "Select recent..."] + recents, key=f"{loader_name}_recent_sel", on_change=on_recent_change, label_visibility="collapsed")
                if c_clr.button("Clear", help="Clear History"):
                    st.session_state[recent_paths_key] = []
                    st.rerun()

            col_path, col_btn = st.columns([0.85, 0.15])
            path_input = col_path.text_input("File Path", key=path_key, disabled=is_busy,
                                             help="Enter path to file.")

            def callback_pick_file():
                picked = pick_file("Select File")
                if picked:
                    st.session_state[path_key] = picked
            col_btn.button("📂", on_click=callback_pick_file,
                           key="btn_pick_file", help="Browse Files", disabled=is_busy)
            effective_path = path_input

        else:  # Folder Pattern
            col_dir, col_btn = st.columns([0.85, 0.15])
            folder_input = col_dir.text_input(
                "Base Folder", key=folder_key, disabled=is_busy)

            def callback_pick_folder():
                picked = pick_folder("Select Folder")
                if picked:
                    st.session_state[folder_key] = picked
            col_btn.button("📂", on_click=callback_pick_folder,
                           key="btn_pick_folder", help="Browse Folder", disabled=is_busy)

            # Pattern Config
            c1, c2, c_rec = st.columns([0.4, 0.35, 0.25])
            PATTERNS = {
                "CSV (*.csv)": "*.csv",
                "Excel (*.xlsx)": "*.xlsx",
                "Parquet (*.parquet)": "*.parquet",
                "JSON (*.json)": "*.json",
                "All Supported Files (*)": "*",
                "Custom": "custom"
            }

            pat_key = f"dlg_{loader_name}_pat_type"
            sel_pat_label = c1.selectbox(
                "Pattern Type", list(PATTERNS.keys()), key=pat_key, disabled=is_busy)

            base_pattern = PATTERNS[sel_pat_label]
            is_custom = base_pattern == "custom"

            if is_custom:
                base_pattern = c2.text_input(
                    "Custom Pattern", value="*.csv", key=f"dlg_{loader_name}_pat_custom", disabled=is_busy)
                # Disable recursive for custom (user can type their own)
                recursive = False
                c_rec.caption("Recursive: N/A")
                final_pattern = base_pattern
            else:
                # Recursive checkbox first (so we can compute preview)
                recursive = c_rec.checkbox(
                    "🔄 Recursive",
                    key=f"dlg_{loader_name}_recursive",
                    help="Search subdirectories (adds **/ prefix)",
                    disabled=is_busy
                )

                # Build final pattern for preview
                if recursive and not base_pattern.startswith("**/"):
                    final_pattern = f"**/{base_pattern}"
                else:
                    final_pattern = base_pattern

                # Show final pattern in preview
                c2.text_input("Pattern Preview",
                              value=final_pattern, disabled=True)

            if folder_input and final_pattern:
                effective_path = os.path.join(folder_input, final_pattern)

        # --- ADVANCED PATH FILTERS ---
        filter_key = f"dlg_{loader_name}_filters"
        if filter_key not in st.session_state:
            st.session_state[filter_key] = []

        effective_filters = []

        if mode == "Folder Pattern":
            with st.expander("🔍 Advanced File & Path Filters", expanded=False):
                st.caption(
                    "Apply additional filters to file paths & file names.")

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
                        "✕", key=f"btn_del_filt_{i}", on_click=delete_filter, args=(i,), disabled=is_busy)

                # Add New
                st.divider()
                c_add_1, c_add_2, c_add_3, c_add_4 = st.columns(
                    [0.25, 0.25, 0.4, 0.1])
                new_f_type = c_add_1.selectbox(
                    "Type", ["contains", "regex", "exact", "glob", "not_contains", "is_not"], key="new_filt_type", disabled=is_busy)
                new_f_target = c_add_2.selectbox(
                    "Target", ["filename", "path"], key="new_filt_target", disabled=is_busy)
                new_f_val = c_add_3.text_input(
                    "Value", key="new_filt_val", disabled=is_busy)

                def add_filter():
                    if st.session_state.new_filt_val:
                        st.session_state[filter_key].append({
                            "type": st.session_state.new_filt_type,
                            "value": st.session_state.new_filt_val,
                            "target": st.session_state.new_filt_target
                        })
                        st.session_state.new_filt_val = ""

                c_add_4.button("➕", on_click=add_filter,
                               key="btn_add_filt", disabled=is_busy)

            # Convert to FileFilter objects
            if st.session_state[filter_key]:
                for f in st.session_state[filter_key]:
                    if f['type'] in FILTER_TYPE_MAP:
                        effective_filters.append(FileFilter(
                            type=FILTER_TYPE_MAP[f['type']],
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

        # --- EXCEL SHEETS (Conditional) ---
        selected_sheets = ["Sheet1"]

        if is_excel and effective_path:
            with st.expander("📊 Excel Settings", expanded=True):
                try:
                    # Handle Glob Base Selection
                    if "*" in effective_path:
                        # Quick scan for potential base files (limit 50 for UI)
                        matches = []
                        try:
                            # Use cached resolver to verify filters are respected
                            resolved = get_cached_resolved_files(
                                engine, effective_path, effective_filters, limit=50)

                            # Filter for Excel extensions just in case pattern was broad
                            for f in resolved:
                                if f.lower().endswith(('.xlsx', '.xls', '.xlsm')):
                                    matches.append(f)
                        except:
                            pass

                        if matches:
                            base_selection = st.selectbox(
                                "Select Base File (Template)",
                                matches,
                                help="Choose a file to populate the sheet list from.",
                                disabled=is_busy
                            )
                            sheet_source_file = base_selection
                        else:
                            st.warning(
                                "No Excel files found matching pattern.")
                            sheet_source_file = None

                    if sheet_source_file:
                        # --- EXCEL LOAD TARGET MODE ---
                        c_target, c_mode_sel = st.columns(2)

                        # LEFT: Toggle between Sheets and Tables
                        excel_load_target = c_target.radio("Load Target", [
                            "Sheet", "Table"], horizontal=True, key=f"dlg_{loader_name}_excel_target", disabled=is_busy)

                        if excel_load_target == "Table":
                            # TABLE MODE
                            # RIGHT: Selection Mode
                            table_mode = c_mode_sel.radio("Selection Mode", [
                                "Manual Selection", "Dynamic Filter"], horizontal=True, key=f"dlg_{loader_name}_table_mode", disabled=is_busy)
                            # Persist
                            st.session_state[f"dlg_{loader_name}_table_mode_selection"] = table_mode

                            st.divider()

                            if table_mode == "Manual Selection":
                                tables = get_cached_table_names(
                                    engine, sheet_source_file)
                                if not tables:
                                    st.warning(
                                        "No named tables found in this file.")
                                    st.session_state[f"dlg_{loader_name}_final_table"] = None
                                else:
                                    # Filter UI
                                    t_col_f, t_col_act = st.columns([0.6, 0.4])
                                    table_filter = t_col_f.text_input(
                                        "Filter Tables", "", placeholder="e.g. Table.*", key=f"dlg_{loader_name}_tbl_regex")

                                    filtered_tables = tables
                                    if table_filter:
                                        filtered_tables = filter_list_by_regex(
                                            tables, table_filter)

                                    # Select All Logic
                                    c_all, c_vis = t_col_act.columns(2)
                                    sel_all_global = c_all.checkbox(
                                        "All", key=f"dlg_{loader_name}_tbl_all_g", help="Select all tables in file")
                                    sel_all_vis = c_vis.checkbox(
                                        "Filtered", key=f"dlg_{loader_name}_tbl_all_v", disabled=not table_filter, help="Select all visible tables")

                                    if sel_all_global:
                                        st.session_state[f"dlg_{loader_name}_final_table"] = tables
                                        st.caption(
                                            f"Selected all {len(tables)} tables.")
                                    elif sel_all_vis:
                                        st.session_state[f"dlg_{loader_name}_final_table"] = filtered_tables
                                        st.caption(
                                            f"Selected {len(filtered_tables)} filtered tables.")
                                    else:
                                        selected_table = st.multiselect(
                                            "Select Table(s)",
                                            filtered_tables,
                                            default=[filtered_tables[0]
                                                     ] if filtered_tables else [],
                                            key=f"dlg_{loader_name}_sel_table",
                                            disabled=is_busy
                                        )
                                        st.session_state[f"dlg_{loader_name}_final_table"] = selected_table
                            else:
                                # DYNAMIC TABLE FILTERS
                                st.caption(
                                    "Define rules to select tables automatically from ALL files.")
                                # Clear manual selection
                                st.session_state[f"dlg_{loader_name}_final_table"] = [
                                ]

                                t_filter_key = f"dlg_{loader_name}_table_filters"
                                if t_filter_key not in st.session_state:
                                    st.session_state[t_filter_key] = []

                                # Show Existing Filters
                                for i, f in enumerate(st.session_state[t_filter_key]):
                                    c1, c2, c3 = st.columns([0.3, 0.6, 0.1])
                                    c1.markdown(f"**{f['type']}**")
                                    c2.text(f['value'])

                                    def del_t_filter(idx):
                                        st.session_state[t_filter_key].pop(idx)
                                    c3.button("✕", key=f"btn_del_tfilt_{i}", on_click=del_t_filter, args=(
                                        i,), disabled=is_busy)

                                # Add New Filter
                                with st.container(border=True):
                                    c_add_1, c_add_2, c_add_3 = st.columns(
                                        [0.4, 0.5, 0.1])
                                    new_t_type = c_add_1.selectbox("Type", [
                                                                   "contains", "regex", "exact", "glob", "not_contains", "is_not"], key="new_tfilt_type", disabled=is_busy)
                                    new_t_val = c_add_2.text_input(
                                        "Pattern", key="new_tfilt_val", disabled=is_busy)

                                    def add_t_filter():
                                        if st.session_state.new_tfilt_val:
                                            st.session_state[t_filter_key].append({
                                                "type": st.session_state.new_tfilt_type,
                                                "value": st.session_state.new_tfilt_val
                                            })
                                            st.session_state.new_tfilt_val = ""

                                    c_add_3.button(
                                        "➕", on_click=add_t_filter, key="btn_add_tfilt", disabled=is_busy)

                                # Preview Matches (Base File)
                                if st.session_state[t_filter_key]:
                                    try:
                                        base_tables = get_cached_table_names(
                                            engine, sheet_source_file)
                                        st.caption(
                                            f"Filters will be applied to all files. (Base file has {len(base_tables)} tables)")
                                    except:
                                        pass

                        else:
                            # SHEET MODE
                            # RIGHT: Selection Mode
                            sheet_mode = c_mode_sel.radio("Selection Mode", [
                                "Manual Selection", "Dynamic Filter"], horizontal=True, key=f"dlg_{loader_name}_sheet_mode", disabled=is_busy)
                            st.session_state[f"dlg_{loader_name}_sheet_mode_selection"] = sheet_mode

                            st.divider()

                            # Reset
                            st.session_state[f"dlg_{loader_name}_final_table"] = None

                            if sheet_mode == "Manual Selection":
                                # Existing Logic
                                sheets = get_cached_sheet_names(
                                    engine, sheet_source_file)

                                col_filter, col_act = st.columns([0.6, 0.4])
                                sheet_filter = col_filter.text_input(
                                    "Filter Sheets", "", key="sheet_regex_filter", placeholder="e.g. Sheet.*", disabled=is_busy)

                                filtered_sheets = sheets
                                if sheet_filter:
                                    filtered_sheets = filter_list_by_regex(
                                        sheets, sheet_filter)

                                c_all_s, c_vis_s = col_act.columns(2)
                                all_sheets_global = c_all_s.checkbox(
                                    "All", value=False, key=f"dlg_{loader_name}_sht_all_g", disabled=is_busy, help="Select all sheets")
                                all_sheets_vis = c_vis_s.checkbox(
                                    "Filtered", value=False, key=f"dlg_{loader_name}_sht_all_v", disabled=not sheet_filter, help="Select visible sheets")

                                if all_sheets_global:
                                    selected_sheets = sheets
                                    st.caption(
                                        f"Selected all {len(sheets)} sheets.")
                                elif all_sheets_vis:
                                    selected_sheets = filtered_sheets
                                    st.caption(
                                        f"Selected {len(filtered_sheets)} filtered sheets.")
                                else:
                                    # Get pre-filled sheets from edit mode if available
                                    prefill_key = f"dlg_{loader_name}_sel_sheet"
                                    prefilled_sheets = st.session_state.get(
                                        prefill_key, [])

                                    # Determine default - use prefilled if valid, else fallback
                                    if prefilled_sheets and all(s in filtered_sheets for s in prefilled_sheets):
                                        default_sheets = prefilled_sheets
                                    elif "Sheet1" in filtered_sheets:
                                        default_sheets = ["Sheet1"]
                                    elif filtered_sheets:
                                        default_sheets = [filtered_sheets[0]]
                                    else:
                                        default_sheets = []

                                    selected_sheets = st.multiselect(
                                        "Select Sheets",
                                        filtered_sheets,
                                        default=default_sheets,
                                        disabled=is_busy
                                    )
                            else:
                                # DYNAMIC FILTERS (New)
                                st.caption(
                                    "Define rules to select sheets automatically from ALL files.")

                                s_filter_key = f"dlg_{loader_name}_sheet_filters"
                                if s_filter_key not in st.session_state:
                                    st.session_state[s_filter_key] = []

                                # Show Existing Filters
                                for i, f in enumerate(st.session_state[s_filter_key]):
                                    c1, c2, c3 = st.columns([0.3, 0.6, 0.1])
                                    c1.markdown(f"**{f['type']}**")
                                    c2.text(f['value'])

                                    def del_s_filter(idx):
                                        st.session_state[s_filter_key].pop(idx)
                                    c3.button("✕", key=f"btn_del_sfilt_{i}", on_click=del_s_filter, args=(
                                        i,), disabled=is_busy)

                                # Add New Filter
                                with st.container(border=True):
                                    c_add_1, c_add_2, c_add_3 = st.columns(
                                        [0.4, 0.5, 0.1])
                                    new_s_type = c_add_1.selectbox("Type", [
                                                                   "contains", "regex", "exact", "glob", "not_contains", "is_not"], key="new_sfilt_type", disabled=is_busy)
                                    new_s_val = c_add_2.text_input(
                                        "Pattern", key="new_sfilt_val", disabled=is_busy)

                                    def add_s_filter():
                                        if st.session_state.new_sfilt_val:
                                            st.session_state[s_filter_key].append({
                                                "type": st.session_state.new_sfilt_type,
                                                "value": st.session_state.new_sfilt_val
                                            })
                                            st.session_state.new_sfilt_val = ""

                                    c_add_3.button(
                                        "➕", on_click=add_s_filter, key="btn_add_sfilt", disabled=is_busy)

                                # Preview Matches (Base File)
                                if st.session_state[s_filter_key]:
                                    try:
                                        base_sheets = get_cached_sheet_names(
                                            engine, sheet_source_file)
                                        # Client-side preview check (simple approximation)
                                        # converting dict filters to IO Params filters logic is strict in backend
                                        # Here we approximate for UI feedback
                                        preview_matches = []

                                        # Build temporary filters
                                        temp_filters = []
                                        for f in st.session_state[s_filter_key]:
                                            if f['type'] in FILTER_TYPE_MAP:
                                                temp_filters.append(ItemFilter(
                                                    type=FILTER_TYPE_MAP[f['type']], value=f['value']))

                                        # Reuse Backend Helper logic (replicated for Frontend simplicity or imported?)
                                        # Since we can't easily import backend internal helpers, we use a simple loop
                                        # Or better: Just show "Applied dynamically to all files"
                                        st.caption(
                                            f"Filters will be applied to all files. (Base file has {len(base_sheets)} sheets)")
                                    except:
                                        pass
                except Exception as e:
                    st.warning(f"Could not read sheets: {e}")

        # --- PREVIEW & REVIEW (Dynamic Tabs) ---
        with st.expander("🔎 Preview & Review", expanded=True):
            tabs_labels = ["📂 Matched Files"]
            if is_excel and effective_path:
                target_mode = st.session_state.get(
                    f"dlg_{loader_name}_excel_target", "Sheet")
                if target_mode == "Table":
                    tabs_labels.append("📑 Selected Tables")
                else:
                    tabs_labels.append("📑 Selected Sheets")

            tabs = st.tabs(tabs_labels)

            # TAB 1: Files
            with tabs[0]:
                if effective_path:
                    if st.button("Load File Preview", key=f"btn_{loader_name}_preview"):
                        try:
                            # Use resolve_files via Engine (CACHED)
                            found_files = []
                            try:
                                found_files = get_cached_resolved_files(
                                    engine, effective_path, effective_filters, limit=1000)
                            except Exception as e:
                                st.error(f"Error resolving paths: {e}")

                            scan_limit = 1000
                            count = len(found_files)

                            display_files = found_files[:scan_limit]
                            data = []
                            for f in display_files:
                                data.append({
                                    "File Name": os.path.basename(f),
                                    "Type": os.path.splitext(f)[1],
                                    "Path": f
                                })

                            if found_files:
                                st.success(
                                    f"Found {len(found_files)}{'+' if count >= scan_limit else ''} files.")
                                st.dataframe(pd.DataFrame(data))
                            else:
                                st.warning(
                                    "No files found matching the pattern.")
                        except Exception as e:
                            st.error(f"Error previewing files: {e}")
                    else:
                        st.caption(
                            "Click to preview matched files (Optimized for speed).")
                else:
                    st.info("Select a path to preview files.")

            # TAB 2: Sheets or Tables
            if is_excel:
                final_table = st.session_state.get(
                    f"dlg_{loader_name}_final_table")
                src_fname = os.path.basename(
                    sheet_source_file) if sheet_source_file else "Multiple/Pattern"

                if final_table and len(tabs) > 1:
                    with tabs[1]:
                        # Enhanced Table Layout
                        df_table = pd.DataFrame({
                            "Table Name": final_table,
                            "Source Type": ["Manual Selection"] * len(final_table),
                            "Source File": [src_fname] * len(final_table)
                        })
                        st.dataframe(df_table, hide_index=True)

                elif len(tabs) > 1:
                    with tabs[1]:
                        # Logic depends on mode
                        target_mode = st.session_state.get(
                            f"dlg_{loader_name}_excel_target", "Sheet")
                        is_table_dynamic = target_mode == "Table" and st.session_state.get(
                            f"dlg_{loader_name}_table_mode_selection") == "Dynamic Filter"
                        is_sheet_dynamic = target_mode == "Sheet" and st.session_state.get(
                            f"dlg_{loader_name}_sheet_mode_selection") == "Dynamic Filter"

                        if is_table_dynamic:
                            t_filts = st.session_state.get(
                                f"dlg_{loader_name}_table_filters", [])
                            if t_filts:
                                st.info(
                                    f"Filters check against template: {src_fname}")
                                try:
                                    # Reconstruct Filters
                                    preview_filters = []
                                    for f in t_filts:
                                        if f['type'] in FILTER_TYPE_MAP:
                                            preview_filters.append(ItemFilter(
                                                type=FILTER_TYPE_MAP[f['type']],
                                                value=f['value']
                                            ))

                                    # Get Tables & Filter
                                    if sheet_source_file:
                                        base_tables = get_cached_table_names(
                                            engine, sheet_source_file)
                                    else:
                                        base_tables = []

                                    # Reuse filter_sheet_names as generic string filter
                                    matched = filter_sheet_names(
                                        base_tables, preview_filters)

                                    # Enhanced Dynamic Preview
                                    df_dynamic = pd.DataFrame({
                                        "Matched Table Name": matched,
                                        "Match Rule": ["Dynamic Filter"] * len(matched),
                                        "Source File": [src_fname] * len(matched)
                                    })

                                    st.dataframe(df_dynamic, hide_index=True)

                                    if not matched:
                                        st.warning(
                                            "No tables in the template file match these filters.")

                                except Exception as e:
                                    st.error(f"Error generating preview: {e}")
                            else:
                                st.info("No table filters defined.")

                        elif is_sheet_dynamic:
                            s_filts = st.session_state.get(
                                f"dlg_{loader_name}_sheet_filters", [])
                            if s_filts:
                                st.info(
                                    f"Filters check against template: {src_fname}")

                                try:
                                    # Reconstruct Filters
                                    preview_filters = []
                                    for f in s_filts:
                                        if f['type'] in FILTER_TYPE_MAP:
                                            preview_filters.append(ItemFilter(
                                                type=FILTER_TYPE_MAP[f['type']],
                                                value=f['value']
                                            ))

                                    # Get Sheets & Filter
                                    if sheet_source_file:
                                        base_sheets = get_cached_sheet_names(
                                            engine, sheet_source_file)
                                    else:
                                        base_sheets = []
                                    matched = filter_sheet_names(
                                        base_sheets, preview_filters)

                                    # Enhanced Dynamic Preview
                                    df_dynamic = pd.DataFrame({
                                        "Matched Sheet Name": matched,
                                        "Match Rule": ["Dynamic Filter"] * len(matched),
                                        "Source File": [src_fname] * len(matched)
                                    })

                                    st.dataframe(df_dynamic, hide_index=True)

                                    if not matched:
                                        st.warning(
                                            "No sheets in the template file match these filters.")

                                except Exception as e:
                                    st.error(f"Error generating preview: {e}")
                            else:
                                st.info("No filters defined.")
                        elif selected_sheets:
                            # Enhanced Manual Sheet Layout
                            df_manual = pd.DataFrame({
                                "Sheet Name": selected_sheets,
                                "Source Type": ["Manual Selection"] * len(selected_sheets),
                                "Source File": [src_fname] * len(selected_sheets)
                            })
                            st.dataframe(df_manual, hide_index=True)

        # --- SETTINGS ---
        with st.expander("⚙️ Loading Settings", expanded=not is_busy):
            c_s1, c_s2 = st.columns(2)

            with c_s1:
                st.markdown("**Extraction Behavior**")
                process_individual = False
                split_sheets = False

                # Initialize toggle defaults if not in session state
                if f"dlg_{loader_name}_process_individual" not in st.session_state:
                    st.session_state[f"dlg_{loader_name}_process_individual"] = False
                if f"dlg_{loader_name}_split_sheets" not in st.session_state:
                    st.session_state[f"dlg_{loader_name}_split_sheets"] = False
                if f"dlg_{loader_name}_clean_headers" not in st.session_state:
                    st.session_state[f"dlg_{loader_name}_clean_headers"] = False
                if f"dlg_{loader_name}_include_src" not in st.session_state:
                    st.session_state[f"dlg_{loader_name}_include_src"] = False
                if f"dlg_{loader_name}_auto_infer" not in st.session_state:
                    st.session_state[f"dlg_{loader_name}_auto_infer"] = False

                if mode == "Folder Pattern":
                    process_individual = st.toggle(
                        "Process Individually",
                        key=f"dlg_{loader_name}_process_individual",
                        help="Process each file as an individual unit rather than combining them.",
                        disabled=is_busy
                    )
                    split_files = st.toggle(
                        "Split Files",
                        key=f"dlg_{loader_name}_split_files",
                        help="Create a separate dataset for each file found.",
                        disabled=is_busy or edit_mode
                    )
                else:
                    st.caption("Not applicable for single file.")
                    # Reset if switching back to single file
                    st.session_state[f"dlg_{loader_name}_split_files"] = False

                if is_excel:
                    split_sheets = st.toggle(
                        "Split Sheets",
                        key=f"dlg_{loader_name}_split_sheets",
                        help="Create a separate dataset for each selected sheet/table in every matching file.",
                        disabled=is_busy or edit_mode
                    )
                else:
                    # Reset if not applicable
                    st.session_state[f"dlg_{loader_name}_split_sheets"] = False

            with c_s2:
                st.markdown("**Schema & Metadata**")
                clean_headers = st.toggle(
                    "Clean Headers", key=f"dlg_{loader_name}_clean_headers", help="Standardize header names.", disabled=is_busy)
                include_src = st.toggle(
                    "Include Source Path", key=f"dlg_{loader_name}_include_src", help="Add 'source_file' column.", disabled=is_busy)
                auto_infer = st.toggle("Auto Infer Types", key=f"dlg_{loader_name}_auto_infer",
                                       help="Inspect & Cast types after load.", disabled=is_busy)

    # Combined Button Label
    btn_label = "Update Dataset" if edit_mode else "Load Data"
    btn_type = "primary"

    c_cancel, c_submit = st.columns([0.3, 0.7])

    if c_cancel.button("Cancel", key=f"btn_{loader_name}_cancel", disabled=is_busy):
        st.session_state.show_loader_file = False
        st.rerun()

    if c_submit.button(btn_label, type=btn_type, width="stretch", disabled=is_busy):
        if not alias_val:
            st.error("Alias is required.")
        elif mode == "Single File" and (not effective_path or not os.path.exists(effective_path)):
            st.error(f"File not found: {effective_path}")
        elif mode == "Single File" and not os.path.isfile(effective_path):
            st.error(f"Not a file: {effective_path}")
        elif mode == "Folder Pattern" and (not folder_input or not os.path.isdir(folder_input)):
            st.error(f"Directory not found: {folder_input}")
        else:
            # PACK JOB PARAMS
            final_table = st.session_state.get(
                f"dlg_{loader_name}_final_table")

            # Prepare Filters
            effective_sheet_filters = None
            effective_table_filters = None
            effective_sheets = None

            # Check target mode from session state to handle empty selections correctly
            excel_target_mode = st.session_state.get(
                f"dlg_{loader_name}_excel_target", "Sheet")

            if excel_target_mode == "Table":
                # Table Mode
                table_mode = st.session_state.get(
                    f"dlg_{loader_name}_table_mode_selection")

                # Check Select All Global
                if st.session_state.get(f"dlg_{loader_name}_tbl_all_g", False):
                    final_table = "__ALL_TABLES__"

                elif table_mode == "Dynamic Filter":
                    # BUILD TABLE FILTERS
                    t_filts = st.session_state.get(
                        f"dlg_{loader_name}_table_filters", [])
                    if t_filts:
                        effective_table_filters = []
                        for f in t_filts:
                            if f['type'] in FILTER_TYPE_MAP:
                                effective_table_filters.append(ItemFilter(
                                    type=FILTER_TYPE_MAP[f['type']],
                                    value=f['value']
                                ))

            elif not final_table:
                # Sheet Mode (and no table selected - creating mutually exclusive path)
                sheet_mode = st.session_state.get(
                    f"dlg_{loader_name}_sheet_mode_selection")

                # Check Select All Global Sheet
                if st.session_state.get(f"dlg_{loader_name}_sht_all_g", False):
                    effective_sheets = "__ALL_SHEETS__"

                elif sheet_mode == "Dynamic Filter":
                    # BUILD SHET FILTERS
                    s_filts = st.session_state.get(
                        f"dlg_{loader_name}_sheet_filters", [])
                    if s_filts:
                        effective_sheet_filters = []
                        for f in s_filts:
                            if f['type'] in FILTER_TYPE_MAP:
                                effective_sheet_filters.append(ItemFilter(
                                    type=FILTER_TYPE_MAP[f['type']],
                                    value=f['value']
                                ))
                else:
                    effective_sheets = selected_sheets

            params = {
                "path": effective_path,
                "filters": effective_filters,
                "sheet": effective_sheets,
                "sheet_filters": effective_sheet_filters,
                "table": final_table,
                "table_filters": effective_table_filters,
                "alias": alias_val,
                "process_individual": process_individual,
                "include_source_info": include_src,
                "clean_headers": clean_headers,
                "auto_infer": auto_infer,
                "split_sheets": split_sheets,
                "split_files": st.session_state.get(f"dlg_{loader_name}_split_files", False)
            }

            st.session_state[job_params_key] = params
            st.session_state[busy_key] = True
            st.session_state[action_key] = "check_and_load"  # New start state
            st.rerun()

    # --- EXECUTION (VISUALIZED BELOW) ---
    if is_busy:
        action = st.session_state[action_key]
        job_params = st.session_state[job_params_key]

        # Container for Status - Below the form
        with st.status(f"Processing...", expanded=True) as status:
            try:
                # --- STEP 1: RESOLVE & CHECK ENCODING ---
                if action == "check_and_load":
                    st.write("🔍 Resolving files & checking encodings...")

                    effective_path = job_params["path"]
                    effective_filters = job_params["filters"]

                    # 1. Resolve Files
                    all_files = get_cached_resolved_files(
                        engine, effective_path, effective_filters)
                    if not all_files:
                        raise Exception("No files matches the criteria.")

                    # 2. Check Encodings (Only for relevant types)
                    issues = {}
                    is_csv_or_text = False

                    # Heuristic check on first file or path extension
                    sample_ext = os.path.splitext(effective_path)[1].lower(
                    ) if os.path.isfile(effective_path) else ""
                    if not sample_ext and all_files:
                        sample_ext = os.path.splitext(all_files[0])[1].lower()

                    if sample_ext in [".csv", ".txt", ".json", ".ndjson"] or "*" in effective_path:
                        # Perform scan
                        issues = get_cached_encoding_scan(engine, all_files)

                    if issues:
                        st.info(
                            f"⚠️ Found {len(issues)} files with non-standard valid encoding. Converting...")
                        job_params["issues"] = issues
                        job_params["all_files"] = all_files
                        action = "convert_and_load"
                    else:
                        st.write("✅ Encodings are valid.")
                        job_params["all_files"] = all_files
                        action = "load"

                # --- STEP 2: CONVERT (If needed) ---
                if action == "convert_and_load":
                    st.info("🔄 Converting files to UTF-8...")
                    issues = job_params.get("issues", {})
                    all_files = job_params.get("all_files", [])

                    new_file_list = []
                    # 1. Perform Conversion
                    for f in all_files:
                        if f in issues:
                            # st.write(f"Converting {os.path.basename(f)}...")
                            src_enc = issues[f]
                            new_path = engine.io.convert_encoding(f, src_enc)
                            new_file_list.append(new_path)
                        else:
                            new_file_list.append(f)

                    st.success(f"✅ Converted {len(issues)} files.")

                    # 2. Update params with converted files override
                    job_params["files"] = new_file_list
                    action = "load"

                # --- STEP 3: LOAD ---
                if action == "load":
                    # --- LOAD LOGIC ---
                    st.info("📖 Reading data...")

                    alias_val = job_params["alias"]
                    split_sheets = job_params.get("split_sheets", False)
                    split_files = job_params.get("split_files", False)
                    auto_infer = job_params.get("auto_infer", False)

                    # --- SPLIT FILES LOGIC (Folder Mode) ---
                    # Priority: Split Sheets > Split Files
                    # If both are selected, we want Split Sheets logic (which is granular per file-sheet)
                    if split_files and not split_sheets and job_params.get("all_files"):
                        # We use 'all_files' from the 'check' phase
                        target_files = job_params["all_files"]

                        last_active_alias = alias_val
                        progress_text = "Importing Files..."
                        my_bar = st.progress(0, text=progress_text)

                        total_files = len(target_files)

                        for i, file_path in enumerate(target_files):
                            fname = os.path.basename(file_path)
                            my_bar.progress((i + 1) / total_files,
                                            text=f"Importing {fname}...")

                            # Clean filename for alias
                            safe_name = re.sub(
                                r'[^a-zA-Z0-9_]', '_', os.path.splitext(fname)[0])
                            current_alias = f"{alias_val}_{safe_name}"

                            curr_params = job_params.copy()
                            # Point to specific file
                            curr_params["path"] = file_path
                            curr_params["alias"] = current_alias
                            # Clear filters as we resolved specific file
                            curr_params["filters"] = []
                            # Single file now
                            curr_params["process_individual"] = False

                            # Load
                            res_item = engine.io.run_loader(
                                "File", curr_params)
                            if res_item:
                                lf, meta = res_item
                                engine.datasets.add(current_alias, lf, meta,
                                                    loader_type="File",
                                                    loader_params=curr_params)

                                if current_alias not in st.session_state.all_recipes:
                                    st.session_state.all_recipes[current_alias] = [
                                    ]

                                if auto_infer:
                                    handle_auto_inference(
                                        engine, current_alias)

                                last_active_alias = current_alias

                        st.session_state.active_base_dataset = last_active_alias
                        st.session_state.recipe_steps = []
                        my_bar.empty()

                    elif split_sheets:
                        # Multi-Dataset Load (Split Sheets Mode - Supports Single & Multi File)

                        target_files = job_params.get(
                            "all_files", [job_params["path"]])
                        if not target_files:
                            raise Exception(
                                "No source files found for splitting.")

                        last_active_alias = alias_val

                        progress_text = "Splitting Sheets..."
                        my_bar = st.progress(0, text=progress_text)

                        # Total Progress Calculation (Approximate: Files * Avg Sheets? Or just files)
                        # We'll stick to File Progress for simplicity in UI, or nested log
                        total_files = len(target_files)

                        for f_idx, current_file in enumerate(target_files):
                            fname = os.path.basename(current_file)
                            f_base = os.path.splitext(fname)[0]
                            # Clean Base
                            f_base_safe = re.sub(r'[^a-zA-Z0-9_]', '_', f_base)

                            my_bar.progress((f_idx) / total_files,
                                            text=f"Scanning {fname}...")

                            target_items = []
                            item_type = "Sheet"  # Default

                            # --- 1. RESOLVE CONTENTS for THIS file ---
                            try:
                                tables_in_file = []
                                sheets_in_file = []

                                # Optimization: Only scan what's needed
                                need_tables = bool(job_params.get(
                                    "table") or job_params.get("table_filters"))
                                need_sheets = bool(job_params.get(
                                    "sheet") or job_params.get("sheet_filters"))
                                if not need_tables and not need_sheets:
                                    # Fallback to Sheet mode if nothing specified (Auto logic usually handled by params)
                                    need_sheets = True

                                if need_tables:
                                    tables_in_file = get_cached_table_names(
                                        engine, current_file)
                                if need_sheets:
                                    sheets_in_file = get_cached_sheet_names(
                                        engine, current_file)

                                # --- 2. FILTER CONTENTS ---

                                # A. TABLES
                                if job_params.get("table") or job_params.get("table_filters"):
                                    item_type = "Table"
                                    if job_params.get("table"):
                                        t_val = job_params["table"]
                                        if isinstance(t_val, list):
                                            # If manual selection, we only take those that EXIST in this file
                                            # (Assuming user wants specific table names across files)
                                            target_items = [
                                                t for t in t_val if t in tables_in_file]
                                        elif t_val == "__ALL_TABLES__":
                                            target_items = tables_in_file

                                    elif job_params.get("table_filters"):
                                        target_items = filter_sheet_names(
                                            tables_in_file, job_params["table_filters"])

                                # B. SHEETS (Else)
                                elif job_params.get("sheet") or job_params.get("sheet_filters"):
                                    item_type = "Sheet"

                                    if job_params.get("sheet"):
                                        s_val = job_params["sheet"]
                                        if s_val == "__ALL_SHEETS__":
                                            target_items = sheets_in_file
                                        elif isinstance(s_val, list):
                                            target_items = [
                                                s for s in s_val if s in sheets_in_file]

                                    elif job_params.get("sheet_filters"):
                                        target_items = filter_sheet_names(
                                            sheets_in_file, job_params["sheet_filters"])

                                # Fallback (Implicit All Sheets if nothing selected but split requested?)
                                # CLI logic does "Auto" mode (Tables -> Sheets).
                                if not target_items and not (job_params.get("table_filters") or job_params.get("sheet_filters")):
                                    # If manual selection was empty/invalid, maybe try auto?
                                    # For now, strict: If params empty, maybe Sheets?
                                    pass

                            except Exception as e:
                                st.warning(f"Could not scan {fname}: {e}")
                                continue

                            # --- 3. LOAD ITEMS ---
                            if target_items:
                                for item_name in target_items:
                                    # Unique Alias: {File}_{Item}
                                    # Clean Item Name
                                    i_safe = re.sub(
                                        r'[^a-zA-Z0-9_]', '_', item_name)

                                    # If User provided alias "MyData", Result: "MyData_Sales2023_Sheet1"
                                    # If Single File mode, maybe users prefer "MyData_Sheet1"?
                                    # To be consistent: Always append File identifier if > 1 file?
                                    # Use safe naming:
                                    if len(target_files) > 1:
                                        current_alias = f"{alias_val}_{f_base_safe}_{i_safe}"
                                    else:
                                        # Single File Mode - cleaner alias
                                        current_alias = f"{alias_val}_{i_safe}"

                                    curr_params = job_params.copy()
                                    # POINT TO SPECIFIC FILE
                                    curr_params["path"] = current_file

                                    if item_type == "Table":
                                        curr_params["table"] = [item_name]
                                        curr_params.pop("table_filters", None)
                                        curr_params["sheet"] = None
                                        curr_params.pop("sheet_filters", None)
                                    else:
                                        curr_params["sheet"] = [item_name]
                                        curr_params.pop("sheet_filters", None)
                                        curr_params["table"] = None
                                        curr_params.pop("table_filters", None)

                                    curr_params["alias"] = current_alias

                                    res_item = engine.io.run_loader(
                                        "File", curr_params)
                                    if res_item:
                                        lf, meta = res_item
                                        engine.datasets.add(current_alias, lf, meta,
                                                            loader_type="File",
                                                            loader_params=curr_params)

                                        # Init Recipe
                                        if current_alias not in st.session_state.all_recipes:
                                            st.session_state.all_recipes[current_alias] = [
                                            ]

                                        # Auto Infer
                                        if auto_infer:
                                            handle_auto_inference(
                                                engine, current_alias)

                                        last_active_alias = current_alias
                                    else:
                                        st.warning(
                                            f"Skipped {item_type}: {item_name} in {fname}")

                        st.session_state.active_base_dataset = last_active_alias
                        st.session_state.recipe_steps = engine.recipes.get(
                            last_active_alias)
                        my_bar.empty()

                    else:
                        # Single Buffer Load
                        res = engine.io.run_loader("File", job_params)
                        if res:
                            lf, meta = res

                            # Handle Edit Mode: Remove old dataset if exists and name changed
                            if edit_mode and edit_dataset_name:
                                if alias_val != edit_dataset_name:
                                    # Rename: Move recipes, remove old
                                    if edit_dataset_name in st.session_state.all_recipes:
                                        st.session_state.all_recipes[alias_val] = st.session_state.all_recipes.pop(
                                            edit_dataset_name)

                                    # Backend Recipe Migration
                                    engine.recipes.rename(
                                        edit_dataset_name, alias_val)

                                    engine.datasets.remove(edit_dataset_name)
                                else:
                                    # Same name: Just remove to re-add with new data
                                    engine.datasets.remove(alias_val)

                            engine.datasets.add(alias_val, lf, meta,
                                                loader_type="File",
                                                loader_params=job_params)

                            if alias_val not in st.session_state.all_recipes:
                                st.session_state.all_recipes[alias_val] = []

                            st.session_state.active_base_dataset = alias_val
                            # LINK BY REFERENCE to ensure updates propagate (initially)
                            st.session_state.recipe_steps = st.session_state.all_recipes[alias_val]

                            if auto_infer:
                                st.info("🪄 Auto-detecting column types...")
                                handle_auto_inference(engine, alias_val)
                                # Explicit refresh to ensure step is visible
                                st.session_state.recipe_steps = engine.recipes.get(
                                    alias_val)
                        else:
                            raise Exception("Engine returned no data.")

                    status.update(label="✅ Data Loaded Successfully!",
                                  state="complete", expanded=False)
                    st.success("Done! Closing...")

                    # Update Recent Paths
                    if 'path' in job_params and job_params['path'] and mode == "Single File":
                        rp = job_params['path']
                        if rp not in st.session_state[recent_paths_key]:
                            # Keep max 10
                            st.session_state[recent_paths_key].insert(0, rp)
                            st.session_state[recent_paths_key] = st.session_state[recent_paths_key][:10]

                # SUCCESS CLEANUP
                st.session_state[busy_key] = False
                st.session_state[action_key] = None

                # Signal sidebar to close dialog
                st.session_state.show_loader_file = False

                st.rerun()

            except Exception as e:
                status.update(label="❌ Operation Failed",
                              state="error", expanded=True)
                st.error(f"Error: {e}")
                if st.button("Reset Form"):
                    st.session_state[busy_key] = False
                    st.session_state[action_key] = None
                    st.rerun()
