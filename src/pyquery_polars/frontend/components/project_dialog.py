from typing import cast

import os
import streamlit as st

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.frontend.state_manager import sync_all_from_backend
from pyquery_polars.frontend.utils.file_picker import pick_folder


def _reset_other_dialogs():
    """Reset other dialog states when opening project dialogs."""
    st.session_state.show_loader_file = False
    st.session_state.show_loader_sql = False
    st.session_state.show_loader_api = False
    st.session_state.edit_mode_dataset = None
    # Clear dialog-specific state
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith("dlg_"):
            del st.session_state[key]


def render_project_section():
    """
    Render the Project section in the sidebar.
    Compact design that integrates well with the sidebar flow.
    """
    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        return

    # Initialize dialog state
    if "show_project_export" not in st.session_state:
        st.session_state.show_project_export = False
    if "show_project_import" not in st.session_state:
        st.session_state.show_project_import = False

    def open_export_dialog():
        _reset_other_dialogs()
        st.session_state.show_project_export = True
        st.session_state.show_project_import = False

    def open_import_dialog():
        _reset_other_dialogs()
        st.session_state.show_project_import = True
        st.session_state.show_project_export = False

    # Compact horizontal layout - project actions as small icon-style buttons
    col_label, col_save, col_load = st.columns([0.5, 0.25, 0.25])
    col_label.caption("📁 **Project**")
    col_save.button("💾", help="Save Project (.pyquery)",
                    key="btn_proj_save", on_click=open_export_dialog)
    col_load.button("📂", help="Load Project (.pyquery)",
                    key="btn_proj_load", on_click=open_import_dialog)


def show_project_export_dialog(engine: PyQueryEngine):
    """Render the project export dialog (called from sidebar after state check)."""

    @st.dialog("Export Project", width="large")
    def export_dialog():
        dataset_names = engine.datasets.list_names()

        if not dataset_names:
            st.warning("No datasets to export. Load some data first!")
            if st.button("Close"):
                st.session_state.show_project_export = False
                st.rerun()
            return

        st.info(
            f"📦 This project contains **{len(dataset_names)} dataset(s)**: {', '.join(dataset_names)}")

        # Path mode selection
        st.markdown("#### Path Settings")
        path_mode = st.radio(
            "Path Mode",
            ["Absolute Paths", "Relative Paths"],
            horizontal=True,
            help="**Absolute**: Full paths (only works on this machine)\n\n**Relative**: Portable across machines"
        )

        base_dir = None
        if path_mode == "Relative Paths":
            st.caption(
                "Relative paths will be calculated from the base directory.")

            col_base, col_pick = st.columns([0.8, 0.2])
            base_dir = col_base.text_input(
                "Base Directory",
                value=st.session_state.get(
                    "proj_export_base_dir", os.getcwd()),
                key="proj_export_base_dir_input"
            )

            def on_pick_base():
                picked = pick_folder("Select Base Directory")
                if picked:
                    st.session_state.proj_export_base_dir = picked

            col_pick.button("📁", on_click=on_pick_base,
                            help="Browse for folder")

        # Output file
        st.markdown("#### Output File")

        col_path, col_pick = st.columns([0.8, 0.2])

        default_filename = "project.pyquery"

        # Default folder from active dataset's source path (like export component)
        default_folder = os.getcwd()
        active_ds = st.session_state.get("active_base_dataset")
        if active_ds:
            dataset_meta = engine.datasets.get_metadata(active_ds)
            source_path = dataset_meta.source_path if dataset_meta else None
            if source_path and isinstance(source_path, str):
                if os.path.isfile(source_path):
                    default_folder = os.path.dirname(source_path)
                elif os.path.isdir(source_path):
                    default_folder = source_path

        default_path = os.path.join(default_folder, default_filename)

        output_path = col_path.text_input(
            "Save As",
            value=st.session_state.get("proj_export_path", default_path),
            key="proj_export_path_input",
            placeholder="e.g., C:\\Projects\\my_analysis.pyquery"
        )

        def on_pick_output():
            picked = pick_folder("Select Output Directory")
            if picked:
                st.session_state.proj_export_path = os.path.join(
                    picked, default_filename)

        col_pick.button("📁", on_click=on_pick_output,
                        key="btn_pick_export", help="Browse for folder")

        # Description (optional)
        description = st.text_area(
            "Description (optional)",
            placeholder="Brief description of this project...",
            max_chars=500
        )

        # Action buttons
        col_cancel, col_export = st.columns([0.3, 0.7])

        if col_cancel.button("Cancel", use_container_width=True):
            st.session_state.show_project_export = False
            st.rerun()

        if col_export.button("💾 Export Project", type="primary", use_container_width=True):
            if not output_path:
                st.error("Please specify an output path.")
                return

            try:
                with st.spinner("Exporting project..."):
                    path_mode_value = "relative" if path_mode == "Relative Paths" else "absolute"

                    saved_path = engine.projects.save_to_file(
                        file_path=output_path,
                        path_mode=path_mode_value,
                        base_dir=base_dir,
                        description=description if description else None
                    )

                st.success(f"✅ Project saved to:\n`{saved_path}`")

                # Close after short delay
                import time
                time.sleep(1.5)
                st.session_state.show_project_export = False
                st.rerun()

            except Exception as e:
                st.error(f"Export failed: {e}")

    export_dialog()


