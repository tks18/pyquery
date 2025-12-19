import streamlit as st
from src.frontend.utils.dynamic_ui import render_schema_fields

def render_export_section(dataset_name): # Takes name
    st.divider()
    st.subheader("📤 Export Data")
    
    engine = st.session_state.get('engine')
    if not engine: return

    with st.expander("Export Options"):
        exporters = engine.get_exporters()
        if not exporters:
             st.warning("No exporters registered.")
             return
             
        exporter_map = {e['name']: e for e in exporters}
        selected_exporter_name = st.selectbox("Format", list(exporter_map.keys()))
        selected_exporter = exporter_map[selected_exporter_name]
        
        with st.form("export_form"):
            # Use Shared UI Renderer
            # For export we often want columns. Pass columns=2
            params = render_schema_fields(
                selected_exporter.get('ui_schema', []), 
                key_prefix=f"exp_{selected_exporter_name}", 
                columns=2
            )

            if st.form_submit_button("Export Start"):
                    # Start Backend Job (using plugin params)
                    job_id = engine.start_export_job(
                        dataset_name, 
                        st.session_state.recipe_steps, 
                        selected_exporter_name, 
                        params
                    )
                    
                    # Polling UI
                    status_placeholder = st.empty()
                    
                    with st.spinner("Exporting in background..."):
                        import time
                        while True:
                            job_info = engine.get_job_status(job_id)
                            status = job_info.get("status")
                            
                            if status == "RUNNING":
                                time.sleep(0.5)
                            elif status == "COMPLETED":
                                dur = job_info.get("duration", 0)
                                size = job_info.get("size_str", "Unknown")
                                status_placeholder.success(f"✅ Export Complete! Time: {dur:.2f}s | Size: {size}")
                                break
                            elif status == "FAILED":
                                status_placeholder.error(f"❌ Failed: {job_info.get('error')}")
                                break
                            else:
                                time.sleep(0.1)
