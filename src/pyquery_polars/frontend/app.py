"""
PyQuery Frontend - Main Application Entry Point

This is the Streamlit application entry point. It initializes the AppContext
and renders all UI components.
"""

import streamlit as st
import sys
import os
import mimetypes

from pyquery_polars.frontend.utils.styles import inject_custom_css
from pyquery_polars.frontend.transforms import register_frontend
from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.frontend.base import AppContext

from pyquery_polars.frontend.components import (
    ExportComponent, ProfileComponent, RecipeEditorComponent, SQLTabComponent, SidebarComponent, EDAComponent
)

# Fix MIME types on Windows to prevent 403/Content-Type errors with custom components
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ==========================================
# 0. CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="Shan's PyQuery | Enterprise ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. ENGINE & CONTEXT INITIALIZATION
# ==========================================


@st.cache_resource
def get_engine() -> PyQueryEngine:
    """Get or create the PyQueryEngine singleton."""
    return PyQueryEngine()


def get_app_context() -> AppContext:
    """
    Get or create AppContext for current session.

    The AppContext is stored in session_state and contains:
    - engine: PyQueryEngine instance
    - state_manager: StateManager instance

    Returns:
        The application context
    """
    if "app_context" not in st.session_state:
        engine = get_engine()
        st.session_state.app_context = AppContext.create(engine)
    return st.session_state.app_context


# Initialize context
ctx = get_app_context()

# Register frontend renderers
register_frontend()

# Sync state from backend
ctx.state_manager.sync_all_from_backend()

# Auto cleanup (once per session)
if not ctx.state_manager.cleanup_done:
    ctx.engine.io.cleanup_staging(24)
    ctx.state_manager.cleanup_done = True


# Inject custom CSS
inject_custom_css()


# ==========================================
# 2. SIDEBAR (PROJECT MANAGER)
# ==========================================
SidebarComponent(ctx).render()


# ==========================================
# 3. MAIN AREA
# ==========================================
st.title("🛠️ Transformation Recipe")

active_dataset_name = ctx.state_manager.active_dataset

if active_dataset_name:
    st.caption(f"Active Dataset: **{active_dataset_name}**")

    t1, t2, t3, t4 = st.tabs(
        ["🍴 Recipe & Preview", "📊 EDA", "🧑‍💻 SQL Lab", "💳 Profiling"]
    )

    with t1:
        RecipeEditorComponent(ctx).render(active_dataset_name)
        ExportComponent(ctx).render(active_dataset_name)

    with t2:
        EDAComponent(ctx).render(active_dataset_name)

    with t3:
        SQLTabComponent(ctx).render()

    with t4:
        ProfileComponent(ctx).render(active_dataset_name)

else:
    st.info("👈 Please load a dataset from the sidebar to begin.")
