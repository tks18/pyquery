from typing import cast
import streamlit as st
import copy
import pandas as pd
from pyquery_polars.frontend.utils.dynamic_ui import render_schema_fields
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.utils.io_schemas import get_exporter_schema
from pyquery_polars.frontend.utils.file_picker import pick_folder
import os


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

        # Decoupled Schema Lookup
        base_schema = get_exporter_schema(selected_exporter.name)
        # Filter out 'path' from auto-renderer
        ui_schema = [f for f in base_schema if f.name != "path"]

        # --- PATH BUILDER UI ---
        st.write("###### Output Destination")
        
        # 1. Setup Keys & Defaults
        folder_key = f"exp_{selected_exporter_name}_folder"
        filename_key = f"exp_{selected_exporter_name}_filename"
        
        # Default Folder
        dataset_meta = engine.get_dataset_metadata(dataset_name)
        source_path = dataset_meta.get("source_path")
        default_folder = os.getcwd()
        if source_path:
            if os.path.isfile(source_path):
                default_folder = os.path.dirname(source_path)
            else:
                default_folder = source_path
        
        # Init Folder State
        if folder_key not in st.session_state:
            st.session_state[folder_key] = default_folder
            
        # Default Filename
        default_filename = f"export_{dataset_name}"
        # Init Filename State
        if filename_key not in st.session_state:
            st.session_state[filename_key] = default_filename

        # 2. Render UI
        
        # Folder Picker
        c1, c2 = st.columns([0.85, 0.15])
        folder_path = c1.text_input("Destination Folder", key=folder_key)
        
        def on_pick_folder(key):
            picked = pick_folder(title="Select Output Folder")
            if picked:
                st.session_state[key] = picked
        
        c2.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True) # Spacer alignment
        c2.button("📂", key=f"btn_browse_{selected_exporter_name}", 
                 on_click=on_pick_folder, args=(folder_key,), help="Pick Folder", width="stretch")
        
        # CHECKBOX: Export Individual (Prominent Placement)
        exp_ind = False
        meta = engine.get_dataset_metadata(dataset_name)
        if meta and meta.get("process_individual") and meta.get("input_type") == "folder":
             exp_ind = st.checkbox(
                 "📂 Export as Separate Files", 
                 value=False,
                 help="Apply recipe to each source file individually.",
                 key=f"exp_{selected_exporter_name}_individual"
             )
             if exp_ind:
                 st.info("Each source file will be exported with the prefix defined below.")
        
        # Filename Input
        fname_label = "Filename Prefix" if exp_ind else "Filename"
        filename_val = st.text_input(fname_label, key=filename_key)

        # Format Extension Logic
        ext = ".parquet" if selected_exporter_name == "Parquet" else f".{selected_exporter_name.lower()}"
        if selected_exporter_name == "Arrow IPC": ext = ".arrow"
        if selected_exporter_name == "Excel": ext = ".xlsx"
        
        # Preview
        if exp_ind:
             full_path = os.path.join(folder_path, f"{filename_val}_*{ext}")
             st.caption(f"📝 **Target Pattern:** `{full_path}`")
             # Real path for backend (backend handles splitting)
             full_path_backend = os.path.join(folder_path, f"{filename_val}{ext}")
        else:
             full_path = os.path.join(folder_path, f"{filename_val}{ext}")
             full_path_backend = full_path
             st.caption(f"📝 **Target:** `{full_path}`")
        
        st.divider()

        # Use Shared UI Renderer for REST of params
        params = render_schema_fields(
            ui_schema,
            key_prefix=f"exp_{selected_exporter_name}",
            columns=2
        )
        
        # Injection
        params["path"] = full_path_backend
        if exp_ind:
            params["export_individual"] = True

        if st.button("Export Start", type="primary", key=f"btn_start_exp_{selected_exporter_name}"):
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
                        if dur <= 0.001:
                            dur = elapsed

                        size = getattr(job_info, 'size_str', "Unknown")
                        
                        # SUCCESS MESSAGE
                        status_placeholder.success(
                            f"✅ Export Complete! Time: {dur:.2f}s | Total Size: {size}")
                        
                        # DETAILED FILE LIST
                        details = getattr(job_info, 'file_details', None)
                        if details:
                            with st.expander("📄 Exported Files Details", expanded=True):
                                # Convert to DataFrame for pretty display
                                df_details = pd.DataFrame(details)
                                if not df_details.empty:
                                    # Select and Rename cols
                                    df_display = df_details[['name', 'size', 'path']]
                                    df_display.columns = ['Filename', 'Size', 'Full Path']
                                    st.dataframe(df_display, width="stretch", hide_index=True)
                        break
                    elif status == "FAILED":
                        err_msg = getattr(
                            job_info, 'error', "Unknown Error")
                        status_placeholder.error(
                            f"❌ Failed: {err_msg}")
                        break
                    else:
                        time.sleep(0.1)
