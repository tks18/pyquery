import streamlit as st
import sys
import os
import mimetypes
from pyquery_polars.frontend.utils.styles import inject_custom_css
from pyquery_polars.frontend.registry_init import register_frontend
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.components.export import render_export_section
from pyquery_polars.frontend.components.profile import render_profile_tab
from pyquery_polars.frontend.components.recipe_editor import render_recipe_editor
from pyquery_polars.frontend.components.eda import render_eda_tab
from pyquery_polars.frontend.components.sql_tab import render_sql_tab
from pyquery_polars.frontend.components.sidebar import render_sidebar
from pyquery_polars.frontend.state_manager import init_session_state

# Fix MIME types on Windows to prevent 403/Content-Type errors with custom components
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ==========================================
# 0. ENGINE INITIALIZATION
# ==========================================


@st.cache_resource
def get_engine() -> PyQueryEngine:
    # Backend auto-registers its own logic
    return PyQueryEngine()


# Initialize Engine in Session State (Reference)
st.session_state.engine = get_engine()

# --- FRONTEND REGISTRY INIT ---
register_frontend()

init_session_state()

# AUTO CLEANUP (Once per session)
if "cleanup_done" not in st.session_state:
    st.session_state.engine.cleanup_staging(24)
    st.session_state["cleanup_done"] = True

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="Shan's PyQuery | Enterprise ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
inject_custom_css()


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

    t1, t2, t3, t4 = st.tabs(
        ["🍴 Recipe & Preview", "📊 EDA", "🧑‍💻 SQL Lab", "💳 Profiling"])

    with t1:
        render_recipe_editor(active_dataset_name)
        render_export_section(active_dataset_name)

    with t2:
        render_eda_tab(active_dataset_name)

    with t3:
        render_sql_tab()

    with t4:
        render_profile_tab(active_dataset_name)

else:
    st.info("👈 Please load a dataset from the sidebar to begin.")
