"""
Sidebar Pipeline Tools component.

Handles pipeline actions (undo/redo), step addition, and recipe management.
"""

import streamlit as st
import json

from pyquery_polars.frontend.base import BaseComponent
from pyquery_polars.core.registry import StepRegistry


class SidebarPipelineTools(BaseComponent):
    """
    Manages transformation pipeline tools in the sidebar.
    """

    def render(self) -> None:
        """Render pipeline tools and recipe actions."""
        self._render_pipeline_tools()
        st.divider()
        self._render_recipe_actions()

    def _undo_cb(self) -> None:
        self.ctx.state_manager.undo()

    def _redo_cb(self) -> None:
        self.ctx.state_manager.redo()

    def _render_pipeline_tools(self):
        st.subheader("🛠️ Pipeline")
        c_undo, c_redo = st.columns(2)
        can_undo = self.state.can_undo
        can_redo = self.state.can_redo

        # Use methods from ctx.state_manager via wrappers
        c_undo.button("↩ Undo", on_click=self._undo_cb,
                      disabled=not can_undo, width="stretch", key="btn_undo")
        c_redo.button("↪ Redo", on_click=self._redo_cb,
                      disabled=not can_redo, width="stretch", key="btn_redo")

        registry = StepRegistry.get_all()
        if not registry:
            st.warning("System updated. Reload required.")
            if st.button("♻️ Reload System", key="btn_reload_sys", type="primary"):
                self.ctx.state_manager.hard_reset()
                st.rerun()
            return

        # Group logic
        grouped_steps = {}
        for step_type, def_obj in registry.items():
            group = def_obj.metadata.group
            if group not in grouped_steps:
                grouped_steps[group] = []
            grouped_steps[group].append((step_type, def_obj.metadata.label))

        preferred_order = ["Columns", "Rows", "Combine",
                           "Clean", "Analytics", "Math & Date"]
        sorted_groups = sorted(grouped_steps.keys(), key=lambda x: preferred_order.index(
            x) if x in preferred_order else 99)

        if sorted_groups:
            selected_group = st.selectbox(
                "Category", sorted_groups, key="sel_category")
            steps = grouped_steps[selected_group]
            options_map = {label: step_type for step_type, label in steps}
            selected_label = st.selectbox("Operation", list(
                options_map.keys()), key="sel_operation")

            if selected_label and st.button("Add Step", key="btn_add_step", type="primary", width="stretch"):
                # Call add_step on state_manager
                self.ctx.state_manager.add_step(
                    options_map[selected_label], selected_label)

    def _render_recipe_actions(self):
        """Render recipe management actions."""
        with st.expander("🔪 Recipe Actions", expanded=False):
            active_ds = self.state.active_dataset
            dataset_recipe = self.state.get_active_recipe()

            if not dataset_recipe:
                st.info(f"ℹ️ No recipe steps for '{active_ds}' yet.")

            serialized_recipe = [s.model_dump() for s in dataset_recipe]
            recipe_json = json.dumps(serialized_recipe, indent=2)

            st.download_button("💾 Download JSON", recipe_json,
                               f"recipe_{active_ds}.json", "application/json", width="stretch", disabled=not dataset_recipe)

            uploaded_recipe = st.file_uploader("Restore JSON", type=["json"])
            if uploaded_recipe and st.button("Apply Restore", width="stretch"):
                self.ctx.state_manager.load_recipe_from_json(uploaded_recipe)
                st.rerun()

            if st.button("🗑️ Clear All Steps", type="secondary", width="stretch"):
                if active_ds:
                    self.state.clear_active_recipe()
                    st.rerun()
