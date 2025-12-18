import streamlit as st
from src.state_manager import init_session_state
from src.components.sidebar import render_sidebar
from src.components.recipe_editor import render_recipe_editor
from src.components.profile import render_profile_tab
from src.components.export import render_export_section

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="Shan's PyQuery | Enterprise ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()

# ==========================================
# 2. SIDEBAR (PROJECT MANAGER)
# ==========================================
render_sidebar()

# ==========================================
# 3. MAIN PIPELINE
# ==========================================

if not st.session_state.datasets:
    st.info("👈 Start by importing a dataset in the 'Project Datasets' sidebar.")
    st.stop()

dataset_names = list(st.session_state.datasets.keys())
index_base = 0
if st.session_state.active_base_dataset in dataset_names:
    index_base = dataset_names.index(st.session_state.active_base_dataset)

selected_base = st.selectbox(
    "Pipeline Source (Base Dataset)", dataset_names, index=index_base)
st.session_state.active_base_dataset = selected_base
current_lf = st.session_state.datasets[selected_base]

# ----------------------------------------------------
# TAB LAYOUT: RECIPE EDITOR VS DATA PROFILE
# ----------------------------------------------------
tab_recipe, tab_profile = st.tabs(["🛠️ Recipe Editor", "🔍 Data Profile"])

with tab_recipe:
    # Render recipe steps and apply transformations
    # This renders the "Live Preview" as well inside the editor component
    current_lf = render_recipe_editor(current_lf)
    
    # Export Section
    render_export_section(current_lf)

with tab_profile:
    render_profile_tab(current_lf)
