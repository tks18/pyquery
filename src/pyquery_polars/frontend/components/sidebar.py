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
from pyquery_polars.backend.utils.io import cleanup_staging_files


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

                # Decoupled Schema Lookup
                base_schema = get_loader_schema(loader.name)

                # 1. Custom Path Resolver for Files
                path_val = st.session_state.get(f"load_{loader.name}_path", "")

                if loader.name == "File":
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
                        else:
                            path_val = ""

                # 2. Check Extension (for Excel logic)
                is_excel = path_val and (path_val.lower().endswith(
                    ".xlsx") or path_val.lower().endswith(".xls"))

                # 3. Dynamic UI Schema Generation
                # We filter 'path' out if we are in File mode, because we handled it separately above
                ui_schema = []
                for field in base_schema:
                    if loader.name == "File" and field.name == "path":
                        continue  # Skip rendering generic path input

                    if field.name == "sheet" and not is_excel:
                        continue
                    ui_schema.append(field)

                # DYNAMIC OVERRIDE: Excel Sheet Dropdown
                override_defaults = {}

                sheet_options = None
                if (loader.name == "File" and is_excel and
                    isinstance(path_val, str) and
                        path_val.strip()):
                    # Only try to fetch sheets if it's a valid single file. Globs containing excel can't be sheet-scanned easily pre-load.
                    try:
                        sheets = engine.get_file_sheet_names(path_val)
                        sheet_options = sheets
                    except:
                        pass  # Ignore sheet scan errors for globs or invalid paths

                # Enhanced UI Renderer with Override Support
                params = render_schema_fields(
                    ui_schema,
                    key_prefix=f"load_{loader.name}",
                    override_options={
                        "sheet": sheet_options} if sheet_options else None
                )

                # Injection
                if loader.name == "File":
                    params["path"] = path_val
                alias_val = params.get('alias')

                # Auto Infer Checkbox
                auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False,
                                         help="Automatically scan first 1000 rows and add a cleaning step.", key=f"chk_infer_{loader.name}")

                if st.button("Load Data", type="primary", key=f"btn_load_{loader.name}", width="stretch"):
                    if not alias_val:
                        st.error("Alias required.")
                    else:
                        final_params = params
                        if loader.params_model:
                            try:
                                final_params = loader.params_model.model_validate(
                                    params)
                            except Exception as e:
                                st.error(f"Invalid Config: {e}")
                                st.stop()

                        # Return is now (Optional[LazyFrame], Metadata)
                        result = engine.run_loader(loader.name, final_params)

                        lf = None
                        metadata = {}

                        if isinstance(result, tuple):
                            lf, metadata = result
                        elif result is not None:
                            lf = result  # Legacy fallback

                        if lf is not None:
                            # Pass source_path if available
                            src_path = metadata.get('source_path')
                            engine.add_dataset(
                                alias_val, lf, source_path=src_path)

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
            # Serialize for Generic RecipeStep (which has .model_dump())
            serialized_recipe = [s.model_dump()
                                 for s in st.session_state.recipe_steps]
            recipe_json = json.dumps(serialized_recipe, indent=2)

            st.download_button("💾 Download JSON", recipe_json, "recipe.json",
                               "application/json", width="stretch")

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
                    cleanup_staging_files(max_age_hours=0)  # Force clear
                    st.toast("Cache cleared successfully!", icon="🧹")
                except Exception as e:
                    st.error(f"Cleanup failed: {e}")
