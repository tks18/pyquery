import streamlit as st
import json
from typing import cast
import os
from pyquery_polars.frontend.state_manager import add_step, load_recipe_from_json, undo, redo
from pyquery_polars.frontend.utils.dynamic_ui import render_schema_fields
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.frontend.utils.io_schemas import get_loader_schema
from pyquery_polars.frontend.utils.file_picker import pick_file, pick_folder



def render_sidebar():
    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        st.error("Engine not initialized.")
        return

    with st.sidebar:
        st.title("⚡ Shan's PyQuery")

        active_ds = st.session_state.active_base_dataset

        # --- 0. ACTIVE DATASET METRICS ---
        if active_ds:
            st.caption(f"Active: **{active_ds}**")
            st.divider()

        # --- 1. DATASET MANAGER ---
        st.subheader("🗂️ Datasets")

        with st.expander("Import Data", expanded=not bool(active_ds)):
            loaders = engine.get_loaders()
            if not loaders:
                st.warning("No loaders.")
            else:
                loader_map = {l.name: l for l in loaders}
                selected_source = st.selectbox(
                    "Source Type", list(loader_map.keys()), key="imp_src")
                loader = loader_map[selected_source]

                params = {}
                alias_val = ""

                # --- 1. FILE LOADER UI ---
                if loader.name == "File":
                    # Decoupled Schema Lookup
                    base_schema = get_loader_schema(loader.name)
                    
                    # Init global vars for loader scope
                    final_pattern = None
                    includes_excel = False

                    # A. Custom Path Resolver for Files
                    path_val = st.session_state.get(f"load_{loader.name}_path", "")
                    
                    st.write("###### File Selection")
                    file_mode = st.radio("Mode", ["Single File", "Folder (Glob)"], horizontal=True,
                                         label_visibility="collapsed", key=f"mode_{loader.name}")

                    # Helper Callbacks
                    def callback_pick_file(target_key):
                        picked = pick_file(title="Select Dataset")
                        if picked:
                            st.session_state[target_key] = picked

                    def callback_pick_folder(target_key):
                        picked = pick_folder(title="Select Dataset Folder")
                        if picked:
                            st.session_state[target_key] = picked

                    if file_mode == "Single File":
                        col_in, col_btn = st.columns([0.8, 0.2])
                        key_manual = f"load_{loader.name}_path_manual"

                        # Init state to avoid value conflict warning
                        if key_manual not in st.session_state:
                            st.session_state[key_manual] = path_val if path_val else ""

                        path_val = col_in.text_input(
                            "File Path", key=key_manual)
                        col_btn.button("📂", key="btn_browse_file", help="Pick a file",
                                       on_click=callback_pick_file, args=(key_manual,))

                    else:  # Glob Mode
                        col_in, col_btn = st.columns([0.8, 0.2])
                        # Manage Folder State
                        base_folder_key = f"load_{loader.name}_base_folder"

                        # Init state for widget
                        if base_folder_key not in st.session_state:
                            st.session_state[base_folder_key] = ""

                        base_folder = col_in.text_input(
                            "Base Folder", key=base_folder_key)
                        col_btn.button("📂", key="btn_browse_folder", help="Pick a folder",
                                       on_click=callback_pick_folder, args=(base_folder_key,))

                        # Pattern Selector
                        PATTERNS = {
                            "CSV (*.csv)": "*.csv",
                            "Excel (*.xlsx)": "*.xlsx",
                            "Parquet (*.parquet)": "*.parquet",
                            "JSON (*.json)": "*.json",
                            "Recursive CSV (**/*.csv)": "**/*.csv",
                            "All Supported Files (*)": "*",
                            "Custom": "custom"
                        }

                        c1, c2 = st.columns([0.5, 0.5])
                        pat_key = f"load_{loader.name}_glob_pattern_sel"
                        sel_pat_label = c1.selectbox(
                            "Pattern Type", list(PATTERNS.keys()), key=pat_key)

                        final_pattern = PATTERNS[sel_pat_label]
                        if final_pattern == "custom":
                            final_pattern = c2.text_input(
                                "Custom Pattern", value="*.csv", key=f"load_{loader.name}_glob_custom")
                        else:
                            c2.text_input("Pattern Preview",
                                          value=final_pattern, disabled=True)

                        if base_folder and final_pattern:
                            path_val = os.path.join(base_folder, final_pattern)
                            st.caption(f"**Effective Path:** `{path_val}`")
                            
                            # Mixed Type Safety
                            if final_pattern == "*":
                                st.warning("Mixed types. Ensure schemas match!", icon="⚠️")
                                includes_excel = st.checkbox("Includes Excel files?", value=False, key=f"load_{loader.name}_mixed_excel")
                            else:
                                includes_excel = False
                        else:
                            path_val = ""
                            includes_excel = False
                        
                    
                    # B. Check Extension (for Excel logic)
                    is_excel = path_val and (path_val.lower().endswith(".xlsx") or path_val.lower().endswith(".xls"))
                    if final_pattern == "*" and includes_excel:
                        is_excel = True

                    # C. Dynamic UI Schema Generation (Filtered)
                    ui_schema = []
                    for field in base_schema:
                        if field.name in ["path", "alias"]: continue
                        if field.name == "sheet" and not is_excel: continue
                        ui_schema.append(field)

                    # D. Excel Sheet Logic
                    sheet_options = None
                    if (is_excel and final_pattern != "*" and 
                        isinstance(path_val, str) and path_val.strip()):
                        try:
                            sheets = engine.get_file_sheet_names(path_val)
                            sheet_options = sheets
                        except:
                            pass

                    selected_sheet = "Sheet1"
                    if sheet_options:
                         selected_sheet = st.selectbox("Select Sheet", sheet_options, key=f"load_{loader.name}_sheet_top")
                    elif final_pattern == "*" and includes_excel:
                         selected_sheet = st.text_input("Excel Sheet Name", value="Sheet1", key=f"load_{loader.name}_sheet_mixed", help="Enter the sheet name to read from Excel files found in the folder.")

                    # E. Alias
                    alias_default = f"data_{len(st.session_state.all_recipes) + 1}"
                    alias_val = st.text_input("Dataset Alias", value=alias_default, 
                                            key=f"load_{loader.name}_alias",
                                            help="Unique name for this dataset")

                    # F. Options & Params Construction
                    with st.expander("⚙️ Loading Options", expanded=True):
                        params = render_schema_fields(
                            ui_schema,
                            key_prefix=f"load_{loader.name}",
                            override_options={"sheet": sheet_options} if sheet_options else None,
                            exclude=["sheet"] if sheet_options else []
                        )
                        
                        # Add Explicit Params
                        params["path"] = path_val
                        params["sheet"] = selected_sheet
                        params["alias"] = alias_val
                        
                        # Process Individual
                        if file_mode == "Folder (Glob)":
                            params["process_individual"] = st.checkbox(
                                "🔨 Process Files Individually",
                                value=False,
                                key=f"load_{loader.name}_process_individual",
                                help="Apply transformation steps to each file separately before concatenating."
                            )
                        else:
                            params["process_individual"] = False
                        
                        # Source Metadata
                        params["include_source_info"] = st.checkbox(
                            "📄 Include Source Details", 
                            value=False,
                            key=f"load_{loader.name}_src_info",
                            help="Add info columns: __pyquery_source_path__, __pyquery_source_name__"
                        )
                        
                        # Auto Infer
                        auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False,
                                                help="Automatically scan first 1000 rows and add a cleaning step.", key=f"chk_infer_{loader.name}")

                # --- 2. SQL LOADER UI ---
                elif loader.name == "Sql":
                    st.write("###### SQL Configuration")
                    conn_val = st.text_input("Connection String", key=f"load_{loader.name}_conn", help="SQLAlchemy connection string (e.g., sqlite:///data.db, postgresql://user:pass@host/db)")
                    query_val = st.text_area("SQL Query", key=f"load_{loader.name}_query", height=100)
                    
                    alias_default = f"sql_data_{len(st.session_state.all_recipes) + 1}"
                    alias_val = st.text_input("Dataset Alias", value=alias_default, key=f"load_{loader.name}_alias")
                    
                    params = {"conn": conn_val, "query": query_val, "alias": alias_val}
                    
                    with st.expander("⚙️ Advanced Options", expanded=False):
                         auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False,
                                                help="Automatically scan first 1000 rows and add a cleaning step.", key=f"chk_infer_{loader.name}")

                # --- 3. API LOADER UI ---
                elif loader.name == "Api":
                    st.write("###### API Configuration")
                    url_val = st.text_input("Endpoint URL", key=f"load_{loader.name}_url", help="REST API Endpoint")
                    
                    alias_default = f"api_data_{len(st.session_state.all_recipes) + 1}"
                    alias_val = st.text_input("Dataset Alias", value=alias_default, key=f"load_{loader.name}_alias")
                    
                    params = {"url": url_val, "alias": alias_val}
                    
                    with st.expander("⚙️ Advanced Options", expanded=False):
                         auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False,
                                                help="Automatically scan first 1000 rows and add a cleaning step.", key=f"chk_infer_{loader.name}")

                # --- 4. GENERIC LOADER FALLBACK ---
                else: 
                     base_schema = get_loader_schema(loader.name)
                     params = render_schema_fields(base_schema, key_prefix=f"load_{loader.name}")
                     alias_val = params.get("alias", f"data_{len(st.session_state.all_recipes)+1}")
                     auto_infer = False

                # --- 5. EXECUTION ---
                if st.button("Load Data", type="primary", key=f"btn_load_{loader.name}", width="stretch"):
                    if not alias_val:
                        st.error("Alias required.")
                    else:
                        final_params = params
                        # Ensure alias is set if missing
                        if "alias" not in final_params:
                            final_params["alias"] = alias_val
                        if loader.params_model:
                            try:
                                final_params = loader.params_model.model_validate(
                                    params)
                            except Exception as e:
                                st.error(f"Invalid Config: {e}")
                                st.stop()

                        # Return is now (Optional[LazyFrame], Metadata)
                        result = engine.run_loader(loader.name, final_params)

                        # Handle both LazyFrame and List[LazyFrame]
                        lf_or_lfs = None
                        metadata = {}

                        if isinstance(result, tuple):
                            lf_or_lfs, metadata = result
                        elif result is not None:
                            lf_or_lfs = result  # Legacy fallback

                        if lf_or_lfs is not None:
                            # add_dataset handles both single LF and list
                            engine.add_dataset(alias_val, lf_or_lfs, metadata=metadata)

                            if alias_val not in st.session_state.all_recipes:
                                st.session_state.all_recipes[alias_val] = []

                            # --- AUTO INFER LOGIC ---
                            if auto_infer:
                                try:
                                    with st.spinner("Auto-detecting types..."):
                                        inferred = engine.infer_types(
                                            alias_val, [], sample_size=1000)
                                        if inferred:
                                            from pyquery_polars.core.params import CleanCastParams, CastChange
                                            from pyquery_polars.core.models import RecipeStep
                                            import uuid

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
                                                action = TYPE_ACTION_MAP.get(
                                                    dtype)
                                                if action:
                                                    p.changes.append(CastChange(
                                                        col=col, action=action))
                                                    count += 1

                                            if count > 0:
                                                new_step = RecipeStep(
                                                    id=str(uuid.uuid4()),
                                                    type="clean_cast",
                                                    label="Auto Clean Types",
                                                    params=p.model_dump()
                                                )
                                                st.session_state.all_recipes[alias_val].append(
                                                    new_step)
                                                st.toast(
                                                    f"✨ Auto-added cleaning step for {count} columns!", icon="🪄")
                                except Exception as e:
                                    print(f"Auto infer error: {e}")

                            if len(engine.get_dataset_names()) == 1:
                                st.session_state.active_base_dataset = alias_val
                                st.session_state.recipe_steps = []

                            # Sync active steps if this is the active dataset
                            if st.session_state.active_base_dataset == alias_val:
                                st.session_state.recipe_steps = st.session_state.all_recipes[alias_val]

                            st.success(f"Loaded {alias_val}")
                            st.rerun()
                        else:
                            st.error("Load failed.")

        # B. LIST EXISTING
        dataset_names = engine.get_dataset_names()
        if dataset_names:
            st.markdown("---")
            st.caption("Available Projects")
            for name in dataset_names:
                c1, c2 = st.columns([0.8, 0.2])
                label = f"📂 {name}" if name != active_ds else f"🟢 **{name}**"

                if c1.button(label, key=f"sel_{name}", width="stretch"):
                    st.session_state.active_base_dataset = name
                    st.session_state.recipe_steps = st.session_state.all_recipes.get(name, [
                    ])
                    st.rerun()

                if c2.button("🗑️", key=f"del_{name}"):
                    engine.remove_dataset(name)
                    if name in st.session_state.all_recipes:
                        del st.session_state.all_recipes[name]
                    if st.session_state.active_base_dataset == name:
                        st.session_state.active_base_dataset = None
                        st.session_state.recipe_steps = []
                    st.rerun()

        st.divider()

        # --- 2. TRANSFORMATION PIPELINE ---
        st.subheader("🛠️ Pipeline")

        c_undo, c_redo = st.columns(2)
        can_undo = len(st.session_state.get('history_stack', [])) > 0
        can_redo = len(st.session_state.get('redo_stack', [])) > 0

        c_undo.button("↩ Undo", on_click=undo,
                      disabled=not can_undo, width="stretch", key="btn_undo")
        c_redo.button("↪ Redo", on_click=redo,
                      disabled=not can_redo, width="stretch", key="btn_redo")

        # Dynamic Registry Usage
        registry = StepRegistry.get_all()

        # Stale State Recovery
        if not registry:
            st.warning("System updated. Reload required.")
            if st.button("♻️ Reload System", key="btn_reload_sys", type="primary"):
                st.cache_resource.clear()
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        if registry:
            # 1. Group Steps
            grouped_steps = {}
            for step_type, def_obj in registry.items():
                label = def_obj.metadata.label
                group = def_obj.metadata.group
                if group not in grouped_steps:
                    grouped_steps[group] = []
                grouped_steps[group].append((step_type, label))

            # 2. Render Groups
            preferred_order = ["Columns", "Rows", "Combine",
                               "Clean", "Analytics", "Math & Date"]
            sorted_groups = sorted(grouped_steps.keys(), key=lambda x: preferred_order.index(
                x) if x in preferred_order else 99)

            if sorted_groups:
                selected_group = st.selectbox(
                    "Category", sorted_groups, key="sel_category")

                steps = grouped_steps[selected_group]
                options_map = {label: step_type for step_type, label in steps}

                selected_label = st.selectbox(
                    "Operation", list(options_map.keys()), key="sel_operation"
                )

                if selected_label and st.button("Add Step", key="btn_add_step", type="primary", width="stretch"):
                    step_type = options_map[selected_label]
                    add_step(step_type, selected_label)

        st.divider()

        # --- 3. RECIPE ACTIONS ---
        with st.expander("🔪 Recipe Actions", expanded=False):
            active_ds = st.session_state.get('active_base_dataset')
            
            if not active_ds:
                st.warning("⚠️ No active dataset. Load data first.")
            else:
                # Get recipe for the active dataset from all_recipes
                dataset_recipe = st.session_state.all_recipes.get(active_ds, [])
                
                if not dataset_recipe:
                    st.info(f"ℹ️ No recipe steps for '{active_ds}' yet. Add transformations to create a recipe.")
                
                # Serialize for Generic RecipeStep (which has .model_dump())
                serialized_recipe = [s.model_dump() for s in dataset_recipe]
                recipe_json = json.dumps(serialized_recipe, indent=2)

                st.download_button("💾 Download JSON", recipe_json, f"recipe_{active_ds}.json",
                                   "application/json", width="stretch", 
                                   disabled=not dataset_recipe,
                                   help=f"Download recipe for {active_ds} ({len(dataset_recipe)} steps)")

                uploaded_recipe = st.file_uploader("Restore JSON", type=["json"])
                if uploaded_recipe and st.button("Apply Restore", width="stretch"):
                    load_recipe_from_json(uploaded_recipe)
                    st.rerun()

            if st.button("🗑️ Clear All Steps", type="secondary", width="stretch"):
                active_ds = st.session_state.active_base_dataset
                if active_ds:
                    st.session_state.all_recipes[active_ds] = []
                    st.session_state.recipe_steps = []
                    st.rerun()

        st.divider()

        # --- 4. SETTINGS ---
        with st.expander("⚙️ Application Settings", expanded=False):
            if st.button("🧹 Clear Cache / Staging", help="Force delete all temporary files.", width="stretch"):
                try:
                    engine.cleanup_staging(0)  # Force clear
                    st.toast("Cache cleared successfully!", icon="🧹")
                except Exception as e:
                    st.error(f"Cleanup failed: {e}")
