"""
EDA Contrast Tab - Comparative analysis between cohorts.

This module provides statistical comparison tools for analyzing differences
between two groups including hypothesis testing and effect sizes.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from pyquery_polars.frontend.components.eda.core import BaseEDATab


class ContrastTab(BaseEDATab):
    """
    Contrast tab for comparative cohort analysis.

    Displays:
    - Group selection controls
    - Statistical settings
    - Volcano plot (effect size vs significance)
    - Feature raincloud visualization
    """

    TAB_NAME = "Contrast"
    TAB_ICON = "⚖️"

    def render(self) -> None:
        """Render the Contrast tab content."""
        st.caption(
            "Rigorous statistical comparison of two cohorts (Hypothesis Testing & Effect Sizes).")

        df = self.get_data()

        # Get control panel selections
        result = self._render_control_panel(df)
        if result is None:
            return

        group_col, val_a, val_b = result

        if val_a == val_b:
            st.error("Select different groups.")
            return

        # Get settings and run comparison
        p_threshold, use_mw = self._render_settings()
        stats = self._run_comparison(
            df, group_col, val_a, val_b, p_threshold, use_mw)

        if stats is not None:
            self._render_results(df, stats, group_col,
                                 val_a, val_b, p_threshold, use_mw)

    def _render_control_panel(self, df: pd.DataFrame):
        """Render the group selection control panel."""
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)

            valid_groups = [
                c for c in self.ctx.cat_cols if df[c].nunique() < 30]
            if not valid_groups:
                st.warning("No suitable grouping columns (<30 unique).")
                return None

            group_col = c1.selectbox("Split By", valid_groups, key="ct_grp")
            uniques = sorted(df[group_col].dropna().unique().tolist())

            if len(uniques) < 2:
                st.warning("Group has <2 values.")
                return None

            val_a = c2.selectbox("Group A", uniques, index=0, key="ct_a")
            val_b = c3.selectbox("Group B", uniques,
                                 index=1 if len(uniques) > 1 else 0, key="ct_b")

        return group_col, val_a, val_b

    def _render_settings(self):
        """Render statistical settings expander."""
        with st.expander("⚙️ Statistical Settings"):
            p_threshold = st.slider(
                "Significance Threshold (P-Value)", 0.01, 0.10, 0.05, 0.01)
            test_type = st.radio("Numeric Test Type",
                                 ["Mann-Whitney U (Non-Parametric)",
                                  "T-Test (Parametric)"],
                                 horizontal=True)
            use_mw = "Mann" in test_type

        return p_threshold, use_mw

    def _run_comparison(self, df: pd.DataFrame, group_col: str,
                        val_a, val_b, p_threshold: float, use_mw: bool):
        """Run the comparison and cache results."""
        session_key = "contrast_stats"
        param_key = "contrast_params"

        current_params = {
            "group_col": group_col, "val_a": val_a, "val_b": val_b,
            "use_mw": use_mw, "p_threshold": p_threshold,
            "df_hash": str(df.shape)
        }

        run_clicked = st.button("⚖️ Run Comparison", type="primary")
        stats = None

        if run_clicked:
            with st.spinner("Calculating Hypothesis Tests..."):
                stats = self.engine.analytics.stats.get_comparative_stats(
                    df, group_col, val_a, val_b, self.ctx.num_cols, self.ctx.cat_cols
                )
                self.state.set_value(session_key, stats)
                self.state.set_value(param_key, current_params)

        elif self.state.has_value(session_key) and self.state.get_value(param_key) == current_params:
            stats = self.state.get_value(session_key)

        return stats

    def _render_results(self, df: pd.DataFrame, stats: pd.DataFrame,
                        group_col: str, val_a, val_b, p_threshold: float, use_mw: bool) -> None:
        """Render comparison results."""
        if stats.empty:
            st.warning("No results.")
            return

        p_col = "P_Value_MW" if use_mw else "P_Value_TT"

        # Create significance flags
        stats['Significant'] = stats[p_col] < p_threshold
        stats['LogP'] = -np.log10(stats[p_col].replace(0, 1e-10))

        # Volcano Plot
        self._render_volcano_plot(stats, val_a, val_b, p_threshold, p_col)

        st.divider()

        # Raincloud/Detail view
        self._render_feature_detail(df, stats, group_col, val_a, val_b, p_col)

        # Results table
        st.dataframe(
            stats[['Feature', 'Type', 'Effect_Size', p_col, 'Desc', 'Significant']])

    def _render_volcano_plot(self, stats: pd.DataFrame, val_a, val_b,
                             p_threshold: float, p_col: str) -> None:
        """Render the volcano plot visualization."""
        st.subheader("🌋 Volcano Plot: Impact vs. Reliability")
        st.caption(
            f"Visualizing Effect Size (Magnitude) vs Significance (Statistical Confidence). Threshold P < {p_threshold}")

        # Color points by significance and effect size
        stats['Color'] = 'Insignificant'
        stats.loc[(stats['Significant']) & (
            stats['Effect_Size'] > 0.2), 'Color'] = 'Significant'
        stats.loc[(stats['Significant']) & (
            stats['Effect_Size'] > 0.5), 'Color'] = 'High Impact'

        fig_vol = px.scatter(stats, x="Effect_Size", y="LogP", color="Color",
                             hover_data=["Feature", "Desc", p_col],
                             text="Feature",
                             title=f"Volcano Plot ({val_a} vs {val_b})",
                             labels={
                                 "LogP": "-Log10(P-Value)",
                                 "Effect_Size": "Effect Size (Cohen's D / Cramer's V)"
                             },
                             template=self.ctx.theme,
                             color_discrete_map={
                                 'Insignificant': 'gray',
                                 'Significant': 'orange',
                                 'High Impact': 'red'
                             })
        fig_vol.add_hline(y=-np.log10(p_threshold), line_dash="dash",
                          line_color="green", annotation_text=f"P={p_threshold}")
        fig_vol.update_traces(textposition='top center')
        st.plotly_chart(fig_vol)

    def _render_feature_detail(self, df: pd.DataFrame, stats: pd.DataFrame,
                               group_col: str, val_a, val_b, p_col: str) -> None:
        """Render detailed feature inspection (raincloud plot)."""
        st.subheader("🌧️ Feature Raincloud")

        sig_feats = stats[stats['Significant']]['Feature'].tolist()
        opts = sig_feats if sig_feats else stats['Feature'].tolist()

        feat_insp = st.selectbox("Inspect Feature Detail", opts, key="ct_insp")

        if feat_insp:
            row = stats[stats['Feature'] == feat_insp].iloc[0]
            is_num = row['Type'] == 'Numeric'

            # Metrics header
            m1, m2, m3 = st.columns(3)
            m1.metric("Effect Size", f"{row['Effect_Size']:.3f}")
            m2.metric("P-Value", f"{row[p_col]:.2e}",
                      delta="Significant" if row['Significant'] else "Not Sig")
            m3.metric("Difference", row['Desc'])

            # Visualization
            sub_df = df[df[group_col].isin([val_a, val_b])]

            if is_num:
                fig_rain = px.violin(sub_df, x=group_col, y=feat_insp, color=group_col,
                                     box=True, points="all",
                                     title=f"Distribution: {feat_insp} by Cohort",
                                     template=self.ctx.theme)
                st.plotly_chart(fig_rain)
            else:
                ct = pd.crosstab(
                    sub_df[group_col], sub_df[feat_insp], normalize='index').reset_index()
                fig_bar = px.bar(ct, x=group_col, y=ct.columns[1:], barmode="stack",
                                 title=f"Proportions: {feat_insp}", template=self.ctx.theme)
                st.plotly_chart(fig_bar)
