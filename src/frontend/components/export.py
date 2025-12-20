from typing import cast
import streamlit as st
from src.frontend.utils.dynamic_ui import render_schema_fields
from src.backend.engine import PyQueryEngine


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
            # Use Shared UI Renderer
            params = render_schema_fields(
                selected_exporter.ui_schema,
                key_prefix=f"exp_{selected_exporter_name}",
                columns=2
            )

            if st.form_submit_button("Export Start"):
                # Enterprise: Instatiate specific Param Model if available
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
                    final_params
                )

                # Polling UI
                status_placeholder = st.empty()

                with st.spinner("Exporting in background..."):
                    import time
                    while True:
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
