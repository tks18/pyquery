import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from .core import EDAContext


def render_contrast(ctx: EDAContext):
    """Render the Enhanced Comparative Analysis (Contrast 2.0)"""

    st.caption(
        "Rigorous statistical comparison of two cohorts (Hypothesis Testing & Effect Sizes).")

    df = ctx.get_pandas()

    # CONTROL PANEL
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)

        valid_groups = [c for c in ctx.cat_cols if df[c].nunique() < 30]
        if not valid_groups:
            st.warning("No suitable grouping columns (<30 unique).")
            return

        group_col = c1.selectbox("Split By", valid_groups, key="ct_grp")
        uniques = sorted(df[group_col].dropna().unique().tolist())

        if len(uniques) < 2:
            st.warning("Group has <2 values.")
            return

        val_a = c2.selectbox("Group A", uniques, index=0, key="ct_a")
        val_b = c3.selectbox("Group B", uniques, index=1 if len(
            uniques) > 1 else 0, key="ct_b")

    if val_a == val_b:
        st.error("Select different groups.")
        return

    # SETTINGS
    with st.expander("⚙️ Statistical Settings"):
        p_threshold = st.slider(
            "Significance Threshold (P-Value)", 0.01, 0.10, 0.05, 0.01)
        test_type = st.radio("Numeric Test Type", [
                             "Mann-Whitney U (Non-Parametric)", "T-Test (Parametric)"], horizontal=True)
        use_mw = "Mann" in test_type

    # Persist Results
    session_key = "contrast_stats"
    param_key = "contrast_params"

    current_params = {
        "group_col": group_col, "val_a": val_a, "val_b": val_b,
        "test_type": test_type, "p_threshold": p_threshold,
        "df_hash": str(df.shape)
    }

    run_clicked = st.button("⚖️ Run Comparison", type="primary")
    stats = None

    if run_clicked:
        with st.spinner("Calculating Hypothesis Tests..."):
            engine = ctx.engine
            # Backend Call
            stats = engine.analysis.stats.get_comparative_stats(
                df, group_col, val_a, val_b, ctx.num_cols, ctx.cat_cols
            )
            st.session_state[session_key] = stats
            st.session_state[param_key] = current_params

    elif session_key in st.session_state and st.session_state.get(param_key) == current_params:
        stats = st.session_state[session_key]

    if stats is not None:
        if stats.empty:
            st.warning("No results.")
            return

        # Determine P-Value column based on user choice
        p_col = "P_Value_MW" if use_mw else "P_Value_TT"

        # Create Flag for Significance
        stats['Significant'] = stats[p_col] < p_threshold
        stats['LogP'] = - \
            np.log10(stats[p_col].replace(0, 1e-10))  # Avoid inf

        # --- VOLCANO PLOT (Effect Size vs Significance) ---
        st.subheader("🌋 Volcano Plot: Impact vs. Reliability")
        st.caption(
            f"Visualizing Effect Size (Magnitude) vs Significance (Statistical Confidence). Threshold P < {p_threshold}")

        # Color points: Significant & Large Effect vs Others
        # Heuristic for "Large Effect": Cohen's D > 0.5 or Cramer's V > 0.3
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
                                 "LogP": "-Log10(P-Value)", "Effect_Size": "Effect Size (Cohen's D / Cramer's V)"},
                             template=ctx.theme,
                             color_discrete_map={'Insignificant': 'gray', 'Significant': 'orange', 'High Impact': 'red'})
        fig_vol.add_hline(y=-np.log10(p_threshold), line_dash="dash",
                          line_color="green", annotation_text=f"P={p_threshold}")
        fig_vol.update_traces(textposition='top center')
        st.plotly_chart(fig_vol)

        st.divider()

        # --- DEEP DIVE (RAINCLOUD) ---
        st.subheader("🌧️ Feature Raincloud")

        # Select feature from significant ones if possible
        sig_feats = stats[stats['Significant']]['Feature'].tolist()
        opts = sig_feats if sig_feats else stats['Feature'].tolist()

        feat_insp = st.selectbox(
            "Inspect Feature Detail", opts, key="ct_insp")

        if feat_insp:
            row = stats[stats['Feature'] == feat_insp].iloc[0]
            is_num = row['Type'] == 'Numeric'

            # Metrics header
            m1, m2, m3 = st.columns(3)
            m1.metric("Effect Size", f"{row['Effect_Size']:.3f}")
            m2.metric(
                "P-Value", f"{row[p_col]:.2e}", delta="Significant" if row['Significant'] else "Not Sig")
            m3.metric("Difference", row['Desc'])

            # Viz
            sub_df = df[df[group_col].isin([val_a, val_b])]

            if is_num:
                # RAINCLOUD PLOT (Half Violin + Box + Strip)
                # Plotly doesn't have native "Raincloud", but we can combine Violin + Box + Scatter
                # Actually, simple Box + Points is very effective and cleaner
                fig_rain = px.violin(sub_df, x=group_col, y=feat_insp, color=group_col,
                                     box=True, points="all",  # Points="all" makes it a raincloud-like strip
                                     title=f"Distribution: {feat_insp} by Cohort",
                                     template=ctx.theme)
                st.plotly_chart(fig_rain)
            else:
                # Categorical Bar Comparison
                # Stacked 100% Bar
                ct = pd.crosstab(
                    sub_df[group_col], sub_df[feat_insp], normalize='index').reset_index()
                fig_bar = px.bar(ct, x=group_col, y=ct.columns[1:], barmode="stack",
                                 title=f"Proportions: {feat_insp}", template=ctx.theme)
                st.plotly_chart(fig_bar)

        st.dataframe(stats[['Feature', 'Type', 'Effect_Size', p_col,
                            'Desc', 'Significant']])
