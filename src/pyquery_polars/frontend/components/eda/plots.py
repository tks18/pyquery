"""
EDA Plots Tab - Advanced visualization and analysis.

This module provides the Plots tab for the EDA module, including
time series analysis, distributions, hierarchy/composition, and relationships.
"""

import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import calendar
from plotly.subplots import make_subplots

from pyquery_polars.frontend.components.eda.core import BaseEDATab


class PlotsTab(BaseEDATab):
    """
    Plots tab for EDA module.

    Displays:
    - Time Series Analysis (Trend, Decomposition, Forecast, Anomaly)
    - Distributions (Histograms, Box/Violin, ECDF, QQ)
    - Hierarchy (Sunburst, Treemap, Icicle, Concentration)
    - Relationships (Scatter, Matrix, 3D, Heatmap, Sankey, Parallel Coords)
    """

    TAB_NAME = "Plots"
    TAB_ICON = "📈"

    def render(self) -> None:
        """Render the Plots tab content."""
        # Main Navigation for Plots Tab
        with st.container(border=True):
            plot_mode = st.radio("Visualization Module", [
                "Time Series", "Distributions", "Hierarchy", "Relationships"
            ], horizontal=True, label_visibility="collapsed")

        if plot_mode == "Time Series":
            self.render_time_series()
        elif plot_mode == "Distributions":
            self.render_distributions()
        elif plot_mode == "Hierarchy":
            self.render_hierarchy()
        elif plot_mode == "Relationships":
            self.render_relationships()

    def render_time_series(self) -> None:
        """Render Time Series Tab (Advanced)"""
        if not self.ctx.date_cols:
            st.info("No DateTime columns found.")
            return

        # --- Controls ---
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            dt_col = c1.selectbox(
                "Time Axis", self.ctx.date_cols, key="ts_time")
            val_col = c2.selectbox("Value", self.ctx.num_cols, key="ts_val")
            freq = c3.selectbox("Granularity", ["Auto", "Daily (D)", "Weekly (W)",
                                "Monthly (M)", "Quarterly (Q)", "Yearly (Y)"], index=0, key="ts_freq")
            agg_func = c4.selectbox(
                "Aggregation", ["Sum", "Mean", "Max", "Min", "Count"], index=1, key="ts_agg")

        mode = st.radio("Analysis Mode",
                        ["📈 Trend Tracker", "🔍 Decomposition", "🔮 Future Forecast",
                            "🌡️ Heatmap View", "⚠️ Anomaly Detection"],
                        horizontal=True, key="ts_mode")

        if st.button("Run Time Series Analysis", type="primary"):
            self.state.eda_ts_run = True

        if self.state.eda_ts_run:
            if not val_col:
                return

            with st.spinner("Processing Time Series..."):
                try:
                    df_all = self.get_data()
                    if df_all is None:
                        return

                    # Pandas Resample Logic
                    df_ts = df_all.copy()
                    df_ts[dt_col] = pd.to_datetime(df_ts[dt_col])

                    p_freq_map = {
                        "Auto": "ME", "Daily (D)": "D", "Weekly (W)": "W",
                        "Monthly (M)": "ME", "Quarterly (Q)": "QE", "Yearly (Y)": "YE"
                    }
                    p_freq = p_freq_map.get(str(freq), "D")

                    df_ts = df_ts.set_index(dt_col).resample(
                        p_freq)[val_col].agg(agg_func.lower())
                    df_ts = df_ts.reset_index().rename(
                        columns={dt_col: 'ts_date', val_col: val_col})

                    if df_ts.empty:
                        st.warning("No data found for this selection.")
                        return

                    # --- RENDER MODES ---
                    if mode == "📈 Trend Tracker":
                        self._render_ts_trend(df_ts, val_col)
                    elif mode == "🔍 Decomposition":
                        self._render_ts_decomposition(df_ts, val_col, p_freq)
                    elif mode == "🌡️ Heatmap View":
                        self._render_ts_heatmap(df_ts, val_col, agg_func)
                    elif mode == "🔮 Future Forecast":
                        self._render_ts_forecast(df_ts, val_col, p_freq)
                    elif mode == "⚠️ Anomaly Detection":
                        self._render_ts_anomalies(df_ts, val_col)

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    def _render_ts_trend(self, df_ts, val_col):
        roll_window = st.slider("Smoothing Window", 1, 30, 7)
        smoothed = self.engine.analytics.stats.get_rolling_stats(
            df_ts, 'ts_date', val_col, window=roll_window, stat_type='mean', center=True
        )
        df_ts['Smoothed'] = smoothed

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_ts['ts_date'], y=df_ts[val_col], mode='lines',
                                 name='Actual', line=dict(color='#636EFA', width=1)))
        fig.add_trace(go.Scatter(x=df_ts['ts_date'], y=df_ts['Smoothed'], mode='lines',
                                 name=f'{roll_window}-Period Avg', line=dict(color='orange', width=2)))

        fig.update_layout(
            title=f"Trend Analysis: {val_col}", template=self.ctx.theme, hovermode="x unified")
        st.plotly_chart(fig)

        if len(df_ts) > 1:
            fst = df_ts[val_col].iloc[0]
            lst = df_ts[val_col].iloc[-1]
            growth = (lst - fst) / fst if fst != 0 else 0
            st.metric("Total Period Growth",
                      f"{growth:+.1%}", f"From {fst:,.0f} to {lst:,.0f}")

    def _render_ts_decomposition(self, df_ts, val_col, p_freq):
        f_shorts = {"D": "D", "W": "W", "ME": "ME", "QE": "Q", "YE": "Y"}
        res = self.engine.analytics.stats.perform_ts_decomposition(
            df_ts, "ts_date", val_col, freq_str=f_shorts.get(p_freq, "D")
        )

        if res.get("error"):
            st.error(f"Decomposition Failed: {res.get('error')}")
        else:
            dates = res['dates']
            fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                                subplot_titles=("Observed", "Trend", "Seasonality", "Residuals"))

            fig.add_trace(go.Scatter(
                x=dates, y=res['observed'], name="Observed"), row=1, col=1)
            fig.add_trace(go.Scatter(x=dates, y=res['trend'], name="Trend", line=dict(
                color='orange')), row=2, col=1)
            fig.add_trace(go.Scatter(x=dates, y=res['seasonal'], name="Seasonal", line=dict(
                color='green')), row=3, col=1)
            fig.add_trace(go.Scatter(
                x=dates, y=res['resid'], name="Resid", mode='markers'), row=4, col=1)

            fig.update_layout(height=700, template=self.ctx.theme,
                              title="Time Series Components")
            st.plotly_chart(fig)

    def _render_ts_heatmap(self, df_ts, val_col, agg_func):
        df_ts['Year'] = df_ts['ts_date'].dt.year
        df_ts['Month'] = df_ts['ts_date'].dt.month_name()
        df_ts['MonthNum'] = df_ts['ts_date'].dt.month

        try:
            pivot_hm = df_ts.pivot_table(
                index='Year', columns='MonthNum', values=val_col, aggfunc='sum')
            month_names = [
                calendar.month_abbr[int(i)] for i in pivot_hm.columns]

            fig = px.imshow(pivot_hm, labels=dict(x="Month", y="Year", color=val_col),
                            x=month_names,
                            title=f"Seasonality Heatmap ({agg_func} {val_col})",
                            template=self.ctx.theme, color_continuous_scale="Viridis")
            st.plotly_chart(fig)
        except Exception as e:
            st.error(f"Heatmap Error (Need at least 2 years/months): {e}")

    def _render_ts_forecast(self, df_ts, val_col, p_freq):
        periods = st.slider("Forecast Horizon (Steps)", 7, 365, 30)
        f_shorts = {"D": "D", "W": "W", "ME": "M", "QE": "Q", "YE": "Y"}
        res = self.engine.analytics.stats.get_ts_forecast(
            df_ts, "ts_date", val_col, periods=periods, freq=f_shorts.get(p_freq, "D")
        )

        if res.get("error"):
            st.error(f"Forecast Failed: {res.get('error')}")
        else:
            method = res.get("method", "Unknown")
            st.info(f"Forecasting Method: **{method}**")

            h_dates = res['history_dates']
            f_dates = res['forecast_dates']

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=h_dates, y=res['history_values'], name="History", line=dict(color='gray', width=1.5)))
            fig.add_trace(go.Scatter(
                x=f_dates, y=res['forecast_values'], name="Forecast", line=dict(color='#636EFA', width=3)))

            fig.add_trace(go.Scatter(
                x=f_dates, y=res['upper_bound'], mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=f_dates, y=res['lower_bound'], mode='lines', line=dict(width=0),
                fill='tonexty', fillcolor='rgba(99, 110, 250, 0.2)', name='95% Confidence'
            ))

            fig.update_layout(
                title=f"Forecast: {val_col} (+{periods} steps)", template=self.ctx.theme)
            st.plotly_chart(fig)

    def _render_ts_anomalies(self, df_ts, val_col):
        sens = st.slider("Sensitivity (Sigma)", 1.0, 5.0, 2.5)
        outliers = self.engine.analytics.stats.detect_ts_outliers(
            df_ts, "ts_date", val_col, sensitivity=sens)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_ts['ts_date'], y=df_ts[val_col], name="Normal", line=dict(color='gray', width=1)))

        if not outliers.empty:
            fig.add_trace(go.Scatter(x=outliers['ts_date'], y=outliers[val_col],
                                     mode='markers', name="Anomaly",
                                     marker=dict(color='red', size=8, symbol='x')))
            st.error(f"Detected {len(outliers)} anomalies!")
            st.dataframe(outliers.sort_values(
                val_col, ascending=False).head(10))
        else:
            st.success("No anomalies detected at this sensitivity.")

        fig.update_layout(title="Outlier Detection", template=self.ctx.theme)
        st.plotly_chart(fig)

    def render_distributions(self) -> None:
        """Render Advanced Distributions Tab"""
        if not self.ctx.num_cols:
            st.info("No numeric columns found.")
            return

        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 1, 1])
            col = c1.selectbox("Variable", self.ctx.num_cols, key="dist_col")
            cat = c2.selectbox(
                "Split/Color By", ["None"] + self.ctx.cat_cols, key="dist_cat")
            mode = c3.selectbox("Chart Type",
                                ["Histogram", "Box Plot", "Violin Plot",
                                    "ECDF (Cumulative)", "QQ Plot (Normality)"],
                                key="dist_mode")

            params = {}
            if mode == "Histogram":
                c_h1, c_h2 = st.columns(2)
                params['bins'] = c_h1.slider(
                    "Bins", 5, 200, 30, key="dist_bins")
                with st.expander("Overlays"):
                    params['kde'] = st.checkbox(
                        "Add KDE Curve", value=True, key="dist_kde")
                    params['fit_norm'] = st.checkbox(
                        "Fit Normal Curve", value=False, key="dist_fitn")
                    params['norm_hist'] = st.checkbox("Show Density",
                                                      value=(
                                                          params['kde'] or params['fit_norm']),
                                                      key="dist_norm",
                                                      disabled=(params['kde'] or params['fit_norm']))
            elif mode in ["Box Plot", "Violin Plot"]:
                params['points'] = st.selectbox("Show Points", ["outliers", "all", "suspectedoutliers", False],
                                                index=0, key="dist_pts")

        if st.button("📊 Render Distribution Analysis", type="primary"):
            self.state.eda_dist_run = True

        if self.state.eda_dist_run:
            if not col:
                return
            with st.spinner("Analyzing Distribution..."):
                self._generate_distribution_chart(col, cat, mode, params)

    def _generate_distribution_chart(self, col, cat, mode, params):
        df_all = self.get_data()
        cols_needed = [col]
        if cat != "None":
            cols_needed.append(cat)
        df_dist = df_all[cols_needed].dropna(subset=[col])

        if df_dist.empty:
            st.warning("No data.")
            return

        color_arg = cat if cat != "None" else None

        if mode == "Histogram":
            self._plot_histogram(df_dist, col, color_arg, params)
        elif mode == "Box Plot":
            st.plotly_chart(px.box(df_dist, y=col, x=color_arg, color=color_arg, points=params['points'],
                                   notched=True, title=f"Box Plot: {col}", template=self.ctx.theme))
        elif mode == "Violin Plot":
            st.plotly_chart(px.violin(df_dist, y=col, x=color_arg, color=color_arg, box=True,
                                      points=params['points'], title=f"Violin Plot: {col}", template=self.ctx.theme))
        elif mode == "ECDF (Cumulative)":
            st.plotly_chart(px.ecdf(df_dist, x=col, color=color_arg,
                                    title=f"ECDF: {col}", template=self.ctx.theme))
        elif mode == "QQ Plot (Normality)":
            self._plot_qq(df_dist[col], col)

        st.divider()
        self._render_distribution_stats(df_dist, col)

    def _plot_histogram(self, df_dist, col, color_arg, params):
        use_density = params.get('kde') or params.get(
            'fit_norm') or params.get('norm_hist')
        histnorm = "probability density" if use_density else None

        fig = px.histogram(df_dist, x=col, color=color_arg, nbins=params['bins'],
                           marginal="box", histnorm=histnorm, opacity=0.6, barmode="overlay",
                           title=f"Histogram of {col}", template=self.ctx.theme)

        series = df_dist[col]
        x_min, x_max = series.min(), series.max()
        rng = x_max - x_min
        x_axis = np.linspace(x_min - 0.1*rng, x_max + 0.1*rng, 500)

        if params.get('kde'):
            kde_res = self.engine.analytics.stats.get_kde_curve(series, x_axis)
            if kde_res and "error" not in kde_res:
                fig.add_trace(go.Scatter(x=kde_res['x_values'], y=kde_res['y_values'],
                                         mode='lines', name='KDE', line=dict(color='magenta', width=2)))

        if params.get('fit_norm'):
            norm_res = self.engine.analytics.stats.get_normal_fit(
                series, x_axis)
            if norm_res and "error" not in norm_res:
                fig.add_trace(go.Scatter(x=norm_res['x_values'], y=norm_res['y_values'],
                                         mode='lines', name=f'Normal (μ={norm_res["mu"]:.1f})',
                                         line=dict(color='red', dash='dash')))
        st.plotly_chart(fig)

    def _plot_qq(self, series, col):
        qq_res = self.engine.analytics.stats.get_qq_plot_data(series)
        if qq_res and "error" not in qq_res:
            qq_df = pd.DataFrame(
                {"Theoretical": qq_res['theoretical'], "Observed": qq_res['observed']})
            fig = px.scatter(qq_df, x="Theoretical", y="Observed", height=600,
                             title=f"QQ Plot: {col} vs Normal", template=self.ctx.theme)

            min_v = min(qq_res['theoretical'].min(), qq_res['observed'].min())
            max_v = max(qq_res['theoretical'].max(), qq_res['observed'].max())

            slope = qq_res.get('slope', 1)
            intercept = qq_res.get('intercept', 0)
            x_line = np.array([min_v, max_v])
            y_line = slope * x_line + intercept

            fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines',
                                     line=dict(color='red', dash='dash'), name='Fit'))
            st.plotly_chart(fig)
        else:
            st.warning("QQ Plot calculation failed.")

    def _render_distribution_stats(self, df_dist, col):
        st.write("###### 📐 Statistical Summary")
        c_stat, c_quant = st.columns([1.5, 1])

        with c_stat:
            stats_res = self.engine.analytics.stats.get_distribution_stats(
                df_dist, col)
            if "error" not in stats_res:
                m1, m2, m3 = st.columns(3)
                m1.metric("Mean", f"{stats_res.get('Mean', 0):.2f}")
                m2.metric("Median", f"{stats_res.get('Median', 0):.2f}")
                m3.metric("Std Dev", f"{stats_res.get('Std Dev', 0):.2f}")

                m4, m5, m6 = st.columns(3)
                m4.metric("Skewness", f"{stats_res.get('Skewness', 0):.2f}")
                m5.metric("Kurtosis", f"{stats_res.get('Kurtosis', 0):.2f}")
                m6.metric(
                    "Min/Max", f"{stats_res.get('Min'):.1f} / {stats_res.get('Max'):.1f}")

        with c_quant:
            st.caption("Quantiles")
            qs = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
            q_res = self.engine.analytics.stats.get_quantiles(df_dist[col], qs)
            if q_res:
                q_df = pd.DataFrame(
                    {"Percentile": [f"{q:.0%}" for q in qs], "Value": [q_res[q] for q in qs]})
                st.dataframe(q_df, hide_index=True)

        outliers = self.engine.analytics.stats.get_outliers_iqr(df_dist, col)
        if not outliers.empty:
            with st.expander(f"⚠️ Extreme Outliers Detected ({len(outliers)})"):
                st.dataframe(outliers.head(20))

    def render_hierarchy(self) -> None:
        """Render Advanced Hierarchy Tab"""
        st.caption("Analyze hierarchical composition and market concentration.")

        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            path = c1.multiselect("Hierarchy Path (Order Matters)", self.ctx.cat_cols,
                                  default=self.ctx.cat_cols[:2] if len(self.ctx.cat_cols) >= 2 else self.ctx.cat_cols)
            val = c2.selectbox(
                "Size By", ["Count"] + self.ctx.num_cols, index=0, key="hier_val")
            chart_type = c3.selectbox(
                "Visual", ["Sunburst", "Treemap", "Icicle"], key="hier_type")

        if st.button("🕸️ Render Hierarchy Analysis", type="primary"):
            self.state.eda_hier_run = True

        if self.state.eda_hier_run:
            if not path:
                st.warning("Select at least one category.")
                return

            with st.spinner("Aggregating & Analyzing..."):
                self._generate_hierarchy_chart(path, val, chart_type)

    def _generate_hierarchy_chart(self, path, val, chart_type):
        df_all = self.get_data()
        df_hier = df_all.dropna(subset=path).copy()

        if val == "Count":
            df_agg = df_hier.groupby(path).size().reset_index(name='count')
            metric_col = 'count'
        else:
            df_agg = df_hier.groupby(path)[val].sum().reset_index()
            metric_col = val
            df_agg = df_agg[df_agg[val] > 0]

        if df_agg.empty:
            st.warning("No data found.")
            return

        if chart_type == "Sunburst":
            st.plotly_chart(px.sunburst(df_agg, path=path, values=metric_col,
                            title=f"Hierarchical View ({val})", template=self.ctx.theme))
        elif chart_type == "Treemap":
            st.plotly_chart(px.treemap(df_agg, path=path, values=metric_col,
                            title=f"Treemap View ({val})", template=self.ctx.theme))
        else:
            st.plotly_chart(px.icicle(df_agg, path=path, values=metric_col,
                            title=f"Icicle View ({val})", template=self.ctx.theme))

        st.divider()
        st.subheader("📉 Concentration Analysis")
        drill_col = st.selectbox(
            "Analyze Concentration at Level:", path, index=0, key="hier_conc_lvl")

        df_level = df_agg.groupby(drill_col)[metric_col].sum(
        ).reset_index().sort_values(metric_col, ascending=False)
        conc_stats = self.engine.analytics.stats.get_concentration_metrics(
            df_level, drill_col, metric_col)

        if conc_stats and "error" not in conc_stats:
            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
            c_m1.metric("Total Groups", f"{conc_stats['Total_Groups']:,}")
            c_m2.metric("Top 3 Share", f"{conc_stats['Top_3_Share']:.1%}")
            c_m3.metric("Gini Coefficient", f"{conc_stats['Gini']:.2f}")
            c_m4.metric("HHI Score", f"{conc_stats['HHI']:,.0f}")

            df_level["Share"] = df_level[metric_col] / \
                df_level[metric_col].sum()
            df_level["Cum. Share"] = df_level["Share"].cumsum()
            st.dataframe(df_level.head(10), hide_index=True)

    def render_relationships(self) -> None:
        """Render Relationships Tab"""
        with st.container(border=True):
            mode = st.radio("Visualization Mode", [
                "Scatter Plot (2D)", "Scatter Matrix (SPLOM)", "3D Scatter",
                "Heatmap (Density)", "Sankey Flow", "Parallel Coords"
            ], horizontal=True, label_visibility="collapsed", key="rel_viz_mode")

        df_all = self.get_data()

        if mode == "Scatter Plot (2D)":
            self._render_scatter_2d(df_all)
        elif mode == "Scatter Matrix (SPLOM)":
            self._render_splom(df_all)
        elif mode == "3D Scatter":
            self._render_scatter_3d(df_all)
        elif mode == "Heatmap (Density)":
            self._render_heatmap_density(df_all)
        elif mode == "Sankey Flow":
            self._render_sankey(df_all)
        elif mode == "Parallel Coords":
            self._render_parallel_coords(df_all)

    def _render_scatter_2d(self, df_all):
        c1, c2, c3, c4 = st.columns(4)
        x = c1.selectbox("X Axis", self.ctx.num_cols, index=0, key="fg_x")
        y = c2.selectbox("Y Axis", self.ctx.num_cols, index=1 if len(
            self.ctx.num_cols) > 1 else 0, key="fg_y")
        cat = c3.selectbox(
            "Color By", ["None"] + self.ctx.cat_cols, key="fg_cat")
        trend = c4.checkbox("Show Trend Line", value=True)

        if st.button("💠 Render Scatter", type="primary"):
            self.state.eda_rel_scatter_run = True

        if self.state.eda_rel_scatter_run:
            cols_needed = [x, y]
            if cat != "None":
                cols_needed.append(cat)
            df_rel = df_all[cols_needed].dropna()

            fig = px.scatter(df_rel, x=x, y=y, color=cat if cat != "None" else None,
                             trendline="ols" if trend else None, trendline_color_override="red",
                             opacity=0.7, template=self.ctx.theme, title=f"Scatter: {x} vs {y}")
            st.plotly_chart(fig)

            st.divider()
            assoc = self.engine.analytics.stats.get_pairwise_association(
                df_rel, x, y)
            if assoc and "error" not in assoc:
                st.metric(
                    "Correlation Score", f"{assoc.get('score', 0):.3f}", help=assoc.get("note", ""))

    def _render_splom(self, df_all):
        sel_cols = st.multiselect(
            "Select Dimensions", self.ctx.num_cols, default=self.ctx.num_cols[:4], key="splom_cols")
        c_col = st.selectbox(
            "Color By", ["None"] + self.ctx.cat_cols, key="splom_c")

        if st.button("🧩 Render Matrix"):
            if len(sel_cols) < 2:
                st.warning("Select at least 2 columns.")
            else:
                cols_needed = list(sel_cols)
                if c_col != "None":
                    cols_needed.append(c_col)
                df_splom = df_all[cols_needed].dropna()
                st.plotly_chart(px.scatter_matrix(df_splom, dimensions=sel_cols,
                                                  color=c_col if c_col != "None" else None,
                                                  height=800, width=800, opacity=0.5,
                                                  template=self.ctx.theme, title="Multivariate Scatter Matrix"))

    def _render_scatter_3d(self, df_all):
        if len(self.ctx.num_cols) < 3:
            st.warning("Need at least 3 numeric columns.")
            return
        c1, c2, c3, c4 = st.columns(4)
        x3 = c1.selectbox("X", self.ctx.num_cols, index=0, key="3d_x")
        y3 = c2.selectbox("Y", self.ctx.num_cols, index=1, key="3d_y")
        z3 = c3.selectbox("Z", self.ctx.num_cols, index=2, key="3d_z")
        c3d = c4.selectbox(
            "Color", ["None"] + self.ctx.cat_cols + self.ctx.num_cols, key="3d_c")

        if st.button("🧊 Render 3D Plot"):
            cols = [x3, y3, z3]
            if c3d != "None":
                cols.append(c3d)
            df_3d = df_all[cols].dropna()
            st.plotly_chart(px.scatter_3d(df_3d, x=x3, y=y3, z=z3, color=c3d if c3d != "None" else None,
                                          opacity=0.6, template=self.ctx.theme, title=f"3D Analysis: {x3}-{y3}-{z3}"))

    def _render_heatmap_density(self, df_all):
        c1, c2 = st.columns(2)
        hx = c1.selectbox("X Axis", self.ctx.num_cols, index=0, key="thm_x")
        hy = c2.selectbox("Y Axis", self.ctx.num_cols, index=1, key="thm_y")

        if st.button("🔥 Render Heatmap"):
            df_hm = df_all[[hx, hy]].dropna()
            st.plotly_chart(px.density_heatmap(df_hm, x=hx, y=hy, marginal_x="histogram", marginal_y="histogram",
                                               title=f"Density Heatmap: {hx} vs {hy}", template=self.ctx.theme, text_auto=True))

    def _render_sankey(self, df_all):
        c1, c2 = st.columns(2)
        if len(self.ctx.cat_cols) < 2:
            st.warning("Need at least 2 categorical columns.")
            return
        src = c1.selectbox("Source", self.ctx.cat_cols,
                           index=0, key="sank_src")
        tgt = c2.selectbox("Target", self.ctx.cat_cols,
                           index=1, key="sank_tgt")

        if st.button("🌊 Render Sankey"):
            if src == tgt:
                st.warning("Select distinct columns.")
            else:
                with st.spinner("Analyzing Flow..."):
                    df_sank = df_all[[src, tgt]].dropna()
                    st.plotly_chart(px.parallel_categories(
                        df_sank, dimensions=[src, tgt], template=self.ctx.theme))

    def _render_parallel_coords(self, df_all):
        dims = st.multiselect("Dimensions", self.ctx.num_cols, default=self.ctx.num_cols[:4] if len(
            self.ctx.num_cols) >= 4 else self.ctx.num_cols)
        c = st.selectbox("Color Scale", self.ctx.num_cols,
                         index=0, key="par_c")

        if st.button("🎼 Render Parallel Coords"):
            if not dims:
                return
            cols_needed = list(dims)
            if c:
                cols_needed.append(c)
            df_par = df_all[list(set(cols_needed))].dropna()
            st.plotly_chart(px.parallel_coordinates(
                df_par, dimensions=dims, color=c, template=self.ctx.theme))
