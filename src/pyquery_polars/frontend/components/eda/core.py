"""
EDA Core - Base classes and context for EDA components.

This module provides the foundational classes for the EDA (Exploratory Data Analysis)
module, including the EDAContext dataclass and BaseEDATab abstract class.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dataclasses import dataclass

import streamlit as st
import pandas as pd
import polars as pl

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.frontend.base.state import StateManager


@st.cache_data(show_spinner=False, max_entries=5)
def _cached_collect(fingerprint: str, _lf: pl.LazyFrame) -> pd.DataFrame:
    """
    Cache the expensive collection step.
    'fingerprint' is the cache key (dataset_name + query hash).
    '_lf' is ignored for hashing but used for computation.
    """
    return _lf.collect().to_pandas()


@dataclass
class EDAContext:
    """
    Encapsulates the state required for EDA components.

    This context is passed to all EDA tabs and provides:
    - Access to the data (LazyFrame and cached Pandas DataFrame)
    - Column classification (numeric, categorical, date)
    - Engine access for analytics
    - Theme and display settings

    Attributes:
        lf: The Polars LazyFrame for the dataset
        engine: PyQueryEngine instance for analytics
        all_cols: List of all column names
        num_cols: List of numeric column names
        cat_cols: List of categorical column names
        date_cols: List of date/datetime column names
        fingerprint: Unique ID for caching
        df: Cached pandas DataFrame (optional)
        theme: Plotly theme name
        show_labels: Whether to show labels on charts
    """
    lf: pl.LazyFrame
    engine: PyQueryEngine
    state_manager: 'StateManager'
    all_cols: List[str]
    num_cols: List[str]
    cat_cols: List[str]
    date_cols: List[str]
    fingerprint: str
    df: Optional[pd.DataFrame] = None
    theme: str = "plotly"
    show_labels: bool = False

    def get_pandas(self) -> pd.DataFrame:
        """
        Return the cached pandas DataFrame or collect from LazyFrame.
        Uses Streamlit cache_data to persist across reruns.
        """
        if self.df is None:
            self.df = _cached_collect(self.fingerprint, self.lf)
        return self.df


class BaseEDATab(ABC):
    """
    Abstract base class for EDA tab components.

    Each EDA tab (Overview, Plots, ML, etc.) should inherit from this class
    and implement the render() method to display the tab content.

    The tab receives an EDAContext containing all necessary data and settings.

    Example:
        class OverviewTab(BaseEDATab):
            def render(self):
                df = self.ctx.get_pandas()
                # Display overview visualizations
                ...
    """

    # Tab display name (override in subclasses)
    TAB_NAME: str = "Base"
    TAB_ICON: str = "📊"

    def __init__(self, ctx: EDAContext) -> None:
        """
        Initialize the EDA tab with context.

        Args:
            ctx: EDAContext with data and settings
        """
        self.ctx = ctx
        self.df: Optional[pd.DataFrame] = None

    @property
    def engine(self) -> PyQueryEngine:
        """Shortcut to access engine from context."""
        return self.ctx.engine

    @property
    def state(self) -> 'StateManager':
        """Shortcut to access state manager from context."""
        return self.ctx.state_manager

    def get_data(self) -> pd.DataFrame:
        """
        Get the pandas DataFrame, caching for this tab's use.

        Returns:
            Pandas DataFrame with collected data
        """
        if self.df is None:
            self.df = self.ctx.get_pandas()
        return self.df

    @abstractmethod
    def render(self) -> Any:
        """
        Render the tab content.

        This method is called when the tab is active and should
        display all visualizations and UI components for this tab.

        Returns:
            Implementation-specific return value (typically None)
        """
        pass

    def render_with_error_handling(self) -> None:
        """
        Render the tab with error handling wrapper.

        Catches exceptions and displays error messages in the UI.
        """
        try:
            self.render()
        except Exception as e:
            st.error(f"Error rendering {self.TAB_NAME} tab: {e}")
            if st.checkbox("Show details", key=f"err_details_{self.TAB_NAME}"):
                st.exception(e)
