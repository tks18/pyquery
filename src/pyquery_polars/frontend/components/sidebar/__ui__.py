"""
Sidebar component module.

Provides dataset management, pipeline tools, and application settings.
Includes subcomponents for modularity.
"""

import streamlit as st

from pyquery_polars.frontend.base import BaseComponent
from pyquery_polars.frontend.components.sidebar.dataset_manager import SidebarDatasetManager
from pyquery_polars.frontend.components.sidebar.pipeline_tools import SidebarPipelineTools


class SidebarComponent(BaseComponent):
    """
    Component handling the application sidebar.
    Includes Dataset Manager, Pipeline Tools, and Global Actions.
    """

    def render(self) -> None:
        """Render the application sidebar."""
        if not self.engine:
            st.error("Engine not initialized.")
            return

        with st.sidebar:
            st.title("⚡ Shan's PyQuery")

            self._render_header_actions()
            st.divider()

            # Dataset Manager
            ds_manager = SidebarDatasetManager(self.ctx)
            ds_manager.render()

            if self.state.active_dataset:
                st.divider()
                # Pipeline Tools
                SidebarPipelineTools(self.ctx).render()

            st.divider()
            self._render_settings()

    def _render_header_actions(self):
        """Render active dataset indicator and project actions."""
        active_ds = self.state.active_dataset
        col_ds, col_save, col_load = st.columns([0.6, 0.2, 0.2])

        if active_ds:
            col_ds.markdown(f"🎯 **{active_ds}**")
        else:
            col_ds.caption("No dataset loaded")

        col_save.button("💾", help="Save Project", key="header_proj_save",
                        on_click=self._open_project_export)
        col_load.button("📂", help="Load Project", key="header_proj_load",
                        on_click=self._open_project_import)

    def _open_project_export(self):
        self.state.reset_dialog_state()
        self.state.close_all_dialogs()
        self.state.open_dialog("project_export")

    def _open_project_import(self):
        self.state.reset_dialog_state()
        self.state.close_all_dialogs()
        self.state.open_dialog("project_import")

    def _render_settings(self):
        if st.button("🧹 Clear Cache / Staging", help="Force delete all temporary files.", width="stretch"):
            try:
                self.engine.io.cleanup_staging(0)
                st.toast("Cache cleared successfully!", icon="🧹")
            except Exception as e:
                st.error(f"Cleanup failed: {e}")
