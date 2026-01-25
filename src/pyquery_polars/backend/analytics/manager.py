"""
AnalyticsManager

This Module provides unified access to:
- Statistical analysis (StatsEngine)
- Machine Learning operations (MLEngine)
- Type inference (TypeInferenceEngine)
- Join analysis (JoinAnalyzer)
"""
from typing import Any, Dict, List, Optional, Sequence

import polars as pl
import pandas as pd

from pyquery_polars.backend.analytics.stats import StatsEngine
from pyquery_polars.backend.analytics.ml import MLEngine
from pyquery_polars.backend.analytics.inference import TypeInferenceEngine
from pyquery_polars.backend.analytics.joins import JoinAnalyzer
from pyquery_polars.backend.processing import ProcessingManager


class AnalyticsManager:
    """
    Provide unified interface for all analytics.

    Dependencies:
    - ProcessingManager: To resolve data for analysis

    This is a facade that aggregates:
    - StatsEngine: Statistical analysis, correlations, distributions
    - MLEngine: Clustering, anomaly detection, predictive models
    - TypeInferenceEngine: Data type inference
    - JoinAnalyzer: Join overlap analysis
    """

    def __init__(self, processing_manager: Optional["ProcessingManager"] = None):
        """
        Initialize AnalyticsManager.

        Args:
           processing_manager: Optional reference for internal data resolution
        """
        self._processing = processing_manager
        self.stats = StatsEngine()
        self.ml = MLEngine()
        self.inference = TypeInferenceEngine
        self.joins = JoinAnalyzer

    # ========== Type Inference ==========

    def infer_types(
        self,
        base_lf: pl.LazyFrame,
        recipe: Sequence[Any],
        columns: Optional[List[str]] = None,
        sample_size: int = 1000,
        # Legacy/Optional args for compatibility or override
        datasets_dict: Optional[Dict[str, pl.LazyFrame]] = None,
        project_recipes: Optional[Dict[str, List[Any]]] = None
    ) -> Dict[str, str]:
        """
        Infer data types for specific columns based on a sample of the transformed data.
        Delegates to TypeInferenceEngine.
        """
        # Resolving dependencies locally if not provided
        if datasets_dict is None and self._processing:
            datasets_dict = self._processing._get_context()

        if project_recipes is None and self._processing:
            project_recipes = self._processing._get_project_recipes()

        return TypeInferenceEngine.infer_types(
            base_lf=base_lf,
            recipe=recipe,
            datasets_dict=datasets_dict or {},
            project_recipes=project_recipes,
            columns=columns,
            sample_size=sample_size
        )

    # ========== Join Analysis ==========

    def analyze_join_overlap(
        self,
        left_df: pl.DataFrame,
        right_df: pl.DataFrame,
        left_on: List[str],
        right_on: List[str]
    ) -> Dict[str, Any]:
        """Analyze join overlap between two DataFrames."""
        return JoinAnalyzer.analyze_overlap(left_df, right_df, left_on, right_on)

    # ========== Statistical Analysis Shortcuts ==========

    def get_correlations(
        self,
        df: pd.DataFrame,
        num_cols: List[str],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Analyze correlations in numeric columns."""
        return self.stats.analyze_correlations(df, num_cols, threshold)

    def get_distribution_stats(self, df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Get distribution statistics for a column."""
        return self.stats.get_distribution_stats(df, col)

    def get_dataset_health(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute dataset health metadata."""
        return self.stats.get_dataset_health(df)

    def get_feature_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate a summary dataframe for all columns."""
        return self.stats.get_feature_summary(df)

    # ========== ML Shortcuts ==========

    def cluster_data(
        self,
        df: pd.DataFrame,
        features: List[str],
        n_clusters: int = 3,
        algo: str = "K-Means",
        optimize_k: bool = False
    ) -> Dict[str, Any]:
        """Run clustering on data."""
        return self.ml.cluster_data(df, features, n_clusters, algo, optimize_k)

    def detect_anomalies(
        self,
        df: pd.DataFrame,
        features: List[str],
        contamination: float = 0.05
    ) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest."""
        return self.ml.detect_anomalies(df, features, contamination)
