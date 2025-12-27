import streamlit as st
from typing import cast
import copy
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.utils.dynamic_ui import render_schema_fields
from pyquery_polars.frontend.utils.io_schemas import get_exporter_schema
import time
import os
from pyquery_polars.frontend.utils.file_picker import pick_folder

def render_sql_tab():
    st.subheader("SQL Editor")

    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        st.error("Engine not initialized.")
        return

    # 1. Available Tables
    with st.expander("📚 Available Tables"):
        tables = engine.get_dataset_names()
        if tables:
            st.markdown(", ".join([f"`{t}`" for t in tables]))
        else:
            st.warning("No datasets loaded.")

    # 2. Query Editor
    default_query = "SELECT * FROM " + (tables[0] if tables else "table_name") + " LIMIT 10"
    
    if "sql_query" not in st.session_state:
        st.session_state.sql_query = default_query
        
    if 'sql_history' not in st.session_state:
        st.session_state.sql_history = []
        
    # History Selectbox (Always Visible)
    def on_hist_change():
        val = st.session_state.get("hist_picker")
        if val and val != "Recall recent query...":
            st.session_state.sql_query = val
    
    # Use columns to position it nicely
    st.write("###### Write Query")
    st.selectbox(
        "Recent Queries", 
        ["Recall recent query..."] + st.session_state.sql_history, 
        key="hist_picker", 
        label_visibility="collapsed", 
        on_change=on_hist_change,
        placeholder="Recall recent query..."
    )

    # Standard Text Area
    st.info("💡 Tip: You can write standard SQL queries here.")
    st.text_area(
        "SQL Query", 
        height=200, 
        key="sql_query",
        help="Write your SQL query statement here.",
        label_visibility="collapsed"
    )

    col_run, col_clear = st.columns([1, 6])
    if col_run.button("▶ Run Query", type="primary"):
        st.session_state.sql_run_trigger = True
        # Save History
        q = st.session_state.sql_query
        if q and q.strip():
            hist = st.session_state.sql_history
            if q in hist:
                hist.remove(q)
            hist.insert(0, q)
            if len(hist) > 10:
                hist.pop()
    
    # 3. Preview & Results
    if st.session_state.get("sql_run_trigger"):
        try:
            with st.spinner("Executing SQL (Preview)..."):
                # Use optimized preview (Eager DF) with Context
                preview_df = engine.execute_sql_preview(
                    st.session_state.sql_query, 
                    limit=1000,
                    project_recipes=st.session_state.get('all_recipes')
                )
                
                st.warning("⚠️ **Preview Mode**: Results based on top 1,000 rows only. Export uses full dataset.")
                
                st.dataframe(preview_df, width="stretch")
                st.caption(f"Shape: {preview_df.shape}")
        except Exception as e:
            st.error(f"SQL Error: {e}")

    st.divider()

    # 4. Export SQL Results
    st.subheader("📤 Export SQL Results")
    
    with st.expander("Export Options", expanded=False):
        exporters = engine.get_exporters()
        if not exporters:
            st.warning("No exporters available.")
            return

        exporter_map = {e.name: e for e in exporters}
        selected_exporter_name = st.selectbox(
            "Format", list(exporter_map.keys()), key="sql_export_format")
        selected_exporter = exporter_map[selected_exporter_name]

        # Decoupled Schema Lookup
        base_schema = get_exporter_schema(selected_exporter.name)
        # Filter out 'path' from auto-renderer
        ui_schema = [f for f in base_schema if f.name != "path"]

        # --- PATH BUILDER UI ---
        st.write("###### Output Destination")
        
        # 1. Setup Keys & Defaults
        folder_key = f"sql_exp_{selected_exporter_name}_folder"
        filename_key = f"sql_exp_{selected_exporter_name}_filename"
        
        # Default Folder
        dataset_meta = engine.get_dataset_metadata(tables[0])
        source_path = dataset_meta.get("source_path")
        default_folder = os.path.join(os.getcwd(), "exports")
        
        if source_path and isinstance(source_path, str):
            if os.path.isfile(source_path):
                default_folder = os.path.dirname(source_path)
            else:
                default_folder = source_path
        
        # Ensure Exists (if defaulting to local exports)
        if default_folder.endswith("exports") and not os.path.exists(default_folder):
             try:
                 os.makedirs(default_folder, exist_ok=True)
             except:
                 pass
        
        # Init Folder State
        if folder_key not in st.session_state:
            st.session_state[folder_key] = default_folder
            
        # Default Filename
        default_filename = f"sql_export_{int(time.time())}"
        # Init Filename State
        if filename_key not in st.session_state:
            st.session_state[filename_key] = default_filename

        # 2. Render UI
        
        # Folder Picker
        c1, c2 = st.columns([0.85, 0.15])
        folder_path = c1.text_input("Destination Folder", key=folder_key)
        
        def on_pick_sql_folder(key):
            picked = pick_folder(title="Select SQL Export Folder")
            if picked:
                st.session_state[key] = picked
        
        c2.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True) 
        c2.button("📂", key=f"btn_browse_sql_{selected_exporter_name}", 
                 on_click=on_pick_sql_folder, args=(folder_key,), help="Pick Folder", width="stretch")
        
        # Filename Input
        filename_val = st.text_input("Filename", key=filename_key)

        # Format Extension Logic
        ext = ".parquet" if selected_exporter_name == "Parquet" else f".{selected_exporter_name.lower()}"
        if selected_exporter_name == "Arrow IPC": ext = ".arrow"
        if selected_exporter_name == "Excel": ext = ".xlsx"
        
        # Preview
        full_path = os.path.join(folder_path, f"{filename_val}{ext}")
        st.caption(f"📝 **Target:** `{full_path}`")
        
        st.divider()

        # Use Shared UI Renderer
        params = render_schema_fields(
            ui_schema,
            key_prefix=f"sql_exp_{selected_exporter_name}",
            columns=2
        )
        
        # Injection
        params["path"] = full_path

        if st.button("Export SQL Result", type="primary"):
             # ... submit logic ...
                final_params = params
                if selected_exporter.params_model:
                     try:
                        final_params = selected_exporter.params_model.model_validate(params)
                     except Exception as e:
                        st.error(f"Invalid Params: {e}")
                        st.stop()
                
                # Start Job
                try:
                    job_id = engine.start_sql_export_job(st.session_state.sql_query, selected_exporter_name, final_params)
                    
                    # Polling UI (Duplicated logic, could be refactored but safe for now)
                    status_placeholder = st.empty()
                    start_ts = time.time()

                    with st.spinner(f"Exporting SQL Result..."):
                        while True:
                            elapsed = time.time() - start_ts
                            status_placeholder.info(f"⏳ Exporting... ({elapsed:.2f}s)")
                            
                            job_info = engine.get_job_status(job_id)
                            if not job_info:
                                time.sleep(0.5)
                                continue
                            
                            if job_info.status == "COMPLETED":
                                size = getattr(job_info, 'size_str', "Unknown")
                                status_placeholder.success(f"✅ Export Complete! Time: {job_info.duration:.2f}s | Size: {size}")
                                break
                            elif job_info.status == "FAILED":
                                status_placeholder.error(f"❌ Failed: {getattr(job_info, 'error', 'Unknown')}")
                                break
                            else:
                                time.sleep(0.5)

                except Exception as e:
                    st.error(f"Failed to start export: {e}")
