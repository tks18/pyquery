from typing import cast
import streamlit as st
import copy
from pyquery_polars.frontend.utils.dynamic_ui import render_schema_fields
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.utils.io_schemas import get_exporter_schema


def render_export_section(dataset_name):  # Takes name
    st.divider()
    st.subheader("📤 Export Data")

    # Strict Typing for Engine
    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        return

    with st.expander("Export Options"):
        exporters = engine.get_exporters()
        if not exporters:
            st.warning("No exporters registered.")
            return

        exporter_map = {e.name: e for e in exporters}
        selected_exporter_name = st.selectbox(
            "Format", list(exporter_map.keys()))
        selected_exporter = exporter_map[selected_exporter_name]

        with st.form("export_form"):
            # Decoupled Schema Lookup
            ui_schema = copy.deepcopy(
                get_exporter_schema(selected_exporter.name))

            # DYNAMIC DEFAULT: Output Path
            # Try to default to source directory
            dataset_meta = engine.get_dataset_metadata(dataset_name)
            source_path = dataset_meta.get("source_path")

            if source_path:
                import os
                default_filename = f"export_{dataset_name}"
                # Find the 'path' field in schema
                for field in ui_schema:
                    if field.name == "path":
                        # Suggest a path in the same directory
                        # E.g. /data/foo.csv -> /data/export_foo.parquet
                        ext = ".parquet" if selected_exporter_name == "Parquet" else f".{selected_exporter_name.lower()}"
                        if selected_exporter_name == "Arrow IPC":
                            ext = ".arrow"
                        if selected_exporter_name == "Excel":
                            ext = ".xlsx"

                        field.default = os.path.join(
                            source_path, f"{default_filename}{ext}")
                        break

            # Use Shared UI Renderer
            params = render_schema_fields(
                ui_schema,
                key_prefix=f"exp_{selected_exporter_name}",
                columns=2
            )

            if st.form_submit_button("Export Start"):
                final_params = params
                if selected_exporter.params_model:
                    try:
                        final_params = selected_exporter.params_model.model_validate(
                            params)
                    except Exception as e:
                        st.error(f"Invalid Parameters: {e}")
                        return

                # Start Backend Job (using typed params)
                job_id = engine.start_export_job(
                    dataset_name,
                    st.session_state.recipe_steps,
                    selected_exporter_name,
                    final_params,
                    project_recipes=st.session_state.all_recipes
                )

                # Polling UI
                status_placeholder = st.empty()
                import time
                start_ts = time.time()

                with st.spinner(f"Exporting..."):
                    while True:
                        # Timer Update
                        elapsed = time.time() - start_ts
                        status_placeholder.info(
                            f"⏳ Exporting in background... ({elapsed:.2f}s)")

                        # Status Check
                        job_info = engine.get_job_status(job_id)
                        if not job_info:
                            time.sleep(0.5)
                            continue

                        status = job_info.status

                        if status == "RUNNING":
                            time.sleep(0.5)
                        elif status == "COMPLETED":
                            # Safe access if fields exist (Pydantic model)
                            dur = getattr(job_info, 'duration', 0.0)
                            # DEFENSIVE: If backend returns 0.0 (fast or race), use frontend elapsed
                            if dur <= 0.001:
                                dur = elapsed

                            size = getattr(job_info, 'size_str', "Unknown")
                            status_placeholder.success(
                                f"✅ Export Complete! Time: {dur:.2f}s | Size: {size}")
                            break
                        elif status == "FAILED":
                            err_msg = getattr(
                                job_info, 'error', "Unknown Error")
                            status_placeholder.error(
                                f"❌ Failed: {err_msg}")
                            break
                        else:
                            time.sleep(0.1)
