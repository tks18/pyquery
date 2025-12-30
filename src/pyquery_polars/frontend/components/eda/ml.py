import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import cast, Any
from .core import EDAContext

# Since we don't depend on sklearn directly in frontend, we don't import it unless for local safe plotting if needed.
HAS_SKLEARN = True


def render_ml(ctx: EDAContext):
    """Render the Decision ML Tab (Diagnostic, Clustering, Anomalies)"""

    if ctx.df is None:
        try:
            df = ctx.lf.collect().to_pandas()
        except:
            return
    else:
        df = ctx.df

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

        def_chk = [c for c in (ctx.num_cols[:5] if len(
            ctx.num_cols) >= 5 else ctx.num_cols) if c != target]
        feats = c3.multiselect("Features", [
                               c for c in ctx.all_cols if c != target], default=def_chk, key="qm_feats")

        if st.button("RUN DECISION MODEL", type="primary"):
            if not feats:
                st.error("Select features.")
            else:
                with st.spinner("Executing Analysis..."):
                    try:
                        # Define is_cat for backend hint
                        is_cat = target in ctx.cat_cols or df[target].nunique(
                        ) < 10

                        # --- BACKEND CALL ---
                        res = engine.analysis.ml.run_diagnostic_model(
                            df, target, feats, model_type, is_cat)

                        if "error" in res:
                            st.error(res['error'])
                            return

                        best_model = res.get('model_obj')
                        best_score = res.get('best_score', 0)
                        best_name = res.get('model_name', "Unknown")
                        metrics = res.get('metrics', {})
                        X_test = res.get('X_test')
                        y_test = res.get('y_test')

                        # 1. High Level Summary
                        st.divider()
                        c_s1, c_s2, c_s3 = st.columns(3)
                        c_s1.metric("Model Selected", best_name)
                        c_s2.metric("Test Score", f"{best_score:.3f}",
                                    delta="Strong" if best_score > 0.7 else "Weak", delta_color="normal")

                        tabs = st.tabs(
                            ["📊 Diagnostic Plots", "🔑 Feature Importance", "🧠 Model Logic"])

                        # Tab 1: Diagnostics
                        with tabs[0]:
                            c_d1, c_d2 = st.columns(2)
                            if is_cat:
                                # A. Confusion Matrix
                                cm = metrics.get('confusion_matrix')
                                if cm is not None:
                                    c_d1.plotly_chart(px.imshow(cm, text_auto=True, title="Confusion Matrix",
                                                                color_continuous_scale="Blues", template=ctx.theme))

                                # B. ROC / Calibration
                                if best_model and hasattr(best_model, "predict_proba"):
                                    # ROC
                                    roc_data = engine.analysis.ml.get_classification_curves(
                                        best_model, X_test, y_test)
                                    if 'roc' in roc_data:
                                        rd = roc_data['roc']
                                        fig_roc = px.area(x=rd['fpr'], y=rd['tpr'], title=f"ROC Curve (AUC={rd['auc']:.3f})",
                                                          labels={'x': 'False Positive Rate', 'y': 'True Positive Rate'}, template=ctx.theme)
                                        fig_roc.add_shape(type='line', line=dict(
                                            dash='dash'), x0=0, x1=1, y0=0, y1=1)
                                        c_d2.plotly_chart(
                                            fig_roc)
                            else:
                                # A. Fitted vs Actual
                                y_pred = res.get('y_pred')
                                if y_pred is not None:
                                    fig_pred = px.scatter(x=y_test, y=y_pred, labels={'x': "Actual", 'y': "Predicted"},
                                                          title="Actual vs Predicted", template=ctx.theme, opacity=0.6)
                                    if y_pred is not None and y_test is not None:
                                        fig_pred.add_shape(type='line', line=dict(dash='dash', color='red'),
                                                           x0=y_test.min(), x1=y_test.max(), y0=y_test.min(), y1=y_test.max())
                                    c_d1.plotly_chart(
                                        fig_pred)

                                # B. Residuals
                                resid = metrics.get('residuals')
                                if resid is not None:
                                    fig_res = px.histogram(
                                        resid, nbins=30, title="Residuals Distribution", template=ctx.theme)
                                    c_d2.plotly_chart(
                                        fig_res)

                        # Tab 2: Importance
                        with tabs[1]:
                            importances = engine.analysis.ml.get_permutation_importance(
                                best_model, X_test, y_test)
                            if len(importances) == len(feats):
                                perm_df = pd.DataFrame({'Feature': feats, 'Importance': importances}).sort_values(
                                    'Importance', ascending=True)
                                fig_perm = px.bar(perm_df, x='Importance', y='Feature', orientation='h',
                                                  title="Permutation Importance (Model Agnostic)", template=ctx.theme)
                                st.plotly_chart(
                                    fig_perm)

                        # Tab 3: Model Logic (Coefficients)
                        with tabs[2]:
                            if best_model is not None and hasattr(best_model, "coef_"):
                                st.write(
                                    "###### Interpretation (Linear Weights)")
                                coefs = best_model.coef_
                                if len(coefs.shape) > 1:
                                    # Handle multiclass or weird shape
                                    coefs = coefs[0]
                                coef_df = pd.DataFrame({"Feature": feats, "Weight": coefs}).sort_values(
                                    "Weight", ascending=False)
                                st.dataframe(
                                    coef_df, hide_index=True)
                            else:
                                st.info(
                                    "Tree-based models are non-parametric (no simple coefficients). See Feature Importance.")

                    except Exception as e:
                        st.error(f"Error: {e}")

    # ==========================================
    # B. ADVANCED CLUSTERING
    # ==========================================
    elif mode_ml == "Advanced Clustering":
        st.write("#### 🧬 Clustering Laboratory")

        c1, c2 = st.columns([1, 3])
        algo = c1.selectbox("Algorithm", ["K-Means", "DBSCAN"])
        feats = c2.multiselect("Features", ctx.num_cols, default=ctx.num_cols[:4] if len(
            ctx.num_cols) >= 4 else ctx.num_cols)

        # Optimization Expander
        with st.expander("🔎 Determine Optimal Clusters (Elbow Method)"):
            if st.button("Analyze Optimal K"):
                with st.spinner(" optimizing..."):
                    opt = engine.analysis.ml.get_clustering_optimization(
                        df, feats)
                    if opt and 'k' in opt:
                        c_opt1, c_opt2 = st.columns(2)
                        # Elbow
                        fig_elb = px.line(x=opt['k'], y=opt['wcss'], markers=True, title="Elbow Method (Inertia)",
                                          labels={'x': 'K (Clusters)', 'y': 'Inertia'}, template=ctx.theme)
                        c_opt1.plotly_chart(fig_elb)
                        # Silhouette
                        fig_sil = px.line(x=opt['k'], y=opt['silhouette'], markers=True, title="Silhouette Score (Higher is Better)",
                                          labels={'x': 'K (Clusters)', 'y': 'Silhouette'}, template=ctx.theme)
                        c_opt2.plotly_chart(fig_sil)

        st.divider()

        c_k, c_u = st.columns([1, 4])
        k = 3
        if algo == "K-Means":
            k = c_k.slider("Number of Clusters (K)", 2, 10, 3)

        if c_u.button("RUN CLUSTERING", type="primary"):
            with st.spinner("Running Clustering..."):
                res = engine.analysis.ml.cluster_data(
                    df, feats, n_clusters=k, algo=algo)

                if res and "error" not in res:
                    df_clus = res['df']
                    sil_score = res.get('silhouette_score', -1)

                    st.metric("Cluster Quality (Silhouette)",
                              f"{sil_score:.3f}", delta="Good" if sil_score > 0.5 else "Weak")

                    if df_clus is not None:
                        # 1. Projection
                        c_p1, c_p2 = st.columns([2, 1])
                        if 'PCA1' in df_clus.columns:
                            c_p1.plotly_chart(px.scatter(df_clus, x='PCA1', y='PCA2', color='Cluster',
                                                         title="2D Cluster Map (PCA)", template=ctx.theme, opacity=0.7))
                        c_p2.plotly_chart(px.pie(
                            df_clus, names='Cluster', title="Cluster Size Distribution", template=ctx.theme))

                        # 2. Profiling
                        st.subheader("🧬 Cluster DNA (Profiling)")
                        profile = df_clus.groupby(
                            'Cluster')[feats].mean().reset_index()
                        # Heatmap of means
                        st.plotly_chart(px.imshow(profile.set_index('Cluster'), text_auto=True, aspect="auto",
                                                  title="Average Feature Values by Cluster", color_continuous_scale="RdBu_r", template=ctx.theme))
                else:
                    st.error(res.get('error'))

    # ==========================================
    # C. EXPLAINABLE ANOMALIES
    # ==========================================
    elif mode_ml == "Explainable Anomalies":
        st.write("#### 🚨 Explainable Outlier Detection")

        c1, c2 = st.columns([1, 3])
        contam = c1.slider("Contamination", 0.01, 0.15, 0.05)
        cols_anom = c2.multiselect("Features", ctx.num_cols, default=ctx.num_cols[:3] if len(
            ctx.num_cols) >= 3 else ctx.num_cols)

        if st.button("DETECT & EXPLAIN", type="primary"):
            with st.spinner("Detecting Anomalies..."):
                res = engine.analysis.ml.detect_anomalies(
                    df, cols_anom, contamination=contam)

                if res and "error" not in res:
                    X_a = res.get('df')
                    st.plotly_chart(px.scatter(X_a, x=cols_anom[0], y=cols_anom[1] if len(cols_anom) > 1 else cols_anom[0],
                                               color='Type', color_discrete_map={'Normal': 'lightgrey', 'Outlier': 'red'},
                                               symbol='Type', title="Outlier Identification Map", template=ctx.theme))

                    if X_a is not None:
                        outliers = X_a[X_a['Type'] == 'Outlier']
                        if not outliers.empty:
                            st.write(f"Found **{len(outliers)}** outliers.")

                            # Compare Outliers vs Normal
                            normal_subset = X_a[X_a['Type'] == 'Normal']
                            normal_mean = normal_subset[cols_anom].mean()
                            outlier_mean = outliers[cols_anom].mean()

                            diff = ((outlier_mean - normal_mean) /
                                    normal_mean) * 100
                            diff_df = pd.DataFrame({"Feature": cols_anom, "Deviation %": diff}).sort_values(
                                "Deviation %", key=abs, ascending=False)

                            st.plotly_chart(px.bar(diff_df, x="Deviation %", y="Feature", orientation='h',
                                                   title="Why are they outliers? (Avg Deviation from Normal)",
                                                   color="Deviation %", color_continuous_scale="RdBu_r", template=ctx.theme))
                    else:
                        st.info("No outliers found.")
                else:
                    st.error(res.get('error'))
