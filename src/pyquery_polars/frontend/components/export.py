from typing import cast
import streamlit as st
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
            ui_schema = get_exporter_schema(selected_exporter.name)

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
