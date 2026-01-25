import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pyquery_polars.frontend.components.eda.core import EDAContext

HAS_SKLEARN = True


def render_ml(ctx: EDAContext):
    """Render the Decision ML Tab (Diagnostic, Clustering, Anomalies)"""

    df = ctx.get_pandas()
    if df is None:
        return

    engine = ctx.engine

    if not HAS_SKLEARN:
        st.warning("⚠️ Scikit-Learn not installed.")
        return

    # Modern Layout
    with st.container(border=True):
        mode_ml = st.radio("Intelligence Module", [
            "Diagnostic Model Sandbox", "Advanced Clustering", "Explainable Anomalies"], horizontal=True, label_visibility="collapsed")

    if len(ctx.num_cols) < 2 and mode_ml not in ["Explainable Anomalies"]:
        st.warning("Need features to run ML.")
        return

    # ==========================================
    # A. DIAGNOSTIC SANDBOX
    # ==========================================
    if mode_ml == "Diagnostic Model Sandbox":
        st.write("#### 🧪 Robust Modeling & Calibration")
        st.caption(
            "Train interpretable models to understand relationships and performance.")

        c1, c2, c3 = st.columns([1, 1, 2])
        target = c1.selectbox("Target Variable", ctx.all_cols, key="qm_target")
        model_type = c2.selectbox("Model Type", ["Linear Regression (OLS)", "Ridge (L2)", "Lasso (L1)",
                                                 "Logistic Regression", "Random Forest", "Auto-Pilot (Best Model)"], key="qm_type")

        # Smart defaults
        def_chk = [c for c in (ctx.num_cols[:5] if len(
            ctx.num_cols) >= 5 else ctx.num_cols) if c != target]
        feats = c3.multiselect("Features", [
                               c for c in ctx.all_cols if c != target], default=def_chk, key="qm_feats")

        with st.expander("⚙️ hyper-parameters"):
            use_poly = st.checkbox("Enable Interaction Effects (Polynomial Features)",
                                   help="Captures non-linear relationships (e.g. A*B). Can increase overfit risk.")

        # Persistence Key
        session_key = "ml_results"
        param_key = "ml_params"

        # Define is_cat globally for this run (needed for rendering)
        is_cat = target in ctx.cat_cols or df[target].nunique() < 10

        # Check if we should use cached results or run new
        run_clicked = st.button("RUN DECISION MODEL", type="primary")

        res = None

        # Current Params for cache validation
        current_params = {
            "target": target,
            "feats": feats,
            "model_type": model_type,
            "poly": use_poly,
            "df_shape": df.shape
        }

        if run_clicked:
            if not feats:
                st.error("Select features.")
                return
            else:
                with st.spinner("Training & Calibrating Model..."):
                    # --- BACKEND CALL ---
                    res = engine.analytics.ml.run_diagnostic_model(
                        df, target, feats, model_type, is_cat, use_poly)

                    # Cache Results
                    st.session_state[session_key] = res
                    st.session_state[param_key] = current_params

        elif session_key in st.session_state and st.session_state.get(param_key) == current_params:
            # Load from Cache if params haven't changed
            res = st.session_state[session_key]

        # Render if we have results (either new or cached)
        # Render if we have results (either new or cached)
        if res:
            if "error" in res:
                st.error(res['error'])
                return

            best_model = res.get('model_obj')
            best_score = res.get('best_score', 0)
            best_name = res.get('model_name', "Unknown")
            metrics = res.get('metrics', {})
            diagnostics = res.get('diagnostics', {})

            # Datasets
            X_test = res.get('X_test')
            y_test = res.get('y_test')
            y_pred = res.get('y_pred')

            if best_model is None or y_test is None or y_pred is None:
                st.error("Model returned incomplete results.")
                return

            # Results Layout
            st.divider()

            # 1. Headline Metrics
            c_s1, c_s2, c_s3, c_s4 = st.columns(4)
            c_s1.metric("Model Selected", best_name)

            score_label = "Accuracy" if is_cat else "R² Score"
            c_s2.metric(f"Test {score_label}", f"{best_score:.3f}",
                        delta="Strong" if best_score > 0.7 else "Weak", delta_color="normal")

            if not is_cat:
                c_s3.metric("MAE", f"{metrics.get('mae', 0):.2f}")

            st.divider()

            # 2. Deep Dive Tabs
            tabs = st.tabs([
                "📊 Performance Stats",
                "👁️ Explainability (PDP)",
                "📉 Learning Curves",
                "🧠 Residuals/Errors"
            ])

            # Tab 1: Performance (ROC / Lift / Confusion / Actual vs Pred)
            with tabs[0]:
                c_p1, c_p2 = st.columns(2)
                if is_cat:
                    # A. Confusion Matrix
                    cm = metrics.get('confusion_matrix')
                    if cm is not None:
                        c_p1.plotly_chart(px.imshow(cm, text_auto=True, title="Confusion Matrix",
                                                    color_continuous_scale="Blues", template=ctx.theme))

                    # B. Probability Separation Plot
                    if hasattr(best_model, "predict_proba"):
                        y_probs = best_model.predict_proba(X_test)
                        # Assuming binary for simple separation plot
                        if y_probs.shape[1] == 2:
                            prob_pos = y_probs[:, 1]
                            sep_df = pd.DataFrame(
                                {'Probability': prob_pos, 'Truth': y_test})
                            fig_sep = px.histogram(sep_df, x="Probability", color="Truth", barmode="overlay",
                                                   title="Separation Plot (Predicted Probabilities)", template=ctx.theme, opacity=0.6)
                            c_p2.plotly_chart(fig_sep)

                            # C. Lift Chart / ROC
                            # ROC (already computed)
                            if 'roc' in diagnostics and diagnostics['roc']:
                                roc = diagnostics['roc']
                                fig_roc = px.area(x=roc['fpr'], y=roc['tpr'], title=f"ROC Curve (AUC={roc['auc']:.2f})",
                                                  labels={'x': 'False Positive Rate', 'y': 'True Positive Rate'}, template=ctx.theme)
                                fig_roc.add_shape(type='line', line=dict(
                                    dash='dash'), x0=0, x1=1, y0=0, y1=1)
                                st.plotly_chart(fig_roc)

                else:
                    # Regression Performance
                    # A. Actual vs Predicted (Identity Plot)
                    df_res = pd.DataFrame(
                        {'Actual': y_test, 'Predicted': y_pred})
                    fig_avp = px.scatter(df_res, x="Actual", y="Predicted", trendline="ols",
                                         title="Prediction Error Plot", template=ctx.theme, opacity=0.6)
                    # Add Identity Line
                    min_val = min(y_test.min(), y_pred.min())
                    max_val = max(y_test.max(), y_pred.max())
                    fig_avp.add_shape(type="line", x0=min_val, y0=min_val, x1=max_val, y1=max_val,
                                      line=dict(color="Red", dash="dash"))
                    c_p1.plotly_chart(fig_avp)

                    # B. Error Distribution
                    errors = y_test - y_pred
                    fig_err = px.histogram(
                        errors, title="Error Distribution", template=ctx.theme)
                    c_p2.plotly_chart(fig_err)

            # Tab 2: Explainability (PDP & Importance)
            with tabs[1]:
                st.caption("Understand HOW features affect the prediction.")

                # 1. Permutation Importance
                imp_vals = engine.analytics.ml.get_permutation_importance(
                    best_model, X_test, y_test)
                feat_names = res.get('train_cols', feats)
                df_imp = pd.DataFrame({'Feature': feat_names, 'Importance': imp_vals}).sort_values(
                    'Importance', ascending=True)

                c_ex1, c_ex2 = st.columns([1, 2])

                fig_imp = px.bar(df_imp, x='Importance', y='Feature', orientation='h',
                                 title="Global Feature Importance", template=ctx.theme)
                c_ex1.plotly_chart(fig_imp)

                # 2. Partial Dependence Plot (Interactive)
                with c_ex2:
                    pdp_feat = st.selectbox(
                        "View Effect of Feature:", feats, key="pdp_sel")
                    if pdp_feat:
                        pdp_data = engine.analytics.ml.get_partial_dependence(
                            df, target, pdp_feat, feats)
                        if 'x' in pdp_data:
                            fig_pdp = px.line(x=pdp_data['x'], y=pdp_data['y'], markers=True,
                                              title=f"Partial Dependence: Effect of '{pdp_feat}' on Target",
                                              labels={'x': pdp_feat, 'y': f"Expected {target}"}, template=ctx.theme)
                            st.plotly_chart(fig_pdp)
                        else:
                            st.warning(
                                "Could not calculate PDP for this feature.")

            # Tab 3: Learning Curves
            with tabs[2]:
                lc = diagnostics.get('learning_curve')
                if lc:
                    df_lc = pd.DataFrame({
                        "Training Size": lc['train_sizes'],
                        "Training Score": lc['train_mean'],
                        "Validation Score": lc['test_mean']
                    })
                    df_lc_melt = df_lc.melt(
                        "Training Size", var_name="Metric", value_name="Score")
                    fig_lc = px.line(df_lc_melt, x="Training Size", y="Score", color="Metric", markers=True,
                                     title="Learning Curve (Bias vs Variance Diagnosis)", template=ctx.theme)
                    st.plotly_chart(fig_lc)
                    st.info(
                        "Large gap = Overfitting (needs more data/regularization). Low scores = Underfitting (needs more complex model).")
                else:
                    st.info("Learning curve data unavailable.")

            # Tab 4: Residuals
            with tabs[3]:
                if not is_cat:
                    r = diagnostics.get('residuals')
                    p = diagnostics.get('predicted')
                    fig_res = px.scatter(x=p, y=r, labels={'x': 'Predicted', 'y': 'Residuals'},
                                         title="Residual Plot (Check for Heteroscedasticity)", template=ctx.theme)
                    fig_res.add_hline(y=0, line_dash="dash")
                    st.plotly_chart(fig_res)
                else:
                    st.info("Residual analysis is best suited for regression.")

    # ==========================================
    # B. ADVANCED CLUSTERING (OPTIMIZED)
    # ==========================================
    elif mode_ml == "Advanced Clustering":
        st.write("#### 🧬 Unsupervised Pattern Detection")
        st.caption("Group similar data points and discover segments.")

        c1, c2, c3 = st.columns(3)
        c_feats = c1.multiselect(
            "Features", ctx.num_cols, default=ctx.num_cols[:3], key="cl_feats")
        n_k = c2.slider("Clusters (K)", 2, 10, 3, key="cl_k")
        algo = c3.selectbox("Algorithm", ["K-Means", "DBSCAN"], key="cl_algo")

        # ACTION BAR
        col_run, col_opt = st.columns([1, 1])
        run_clustering = col_run.button("RUN CLUSTERING", type="primary")
        find_optimal = col_opt.button(
            "Find Optimal K (Elbow)", type="secondary")

        if find_optimal and c_feats:
            with st.spinner("Scanning ideal cluster count..."):
                res = engine.analytics.ml.cluster_data(
                    df, c_feats, n_k, algo, optimize_k=True)
                elbow = res.get('elbow_data')
                if elbow:
                    fig_elb = px.line(x=elbow['k'], y=elbow['inertia'], markers=True,
                                      title="Elbow Method: Optimal K", labels={'x': 'K (Clusters)', 'y': 'Inertia (SSE)'},
                                      template=ctx.theme)
                    st.plotly_chart(fig_elb)
                    st.success(
                        "Look for the 'elbow' point where inertia reduction slows down.")

        if run_clustering and c_feats:
            with st.spinner("Clustering..."):
                res = engine.analytics.ml.cluster_data(
                    df, c_feats, n_k, algo, optimize_k=False)
                if "error" in res:
                    st.error(res["error"])
                    return

                res_df = res['df']
                labels = res['labels']
                sil = res['silhouette_score']
                centroids = res.get('centroids', {})

                c1, c2 = st.columns(2)
                c1.metric("Silhouette Score", f"{sil:.3f}")
                c2.caption("Clustering Quality (1.0 = Perfect separation)")

                tabs = st.tabs(["Space Projection (PCA)",
                               "Cluster DNA (Radar)", "Silhouette Analysis"])

                # Tab 1: PCA
                with tabs[0]:
                    fig_pca = px.scatter(res_df, x='PCA1', y='PCA2', color='Cluster',
                                         title=f"2D Projection ({algo})", template=ctx.theme,
                                         hover_data=c_feats)
                    st.plotly_chart(fig_pca)

                # Tab 2: Radar DNA
                with tabs[1]:
                    if centroids:
                        categories = list(
                            centroids[list(centroids.keys())[0]].keys())
                        fig_rad = go.Figure()
                        for cluster_id, feats_vals in centroids.items():
                            vals = list(feats_vals.values())
                            vals += [vals[0]]
                            cats = categories + [categories[0]]
                            fig_rad.add_trace(go.Scatterpolar(
                                r=vals, theta=cats, fill='toself', name=f"Cluster {cluster_id}"
                            ))
                        fig_rad.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[
                                       0, max([max(v.values()) for v in centroids.values()])])),
                            title="Cluster Centroid Signatures", template=ctx.theme
                        )
                        st.plotly_chart(fig_rad)

                # Tab 3: Silhouette Analysis
                with tabs[2]:
                    sil_data = engine.analytics.ml.get_silhouette_samples(
                        df, c_feats, labels)
                    if sil_data and 'scores' in sil_data:
                        scores = sil_data['scores']
                        # Create Knife Plot DF
                        k_df = pd.DataFrame(
                            {'Score': scores, 'Cluster': labels})
                        k_df = k_df.sort_values(['Cluster', 'Score'])
                        k_df['Sample'] = range(len(k_df))

                        fig_knife = px.bar(k_df, x="Sample", y="Score", color="Cluster",
                                           title="Silhouette 'Knife' Plot (Sample Cohesion)",
                                           template=ctx.theme)
                        fig_knife.add_hline(
                            y=sil, line_dash="dash", annotation_text="Avg Score")
                        st.plotly_chart(fig_knife)
                        st.caption(
                            "Bars above avg are well-clustered. Negative bars might be misclassified.")

                st.dataframe(res_df.head(100))

    # ==========================================
    # C. ANOMALIES
    # ==========================================
    elif mode_ml == "Explainable Anomalies":
        st.write("#### 🛡️ Anomaly Detection")
        st.caption("Indentify outliers using Isolation Forests.")

        c1, c2 = st.columns(2)
        anom_feats = c1.multiselect(
            "Features", ctx.num_cols, default=ctx.num_cols, key="anom_feats")
        contam = c2.slider("Contamination", 0.01, 0.2, 0.05, key="anom_cont")

        if st.button("SCAN FOR OUTLIERS", type="primary"):
            if not anom_feats:
                st.error("Select features.")
                return

            res = engine.analytics.ml.detect_anomalies(df, anom_feats, contam)
            if "error" in res:
                st.error(res['error'])
                return

            outliers = res['outliers']

            st.metric("Outliers Detected", len(outliers),
                      f"{len(outliers)/len(df):.1%}")
            st.dataframe(outliers.head(50))
