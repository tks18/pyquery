"""
Project dialog component module.

Provides project import/export dialogs.
"""

import os
import streamlit as st
import tempfile
import time

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.frontend.utils.file_picker import pick_folder


@st.dialog("Export Project", width="large")
def _show_export_dialog_task(ctx: AppContext):
    engine = ctx.engine
    state = ctx.state_manager
    dataset_names = engine.datasets.list_names()

    if not dataset_names:
        st.warning("No datasets to export. Load some data first!")
        if st.button("Close"):
            state.close_dialog("project_export")
            st.rerun()
        return

    st.info(
        f"📦 This project contains **{len(dataset_names)} dataset(s)**: {', '.join(dataset_names)}")

    st.markdown("#### Path Settings")
    path_mode = st.radio("Path Mode", ["Absolute Paths", "Relative Paths"], horizontal=True,
                         help="**Absolute**: Full paths (only works on this machine)\n\n**Relative**: Portable across machines")

    base_dir = None
    if path_mode == "Relative Paths":
        st.caption(
            "Relative paths will be calculated from the base directory.")
        col_base, col_pick_base = st.columns([0.8, 0.2])

        def on_pick_base():
            picked = pick_folder("Select Base Directory")
            if picked:
                state.proj_export_base_dir = picked

        base_dir = col_base.text_input("Base Directory", value=state.proj_export_base_dir or os.getcwd(),
                                       key="dlg_proj_export_base_dir_input")

        col_pick_base.markdown(
            "<div style='height: 28px'></div>", unsafe_allow_html=True)
        col_pick_base.button("📁", on_click=on_pick_base, key="dlg_btn_pick_export_base",
                             help="Browse for folder")

    st.markdown("#### Output File")
    col_path, col_pick = st.columns([0.8, 0.2])
    default_filename = "project.pyquery"
    default_folder = os.getcwd()

    active_ds = state.active_dataset
    if active_ds:
        dataset_meta = engine.datasets.get_metadata(active_ds)
        source_path = dataset_meta.source_path if dataset_meta else None
        if source_path and isinstance(source_path, str):
            if os.path.isfile(source_path):
                default_folder = os.path.dirname(source_path)
            elif os.path.isdir(source_path):
                default_folder = source_path

    default_path = os.path.join(default_folder, default_filename)
    output_path = col_path.text_input("Save As", value=state.proj_export_path or default_path,
                                      key="dlg_proj_export_path_input", placeholder="e.g., C:\\Projects\\my_analysis.pyquery")

    def on_pick_output():
        picked = pick_folder("Select Output Directory")
        if picked:
            state.proj_export_path = os.path.join(picked, default_filename)

    col_pick.button("📁", on_click=on_pick_output,
                    key="dlg_btn_pick_export_out", help="Browse for folder")

    description = st.text_area(
        "Description (optional)", placeholder="Brief description of this project...", max_chars=500, key="dlg_proj_export_desc")

    col_cancel, col_export = st.columns([0.3, 0.7])
    if col_cancel.button("Cancel", use_container_width=True, key="dlg_btn_export_cancel"):
        state.close_dialog("project_export")
        st.rerun()

    if col_export.button("💾 Export Project", type="primary", use_container_width=True, key="dlg_btn_export_confirm"):
        if not output_path:
            st.error("Please specify an output path.")
            return
        try:
            with st.spinner("Exporting project..."):
                path_mode_value = "relative" if path_mode == "Relative Paths" else "absolute"
                saved_path = engine.projects.save_to_file(file_path=output_path, path_mode=path_mode_value,
                                                          base_dir=base_dir, description=description or None)
            st.success(f"✅ Project saved to:\n`{saved_path}`")
            time.sleep(1.5)
            state.close_dialog("project_export")
            st.rerun()
        except Exception as e:
            st.error(f"Export failed: {e}")


@st.dialog("Import Project", width="large")
def _show_import_dialog_task(ctx: AppContext):
    engine = ctx.engine
    state = ctx.state_manager
    st.markdown("#### Select Project File")
    uploaded_file = st.file_uploader("Choose a .pyquery file", type=[
                                     "pyquery"], key="dlg_proj_import_file")

    if uploaded_file:
        st.success(f"Selected: **{uploaded_file.name}**")

    st.markdown("#### Import Mode")
    import_mode = "Replace All"
    if uploaded_file:
        import_mode = st.radio("Mode", ["Replace All", "Merge with Existing"], horizontal=True,
                               help="**Replace**: Clear current | **Merge**: Add alongside", key="dlg_proj_import_mode")
        current_datasets = engine.datasets.list_names()
        if current_datasets and import_mode == "Replace All":
            st.warning(
                f"⚠️ This will replace {len(current_datasets)} existing dataset(s).")

    st.divider()
    col_cancel, col_import = st.columns([0.3, 0.7])

    if col_cancel.button("Cancel", use_container_width=True, key="dlg_btn_import_cancel"):
        state.close_dialog("project_import")
        st.rerun()

    import_disabled = uploaded_file is None
    if col_import.button("📂 Import Project", type="primary", use_container_width=True, disabled=import_disabled, key="dlg_btn_import_confirm"):
        if not uploaded_file:
            return
        try:
            with st.spinner("Importing project..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pyquery") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                try:
                    mode = "replace" if import_mode == "Replace All" else "merge"
                    result = engine.projects.load_from_file(
                        tmp_path, mode=mode)

                    # Use ctx.state_manager.sync_all_from_backend
                    ctx.state_manager.sync_all_from_backend()

                    if result.datasets_loaded:
                        state.active_dataset = result.datasets_loaded[0]
                        st.success(
                            f"✅ Loaded {len(result.datasets_loaded)} dataset(s).")

                    if result.warnings:
                        for w in result.warnings:
                            st.warning(f"⚠️ {w}")
                    if result.errors:
                        for e in result.errors:
                            st.error(f"❌ {e}")

                    if result.success:
                        time.sleep(1.5)
                        state.close_dialog("project_import")
                        st.rerun()
                finally:
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
        except Exception as e:
            st.error(f"Import failed: {e}")


class ProjectDialogComponent(BaseComponent):
    """
    Component for handling Project Import/Export interactions.
    """

    def render(self, show_buttons: bool = True) -> None:
        """Render the Project section and/or handle dialogs."""
        if not self.engine:
            return

        if show_buttons:
            col_label, col_save, col_load = st.columns([0.5, 0.25, 0.25])
            col_label.caption("📁 **Project**")
            col_save.button("💾", help="Save Project (.pyquery)",
                            key="sidebar_proj_save", on_click=self._open_export_dialog)
            col_load.button("📂", help="Load Project (.pyquery)",
                            key="sidebar_proj_load", on_click=self._open_import_dialog)

        # Render dialogs if state is active
        if self.state.is_dialog_open("project_export"):
            _show_export_dialog_task(self.ctx)

        if self.state.is_dialog_open("project_import"):
            _show_import_dialog_task(self.ctx)

    def _open_export_dialog(self):
        self.state.close_all_dialogs()
        self.state.open_dialog("project_export")

    def _open_import_dialog(self):
        self.state.close_all_dialogs()
        self.state.open_dialog("project_import")
