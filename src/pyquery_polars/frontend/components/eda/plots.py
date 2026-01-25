import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import calendar
from plotly.subplots import make_subplots

from pyquery_polars.frontend.components.eda.core import EDAContext


def render_time_series(ctx: EDAContext):
    """Render Time Series Tab (Advanced)"""

    if not ctx.date_cols:
        st.info("No DateTime columns found.")
        return

    # --- Controls ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        dt_col = c1.selectbox("Time Axis", ctx.date_cols, key="ts_time")
        val_col = c2.selectbox("Value", ctx.num_cols, key="ts_val")
        freq = c3.selectbox("Granularity", ["Auto", "Daily (D)", "Weekly (W)",
                            "Monthly (M)", "Quarterly (Q)", "Yearly (Y)"], index=0, key="ts_freq")
        agg_func = c4.selectbox(
            "Aggregation", ["Sum", "Mean", "Max", "Min", "Count"], index=1, key="ts_agg")

    # Map Freq
    freq_map = {
        "Auto": "1mo", "Daily (D)": "1d", "Weekly (W)": "1w",
        "Monthly (M)": "1mo", "Quarterly (Q)": "3mo", "Yearly (Y)": "1y"
    }
    freq_code = freq_map[str(freq)]

    mode = st.radio("Analysis Mode",
                    ["📈 Trend Tracker", "🔍 Decomposition", "🔮 Future Forecast",
                        "🌡️ Heatmap View", "⚠️ Anomaly Detection"],
                    horizontal=True, key="ts_mode"
                    )

    if st.button("Run Time Series Analysis", type="primary"):
        st.session_state.eda_ts_run = True

    if st.session_state.get("eda_ts_run", False):
        if not val_col:
            return

        engine = ctx.engine

        with st.spinner("Processing Time Series..."):
            try:
                # 1. Prepare Aggregated LazyFrame
                # Use Truncate for robust flexible buckets - but for display consistency we often want pandas resampling
                # We will use ctx.get_pandas() as requested for consistency

                df_all = ctx.get_pandas()
                if df_all is None:
                    return

                # Pandas Resample Logic
                # Ensure date is datetime
                df_ts = df_all.copy()
                df_ts[dt_col] = pd.to_datetime(df_ts[dt_col])

                # Pandas Freq Map
                p_freq_map = {
                    "Auto": "ME", "Daily (D)": "D", "Weekly (W)": "W",
                    "Monthly (M)": "ME", "Quarterly (Q)": "QE", "Yearly (Y)": "YE"
                }
                p_freq = p_freq_map.get(str(freq), "D")

                # Agg
                df_ts = df_ts.set_index(dt_col).resample(
                    p_freq)[val_col].agg(agg_func.lower())
                df_ts = df_ts.reset_index().rename(
                    columns={dt_col: 'ts_date', val_col: val_col})

                if df_ts.empty:
                    st.warning("No data found for this selection.")
                    return

                # --- RENDER MODES ---

                if mode == "📈 Trend Tracker":
                    # Simple Line + Area
                    # Add Window Average option
                    roll_window = st.slider("Smoothing Window", 1, 30, 7)
                    # Use backend for rolling calculation
                    smoothed = engine.analytics.stats.get_rolling_stats(
                        df_ts, 'ts_date', val_col, window=roll_window, stat_type='mean', center=True
                    )
                    df_ts['Smoothed'] = smoothed

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_ts['ts_date'], y=df_ts[val_col], mode='lines',
                                             name='Actual', line=dict(color='#636EFA', width=1)))
                    fig.add_trace(go.Scatter(x=df_ts['ts_date'], y=df_ts['Smoothed'], mode='lines',
                                             name=f'{roll_window}-Period Avg', line=dict(color='orange', width=2)))

                    fig.update_layout(
                        title=f"Trend Analysis: {val_col}", template=ctx.theme, hovermode="x unified")
                    st.plotly_chart(fig)

                    # Growth Metric
                    if len(df_ts) > 1:
                        fst = df_ts[val_col].iloc[0]
                        lst = df_ts[val_col].iloc[-1]
                        growth = (lst - fst) / fst if fst != 0 else 0
                        st.metric("Total Period Growth",
                                  f"{growth:+.1%}", f"From {fst:,.0f} to {lst:,.0f}")

                elif mode == "🔍 Decomposition":
                    # Backend Decomp
                    f_shorts = {"D": "D", "W": "W",
                                "ME": "ME", "QE": "Q", "YE": "Y"}

                    res = engine.analytics.stats.perform_ts_decomposition(
                        df_ts, "ts_date", val_col, freq_str=f_shorts.get(p_freq, "D")
                    )

                    if res.get("error"):
                        st.error(f"Decomposition Failed: {res.get('error')}")
                    else:
                        st.success("Decomposed successfully.")
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

                        fig.update_layout(
                            height=700, template=ctx.theme, title="Time Series Components")
                        st.plotly_chart(fig)

                elif mode == "🌡️ Heatmap View":
                    # X=Month/Week, Y=Year
                    df_ts['Year'] = df_ts['ts_date'].dt.year
                    df_ts['Month'] = df_ts['ts_date'].dt.month_name()
                    df_ts['MonthNum'] = df_ts['ts_date'].dt.month

                    # Pivot
                    try:
                        pivot_hm = df_ts.pivot_table(
                            index='Year', columns='MonthNum', values=val_col, aggfunc='sum')
                        # Map Month Num to Name for X axis
                        month_names = [
                            calendar.month_abbr[int(i)] for i in pivot_hm.columns]

                        fig = px.imshow(pivot_hm, labels=dict(x="Month", y="Year", color=val_col),
                                        x=month_names,
                                        title=f"Seasonality Heatmap ({agg_func} {val_col})",
                                        template=ctx.theme,
                                        color_continuous_scale="Viridis")
                        st.plotly_chart(fig)
                    except Exception as e:
                        st.error(
                            f"Heatmap Error (Need at least 2 years/months): {e}")

                elif mode == "🔮 Future Forecast":
                    # Controls
                    periods = st.slider("Forecast Horizon (Steps)", 7, 365, 30)

                    # Run Forecast
                    f_shorts = {"D": "D", "W": "W",
                                "ME": "M", "QE": "Q", "YE": "Y"}
                    res = engine.analytics.stats.get_ts_forecast(
                        df_ts, "ts_date", val_col, periods=periods, freq=f_shorts.get(p_freq, "D")
                    )

                    if res.get("error"):
                        st.error(f"Forecast Failed: {res.get('error')}")
                    else:
                        method = res.get("method", "Unknown")
                        st.info(f"Forecasting Method: **{method}**")

                        # Parse Dates
                        h_dates = res['history_dates']
                        f_dates = res['forecast_dates']

                        fig = go.Figure()

                        # History
                        fig.add_trace(go.Scatter(
                            x=h_dates, y=res['history_values'], name="History", line=dict(color='gray', width=1.5)))

                        # Forecast
                        fig.add_trace(go.Scatter(
                            x=f_dates, y=res['forecast_values'], name="Forecast", line=dict(color='#636EFA', width=3)))

                        # Confidence Intervals
                        fig.add_trace(go.Scatter(
                            x=f_dates, y=res['upper_bound'],
                            mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
                        ))
                        fig.add_trace(go.Scatter(
                            x=f_dates, y=res['lower_bound'],
                            mode='lines', line=dict(width=0),
                            fill='tonexty', fillcolor='rgba(99, 110, 250, 0.2)',
                            name='95% Confidence'
                        ))

                        fig.update_layout(
                            title=f"Forecast: {val_col} (+{periods} steps)", template=ctx.theme)
                        st.plotly_chart(fig)

                elif mode == "⚠️ Anomaly Detection":
                    # Z-Score Anomaly
                    sens = st.slider("Sensitivity (Sigma)", 1.0, 5.0, 2.5)
                    outliers = engine.analytics.stats.detect_ts_outliers(
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
                        st.success(
                            "No anomalies detected at this sensitivity.")

                    fig.update_layout(
                        title="Outlier Detection", template=ctx.theme)
                    st.plotly_chart(fig)

            except Exception as e:
                st.error(f"Analysis failed: {e}")


def render_distributions(ctx: EDAContext):
    """Render Advanced Distributions Tab"""

    if not ctx.num_cols:
        st.info("No numeric columns found.")
        return

    # --- Controls ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        col = c1.selectbox("Variable", ctx.num_cols, key="dist_col")
        cat = c2.selectbox(
            "Split/Color By", ["None"] + ctx.cat_cols, key="dist_cat")

        mode = c3.selectbox("Chart Type",
                            ["Histogram", "Box Plot", "Violin Plot",
                                "ECDF (Cumulative)", "QQ Plot (Normality)"],
                            key="dist_mode"
                            )

        # Sub-controls
        params = {}
        if mode == "Histogram":
            c_h1, c_h2 = st.columns(2)
            params['bins'] = c_h1.slider("Bins", 5, 200, 30, key="dist_bins")

            # Density Options
            st.caption("Overlays")
            c_o1, c_o2, c_o3 = st.columns(3)
            params['kde'] = c_o1.checkbox(
                "Add KDE Curve", value=True, key="dist_kde")
            params['fit_norm'] = c_o2.checkbox(
                "Fit Normal Curve", value=False, key="dist_fitn")
            params['norm_hist'] = c_o3.checkbox("Show Density", value=(params['kde'] or params['fit_norm']), key="dist_norm",
                                                disabled=(
                                                    params['kde'] or params['fit_norm']),
                                                help="Forced to True if Curves are active")

        elif mode in ["Box Plot", "Violin Plot"]:
            params['points'] = st.selectbox("Show Points", [
                                            "outliers", "all", "suspectedoutliers", False], index=0, key="dist_pts")

    if st.button("📊 Render Distribution Analysis", type="primary"):
        st.session_state.eda_dist_run = True

    if st.session_state.get("eda_dist_run", False):
        if not col:
            return

        engine = ctx.engine
        with st.spinner("Analyzing Distribution..."):
            try:
                # Prepare Data using CACHED DF
                df_all = ctx.get_pandas()
                if df_all is None:
                    return

                cols_needed = [col]
                if cat != "None":
                    cols_needed.append(cat)

                df_dist = df_all[cols_needed].dropna(subset=[col])

                if df_dist.empty:
                    st.warning("No data.")
                    return

                # --- 1. VISUALIZATION ---
                color_arg = cat if cat != "None" else None

                if mode == "Histogram":
                    use_density = params.get('kde') or params.get(
                        'fit_norm') or params.get('norm_hist')
                    histnorm = "probability density" if use_density else None

                    # Base Histogram
                    fig = px.histogram(df_dist, x=col, color=color_arg,
                                       nbins=params['bins'],
                                       marginal="box",
                                       histnorm=histnorm,
                                       opacity=0.6,
                                       barmode="overlay",
                                       title=f"Histogram of {col}",
                                       template=ctx.theme)

                    # Add Overlays via BACKEND Engine
                    if (params.get('kde') or params.get('fit_norm')):
                        if cat != "None":
                            st.caption(
                                "ℹ️ Overlays (KDE/Normal) are displayed for the *global* distribution, ignoring split.")

                        # Calculate Global Series
                        series = df_dist[col]
                        x_min, x_max = series.min(), series.max()
                        rng = x_max - x_min
                        x_axis = np.linspace(
                            x_min - 0.1*rng, x_max + 0.1*rng, 500)

                        if params.get('kde'):
                            # Use Engine
                            kde_res = engine.analytics.stats.get_kde_curve(
                                series, x_axis)
                            if kde_res and "error" not in kde_res:
                                fig.add_trace(go.Scatter(
                                    x=kde_res['x_values'], y=kde_res['y_values'],
                                    mode='lines', name='KDE', line=dict(color='magenta', width=2)))
                            else:
                                st.warning(
                                    "Backend KDE failed or scipy missing.")

                        if params.get('fit_norm'):
                            # Use Engine
                            norm_res = engine.analytics.stats.get_normal_fit(
                                series, x_axis)
                            if norm_res and "error" not in norm_res:
                                mu = norm_res['mu']
                                fig.add_trace(go.Scatter(
                                    x=norm_res['x_values'], y=norm_res['y_values'],
                                    mode='lines', name=f'Normal (μ={mu:.1f})',
                                    line=dict(color='red', dash='dash')))

                    st.plotly_chart(fig)

                elif mode == "Box Plot":
                    fig = px.box(df_dist, y=col, x=color_arg, color=color_arg,
                                 points=params['points'], notched=True,
                                 title=f"Box Plot: {col}", template=ctx.theme)
                    st.plotly_chart(fig)

                elif mode == "Violin Plot":
                    fig = px.violin(df_dist, y=col, x=color_arg, color=color_arg,
                                    box=True, points=params['points'],
                                    title=f"Violin Plot: {col}", template=ctx.theme)
                    st.plotly_chart(fig)

                elif mode == "ECDF (Cumulative)":
                    fig = px.ecdf(df_dist, x=col, color=color_arg,
                                  title=f"ECDF: {col}", template=ctx.theme)
                    st.plotly_chart(fig)

                elif mode == "QQ Plot (Normality)":
                    series = df_dist[col]
                    # Use Engine
                    qq_res = engine.analytics.stats.get_qq_plot_data(series)

                    if qq_res and "error" not in qq_res:
                        qq_df = pd.DataFrame({
                            "Theoretical": qq_res['theoretical'],
                            "Observed": qq_res['observed']
                        })
                        fig = px.scatter(qq_df, x="Theoretical", y="Observed",
                                         height=600, title=f"QQ Plot: {col} vs Normal", template=ctx.theme)
                        # Identity line
                        min_v = min(qq_res['theoretical'].min(),
                                    qq_res['observed'].min())
                        max_v = max(qq_res['theoretical'].max(),
                                    qq_res['observed'].max())

                        # Best fit line from engine params
                        slope = qq_res.get('slope', 1)
                        intercept = qq_res.get('intercept', 0)

                        # Add robust line based on regression
                        # y = mx + c
                        x_line = np.array([min_v, max_v])
                        y_line = slope * x_line + intercept

                        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines',
                                                 line=dict(color='red', dash='dash'), name='Fit'))

                        st.plotly_chart(fig)
                    else:
                        st.warning("QQ Plot calculation failed in backend.")

                # --- 2. STATISTICAL INSIGHTS ---
                st.divider()
                st.write("###### 📐 Statistical Summary")

                c_stat, c_quant = st.columns([1.5, 1])

                with c_stat:
                    stats_res = engine.analytics.stats.get_distribution_stats(
                        df_dist, col)
                    if "error" not in stats_res:
                        # 3-col metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Mean", f"{stats_res.get('Mean', 0):.2f}")
                        m2.metric(
                            "Median", f"{stats_res.get('Median', 0):.2f}")
                        m3.metric(
                            "Std Dev", f"{stats_res.get('Std Dev', 0):.2f}")

                        m4, m5, m6 = st.columns(3)
                        m4.metric(
                            "Skewness", f"{stats_res.get('Skewness', 0):.2f}")
                        m5.metric(
                            "Kurtosis", f"{stats_res.get('Kurtosis', 0):.2f}")
                        m6.metric(
                            "Min/Max", f"{stats_res.get('Min'):.1f} / {stats_res.get('Max'):.1f}")

                        norm_test = stats_res.get("Normality_Test")
                        if norm_test:
                            is_norm = stats_res.get("Is_Normal")
                            color = "green" if is_norm else "orange"
                            st.markdown(
                                f":{color}[**{norm_test}**]: p={stats_res.get('Normality_p', 0):.4f} ({'Normal' if is_norm else 'Non-Normal'})")

                with c_quant:
                    st.caption("Quantiles")
                    qs = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
                    # Use backend
                    q_res = engine.analytics.stats.get_quantiles(
                        df_dist[col], qs)
                    if q_res:
                        q_df = pd.DataFrame(
                            {"Percentile": [f"{q:.0%}" for q in qs], "Value": [q_res[q] for q in qs]})
                        st.dataframe(q_df, hide_index=True)

                # Outliers backend
                outliers = engine.analytics.stats.get_outliers_iqr(
                    df_dist, col)
                if not outliers.empty:
                    with st.expander(f"⚠️ Extreme Outliers Detected ({len(outliers)})"):
                        st.dataframe(outliers.head(20))

            except Exception as e:
                st.error(f"Distribution Error: {e}")


