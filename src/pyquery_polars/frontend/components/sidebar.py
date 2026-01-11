import streamlit as st
import json
from typing import cast
from pyquery_polars.frontend.state_manager import add_step, load_recipe_from_json, undo, redo
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.registry import StepRegistry


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

        # New Modal-Based Import Section
        st.write("###### Import Data")
        col_imp1, col_imp2, col_imp3 = st.columns(3)

        from pyquery_polars.frontend.components.loaders import show_file_loader, show_sql_loader, show_api_loader

        if col_imp1.button("📂 File", help="Import Local Files", use_container_width=True):
            show_file_loader(engine)

        if col_imp2.button("🛢️ SQL", help="Connect Database", use_container_width=True):
            show_sql_loader(engine)

        if col_imp3.button("🌐 API", help="REST API Import", use_container_width=True):
            show_api_loader(engine)

        # B. LIST EXISTING
        dataset_names = engine.get_dataset_names()
        if dataset_names:
            st.divider()
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
                    engine.cleanup_staging(0)  # Force clear
                    st.toast("Cache cleared successfully!", icon="🧹")
                except Exception as e:
                    st.error(f"Cleanup failed: {e}")
