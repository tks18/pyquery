import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from pyquery_polars.frontend.components.eda.core import EDAContext


def render_profiling(ctx: EDAContext):
    """Render the Enhanced Data Profiling Tab (Deep Dive 2.0)"""

    st.caption(
        "Deep inspection of column distributions, correlations, and semantic types.")

    df = ctx.get_pandas()
    if df is None:
        return

    engine = ctx.engine

    # --- 1. QUICK SCAN (Summary) ---
    with st.expander("⚡ Dataset Health Scan", expanded=True):
        # Optimized summary
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
        st.dataframe(pd.DataFrame(summary_data),
                     hide_index=True)

    # --- 2. SELECT COLUMN ---
    col_type = st.radio("Column Type", [
                        "Numeric", "Categorical / Text"], horizontal=True, key="prof_type")
    target_cols = ctx.num_cols if col_type == "Numeric" else ctx.cat_cols

    if not target_cols:
        st.info("No columns found.")
        return

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
            # CALL BACKEND (Advanced)
            stats = engine.analytics.stats.get_advanced_profile(df, col)
            if "error" in stats:
                st.error(stats['error'])
                return
            st.session_state[session_key] = stats
            st.session_state[param_key] = current_params

    elif session_key in st.session_state and st.session_state.get(param_key) == current_params:
        stats = st.session_state[session_key]

    if stats:
        # --- TABS FOR ORGANIZED ANALYSIS ---
        tab_sum, tab_dist, tab_corr, tab_sem = st.tabs([
            "📊 Summary", "📈 Distribution", "🔗 Correlations", "🧠 Semantics"
        ])

        # 1. SUMMARY TAB
        with tab_sum:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Count", f"{stats.get('count', 0):,}")
            c2.metric("Missing", f"{stats.get('missing_p', 0):.1%}")
            c3.metric("Unique", f"{stats.get('unique', 0):,}")
            c4.metric("Dtype", stats.get('dtype', 'N/A'))

            st.divider()

            # Numeric Specifics
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
                # Categorical Specifics
                cc1, cc2 = st.columns(2)
                cc1.metric("Mode", str(stats.get('mode', 'N/A')))
                cc2.metric("Rare Values", stats.get('rare_count', 0))

        # 2. DISTRIBUTION TAB
        with tab_dist:
            if stats.get('type') == 'Numeric':
                # Boxen Plot (Letter-value plot) for detailed tails
                fig_boxen = px.box(df, y=col, points="outliers", notched=True,
                                   title=f"Distribution: {col} (Box Plot)", template=ctx.theme)
                st.plotly_chart(fig_boxen)

                # Histogram + KDE
                fig_hist = px.histogram(df, x=col, marginal="box", opacity=0.7,
                                        title="Histogram & Density", template=ctx.theme)
                st.plotly_chart(fig_hist)

            else:
                # Categorical Tree Map
                top_counts = stats.get('top_counts', {})
                if top_counts:
                    tdf = pd.DataFrame(list(top_counts.items()), columns=[
                                       "Category", "Count"])
                    fig_tree = px.treemap(tdf, path=["Category"], values="Count",
                                          title=f"Top Categories in {col}", template=ctx.theme)
                    st.plotly_chart(fig_tree)

                    st.caption("Top 10 Values Table")
                    st.dataframe(tdf, hide_index=True)

        # 3. CORRELATIONS TAB (Numeric Only)
        with tab_corr:
            if stats.get('type') == 'Numeric':
                corrs = stats.get('correlations', {})
                if corrs:
                    cdf = pd.DataFrame(list(corrs.items()), columns=[
                                       "Feature", "Correlation"])
                    fig_corr = px.bar(cdf, x="Correlation", y="Feature", orientation='h',
                                      title=f"Top Correlated Features with {col}", template=ctx.theme,
                                      color="Correlation", range_x=[-1, 1], color_continuous_scale="RdBu")
                    st.plotly_chart(fig_corr)
                else:
                    st.info(
                        "No significant numeric correlations found or only one numeric column exists.")
            else:
                st.info("Correlation analysis is strictly for numeric relationships here. Check 'Relationships' tab for categorical association (Cramer's V).")

        # 4. SEMANTICS TAB (Text Only)
        with tab_sem:
            if stats.get('type') == 'Categorical':
                patterns = stats.get('semantic_entities', {})
                if patterns:
                    st.success(f"💡 Detected semantic entities in this column!")
                    pdf = pd.DataFrame(list(patterns.items()), columns=[
                                       "Entity Type", "Matches"])
                    fig_sem = px.pie(pdf, names="Entity Type", values="Matches", hole=0.4,
                                     title="Detected Entity Types", template=ctx.theme)
                    st.plotly_chart(fig_sem)
                else:
                    st.info(
                        "No specific semantic entities (Email, IP, Date, etc.) detected via regex.")

                # String Length Stats
                st.write("###### String Length Stats")
                c_l1, c_l2, c_l3 = st.columns(3)
                c_l1.metric("Min Len", stats.get('len_min', 0))
                c_l2.metric("Max Len", stats.get('len_max', 0))
                c_l3.metric("Avg Len", f"{stats.get('len_avg', 0):.1f}")
            else:
                st.info("Semantic analysis is for Text/Categorical columns.")