def render_hierarchy(ctx: EDAContext):
    """Render Advanced Hierarchy Tab (Structure & Concentration)"""
    st.caption("Analyze hierarchical composition and market concentration.")

    # --- Controls ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        path = c1.multiselect("Hierarchy Path (Order Matters)", ctx.cat_cols,
                              default=ctx.cat_cols[:2] if len(ctx.cat_cols) >= 2 else ctx.cat_cols)
        val = c2.selectbox(
            "Size By", ["Count"] + ctx.num_cols, index=0, key="hier_val")
        chart_type = c3.selectbox(
            "Visual", ["Sunburst", "Treemap", "Icicle"], key="hier_type")

    if st.button("🕸️ Render Hierarchy Analysis", type="primary"):
        st.session_state.eda_hier_run = True

    if st.session_state.get("eda_hier_run", False):
        if not path:
            st.warning("Select at least one category for hierarchy.")
            return

        engine = ctx.engine
        with st.spinner("Aggregating & Analyzing..."):
            try:
                # 1. Visualization
                # Use CACHED pandas
                df_all = ctx.get_pandas()
                if df_all is None:
                    return

                # Filter nulls in path
                df_hier = df_all.dropna(subset=path).copy()

                # Aggregate manually in pandas for display, or just pass raw data to plotly
                # Plotly handles raw data well, but pre-aggregating is safer for rendering speed if data is large
                # GroupBy in pandas
                if val == "Count":
                    df_agg = df_hier.groupby(
                        path).size().reset_index(name='count')
                    metric_col = 'count'
                else:
                    df_agg = df_hier.groupby(path)[val].sum().reset_index()
                    metric_col = val
                    df_agg = df_agg[df_agg[val] > 0]

                if df_agg.empty:
                    st.warning("No data found.")
                    return

                if chart_type == "Sunburst":
                    fig = px.sunburst(df_agg, path=path, values=metric_col,
                                      title=f"Hierarchical View ({val})", template=ctx.theme)
                elif chart_type == "Treemap":
                    fig = px.treemap(df_agg, path=path, values=metric_col,
                                     title=f"Treemap View ({val})", template=ctx.theme)
                else:  # Icicle
                    fig = px.icicle(df_agg, path=path, values=metric_col,
                                    title=f"Icicle View ({val})", template=ctx.theme)

                st.plotly_chart(fig)

                # 2. Concentration Analysis (Drill Down)
                st.divider()
                st.subheader("📉 Concentration Analysis")

                # Select level to analyze
                drill_col = st.selectbox(
                    "Analyze Concentration at Level:", path, index=0, key="hier_conc_lvl")

                # Re-aggregate for this specific level (Summing up sub-levels)
                df_level = df_agg.groupby(drill_col)[metric_col].sum(
                ).reset_index().sort_values(metric_col, ascending=False)

                # Compute Stats via Backend
                conc_stats = engine.analytics.stats.get_concentration_metrics(
                    df_level, drill_col, metric_col)

                if conc_stats and "error" not in conc_stats:
                    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                    c_m1.metric("Total Groups",
                                f"{conc_stats['Total_Groups']:,}")
                    c_m2.metric("Top 3 Share",
                                f"{conc_stats['Top_3_Share']:.1%}")

                    gini_score = conc_stats['Gini']
                    gini_label = "Equality" if gini_score < 0.2 else (
                        "High Concentration" if gini_score > 0.6 else "Moderate")
                    c_m3.metric(
                        "Gini Coefficient", f"{gini_score:.2f}", delta=gini_label, delta_color="inverse")

                    hhi = conc_stats['HHI']
                    hhi_label = "Competitive" if hhi < 1500 else "Concentrated"
                    c_m4.metric(
                        "HHI Score", f"{hhi:,.0f}", help="< 1500: Competitive, > 2500: Highly Concentrated")

                    # Pareto Table
                    st.caption(f"🏆 Top Contributors ({drill_col})")

                    df_level["Share"] = df_level[metric_col] / \
                        df_level[metric_col].sum()
                    df_level["Cum. Share"] = df_level["Share"].cumsum()

                    # Format
                    df_level["Share"] = df_level["Share"].apply(
                        lambda x: f"{x:.1%}")
                    df_level["Cum. Share"] = df_level["Cum. Share"].apply(
                        lambda x: f"{x:.1%}")

                    st.dataframe(df_level.head(10), hide_index=True)

            except Exception as e:
                st.error(f"Hierarchy Error: {e}")


