import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .core import EDAContext


def render_simulation(ctx: EDAContext):
    """Render the Decision Simulator Tab with Enhanced Interpretability."""

    # 1. Setup
    df = ctx.get_pandas()
    if df is None:
        return

    engine = ctx.engine

    st.write("#### 🎛️ What-If Analysis & Decision Intelligence")
    st.caption(
        "Train a predictive digital twin to simulate outcomes and evaluate scenarios.")

    # 2. Config
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        # Allow Categorical Targets now (Classification)
        all_opts = ctx.num_cols + ctx.cat_cols
        # Try to find a good default
        def_idx = 0
        if len(all_opts) > 0:
            def_idx = 0

        sim_target = c1.selectbox(
            "Target Outcome", all_opts, index=def_idx, key="sim_tgt")

        # Drivers must be numeric for sliders currently
        avail_drivers = [c for c in ctx.num_cols if c != sim_target]
        sim_feats = c2.multiselect(
            "Driver Features (Numeric)", avail_drivers, default=avail_drivers[:5], key="sim_fts")

        model_type = c3.selectbox(
            "Model Type", ["Random Forest", "Linear Model"], key="sim_model_type")

        if st.button("🚀 TRAIN SIMULATOR", type="primary", width="stretch"):
            if not sim_feats:
                st.error("Select numeric driver features.")
            else:
                with st.spinner("Training Model..."):
                    # Delegate training to Backend
                    res = engine.analysis.ml.train_simulator_model(
                        df, sim_target, sim_feats, model_type)

                    if res and "error" not in res:
                        st.session_state['sim_model'] = res['model']
                        st.session_state['sim_feats'] = sim_feats
                        st.session_state['sim_X'] = res['X_sample']
                        st.session_state['sim_score'] = res.get('score', 0)
                        st.session_state['sim_metrics'] = res.get(
                            'metrics', {})
                        st.session_state['sim_is_cat'] = res.get(
                            'is_categorical', False)
                        st.session_state['sim_target'] = sim_target

                        # Train Explainer
                        explainer = engine.analysis.ml.train_surrogate_explainer(
                            res['model'], res['X_sample'])
                        st.session_state['sim_explainer'] = explainer
                        st.rerun()
                    else:
                        st.error(f"Train Error: {res.get('error')}")

    # 3. Simulator & Dashboard
    if 'sim_model' in st.session_state:
        # Consistency Check
        if st.session_state.get('sim_target') != sim_target:
            st.info("Target changed. Please retrain.")
            return

        st.divider()

        # Retrieve State
        model = st.session_state['sim_model']
        metrics = st.session_state.get('sim_metrics', {})
        is_cat = st.session_state.get('sim_is_cat', False)
        score = st.session_state.get('sim_score', 0)
        X_orig = st.session_state.get('sim_X')

        # --- A. PERFORMANCE DASHBOARD ---
        c_m1, c_m2, c_m3 = st.columns([1, 1, 2])

        metric_lbl = "Test Accuracy" if is_cat else "Test R² Score"
        c_m1.metric(metric_lbl, f"{score:.1%}" if is_cat else f"{score:.2f}",
                    delta="Good Fit" if score > 0.7 else "Weak Fit")

        if not is_cat and 'mae' in metrics:
            c_m2.metric(
                "MAE (Error)", f"{metrics['mae']:.2f}", help="Mean Absolute Error on Test Set")

        with st.expander("🔍 Model Diagnostics (Health Check)"):
            if is_cat and 'confusion_matrix' in metrics:
                cm = np.array(metrics['confusion_matrix'])
                if cm.size > 0:
                    try:
                        # Simple Heatmap
                        fig_cm = px.imshow(cm, text_auto=True, title="Confusion Matrix (Test Set)",
                                           labels=dict(x="Predicted Class", y="Actual Class"), color_continuous_scale="Blues")
                        st.plotly_chart(fig_cm)
                    except:
                        st.write("CM Plot Error")
            elif not is_cat and 'residuals' in metrics:
                # Plot Residuals
                resid = metrics.get('residuals', [])
                y_p = metrics.get('y_pred', [])
                y_t = metrics.get('y_test', [])

                if len(resid) > 0 and len(y_p) > 0:
                    c_d1, c_d2 = st.columns(2)

                    # Resids
                    fig_res = px.scatter(x=y_p, y=resid, labels={'x': "Predicted", 'y': "Residuals (Error)"},
                                         title="Residual Plot", template=ctx.theme, opacity=0.6)
                    fig_res.add_hline(y=0, line_dash="dash", line_color="red")
                    c_d1.plotly_chart(fig_res)

                    # Actual vs Pred
                    fig_avp = px.scatter(x=y_t, y=y_p, labels={'x': "Actual", 'y': "Predicted"},
                                         title="Actual vs Predicted", template=ctx.theme, opacity=0.6)
                    # Perfect line
                    min_v = min(min(y_t), min(y_p))
                    max_v = max(max(y_t), max(y_p))
                    fig_avp.add_shape(type="line", x0=min_v, y0=min_v, x1=max_v, y1=max_v, line=dict(
                        color="red", dash="dash"))
                    c_d2.plotly_chart(fig_avp)

        st.divider()

        # --- B. SIMULATION ---
        st.subheader("🔮 Scenario Simulator")

        c_sim, c_res = st.columns([1, 1.5])

        # 1. Inputs
        user_inputs = {}
        with c_sim.container(border=True):
            st.write("#### 🎛️ Scenario Manager")

            # Initialize Scenarios
            if 'sim_scenarios' not in st.session_state:
                st.session_state['sim_scenarios'] = {}

            # Save/Load
            scen_name = st.text_input(
                "Scenario Name", placeholder="e.g. Best Case")
            c_save, c_load = st.columns(2)

            if c_save.button("Save Scenario"):
                if scen_name:
                    # Note: We can't capture inputs here directly as they are generated below.
                    # Workaround: Use session state or previous run inputs.
                    # Better: Move Input Generation BEFORE this block?
                    # Actually, let's just render the inputs first, then put the manager below them?
                    pass
                else:
                    st.warning("Name required")

            st.divider()
            st.caption("Adjust Drivers (Levers)")
            # No reset button easily without callback, keep simple

            for feat in sim_feats:
                if X_orig is None or feat not in X_orig.columns:
                    continue

                min_v = float(X_orig[feat].min())
                max_v = float(X_orig[feat].max())
                mean_v = float(X_orig[feat].mean())

                # Prevent flat slider
                if min_v >= max_v:
                    min_v = mean_v - 1.0  # arbitrary
                    max_v = mean_v + 1.0

                step = (max_v - min_v) / 100 if (max_v - min_v) != 0 else 0.1

                user_inputs[feat] = st.slider(
                    f"{feat}", min_v, max_v, mean_v, step=step)

        # 2. Prediction
        # 2. Prediction & Analysis Modes
        with c_res:
            try:
                input_df = pd.DataFrame([user_inputs])
                # Ensure order and cols match training
                valid_cols = [c for c in sim_feats if c in user_inputs]
                input_df = input_df[valid_cols]  # Filter to known cols

                # A. INSTANT PREDICTION
                pred = model.predict(input_df)[0]

                st.write("##### Outcome Analysis")
                if is_cat:
                    st.metric("Predicted Class", f"{pred}")
                else:
                    st.metric(f"Predicted {sim_target}", f"{pred:,.2f}")

                # --- MODE SELECTION ---
                sim_mode = st.radio("Analysis Mode", ["Single Prediction", "Sensitivity (Tornado)", "Monte Carlo (Risk)"],
                                    horizontal=True, label_visibility="collapsed")
                st.divider()

                # --- MODE 1: SINGLE PREDICTION (Waterfall) ---
                if sim_mode == "Single Prediction":
                    explainer = st.session_state.get('sim_explainer')
                    if explainer and not is_cat:  # Waterfall makes most sense for Regression
                        contribs = engine.analysis.ml.get_prediction_contribution(
                            explainer, user_inputs)
                        if contribs:
                            top_c = contribs[:8]
                            wf_feats = [c['Feature'] for c in top_c]
                            wf_vals = [c['Contribution'] for c in top_c]

                            fig_wf = go.Figure(go.Waterfall(
                                orientation="v", measure=["relative"] * len(wf_vals),
                                x=wf_feats, y=wf_vals,
                                connector={
                                    "line": {"color": "rgb(63, 63, 63)"}}
                            ))
                            fig_wf.update_layout(
                                title="Feature Contribution (Why this result?)", height=350, template=ctx.theme)
                            st.plotly_chart(fig_wf)
                            st.caption(
                                "Shows how each input pushes the prediction UP (Green) or DOWN (Red) from the average.")

                # --- MODE 2: SENSITIVITY (Tornado) ---
                elif sim_mode == "Sensitivity (Tornado)":
                    st.caption(
                        "How much does the output change if we tweak each input?")

                    # Need feature stats for perturbation size
                    feat_stats = {}
                    if X_orig is not None:
                        for c in X_orig.columns:
                            feat_stats[c] = {'std': X_orig[c].std()}

                    sens_df = engine.analysis.ml.get_sensitivity(
                        model, user_inputs, feat_stats)

                    if not sens_df.empty:
                        # Tornado Plot
                        fig_tor = px.bar(sens_df, x="Spread", y="Feature", orientation='h',
                                         title=f"Sensitivity: Output Range (+/- 1 Std Dev)",
                                         template=ctx.theme, color="Spread")
                        st.plotly_chart(fig_tor)
                        st.info(
                            "Longer bars = This feature has a higher impact on the specific outcome.")

                # --- MODE 3: MONTE CARLO (Risk) ---
                elif sim_mode == "Monte Carlo (Risk)":
                    st.caption(
                        "Simulating 1,000 scenarios with random noise to estiamte uncertainty.")

                    # Stats for noise
                    feat_stats = {}
                    if X_orig is not None:
                        for c in X_orig.columns:
                            feat_stats[c] = {'std': X_orig[c].std()}

                    mc_res = engine.analysis.ml.run_monte_carlo(
                        model, user_inputs, feat_stats)
                    preds = mc_res['predictions']

                    fig_dist = px.histogram(preds, nbins=30, title="Probability Distribution of Outcome",
                                            labels={
                                                'value': f"Predicted {sim_target}"},
                                            template=ctx.theme, opacity=0.7)

                    # Add Confidence Intervals
                    p5, p95, mean_val = mc_res['p5'], mc_res['p95'], mc_res['mean']

                    fig_dist.add_vline(
                        x=mean_val, line_dash="dash", line_color="white", annotation_text="Exp. Value")
                    fig_dist.add_vrect(
                        x0=p5, x1=p95, fillcolor="green", opacity=0.1, annotation_text="90% Conf.")

                    st.plotly_chart(fig_dist)

                    c_r1, c_r2, c_r3 = st.columns(3)
                    c_r1.metric("Optimistic (95th)", f"{p95:,.2f}")
                    c_r2.metric("Expected", f"{mean_val:,.2f}")
                    c_r3.metric("Pessimistic (5th)", f"{p5:,.2f}")

            except Exception as e:
                st.error(f"Prediction Error: {e}")


