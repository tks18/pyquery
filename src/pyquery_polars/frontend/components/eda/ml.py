"""
EDA ML Tab - Machine learning diagnostics and clustering.

This module provides the ML tab for the EDA module, including
diagnostic model sandbox, advanced clustering, and anomaly detection.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pyquery_polars.frontend.components.eda.core import BaseEDATab

HAS_SKLEARN = True


class MLTab(BaseEDATab):
    """
    ML tab for EDA module.

    Displays:
    - Diagnostic Model Sandbox (train interpretable models)
    - Advanced Clustering (K-Means, DBSCAN)
    - Explainable Anomalies (Isolation Forest)
    """

    TAB_NAME = "ML"
    TAB_ICON = "🤖"

    def render(self) -> None:
        """Render the ML tab content."""
        df = self.get_data()
        if df is None:
            return

        if not HAS_SKLEARN:
            st.warning("⚠️ Scikit-Learn not installed.")
            return

        # Mode selection
        with st.container(border=True):
            mode_ml = st.radio("Intelligence Module", [
                "Diagnostic Model Sandbox", "Advanced Clustering", "Explainable Anomalies"
            ], horizontal=True, label_visibility="collapsed")

        if len(self.ctx.num_cols) < 2 and mode_ml not in ["Explainable Anomalies"]:
            st.warning("Need features to run ML.")
            return

        if mode_ml == "Diagnostic Model Sandbox":
            self._render_diagnostic_sandbox(df)
        elif mode_ml == "Advanced Clustering":
            self._render_clustering(df)
        elif mode_ml == "Explainable Anomalies":
            self._render_anomalies(df)

    def _render_diagnostic_sandbox(self, df: pd.DataFrame) -> None:
        """Render the diagnostic model sandbox section."""
        st.write("#### 🧪 Robust Modeling & Calibration")
        st.caption(
            "Train interpretable models to understand relationships and performance.")

        c1, c2, c3 = st.columns([1, 1, 2])
        target = c1.selectbox(
            "Target Variable", self.ctx.all_cols, key="qm_target")
        model_type = c2.selectbox("Model Type", [
            "Linear Regression (OLS)", "Ridge (L2)", "Lasso (L1)",
            "Logistic Regression", "Random Forest", "Auto-Pilot (Best Model)"
        ], key="qm_type")

        def_chk = [c for c in (self.ctx.num_cols[:5] if len(self.ctx.num_cols) >= 5
                               else self.ctx.num_cols) if c != target]
        feats = c3.multiselect("Features",
                               [c for c in self.ctx.all_cols if c != target],
                               default=def_chk, key="qm_feats")

        with st.expander("⚙️ hyper-parameters"):
            use_poly = st.checkbox("Enable Interaction Effects (Polynomial Features)",
                                   help="Captures non-linear relationships (e.g. A*B).")

        is_cat = target in self.ctx.cat_cols or df[target].nunique() < 10

        # Session state for caching
        session_key = "ml_results"
        param_key = "ml_params"
        current_params = {
            "target": target, "feats": feats, "model_type": model_type,
            "poly": use_poly, "df_shape": df.shape
        }

        run_clicked = st.button("RUN DECISION MODEL", type="primary")
        res = None

        if run_clicked:
            if not feats:
                st.error("Select features.")
                return
            with st.spinner("Training & Calibrating Model..."):
                res = self.engine.analytics.ml.run_diagnostic_model(
                    df, target, feats, model_type, is_cat, use_poly)
                self.state.set_value(session_key, res)
                self.state.set_value(param_key, current_params)
        elif self.state.has_value(session_key) and self.state.get_value(param_key) == current_params:
            res = self.state.get_value(session_key)

        if res:
            self._render_model_results(df, res, is_cat, feats)

    def _render_model_results(self, df: pd.DataFrame, res: dict,
                              is_cat: bool, feats: list) -> None:
        """Render model training results."""
        if "error" in res:
            st.error(res['error'])
            return

        best_model = res.get('model_obj')
        best_score = res.get('best_score', 0)
        best_name = res.get('model_name', "Unknown")
        metrics = res.get('metrics', {})
        diagnostics = res.get('diagnostics', {})

        X_test = res.get('X_test')
        y_test = res.get('y_test')
        y_pred = res.get('y_pred')

        if best_model is None or y_test is None or y_pred is None:
            st.error("Model returned incomplete results.")
            return

        st.divider()

        # Headline Metrics
        c_s1, c_s2, c_s3, c_s4 = st.columns(4)
        c_s1.metric("Model Selected", best_name)
        score_label = "Accuracy" if is_cat else "R² Score"
        c_s2.metric(f"Test {score_label}", f"{best_score:.3f}",
                    delta="Strong" if best_score > 0.7 else "Weak", delta_color="normal")
        if not is_cat:
            c_s3.metric("MAE", f"{metrics.get('mae', 0):.2f}")

        st.divider()

        # Deep Dive Tabs
        tabs = st.tabs([
            "📊 Performance Stats", "👁️ Explainability (PDP)",
            "📉 Learning Curves", "🧠 Residuals/Errors"
        ])

        with tabs[0]:
            self._render_performance_stats(res, is_cat, metrics, diagnostics,
                                           best_model, X_test, y_test, y_pred)
        with tabs[1]:
            self._render_explainability(
                res, best_model, X_test, y_test, feats, df)
        with tabs[2]:
            self._render_learning_curves(diagnostics)
        with tabs[3]:
            self._render_residuals(is_cat, diagnostics)

    def _render_performance_stats(self, res, is_cat, metrics, diagnostics,
                                  best_model, X_test, y_test, y_pred) -> None:
        """Render performance statistics tab."""
        c_p1, c_p2 = st.columns(2)

        if is_cat:
            cm = metrics.get('confusion_matrix')
            if cm is not None:
                c_p1.plotly_chart(px.imshow(cm, text_auto=True, title="Confusion Matrix",
                                            color_continuous_scale="Blues", template=self.ctx.theme))

            if hasattr(best_model, "predict_proba"):
                y_probs = best_model.predict_proba(X_test)
                if y_probs.shape[1] == 2:
                    prob_pos = y_probs[:, 1]
                    sep_df = pd.DataFrame(
                        {'Probability': prob_pos, 'Truth': y_test})
                    fig_sep = px.histogram(sep_df, x="Probability", color="Truth", barmode="overlay",
                                           title="Separation Plot", template=self.ctx.theme, opacity=0.6)
                    c_p2.plotly_chart(fig_sep)

                    if 'roc' in diagnostics and diagnostics['roc']:
                        roc = diagnostics['roc']
                        fig_roc = px.area(x=roc['fpr'], y=roc['tpr'],
                                          title=f"ROC Curve (AUC={roc['auc']:.2f})",
                                          labels={'x': 'FPR', 'y': 'TPR'}, template=self.ctx.theme)
                        fig_roc.add_shape(type='line', line=dict(
                            dash='dash'), x0=0, x1=1, y0=0, y1=1)
                        st.plotly_chart(fig_roc)
        else:
            df_res = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
            fig_avp = px.scatter(df_res, x="Actual", y="Predicted", trendline="ols",
                                 title="Prediction Error Plot", template=self.ctx.theme, opacity=0.6)
            min_val, max_val = min(y_test.min(), y_pred.min()), max(
                y_test.max(), y_pred.max())
            fig_avp.add_shape(type="line", x0=min_val, y0=min_val, x1=max_val, y1=max_val,
                              line=dict(color="Red", dash="dash"))
            c_p1.plotly_chart(fig_avp)

            errors = y_test - y_pred
            c_p2.plotly_chart(px.histogram(
                errors, title="Error Distribution", template=self.ctx.theme))

    def _render_explainability(self, res, best_model, X_test, y_test, feats, df) -> None:
        """Render explainability tab with importance and PDP."""
        st.caption("Understand HOW features affect the prediction.")

        imp_vals = self.engine.analytics.ml.get_permutation_importance(
            best_model, X_test, y_test)
        feat_names = res.get('train_cols', feats)
        df_imp = pd.DataFrame({'Feature': feat_names, 'Importance': imp_vals}).sort_values(
            'Importance', ascending=True)

        c_ex1, c_ex2 = st.columns([1, 2])
        c_ex1.plotly_chart(px.bar(df_imp, x='Importance', y='Feature', orientation='h',
                                  title="Global Feature Importance", template=self.ctx.theme))

        with c_ex2:
            pdp_feat = st.selectbox(
                "View Effect of Feature:", feats, key="pdp_sel")
            if pdp_feat:
                target = res.get('target', feats[0] if feats else '')
                pdp_data = self.engine.analytics.ml.get_partial_dependence(
                    df, target, pdp_feat, feats)
                if 'x' in pdp_data:
                    st.plotly_chart(px.line(x=pdp_data['x'], y=pdp_data['y'], markers=True,
                                            title=f"Partial Dependence: '{pdp_feat}'",
                                            labels={'x': pdp_feat, 'y': f"Expected Target"}, template=self.ctx.theme))
                else:
                    st.warning("Could not calculate PDP for this feature.")

    def _render_learning_curves(self, diagnostics: dict) -> None:
        """Render learning curves tab."""
        lc = diagnostics.get('learning_curve')
        if lc:
            df_lc = pd.DataFrame({
                "Training Size": lc['train_sizes'],
                "Training Score": lc['train_mean'],
                "Validation Score": lc['test_mean']
            })
            df_lc_melt = df_lc.melt(
                "Training Size", var_name="Metric", value_name="Score")
            st.plotly_chart(px.line(df_lc_melt, x="Training Size", y="Score", color="Metric", markers=True,
                                    title="Learning Curve", template=self.ctx.theme))
            st.info("Large gap = Overfitting. Low scores = Underfitting.")
        else:
            st.info("Learning curve data unavailable.")

    def _render_residuals(self, is_cat: bool, diagnostics: dict) -> None:
        """Render residuals analysis tab."""
        if not is_cat:
            r = diagnostics.get('residuals')
            p = diagnostics.get('predicted')
            fig_res = px.scatter(x=p, y=r, labels={'x': 'Predicted', 'y': 'Residuals'},
                                 title="Residual Plot", template=self.ctx.theme)
            fig_res.add_hline(y=0, line_dash="dash")
            st.plotly_chart(fig_res)
        else:
            st.info("Residual analysis is best suited for regression.")

    def _render_clustering(self, df: pd.DataFrame) -> None:
        """Render the advanced clustering section."""
        st.write("#### 🧬 Unsupervised Pattern Detection")
        st.caption("Group similar data points and discover segments.")

        c1, c2, c3 = st.columns(3)
        c_feats = c1.multiselect("Features", self.ctx.num_cols,
                                 default=self.ctx.num_cols[:3], key="cl_feats")
        n_k = c2.slider("Clusters (K)", 2, 10, 3, key="cl_k")
        algo = c3.selectbox("Algorithm", ["K-Means", "DBSCAN"], key="cl_algo")

        col_run, col_opt = st.columns([1, 1])
        run_clustering = col_run.button("RUN CLUSTERING", type="primary")
        find_optimal = col_opt.button(
            "Find Optimal K (Elbow)", type="secondary")

        if find_optimal and c_feats:
            with st.spinner("Scanning ideal cluster count..."):
                res = self.engine.analytics.ml.cluster_data(
                    df, c_feats, n_k, algo, optimize_k=True)
                elbow = res.get('elbow_data')
                if elbow:
                    st.plotly_chart(px.line(x=elbow['k'], y=elbow['inertia'], markers=True,
                                            title="Elbow Method: Optimal K",
                                            labels={'x': 'K', 'y': 'Inertia'}, template=self.ctx.theme))
                    st.success(
                        "Look for the 'elbow' point where inertia reduction slows down.")

        if run_clustering and c_feats:
            with st.spinner("Clustering..."):
                res = self.engine.analytics.ml.cluster_data(
                    df, c_feats, n_k, algo, optimize_k=False)
                if "error" in res:
                    st.error(res["error"])
                    return

                self._render_clustering_results(res, c_feats, algo, df)

    def _render_clustering_results(self, res: dict, c_feats: list, algo: str, df: pd.DataFrame) -> None:
        """Render clustering results."""
        res_df = res['df']
        labels = res['labels']
        sil = res['silhouette_score']
        centroids = res.get('centroids', {})

        c1, c2 = st.columns(2)
        c1.metric("Silhouette Score", f"{sil:.3f}")
        c2.caption("Clustering Quality (1.0 = Perfect separation)")

        tabs = st.tabs(["Space Projection (PCA)",
                       "Cluster DNA (Radar)", "Silhouette Analysis"])

        with tabs[0]:
            st.plotly_chart(px.scatter(res_df, x='PCA1', y='PCA2', color='Cluster',
                                       title=f"2D Projection ({algo})", template=self.ctx.theme,
                                       hover_data=c_feats))

        with tabs[1]:
            if centroids:
                categories = list(centroids[list(centroids.keys())[0]].keys())
                fig_rad = go.Figure()
                for cluster_id, feats_vals in centroids.items():
                    vals = list(feats_vals.values()) + \
                        [list(feats_vals.values())[0]]
                    cats = categories + [categories[0]]
                    fig_rad.add_trace(go.Scatterpolar(r=vals, theta=cats, fill='toself',
                                                      name=f"Cluster {cluster_id}"))
                fig_rad.update_layout(
                    polar=dict(radialaxis=dict(visible=True,
                               range=[0, max([max(v.values()) for v in centroids.values()])])),
                    title="Cluster Centroid Signatures", template=self.ctx.theme)
                st.plotly_chart(fig_rad)

        with tabs[2]:
            sil_data = self.engine.analytics.ml.get_silhouette_samples(
                df, c_feats, labels)
            if sil_data and 'scores' in sil_data:
                scores = sil_data['scores']
                k_df = pd.DataFrame({'Score': scores, 'Cluster': labels})
                k_df = k_df.sort_values(['Cluster', 'Score'])
                k_df['Sample'] = range(len(k_df))
                fig_knife = px.bar(k_df, x="Sample", y="Score", color="Cluster",
                                   title="Silhouette 'Knife' Plot", template=self.ctx.theme)
                fig_knife.add_hline(y=sil, line_dash="dash",
                                    annotation_text="Avg Score")
                st.plotly_chart(fig_knife)

        st.dataframe(res_df.head(100))

    def _render_anomalies(self, df: pd.DataFrame) -> None:
        """Render the anomaly detection section."""
        st.write("#### 🛡️ Anomaly Detection")
        st.caption("Identify outliers using Isolation Forests.")

        c1, c2 = st.columns(2)
        anom_feats = c1.multiselect("Features", self.ctx.num_cols,
                                    default=self.ctx.num_cols, key="anom_feats")
        contam = c2.slider("Contamination", 0.01, 0.2, 0.05, key="anom_cont")

        if st.button("SCAN FOR OUTLIERS", type="primary"):
            if not anom_feats:
                st.error("Select features.")
                return

            res = self.engine.analytics.ml.detect_anomalies(
                df, anom_feats, contam)
            if "error" in res:
                st.error(res['error'])
                return

            outliers = res['outliers']
            st.metric("Outliers Detected", len(outliers),
                      f"{len(outliers)/len(df):.1%}")
            st.dataframe(outliers.head(50))