def render_relationships(ctx: EDAContext):
    """Render Advanced Relationships Tab (Multivariate & Association)"""

    # Mode Selection
    with st.container(border=True):
        mode = st.radio("Visualization Mode", [
            "Scatter Plot (2D)", "Scatter Matrix (SPLOM)", "3D Scatter",
            "Heatmap (Density)", "Sankey Flow", "Parallel Coords"
        ], horizontal=True, label_visibility="collapsed", key="rel_viz_mode")

    # Get cached DF
    df_all = ctx.get_pandas()
    if df_all is None:
        return

    # --- 1. SCATTER PLOT 2D ---
    if mode == "Scatter Plot (2D)":
        c1, c2, c3, c4 = st.columns(4)
        x = c1.selectbox("X Axis", ctx.num_cols, index=0, key="fg_x")
        y = c2.selectbox("Y Axis", ctx.num_cols, index=1 if len(
            ctx.num_cols) > 1 else 0, key="fg_y")
        cat = c3.selectbox("Color By", ["None"] + ctx.cat_cols, key="fg_cat")
        trend = c4.checkbox("Show Trend Line", value=True)

        if st.button("💠 Render Scatter", type="primary"):
            st.session_state.eda_rel_scatter_run = True

        if st.session_state.get("eda_rel_scatter_run", False):
            with st.spinner("Analyzing..."):
                cols_needed = [x, y]
                if cat != "None":
                    cols_needed.append(cat)

                df_rel = df_all[cols_needed].dropna()

                # Plot
                color_arg = cat if cat != "None" else None
                ols = "ols" if trend else None

                fig = px.scatter(df_rel, x=x, y=y, color=color_arg,
                                 trendline=ols, trendline_color_override="red",
                                 opacity=0.7,
                                 template=ctx.theme, title=f"Scatter: {x} vs {y}")
                st.plotly_chart(fig)

                # Association Stats
                st.divider()
                st.write("###### 🔗 Association Metrics")
                # Use Backend
                assoc = ctx.engine.analytics.stats.get_pairwise_association(
                    df_rel, x, y)
                if assoc and "error" not in assoc:
                    c_s1, c_s2 = st.columns(2)
                    c_s1.metric("Method", assoc.get("method", "Unknown"))

                    score = assoc.get("score", 0)
                    note = assoc.get("note", "")
                    c_s2.metric("Score", f"{score:.3f}", help=note)

                    if assoc.get("p_value") is not None:
                        p = assoc.get('p_value')
                        if p is not None:
                            sig = "Significant (p < 0.05) ✅" if p < 0.05 else "Not Significant ❌"
                            st.caption(f"p-value: {p:.4e} → {sig}")

    # --- 2. SCATTER MATRIX (SPLOM) ---
    elif mode == "Scatter Matrix (SPLOM)":
        sel_cols = st.multiselect(
            "Select Dimensions", ctx.num_cols, default=ctx.num_cols[:4], key="splom_cols")
        c_col = st.selectbox(
            "Color By", ["None"] + ctx.cat_cols, key="splom_c")

        if st.button("🧩 Render Matrix"):
            st.session_state.eda_rel_splom_run = True

        if st.session_state.get("eda_rel_splom_run", False):
            if len(sel_cols) < 2:
                st.warning("Select at least 2 columns.")
            else:
                cols_needed = list(sel_cols)
                if c_col != "None":
                    cols_needed.append(c_col)

                df_splom = df_all[cols_needed].dropna()

                fig = px.scatter_matrix(df_splom, dimensions=sel_cols,
                                        color=c_col if c_col != "None" else None,
                                        height=800, width=800, opacity=0.5,
                                        template=ctx.theme, title="Multivariate Scatter Matrix")
                st.plotly_chart(fig)

    # --- 3. 3D SCATTER ---
    elif mode == "3D Scatter":
        if len(ctx.num_cols) < 3:
            st.warning("Need at least 3 numeric columns.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            x3 = c1.selectbox("X", ctx.num_cols, index=0, key="3d_x")
            y3 = c2.selectbox("Y", ctx.num_cols, index=1, key="3d_y")
            z3 = c3.selectbox("Z", ctx.num_cols, index=2, key="3d_z")
            # Allow numerical color
            c3d = c4.selectbox(
                "Color", ["None"] + ctx.cat_cols + ctx.num_cols, key="3d_c")

            if st.button("🧊 Render 3D Plot"):
                st.session_state.eda_rel_3d_run = True

            if st.session_state.get("eda_rel_3d_run", False):
                cols = [x3, y3, z3]
                if c3d != "None":
                    cols.append(c3d)

                df_3d = df_all[cols].dropna()

                fig = px.scatter_3d(df_3d, x=x3, y=y3, z=z3,
                                    color=c3d if c3d != "None" else None,
                                    opacity=0.6, template=ctx.theme,
                                    title=f"3D Analysis: {x3}-{y3}-{z3}")
                st.plotly_chart(fig)

    # --- 4. HEATMAP (DENSITY) ---
    elif mode == "Heatmap (Density)":
        c1, c2 = st.columns(2)
        hx = c1.selectbox("X Axis", ctx.num_cols, index=0, key="thm_x")
        hy = c2.selectbox("Y Axis", ctx.num_cols, index=1, key="thm_y")

        if st.button("🔥 Render Heatmap"):
            st.session_state.eda_rel_hm_run = True

        if st.session_state.get("eda_rel_hm_run", False):
            df_hm = df_all[[hx, hy]].dropna()
            fig = px.density_heatmap(df_hm, x=hx, y=hy, marginal_x="histogram", marginal_y="histogram",
                                     title=f"Density Heatmap: {hx} vs {hy}",
                                     template=ctx.theme, text_auto=True)
            st.plotly_chart(fig)

    # --- 5. SANKEY FLOW ---
    elif mode == "Sankey Flow":
        c1, c2 = st.columns(2)
        if len(ctx.cat_cols) < 2:
            st.warning("Need at least 2 key categorical columns.")
        else:
            src = c1.selectbox("Source", ctx.cat_cols, index=0, key="sank_src")
            tgt = c2.selectbox("Target", ctx.cat_cols, index=1, key="sank_tgt")

            if st.button("🌊 Render Sankey"):
                st.session_state.eda_rel_sank_run = True

            if st.session_state.get("eda_rel_sank_run", False):
                if src == tgt:
                    st.warning("Select distinct columns.")
                else:
                    with st.spinner("Analyzing Flow..."):
                        # Use Parallel Categories
                        df_sank = df_all[[src, tgt]].dropna()
                        st.plotly_chart(px.parallel_categories(
                            df_sank, dimensions=[src, tgt], template=ctx.theme))

    # --- 6. PARALLEL COORDS ---
    elif mode == "Parallel Coords":
        dims = st.multiselect("Dimensions", ctx.num_cols, default=ctx.num_cols[:4] if len(
            ctx.num_cols) >= 4 else ctx.num_cols)
        c = st.selectbox("Color Scale", ctx.num_cols, index=0, key="par_c")

        if st.button("🎼 Render Parallel Coords"):
            st.session_state.eda_rel_par_run = True

        if st.session_state.get("eda_rel_par_run", False):
            if not dims:
                return

            cols_needed = list(dims)
            if c:
                cols_needed.append(c)
            # Dedup
            cols_needed = list(set(cols_needed))

            df_par = df_all[cols_needed].dropna()

            st.plotly_chart(px.parallel_coordinates(
                df_par, dimensions=dims, color=c, template=ctx.theme))
