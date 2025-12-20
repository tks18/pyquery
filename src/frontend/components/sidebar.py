import streamlit as st
import json
from typing import cast
from src.frontend.state_manager import add_step, load_recipe_from_json
from src.frontend.utils.dynamic_ui import render_schema_fields
from src.backend.engine import PyQueryEngine
from src.core.registry import StepRegistry


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

                params = render_schema_fields(
                    loader.ui_schema, key_prefix=f"load_{loader.name}")
                alias_val = params.get('alias')

                if st.button("Load Data", type="primary", key=f"btn_load_{loader.name}", use_container_width=True):
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

                        lf = engine.run_loader(loader.name, final_params)
                        if lf is not None:
                            engine.add_dataset(alias_val, lf)
                            if alias_val not in st.session_state.all_recipes:
                                st.session_state.all_recipes[alias_val] = []

                            if len(engine.get_dataset_names()) == 1:
                                st.session_state.active_base_dataset = alias_val
                                st.session_state.recipe_steps = []

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

                if c1.button(label, key=f"sel_{name}", use_container_width=True):
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

                if selected_label and st.button("Add Step", key="btn_add_step", type="primary", use_container_width=True):
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
                               "application/json", use_container_width=True)

            uploaded_recipe = st.file_uploader("Restore JSON", type=["json"])
            if uploaded_recipe and st.button("Apply Restore", use_container_width=True):
                load_recipe_from_json(uploaded_recipe)
                st.rerun()

            if st.button("🗑️ Clear All Steps", type="secondary", use_container_width=True):
                active_ds = st.session_state.active_base_dataset
                if active_ds:
                    st.session_state.all_recipes[active_ds] = []
                    st.session_state.recipe_steps = []
                    st.rerun()
