import streamlit as st
from typing import Optional
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.components.loaders.utils import handle_auto_inference


@st.dialog("API Import", width="large")
def show_api_loader(engine: PyQueryEngine, edit_mode: bool = False, edit_dataset_name: Optional[str] = None):
    """
    API Loader Dialog.
    
    Args:
        engine: PyQueryEngine instance
        edit_mode: If True, pre-fill inputs from existing dataset metadata
        edit_dataset_name: Name of dataset to edit (required if edit_mode=True)
    """
    st.caption(f"{'Modify API endpoint settings' if edit_mode else 'Import JSON/Data from REST API'}")
    
    loader_name = "API"

    # State for visibility
    if "show_loader_api" not in st.session_state:
        st.session_state.show_loader_api = False

    # --- PRE-FILL LOGIC FOR EDIT MODE ---
    edit_init_key = f"dlg_{loader_name}_edit_initialized"
    if edit_mode and edit_dataset_name and not st.session_state.get(edit_init_key):
        meta = engine.get_dataset_metadata(edit_dataset_name)
        params = meta.get("loader_params", {}) or {}
        
        if params:
            st.session_state["dlg_api_url"] = params.get("url", "")
            st.session_state["dlg_api_alias"] = edit_dataset_name
            st.session_state["dlg_api_infer"] = params.get("auto_infer", False)
        
        st.session_state[edit_init_key] = True

    url = st.text_input("API Endpoint URL", key="dlg_api_url")
    alias_val = st.text_input(
        "Dataset Alias", value=f"api_data_{len(st.session_state.all_recipes) + 1}", key="dlg_api_alias")
    auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False, key="dlg_api_infer")

    c_cancel, c_submit = st.columns([0.3, 0.7])
    
    if c_cancel.button("Cancel", key=f"dlg_btn_api_cancel"):
        st.session_state.show_loader_api = False
        st.rerun()

    btn_label = "Update Dataset" if edit_mode else "Fetch Data"
    if c_submit.button(btn_label, type="primary", width="stretch"):
        params = {"url": url, "alias": alias_val, "auto_infer": auto_infer}
        
        with st.spinner("Fetching data..."):
            res = engine.run_loader("API", params)
            if res:
                lf_or_lfs, meta = res
                
                # Handle Edit Mode: Remove old dataset if exists
                if edit_mode and edit_dataset_name:
                    if alias_val != edit_dataset_name:
                        if edit_dataset_name in st.session_state.all_recipes:
                            st.session_state.all_recipes[alias_val] = st.session_state.all_recipes.pop(edit_dataset_name)
                        engine.remove_dataset(edit_dataset_name)
                    else:
                        engine.remove_dataset(alias_val)
                
                engine.add_dataset(alias_val, lf_or_lfs, meta,
                                   loader_type="API",
                                   loader_params=params)
                
                if alias_val not in st.session_state.all_recipes:
                    st.session_state.all_recipes[alias_val] = []
                    
                st.session_state.active_base_dataset = alias_val
                st.session_state.recipe_steps = []

                if auto_infer:
                    handle_auto_inference(engine, alias_val)

                st.session_state.show_loader_api = False
                st.rerun()
            else:
                st.error("API Load Failed.")