def render_target_analysis(ctx: EDAContext):
    """Render Advanced Target Analysis Tab (Bivariate & Insights)"""

    # Ensure Data
    df = ctx.get_pandas()
    if df is None:
        return

    engine = ctx.engine

    # 1. Target Selection
    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        target = c1.selectbox("🎯 Target Variable",
                              ctx.all_cols, key="tgt_an_target")

        if not target:
            st.info("Select a target to analyze.")
            return

        # Detect Type
        is_num = target in ctx.num_cols
        t_type = "Numeric (Regression)" if is_num else "Categorical (Classification)"
        c2.info(f"Analysis Pattern: **{t_type}**")

    # 2. Analysis
    if st.button("Run Target Analysis", type="primary"):
        st.session_state.eda_tgt_run = True

    if st.session_state.get("eda_tgt_run", False):
        st.divider()

        # --- A. NUMERIC TARGET ---
        if is_num:
            # 1. Correlation Ranking
            with st.spinner("Calculating Correlations..."):
                corr_df = engine.analysis.stats.get_target_correlations(
                    df, target, ctx.num_cols
                )

            c_left, c_right = st.columns([1.2, 1])

            with c_left:
                st.subheader("📊 Driver Analysis (Correlation)")
                if not corr_df.empty:
                    # Color mapped by Correlation strength
                    fig_corr = px.bar(corr_df.head(10), x="Correlation", y="Feature",
                                      color="Correlation", orientation="h",
                                      color_continuous_scale="RdBu", range_color=[-1, 1],
                                      title=f"Top 10 Correlated Features with {target}",
                                      template=ctx.theme)
                    fig_corr.update_layout(height=400)
                    st.plotly_chart(fig_corr)
                    st.caption(
                        "Pearson Correlation (Linear Relationship). High absolute value = Strong relationship.")
                else:
                    st.warning("No significant numeric correlations found.")

            with c_right:
                st.subheader("🔎 Bivariate Deep Dive")

                # Default to top correlated feature
                defaults = [c for c in ctx.num_cols if c != target]
                def_idx = 0
                if not corr_df.empty:
                    top_f = corr_df.iloc[0]["Feature"]
                    if top_f in defaults:
                        def_idx = defaults.index(top_f)

                feat_x = st.selectbox(
                    "Compare Feature (X)", defaults, index=def_idx, key="tgt_scat_x")

                if feat_x:
                    # Scatter with Trend
                    fig_scat = px.scatter(df, x=feat_x, y=target,
                                          trendline="ols", trendline_color_override="red",
                                          opacity=0.6,
                                          title=f"{target} vs {feat_x}",
                                          template=ctx.theme)
                    st.plotly_chart(fig_scat)

            # 2. Categorical Impact (Box Plots)
            if ctx.cat_cols:
                st.divider()
                st.subheader("📦 Categorical Impact")
                cat_feat = st.selectbox(
                    "Group By Category", ctx.cat_cols, index=0, key="tgt_box_cat")

                if cat_feat:
                    # Sort logic? Order by median target?
                    fig_box = px.box(df, x=cat_feat, y=target, color=cat_feat,
                                     title=f"{target} Distribution by {cat_feat}",
                                     template=ctx.theme)
                    st.plotly_chart(fig_box)

        # --- B. CATEGORICAL TARGET ---
        else:
            # 1. Class Balance
            c_l, c_r = st.columns([1, 1.5])
            with c_l:
                st.subheader("🍰 Class Balance")
                counts = df[target].value_counts().reset_index()
                counts.columns = [target, "Count"]
                fig_pie = px.pie(counts, names=target, values="Count", hole=0.4,
                                 template=ctx.theme, title=f"{target} Proportions")
                st.plotly_chart(fig_pie)

            with c_r:
                st.subheader("📐 Feature Separation")
                st.caption("Does a numeric feature separate the classes?")

                feat_sep = st.selectbox(
                    "Inspect Feature", ctx.num_cols, key="tgt_sep_f")
                if feat_sep:
                    fig_sep = px.box(df, x=target, y=feat_sep, color=target,
                                     points="outliers",
                                     title=f"Distribution of {feat_sep} by Class",
                                     template=ctx.theme)
                    st.plotly_chart(fig_sep)

            # 2. Association (Chi-Square is ideal, but let's stick to Crosstabs heatmap)
            if len(ctx.cat_cols) > 1:
                st.divider()
                st.subheader("🔗 Categorical Association")
                cat_assoc = st.selectbox(
                    "Cross-Tab Feature", [c for c in ctx.cat_cols if c != target], key="tgt_ct")

                if cat_assoc:
                    # Heatmap of counts (or Normalized Pct?)
                    ct = pd.crosstab(df[target], df[cat_assoc],
                                     normalize='index')  # Row pct

                    fig_hm = px.imshow(ct, text_auto=".1%", aspect="auto",  # type: ignore
                                       labels=dict(
                                           x=cat_assoc, y=target, color="Pct"),
                                       title=f"Normalized Association (Row %): {target} vs {cat_assoc}",
                                       template=ctx.theme)
                    st.plotly_chart(fig_hm)
                    st.caption(
                        "Values show: Given the Target Class (Row), what % fall into the Feature Category (Col)?")

        # --- C. ADVANCED: PDP (Model-Based) ---
        with st.expander("🤖 Advanced: Partial Dependence (PDP)"):
            st.caption(
                "Model-independent view of how a feature affects the target based on a simplistic estimator.")

            pdp_opts = [c for c in ctx.num_cols if c != target]
            pdp_f = st.selectbox("Select Feature for PDP",
                                 pdp_opts, key="tgt_pdp_f")

            if st.button("Run PDP Calculation"):
                with st.spinner("Calculating PDP..."):
                    res = engine.analysis.ml.get_partial_dependence(
                        df, target, pdp_f)
                    if "x" in res:
                        fig_pdp = px.line(x=res['x'], y=res['y'], markers=True,
                                          labels={'x': pdp_f,
                                                  'y': f"Predicted {target}"},
                                          title=f"Partial Dependence Plot: {pdp_f}")
                        st.plotly_chart(fig_pdp)
                    else:
                        st.warning(
                            "PDP Failed (possibly due to data type or model constraints).")
