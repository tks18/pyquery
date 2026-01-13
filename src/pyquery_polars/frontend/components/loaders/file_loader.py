import streamlit as st
import os
import re
import glob
import pandas as pd
from typing import List
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.utils.file_picker import pick_file, pick_folder
from pyquery_polars.frontend.utils.cache_utils import get_cached_sheet_names, get_cached_resolved_files, get_cached_encoding_scan
from pyquery_polars.core.io_params import FileFilter, FilterType
from pyquery_polars.frontend.components.loaders.utils import filter_list_by_regex, handle_auto_inference


@st.dialog("Import File", width="large")
def show_file_loader(engine: PyQueryEngine):
    st.caption("Load data from local files (CSV, Excel, Parquet, JSON, IPC)")

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

    # Defaults
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "Single File"
    if path_key not in st.session_state:
        st.session_state[path_key] = ""
    if folder_key not in st.session_state:
        st.session_state[folder_key] = ""
        
    # Encoding States
    enc_checked_key = f"dlg_{loader_name}_enc_checked"
    enc_issues_key = f"dlg_{loader_name}_enc_issues"
    
    if enc_checked_key not in st.session_state:
        st.session_state[enc_checked_key] = False
    if enc_issues_key not in st.session_state:
        st.session_state[enc_issues_key] = {}
    
    # Reset encoding state on path change
    last_path_key = f"dlg_{loader_name}_last_path"
    
    alias_default = f"data_{len(st.session_state.all_recipes) + 1}"

    # 1. CORE IDENTITY (Always Visible)
    c_alias, c_mode = st.columns([0.65, 0.35])
    alias_val = c_alias.text_input(
        "Dataset Alias", value=alias_default, help="Unique name for this dataset", disabled=is_busy)
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
            col_path, col_btn = st.columns([0.85, 0.15])
            path_input = col_path.text_input("File Path", key=path_key, disabled=is_busy)

            def callback_pick_file():
                picked = pick_file("Select File")
                if picked:
                    st.session_state[path_key] = picked
            col_btn.button("📂", on_click=callback_pick_file,
                        key="dlg_btn_pick_file", help="Browse Files", disabled=is_busy)
            effective_path = path_input

        else:  # Folder Pattern
            col_dir, col_btn = st.columns([0.85, 0.15])
            folder_input = col_dir.text_input("Base Folder", key=folder_key, disabled=is_busy)

            def callback_pick_folder():
                picked = pick_folder("Select Folder")
                if picked:
                    st.session_state[folder_key] = picked
            col_btn.button("📂", on_click=callback_pick_folder,
                        key="dlg_btn_pick_folder", help="Browse Folder", disabled=is_busy)

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
                "Pattern Type", list(PATTERNS.keys()), key=pat_key, disabled=is_busy)

            final_pattern = PATTERNS[sel_pat_label]
            if final_pattern == "custom":
                final_pattern = c2.text_input(
                    "Custom Pattern", value="*.csv", key=f"dlg_{loader_name}_pat_custom", disabled=is_busy)
            else:
                c2.text_input("Pattern Preview",
                            value=final_pattern, disabled=True)

            if folder_input and final_pattern:
                effective_path = os.path.join(folder_input, final_pattern)

        # --- RESET CHECK ON PATH CHANGE ---
        if st.session_state.get(last_path_key) != effective_path:
            st.session_state[enc_checked_key] = False
            st.session_state[enc_issues_key] = {}
            st.session_state[last_path_key] = effective_path

        # --- ADVANCED PATH FILTERS ---
        filter_key = f"dlg_{loader_name}_filters"
        if filter_key not in st.session_state:
            st.session_state[filter_key] = []

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
                        "✕", key=f"dlg_btn_del_filt_{i}", on_click=delete_filter, args=(i,), disabled=is_busy)

                # Add New
                st.divider()
                c_add_1, c_add_2, c_add_3, c_add_4 = st.columns([0.25, 0.25, 0.4, 0.1])
                new_f_type = c_add_1.selectbox("Type", ["contains", "regex", "exact", "glob"], key="dlg_new_filt_type", disabled=is_busy)
                new_f_target = c_add_2.selectbox("Target", ["filename", "path"], key="dlg_new_filt_target", disabled=is_busy)
                new_f_val = c_add_3.text_input("Value", key="dlg_new_filt_val", disabled=is_busy)

                def add_filter():
                    val = st.session_state.dlg_new_filt_val
                    if val:
                        st.session_state[filter_key].append({
                            "type": st.session_state.dlg_new_filt_type,
                            "value": val,
                            "target": st.session_state.dlg_new_filt_target
                        })
                        st.session_state.dlg_new_filt_val = ""

                c_add_4.button("➕", on_click=add_filter, key="dlg_btn_add_filt", disabled=is_busy)

            # Convert to FileFilter objects
            if st.session_state[filter_key]:
                type_map = {
                    "contains": FilterType.CONTAINS,
                    "regex": FilterType.REGEX,
                    "exact": FilterType.EXACT,
                    "glob": FilterType.GLOB
                }
                for f in st.session_state[filter_key]:
                    if f['type'] in type_map:
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

        # --- EXCEL SHEETS (Conditional) ---
        selected_sheets = ["Sheet1"]

        if is_excel and effective_path:
            st.write("###### Excel Sheets")
            with st.container(border=True):
                try:
                    # Handle Glob Base Selection
                    if "*" in effective_path:
                        # Quick scan for potential base files (limit 50 for UI)
                        matches = []
                        try:
                            is_rec = "**" in effective_path
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
                            base_selection = st.selectbox(
                                "Select Base File (Template)",
                                matches,
                                help="Choose a file to populate the sheet list from.",
                                disabled=is_busy
                            )
                            sheet_source_file = base_selection
                        else:
                            st.warning("No Excel files found matching pattern.")
                            sheet_source_file = None

                    if sheet_source_file:
                        # Get sheets from file using CACHED function
                        sheets = get_cached_sheet_names(engine, sheet_source_file)

                        col_filter, col_act = st.columns([0.7, 0.3])
                        sheet_filter = col_filter.text_input(
                            "Filter Sheets", "", key="sheet_regex_filter", placeholder="e.g. Sheet.*", disabled=is_busy)

                        filtered_sheets = sheets
                        if sheet_filter:
                            filtered_sheets = filter_list_by_regex(sheets, sheet_filter)

                        all_sheets = col_act.checkbox("Select All Filtered", value=False, disabled=is_busy)

                        if all_sheets:
                            selected_sheets = filtered_sheets
                        else:
                            selected_sheets = st.multiselect(
                                "Select Sheets",
                                filtered_sheets,
                                default=["Sheet1"] if "Sheet1" in filtered_sheets else (
                                    [filtered_sheets[0]] if filtered_sheets else []),
                                disabled=is_busy
                            )
                except Exception as e:
                    st.warning(f"Could not read sheets: {e}")

        # --- PREVIEW & REVIEW (Dynamic Tabs) ---
        with st.expander("🔎 Preview & Review", expanded=True):
            tabs_labels = ["📂 Matched Files"]
            if is_excel:
                tabs_labels.append("📑 Selected Sheets")

            tabs = st.tabs(tabs_labels)

        # TAB 1: Files
        with tabs[0]:
            if effective_path:
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
                            "Path": f
                        })

                    if found_files:
                        st.success(f"Found {len(found_files)}{'+' if count >= scan_limit else ''} files.")
                        st.dataframe(pd.DataFrame(data))
                    else:
                        st.warning("No files found matching the pattern.")
                except Exception as e:
                    st.error(f"Error previewing files: {e}")
            else:
                st.info("Select a path to preview files.")

        # TAB 2: Sheets
        if is_excel and selected_sheets:
            with tabs[1]:
                st.dataframe(pd.DataFrame({"Sheet Name": selected_sheets}), hide_index=True)

        # --- SETTINGS ---
        with st.expander("⚙️ Loading Settings", expanded=not is_busy):
            c_s1, c_s2 = st.columns(2)
            
            with c_s1:
                st.markdown("**Extraction Behavior**")
                process_individual = False
                split_sheets = False
                
                if mode == "Folder Pattern":
                    process_individual = st.toggle(
                        "Process Individually", 
                        value=False,
                        help="Process each file as an individual unit rather than combining them.",
                        disabled=is_busy
                    )
                else:
                    st.caption("Not applicable for single file.")

                if is_excel and mode == "Single File":
                    split_sheets = st.toggle(
                        "Split Sheets", 
                        value=False, 
                        help="Create a separate dataset for each selected sheet.",
                        disabled=is_busy
                    )
                elif is_excel:
                    st.caption("Splitting sheets supported in Single File mode only.")
            
            with c_s2:
                st.markdown("**Schema & Metadata**")
                clean_headers = st.toggle("Clean Headers", value=False, help="Standardize header names.", disabled=is_busy)
                include_src = st.toggle("Include Source Path", value=False, help="Add 'source_file' column.", disabled=is_busy)
                auto_infer = st.toggle("Auto Infer Types", value=False, help="Inspect & Cast types after load.", disabled=is_busy)


        # --- ENCODING VERIFICATION ---
        is_csv_or_text = False
        lp = effective_path.lower()
        if lp.endswith(".csv") or lp.endswith(".txt") or lp.endswith(".json") or lp.endswith(".ndjson"):
            is_csv_or_text = True
        elif "*" in lp:
                if ".csv" in lp or ".txt" in lp or ".json" in lp:
                    is_csv_or_text = True

        has_issues = False
        
        if is_csv_or_text and effective_path:
            with st.expander("🛠️ Encoding Verification", expanded=not is_busy):    
                
                # Automatic Check
                if not st.session_state[enc_checked_key]:
                    with st.spinner("Checking compatibility..."):
                        try:
                            # Use cached utils
                            resolved_files = get_cached_resolved_files(engine, effective_path, effective_filters)
                            if resolved_files:
                                issues = get_cached_encoding_scan(engine, resolved_files)
                                st.session_state[enc_issues_key] = issues
                            else:
                                st.session_state[enc_issues_key] = {}
                            st.session_state[enc_checked_key] = True
                        except Exception as e:
                            st.error(f"Error scanning encodings: {e}")
                
                issues = st.session_state[enc_issues_key]
                if issues:
                    has_issues = True
                    st.error(f"⚠️ Non-UTF-8 Encodings Detected in {len(issues)} files")
                    st.dataframe(pd.DataFrame([
                        {"File": os.path.basename(k), "Detected": v} for k,v in issues.items()
                    ]), hide_index=True)
                    
                    st.info("The loader will automatically convert these files before loading.")
                else:
                    st.success("✅ All files are UTF-8 compatible.")
    
    # Combined Button Label
    btn_label = "Convert & Load Data" if has_issues else "Load Data"
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
            params = {
                "path": effective_path,
                "filters": effective_filters,
                "sheet": selected_sheets,
                "alias": alias_val,
                "process_individual": process_individual,
                "include_source_info": include_src,
                "clean_headers": clean_headers,
                "auto_infer": auto_infer,
                "split_sheets": split_sheets,
                "issues": st.session_state[enc_issues_key] if has_issues else {},
                "all_files": get_cached_resolved_files(engine, effective_path, effective_filters) if has_issues else []
            }
            
            st.session_state[job_params_key] = params
            st.session_state[busy_key] = True
            
            # COMBINED ACTION
            if has_issues:
                st.session_state[action_key] = "convert_and_load"
            else:
                st.session_state[action_key] = "load"
                
            st.rerun()

    # --- EXECUTION (VISUALIZED BELOW) ---
    if is_busy:
        action = st.session_state[action_key]
        job_params = st.session_state[job_params_key]
        
        # Container for Status - Below the form
        with st.status(f"Processing ({action})...", expanded=True) as status:
            try:
                # Combined CONVERT & LOAD Flow
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
                            new_path = engine.convert_encoding(f, src_enc)
                            new_file_list.append(new_path)
                        else:
                            new_file_list.append(f)
                    
                    st.success(f"✅ Converted {len(issues)} files.")
                    
                    # 2. Update params with converted files override
                    job_params["files"] = new_file_list
                    
                    # 3. Proceed to Load (Fallthrough)
                    action = "load" # Logical update for logging/tracking
                
                if action == "load":
                    # --- LOAD LOGIC ---
                    st.info("📖 Reading data...")
                    
                    alias_val = job_params["alias"]
                    split_sheets = job_params.get("split_sheets", False)
                    auto_infer = job_params.get("auto_infer", False)
                    
                    if split_sheets and job_params.get("sheet"):
                        # Multi-Dataset Load
                        sheet_list = job_params["sheet"]
                        last_active_alias = alias_val
                        
                        progress_text = "Importing sheets..."
                        my_bar = st.progress(0, text=progress_text)
                        
                        total_sheets = len(sheet_list)
                        
                        for i, sheet_name in enumerate(sheet_list):
                            my_bar.progress((i + 1) / total_sheets, text=f"Importing {sheet_name}...")
                            
                            current_alias = f"{alias_val}_{sheet_name}"
                            
                            curr_params = job_params.copy()
                            curr_params["sheet"] = [sheet_name]
                            curr_params["alias"] = current_alias
                            
                            res_sheet = engine.run_loader("File", curr_params)
                            if res_sheet:
                                lf, meta = res_sheet
                                engine.add_dataset(current_alias, lf, meta)
                                
                                # Init Recipe
                                if current_alias not in st.session_state.all_recipes:
                                    st.session_state.all_recipes[current_alias] = []
                                
                                # Auto Infer
                                if auto_infer:
                                    st.write(f"Inferring types for {current_alias}...")
                                    handle_auto_inference(engine, current_alias)
                                
                                last_active_alias = current_alias
                            else:
                                st.warning(f"Skipped sheet: {sheet_name} (Load Failed)")
                        
                        st.session_state.active_base_dataset = last_active_alias
                        st.session_state.recipe_steps = []
                        my_bar.empty()
                        
                    else:
                        # Single Buffer Load
                        res = engine.run_loader("File", job_params)
                        if res:
                            lf, meta = res
                            engine.add_dataset(alias_val, lf, meta)
                            
                            if alias_val not in st.session_state.all_recipes:
                                st.session_state.all_recipes[alias_val] = []
                            
                            st.session_state.active_base_dataset = alias_val
                            # LINK BY REFERENCE to ensure updates propagate
                            st.session_state.recipe_steps = st.session_state.all_recipes[alias_val]
                            
                            if auto_infer:
                                st.info("🪄 Auto-detecting column types...")
                                handle_auto_inference(engine, alias_val)
                        else:
                             raise Exception("Engine returned no data.")
                    
                    status.update(label="✅ Data Loaded Successfully!", state="complete", expanded=False)
                    st.success("Done! Closing...")
                    
                # SUCCESS CLEANUP
                st.session_state[busy_key] = False
                st.session_state[action_key] = None
                
                # Signal sidebar to close dialog
                st.session_state.show_loader_file = False
                
                st.rerun()

            except Exception as e:
                status.update(label="❌ Operation Failed", state="error", expanded=True)
                st.error(f"Error: {e}")
                if st.button("Reset Form"):
                    st.session_state[busy_key] = False
                    st.session_state[action_key] = None
                    st.rerun()
