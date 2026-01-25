from typing import cast

import streamlit as st
import json
import hashlib

from pyquery_polars.frontend.state_manager import add_step, load_recipe_from_json, undo, redo
from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.frontend.components.loaders import show_file_loader, show_sql_loader, show_api_loader


def _open_project_export():
    """Helper to open project export dialog."""
    st.session_state.show_loader_file = False
    st.session_state.show_loader_sql = False
    st.session_state.show_loader_api = False
    st.session_state.show_project_export = True
    st.session_state.show_project_import = False


def _open_project_import():
    """Helper to open project import dialog."""
    st.session_state.show_loader_file = False
    st.session_state.show_loader_sql = False
    st.session_state.show_loader_api = False
    st.session_state.show_project_export = False
    st.session_state.show_project_import = True


def render_sidebar():
    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        st.error("Engine not initialized.")
        return

    with st.sidebar:
        st.title("⚡ Shan's PyQuery")

        active_ds = st.session_state.active_base_dataset

        # --- TOP BAR: Active Dataset + Project Actions ---
        if active_ds:
            # Single line: Active dataset name with project action buttons
            col_ds, col_save, col_load = st.columns([0.6, 0.2, 0.2])
            col_ds.markdown(f"🎯 **{active_ds}**")
            col_save.button("💾", help="Save Project", key="btn_proj_save",
                            on_click=lambda: _open_project_export())
            col_load.button("📂", help="Load Project", key="btn_proj_load",
                            on_click=lambda: _open_project_import())
        else:
            # No active dataset - just show project buttons with label
            col_label, col_save, col_load = st.columns([0.6, 0.2, 0.2])
            col_label.caption("No dataset loaded")
            col_save.button("💾", help="Save Project", key="btn_proj_save",
                            on_click=lambda: _open_project_export())
            col_load.button("📂", help="Load Project", key="btn_proj_load",
                            on_click=lambda: _open_project_import())

        st.divider()

        # --- 1. DATASET MANAGER ---
        st.subheader("🗂️ Datasets")

        # New Modal-Based Import Section
        st.write("###### Import Data")
        col_imp1, col_imp2, col_imp3 = st.columns(3)

        # --- STATE INITIALIZATION FOR LOADERS ---
        if "show_loader_file" not in st.session_state:
            st.session_state.show_loader_file = False
        if "show_loader_sql" not in st.session_state:
            st.session_state.show_loader_sql = False
        if "show_loader_api" not in st.session_state:
            st.session_state.show_loader_api = False
        if "edit_mode_dataset" not in st.session_state:
            st.session_state.edit_mode_dataset = None
        if "show_project_export" not in st.session_state:
            st.session_state.show_project_export = False
        if "show_project_import" not in st.session_state:
            st.session_state.show_project_import = False

        # --- HELPER: RESET DIALOG STATE ---
        def reset_dialog_state():
            try:
                for key in list(st.session_state.keys()):
                    if isinstance(key, str) and key.startswith("dlg_"):
                        del st.session_state[key]
            except Exception:
                pass  # Ignore errors during rapid state changes

        # --- BUTTON CALLBACKS ---
        def open_file_loader():
            reset_dialog_state()
            st.session_state.edit_mode_dataset = None  # Clear edit mode for new load
            st.session_state.show_loader_file = True
            st.session_state.show_loader_sql = False
            st.session_state.show_loader_api = False
            st.session_state.show_project_export = False
            st.session_state.show_project_import = False
            st.session_state.dlg_just_opened = True

        def open_sql_loader():
            reset_dialog_state()
            st.session_state.edit_mode_dataset = None  # Clear edit mode for new load
            st.session_state.show_loader_file = False
            st.session_state.show_loader_sql = True
            st.session_state.show_loader_api = False
            st.session_state.show_project_export = False
            st.session_state.show_project_import = False
            st.session_state.dlg_just_opened = True

        def open_api_loader():
            reset_dialog_state()
            st.session_state.edit_mode_dataset = None  # Clear edit mode for new load
            st.session_state.show_loader_file = False
            st.session_state.show_loader_sql = False
            st.session_state.show_loader_api = True
            st.session_state.show_project_export = False
            st.session_state.show_project_import = False
            st.session_state.dlg_just_opened = True

        if col_imp1.button("📂 File", help="Import Local Files", width="stretch", on_click=open_file_loader):
            pass

        if col_imp2.button("🛢️ SQL", help="Connect Database", width="stretch", on_click=open_sql_loader):
            pass

        if col_imp3.button("🌐 API", help="REST API Import", width="stretch", on_click=open_api_loader):
            pass

        # --- AUTO-CLOSE LOGIC (Detect 'X' Close or External Click) ---

        # 2. Compute Current State Hash (Values of inputs)
        # Use list() to create a safe copy of keys to avoid KeyError during iteration
        try:
            current_dlg_values = {
                k: st.session_state.get(k) for k in list(st.session_state.keys())
                if isinstance(k, str) and k.startswith("dlg_")}
        except:
            current_dlg_values = {}

        # Exclude buttons from hash because they don't persist, but check them explicitly
        input_values_str = str(sorted(
            [(k, v) for k, v in current_dlg_values.items() if not k.startswith("dlg_btn")]))
        current_hash = hashlib.md5(input_values_str.encode()).hexdigest()

        # 3. Check for Active Interaction
        # Interaction = (Any dlg_btn is True) OR (Hash changed from last run)
        try:
            any_btn_clicked = any(st.session_state.get(k)
                                  for k in list(st.session_state.keys()) if isinstance(k, str) and k.startswith("dlg_btn"))
        except:
            any_btn_clicked = False
        last_hash = st.session_state.get("last_dlg_hash", "")

        is_interaction = any_btn_clicked or (current_hash != last_hash)

        # 4. Final Decision Logic
        just_opened = st.session_state.get("dlg_just_opened", False)

        if just_opened:
            # Reset flag for next run so future non-interactions will close it
            st.session_state.dlg_just_opened = False
        elif not is_interaction:
            # No internal interaction and not just opened -> External event or Close 'X'
            # Safely close all dialogs
            st.session_state.show_loader_file = False
            st.session_state.show_loader_sql = False
            st.session_state.show_loader_api = False
            st.session_state.edit_mode_dataset = None  # Clear edit mode

            # Reset all dialog inputs
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("dlg_"):
                    del st.session_state[key]

        # --- RENDER DIALOGS IF ACTIVE ---
        edit_ds = st.session_state.get("edit_mode_dataset")

        # Check project dialogs first (they reset loader states when opened)
        if st.session_state.get("show_project_export", False):
            from pyquery_polars.frontend.components.project_dialog import show_project_export_dialog
            show_project_export_dialog(engine)
        elif st.session_state.get("show_project_import", False):
            from pyquery_polars.frontend.components.project_dialog import show_project_import_dialog
            show_project_import_dialog(engine)
        elif st.session_state.show_loader_file:
            if edit_ds:
                show_file_loader(engine, edit_mode=True,
                                 edit_dataset_name=edit_ds)
            else:
                show_file_loader(engine)
        elif st.session_state.show_loader_sql:
            if edit_ds:
                show_sql_loader(engine, edit_mode=True,
                                edit_dataset_name=edit_ds)
            else:
                show_sql_loader(engine)
        elif st.session_state.show_loader_api:
            if edit_ds:
                show_api_loader(engine, edit_mode=True,
                                edit_dataset_name=edit_ds)
            else:
                show_api_loader(engine)

        # B. LIST EXISTING
        dataset_names = engine.datasets.list_names()
        if dataset_names:
            st.divider()

            st.caption("Available Projects")
            for name in dataset_names:
                c1, c_settings, c_delete = st.columns([0.7, 0.15, 0.15])
                label = f"📂 {name}" if name != active_ds else f"🟢 **{name}**"

                if c1.button(label, key=f"sel_{name}", width="stretch"):
                    st.session_state.active_base_dataset = name
                    st.session_state.recipe_steps = st.session_state.all_recipes.get(name, [
                    ])
                    st.rerun()

                if c_settings.button("⚙️", key=f"settings_{name}", help="Edit dataset settings"):
                    # Get loader type from metadata
                    meta = engine.datasets.get_metadata(name)
                    if meta:
                        loader_type = meta.loader_type if meta.loader_type else "File"
                    else:
                        loader_type = "File"
                        st.warning(f"Could not load metadata for {name}")

                    # Reset dialog state before opening
                    reset_dialog_state()

                    # Set edit mode state
                    st.session_state.edit_mode_dataset = name

                    # Open appropriate loader
                    if loader_type == "File":
                        st.session_state.show_loader_file = True
                    elif loader_type == "SQL":
                        st.session_state.show_loader_sql = True
                    elif loader_type == "API":
                        st.session_state.show_loader_api = True
                    else:
                        # Default to File if unknown
                        st.session_state.show_loader_file = True

                    st.session_state.dlg_just_opened = True
                    st.rerun()

                if c_delete.button("🗑️", key=f"del_{name}"):
                    engine.datasets.remove(name)
                    if name in st.session_state.all_recipes:
                        del st.session_state.all_recipes[name]
                    if st.session_state.active_base_dataset == name:
                        st.session_state.active_base_dataset = None
                        st.session_state.recipe_steps = []
                    st.rerun()

        if active_ds:
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
                    options_map = {
                        label: step_type for step_type, label in steps}

                    selected_label = st.selectbox(
                        "Operation", list(options_map.keys()), key="sel_operation"
                    )

                    if selected_label and st.button("Add Step", key="btn_add_step", type="primary", width="stretch"):
                        step_type = options_map[selected_label]
                        add_step(step_type, selected_label)

        if active_ds:
            st.divider()

            # --- 3. RECIPE ACTIONS ---
            with st.expander("🔪 Recipe Actions", expanded=False):
                # Get recipe for the active dataset from all_recipes
                dataset_recipe = st.session_state.all_recipes.get(
                    active_ds, [])

                if not dataset_recipe:
                    st.info(
                        f"ℹ️ No recipe steps for '{active_ds}' yet. Add transformations to create a recipe.")

                # Serialize for Generic RecipeStep (which has .model_dump())
                serialized_recipe = [s.model_dump() for s in dataset_recipe]
                recipe_json = json.dumps(serialized_recipe, indent=2)

                st.download_button("💾 Download JSON", recipe_json, f"recipe_{active_ds}.json",
                                   "application/json", width="stretch",
                                   disabled=not dataset_recipe,
                                   help=f"Download recipe for {active_ds} ({len(dataset_recipe)} steps)")

                uploaded_recipe = st.file_uploader(
                    "Restore JSON", type=["json"])
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
                    engine.io.cleanup_staging(0)  # Force clear
                    st.toast("Cache cleared successfully!", icon="🧹")
                except Exception as e:
                    st.error(f"Cleanup failed: {e}")

        # --- FINAL: PERSIST STATE FOR NEXT RUN ---
        # We compute hash at the END to capture any programmatic state changes made during this run.
        # Use list() to snapshot keys to avoid iteration errors during rapid state changes
        try:
            dlg_keys = [k for k in list(st.session_state.keys()) if isinstance(
                k, str) and k.startswith("dlg_")]
            end_dlg_values = {k: st.session_state.get(k) for k in dlg_keys}
            # Filter buttons
            end_values_str = str(sorted(
                [(k, v) for k, v in end_dlg_values.items() if not k.startswith("dlg_btn")]))
            st.session_state.last_dlg_hash = hashlib.md5(
                end_values_str.encode()).hexdigest()
        except Exception:
            pass  # Ignore hash computation errors during rapid state changes
