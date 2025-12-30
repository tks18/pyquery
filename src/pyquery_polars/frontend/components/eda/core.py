import streamlit as st
import pandas as pd
import polars as pl
from dataclasses import dataclass
from typing import List, Optional
from pyquery_polars.backend.engine import PyQueryEngine

@dataclass
class EDAContext:
    """Encapsulates the state required for EDA components."""
    lf: pl.LazyFrame
    engine: PyQueryEngine
    all_cols: List[str]
    num_cols: List[str]
    cat_cols: List[str]
    date_cols: List[str]
    df: Optional[pd.DataFrame] = None # Cached sample if needed
    theme: str = "plotly"
    show_labels: bool = False