from typing import List, Optional

import streamlit as st
import pandas as pd
import polars as pl
from dataclasses import dataclass

from pyquery_polars.backend import PyQueryEngine


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
    """Encapsulates the state required for EDA components."""
    lf: pl.LazyFrame
    engine: PyQueryEngine
    all_cols: List[str]
    num_cols: List[str]
    cat_cols: List[str]
    date_cols: List[str]
    fingerprint: str  # Unique ID for caching (e.g., "dataset_v1_limit_5000")
    df: Optional[pd.DataFrame] = None  # Cached sample if needed
    theme: str = "plotly"
    show_labels: bool = False

    def get_pandas(self) -> pd.DataFrame:
        """
        Return the cached pandas DataFrame or collect from LazyFrame.
        Uses Streamlit cache_data to persist across reruns.
        """
        if self.df is None:
            # Collect and cache using the fingerprint
            # We prefix fingerprint to ensure uniqueness per session/user if needed,
            # though in single-user strict separation is less critical, but good practice.
            self.df = _cached_collect(self.fingerprint, self.lf)
        return self.df