def show_project_import_dialog(engine: PyQueryEngine):
    """Render the project import dialog (called from sidebar after state check)."""

    @st.dialog("Import Project", width="large")
    def import_dialog():
        st.markdown("#### Select Project File")

        uploaded_file = st.file_uploader(
            "Choose a .pyquery file",
            type=["pyquery"],
            key="proj_import_file"
        )

        if uploaded_file:
            st.success(f"Selected: **{uploaded_file.name}**")

            # Import mode
        st.markdown("#### Import Mode")
        import_mode = "Replace All"  # Default
        if uploaded_file:
            import_mode = st.radio(
                "Mode",
                ["Replace All", "Merge with Existing"],
                horizontal=True,
                help="**Replace**: Clear all current datasets and load from project\n\n**Merge**: Add project datasets alongside existing (skip conflicts)"
            )

            current_datasets = engine.datasets.list_names()
            if current_datasets and import_mode == "Replace All":
                st.warning(
                    f"⚠️ This will replace {len(current_datasets)} existing dataset(s): {', '.join(current_datasets)}")

        st.divider()

        # Action buttons
        col_cancel, col_import = st.columns([0.3, 0.7])

        if col_cancel.button("Cancel", use_container_width=True):
            st.session_state.show_project_import = False
            st.rerun()

        import_disabled = uploaded_file is None

        if col_import.button("📂 Import Project", type="primary", use_container_width=True, disabled=import_disabled):
            if uploaded_file is None:
                return
            try:
                with st.spinner("Importing project..."):
                    # Save uploaded file to temp location
                    import tempfile

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pyquery") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    try:
                        # Import
                        mode = "replace" if import_mode == "Replace All" else "merge"
                        result = engine.projects.load_from_file(
                            tmp_path, mode=mode)

                        # Sync frontend state from backend
                        sync_all_from_backend()

                        # Set active dataset to first loaded
                        if result.datasets_loaded:
                            st.session_state.active_base_dataset = result.datasets_loaded[0]
                            st.session_state.recipe_steps = st.session_state.all_recipes.get(
                                result.datasets_loaded[0], []
                            )

                        # Show results
                        if result.datasets_loaded:
                            st.success(
                                f"✅ Loaded {len(result.datasets_loaded)} dataset(s): {', '.join(result.datasets_loaded)}")

                        if result.warnings:
                            for w in result.warnings:
                                st.warning(f"⚠️ {w}")

                        if result.errors:
                            for e in result.errors:
                                st.error(f"❌ {e}")

                        if result.success:
                            import time
                            time.sleep(1.5)
                            st.session_state.show_project_import = False
                            st.rerun()

                    finally:
                        # Cleanup temp file
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass

            except Exception as e:
                st.error(f"Import failed: {e}")

    import_dialog()
