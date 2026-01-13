import streamlit as st
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.components.loaders.utils import handle_auto_inference


@st.dialog("API Import", width="large")
def show_api_loader(engine: PyQueryEngine):
    st.caption("Import JSON/Data from REST API")
    url = st.text_input("API Endpoint URL", key="dlg_api_url")
    alias_val = st.text_input(
        "Dataset Alias", value=f"api_data_{len(st.session_state.all_recipes) + 1}", key="dlg_api_alias")
    auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False, key="dlg_api_infer")

    # State for visibility
    if "show_loader_api" not in st.session_state:
        st.session_state.show_loader_api = False

    c_cancel, c_submit = st.columns([0.3, 0.7])
    
    if c_cancel.button("Cancel", key=f"dlg_btn_api_cancel"):
        st.session_state.show_loader_api = False
        st.rerun()

    if c_submit.button("Fetch Data", type="primary", width="stretch"):
        params = {"url": url, "alias": alias_val}
        with st.spinner("Fetching data..."):
            res = engine.run_loader("API", params)
            if res:
                lf_or_lfs, meta = res
                engine.add_dataset(alias_val, lf_or_lfs, meta)
                st.session_state.all_recipes[alias_val] = []
                st.session_state.active_base_dataset = alias_val
                st.session_state.recipe_steps = []

                if auto_infer:
                    handle_auto_inference(engine, alias_val)

                st.session_state.show_loader_api = False
                st.rerun()
            else:
                st.error("API Load Failed.")
