import streamlit as st
import threading
import time
from src.utils.io import export_worker

def render_export_section(current_lf):
    st.divider()
    st.subheader("🚀 Export Data (Threaded)")
    
    # Move Format selector OUTSIDE the form so it triggers a re-run on change
    out_fmt = st.selectbox("Format", ["Parquet", "CSV", "Excel", "SQL"], key="export_fmt_global")

    with st.form("export_form"):
        c1, c2 = st.columns(2)
        
        # Dynamic inputs based on format
        out_path = ""
        comp = "" # acts as Compression OR Connection URI
        
        if out_fmt == "SQL":
            out_path = c1.text_input("Table Name", "output_table")
            comp = c2.text_input("DB Connection URI", "postgresql://...")
        else:
            out_path = c1.text_input("Output Path", f"output.{out_fmt.lower()}")
            if out_fmt == "Parquet":
                comp = c2.selectbox("Compression", ["zstd", "snappy", "gzip"])
            else:
                 c2.text("(No Options)")
        
        submitted = st.form_submit_button("Start Background Export")
        
    if submitted:
        if out_fmt == "Excel":
            st.warning("⚠️ Excel export requires RAM.")
        if out_fmt == "SQL" and (not out_path or not comp):
            st.error("Table Name and URI required for SQL export.")
        else:
            result_container = {}
            t = threading.Thread(target=export_worker, args=(
                current_lf, out_path, out_fmt, comp, result_container))
            t.start()
            with st.spinner(f"Exporting..."):
                while t.is_alive():
                    time.sleep(1)
            if result_container.get('status') == 'success':
                st.success(result_container['message'])
            else:
                st.error(f"Export Failed: {result_container.get('message')}")
