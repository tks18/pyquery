import streamlit as st
from src.frontend.state_manager import init_session_state
from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.recipe_editor import render_recipe_editor
from src.frontend.components.profile import render_profile_tab
from src.frontend.components.export import render_export_section

from src.backend.engine import PyQueryEngine

# ==========================================
# 0. ENGINE INITIALIZATION
# ==========================================
@st.cache_resource
def get_engine():
    # Backend auto-registers its own logic
    return PyQueryEngine()

# Initialize Engine in Session State (Reference)
st.session_state.engine = get_engine()

init_session_state()

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="Shan's PyQuery | Enterprise ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# 2. SIDEBAR (PROJECT MANAGER)
# ==========================================
render_sidebar()

# ==========================================
# 3. MAIN AREA
# ==========================================
st.title("🛠️ Transformation Recipe")

active_dataset_name = st.session_state.active_base_dataset

if active_dataset_name:
    st.caption(f"Active Dataset: **{active_dataset_name}**")
    
    t1, t2 = st.tabs(["Recipe & Preview", "Profiling"])
    
    with t1:
        # Pass NAME, not LF
        render_recipe_editor(active_dataset_name)
        render_export_section(active_dataset_name)
        
    with t2:
        render_profile_tab(active_dataset_name)

else:
    st.info("👈 Please load a dataset from the sidebar to begin.")
