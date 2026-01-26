"""
EDA Profiling Tab - Deep data inspection and column analysis.

This module provides detailed column profiling including distributions,
correlations, and semantic type detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from pyquery_polars.frontend.components.eda.core import BaseEDATab


class ProfilingTab(BaseEDATab):
    """
    Profiling tab for deep column inspection.

    Displays:
    - Dataset health scan (quick summary)
    - Column selection and analysis
    - Summary statistics
    - Distribution visualizations
    - Correlation analysis
    - Semantic entity detection
    """

    TAB_NAME = "Profiling"
    TAB_ICON = "🔬"

    def render(self) -> None:
        """Render the Profiling tab content."""
        st.caption(
            "Deep inspection of column distributions, correlations, and semantic types.")

        df = self.get_data()
        if df is None:
            return

        # Health scan
        self._render_health_scan(df)

        # Column selection and analysis
        col, stats = self._render_column_selection(df)

        if stats and col:
            self._render_analysis_tabs(df, col, stats)

    def _render_health_scan(self, df: pd.DataFrame) -> None:
        """Render the quick dataset health scan."""
        with st.expander("⚡ Dataset Health Scan", expanded=True):
            n_rows = len(df)
            summary_data = []
            for c in df.columns:
                missing = df[c].isna().sum()
                summary_data.append({
                    "Column": c,
                    "Type": str(df[c].dtype),
                    "Missing %": f"{missing/n_rows:.1%}",
                    "Unique": df[c].nunique()
                })
            st.dataframe(pd.DataFrame(summary_data), hide_index=True)

    def _render_column_selection(self, df: pd.DataFrame):
        """Render column type selection and run analysis."""
        col_type = st.radio("Column Type",
                            ["Numeric", "Categorical / Text"],
                            horizontal=True, key="prof_type")
        target_cols = self.ctx.num_cols if col_type == "Numeric" else self.ctx.cat_cols

        if not target_cols:
            st.info("No columns found.")
            return None, None

        c_sel, c_btn = st.columns([3, 1])
        col = c_sel.selectbox("Select Column to Analyze",
                              target_cols, key="prof_col_sel")

        # Persistence
        session_key = "prof_stats"
        param_key = "prof_params"
        current_params = {"col": col, "df_hash": str(df.shape)}

        run_clicked = c_btn.button("🔍 Analyze", type="primary")
        stats = None

        if run_clicked:
            with st.spinner(f"Profiling '{col}'..."):
                stats = self.engine.analytics.stats.get_advanced_profile(
                    df, col)
                if "error" in stats:
                    st.error(stats['error'])
                    return col, None
                self.state.set_value(session_key, stats)
                self.state.set_value(param_key, current_params)

        elif self.state.has_value(session_key) and self.state.get_value(param_key) == current_params:
            stats = self.state.get_value(session_key)

        return col, stats

    def _render_analysis_tabs(self, df: pd.DataFrame, col: str, stats: dict) -> None:
        """Render the analysis tabs with profiling results."""
        tab_sum, tab_dist, tab_corr, tab_sem = st.tabs([
            "📊 Summary", "📈 Distribution", "🔗 Correlations", "🧠 Semantics"
        ])

        with tab_sum:
            self._render_summary_tab(stats)

        with tab_dist:
            self._render_distribution_tab(df, col, stats)

        with tab_corr:
            self._render_correlations_tab(col, stats)

        with tab_sem:
            self._render_semantics_tab(stats)

    def _render_summary_tab(self, stats: dict) -> None:
        """Render summary statistics tab."""
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Count", f"{stats.get('count', 0):,}")
        c2.metric("Missing", f"{stats.get('missing_p', 0):.1%}")
        c3.metric("Unique", f"{stats.get('unique', 0):,}")
        c4.metric("Dtype", stats.get('dtype', 'N/A'))

        st.divider()

        if stats.get('type') == 'Numeric':
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("Mean", f"{stats.get('mean', 0):.2f}")
            cc2.metric("Median", f"{stats.get('median', 0):.2f}")
            cc3.metric("Skewness", f"{stats.get('skew', 0):.2f}")
            cc4.metric("Kurtosis", f"{stats.get('kurtosis', 0):.2f}")

            if abs(stats.get('skew', 0)) > 1:
                st.warning(
                    "⚠️ High Skewness detected. Consider log-transformation.")
        else:
            cc1, cc2 = st.columns(2)
            cc1.metric("Mode", str(stats.get('mode', 'N/A')))
            cc2.metric("Rare Values", stats.get('rare_count', 0))

    def _render_distribution_tab(self, df: pd.DataFrame, col: str, stats: dict) -> None:
        """Render distribution visualization tab."""
        if stats.get('type') == 'Numeric':
            fig_boxen = px.box(df, y=col, points="outliers", notched=True,
                               title=f"Distribution: {col} (Box Plot)",
                               template=self.ctx.theme)
            st.plotly_chart(fig_boxen)

            fig_hist = px.histogram(df, x=col, marginal="box", opacity=0.7,
                                    title="Histogram & Density",
                                    template=self.ctx.theme)
            st.plotly_chart(fig_hist)
        else:
            top_counts = stats.get('top_counts', {})
            if top_counts:
                tdf = pd.DataFrame(list(top_counts.items()),
                                   columns=["Category", "Count"])
                fig_tree = px.treemap(tdf, path=["Category"], values="Count",
                                      title=f"Top Categories in {col}",
                                      template=self.ctx.theme)
                st.plotly_chart(fig_tree)

                st.caption("Top 10 Values Table")
                st.dataframe(tdf, hide_index=True)

    def _render_correlations_tab(self, col: str, stats: dict) -> None:
        """Render correlations analysis tab."""
        if stats.get('type') == 'Numeric':
            corrs = stats.get('correlations', {})
            if corrs:
                cdf = pd.DataFrame(list(corrs.items()),
                                   columns=["Feature", "Correlation"])
                fig_corr = px.bar(cdf, x="Correlation", y="Feature", orientation='h',
                                  title=f"Top Correlated Features with {col}",
                                  template=self.ctx.theme,
                                  color="Correlation", range_x=[-1, 1],
                                  color_continuous_scale="RdBu")
                st.plotly_chart(fig_corr)
            else:
                st.info(
                    "No significant numeric correlations found or only one numeric column exists.")
        else:
            st.info("Correlation analysis is strictly for numeric relationships here. "
                    "Check 'Relationships' tab for categorical association (Cramer's V).")

    def _render_semantics_tab(self, stats: dict) -> None:
        """Render semantic entity detection tab."""
        if stats.get('type') == 'Categorical':
            patterns = stats.get('semantic_entities', {})
            if patterns:
                st.success("💡 Detected semantic entities in this column!")
                pdf = pd.DataFrame(list(patterns.items()),
                                   columns=["Entity Type", "Matches"])
                fig_sem = px.pie(pdf, names="Entity Type", values="Matches", hole=0.4,
                                 title="Detected Entity Types", template=self.ctx.theme)
                st.plotly_chart(fig_sem)
            else:
                st.info(
                    "No specific semantic entities (Email, IP, Date, etc.) detected via regex.")

            st.write("###### String Length Stats")
            c_l1, c_l2, c_l3 = st.columns(3)
            c_l1.metric("Min Len", stats.get('len_min', 0))
            c_l2.metric("Max Len", stats.get('len_max', 0))
            c_l3.metric("Avg Len", f"{stats.get('len_avg', 0):.1f}")
        else:
            st.info("Semantic analysis is for Text/Categorical columns.")
