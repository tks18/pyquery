"""
Export Component - Class-based data export functionality.

This module provides the export section for exporting datasets
to various formats (Parquet, CSV, Excel, etc.).
"""

from typing import Optional

import streamlit as st
import pandas as pd
import os
import time

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.frontend.utils.dynamic_ui import render_schema_fields
from pyquery_polars.frontend.utils.io_schemas import get_exporter_schema
from pyquery_polars.frontend.utils.file_picker import pick_folder


class ExportComponent(BaseComponent):
    """
    Export component for data export operations.

    Provides UI for:
    - Format selection
    - Output path configuration
    - Export parameters
    - Progress tracking
    """

    def __init__(self, ctx: AppContext) -> None:
        """Initialize with app context."""
        super().__init__(ctx)
        self.dataset_name: Optional[str] = None

    def render(self, dataset_name: str) -> None:
        """
        Render the export section.

        Args:
            dataset_name: Name of the dataset to export
        """
        st.divider()
        st.subheader("📤 Export Data")

        self.dataset_name = dataset_name

        if not self.engine:
            return

        with st.expander("Export Options"):
            exporters = self.engine.io.get_exporters()
            if not exporters:
                st.warning("No exporters registered.")
                return

            exporter_map = {e.name: e for e in exporters}
            selected_exporter_name = st.selectbox(
                "Format", list(exporter_map.keys()))
            selected_exporter = exporter_map[selected_exporter_name]

            # Decoupled Schema Lookup
            base_schema = get_exporter_schema(selected_exporter.name)
            ui_schema = [f for f in base_schema if f.name != "path"]

            # Path builder
            params = self._render_path_builder(selected_exporter_name)

            # Additional params from schema
            schema_params = render_schema_fields(
                ui_schema,
                key_prefix=f"exp_{selected_exporter_name}",
                columns=2
            )
            params.update(schema_params)

            # Export button
            self._handle_export(selected_exporter,
                                selected_exporter_name, params)

    def _render_path_builder(self, exporter_name: str) -> dict:
        """Render path builder UI and return params dict."""
        st.write("###### Output Destination")

        folder_key = f"exp_{exporter_name}_folder"
        filename_key = f"exp_{exporter_name}_filename"

        # Default folder from dataset source
        if not self.dataset_name:
            return {}

        dataset_meta = self.engine.datasets.get_metadata(self.dataset_name)
        source_path = dataset_meta.source_path if dataset_meta else None
        default_folder = os.getcwd()
        if source_path:
            if os.path.isfile(source_path):
                default_folder = os.path.dirname(source_path)
            else:
                default_folder = source_path

        # Init states
        if not self.state.has_value(folder_key):
            self.state.set_value(folder_key, default_folder)
        if not self.state.has_value(filename_key):
            self.state.set_value(filename_key, f"export_{self.dataset_name}")

        # Folder picker
        c1, c2 = st.columns([0.85, 0.15])
        folder_path = c1.text_input("Destination Folder", key=folder_key)

        def on_pick_folder(key):
            picked = pick_folder(title="Select Output Folder")
            if picked:
                self.state.set_value(key, picked)

        c2.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        c2.button("📂", key=f"btn_browse_{exporter_name}",
                  on_click=on_pick_folder, args=(folder_key,),
                  help="Pick Folder", width="stretch")

        # Export individual checkbox
        exp_ind = False
        meta = self.engine.datasets.get_metadata(self.dataset_name)
        if meta and meta.process_individual and meta.input_type == "folder":
            exp_ind = st.checkbox(
                "📂 Export as Separate Files",
                value=False,
                help="Apply recipe to each source file individually.",
                key=f"exp_{exporter_name}_individual"
            )
            if exp_ind:
                st.info(
                    "Each source file will be exported with the prefix defined below.")

        # Filename input
        fname_label = "Filename Prefix" if exp_ind else "Filename"
        filename_val = st.text_input(fname_label, key=filename_key)

        # Extension logic
        ext = self._get_extension(exporter_name)

        # Preview and build path
        if exp_ind:
            full_path = os.path.join(folder_path, f"{filename_val}_*{ext}")
            st.caption(f"📝 **Target Pattern:** `{full_path}`")
            full_path_backend = os.path.join(
                folder_path, f"{filename_val}{ext}")
        else:
            full_path = os.path.join(folder_path, f"{filename_val}{ext}")
            full_path_backend = full_path
            st.caption(f"📝 **Target:** `{full_path}`")

        st.divider()

        params: dict = {"path": full_path_backend}
        if exp_ind:
            params["export_individual"] = True

        return params

    def _get_extension(self, exporter_name: str) -> str:
        """Get file extension for exporter."""
        if exporter_name == "Parquet":
            return ".parquet"
        elif exporter_name == "Arrow IPC":
            return ".arrow"
        elif exporter_name == "Excel":
            return ".xlsx"
        else:
            return f".{exporter_name.lower()}"

    def _handle_export(self, exporter, exporter_name: str, params: dict) -> None:
        """Handle export button click and progress."""
        if not st.button("Export Start", type="primary", key=f"btn_start_exp_{exporter_name}"):
            return

        final_params = params
        if exporter.params_model:
            try:
                final_params = exporter.params_model.model_validate(params)
            except Exception as e:
                st.error(f"Invalid Parameters: {e}")
                return

        # Start export job
        if not self.dataset_name:
            st.error("No dataset selected")
            return

        job_id = self.engine.jobs.start_export_job(
            self.dataset_name,
            self.state.recipe_steps,
            exporter_name,
            final_params,
            project_recipes=self.state.all_recipes
        )

        # Polling UI
        self._poll_export_progress(job_id)

    def _poll_export_progress(self, job_id: str) -> None:
        """Poll and display export progress."""
        status_placeholder = st.empty()
        start_ts = time.time()

        with st.spinner("Exporting..."):
            while True:
                elapsed = time.time() - start_ts
                status_placeholder.info(
                    f"⏳ Exporting in background... ({elapsed:.2f}s)")

                job_info = self.engine.jobs.get_job_status(job_id)
                if not job_info:
                    time.sleep(0.5)
                    continue

                status = job_info.status

                if status == "RUNNING":
                    time.sleep(0.5)
                elif status == "COMPLETED":
                    dur = getattr(job_info, 'duration', 0.0)
                    if dur <= 0.001:
                        dur = elapsed
                    size = getattr(job_info, 'size_str', "Unknown")

                    status_placeholder.success(
                        f"✅ Export Complete! Time: {dur:.2f}s | Total Size: {size}")

                    # File details
                    details = getattr(job_info, 'file_details', None)
                    if details:
                        with st.expander("📄 Exported Files Details", expanded=True):
                            df_details = pd.DataFrame(details)
                            if not df_details.empty:
                                df_display = df_details[[
                                    'name', 'size', 'path']]
                                df_display.columns = [
                                    'Filename', 'Size', 'Full Path']
                                st.dataframe(
                                    df_display, width="stretch", hide_index=True)
                    break
                elif status == "FAILED":
                    err_msg = getattr(job_info, 'error', "Unknown Error")
                    status_placeholder.error(f"❌ Failed: {err_msg}")
                    break
                else:
                    time.sleep(0.1)
