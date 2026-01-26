"""
EDA Simulation Tab - decision intelligence and target analysis.

This module provides the Simulation tab for the EDA module, including
what-if analysis/decision simulator and advanced target analysis.
"""
from typing import cast, Any

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pyquery_polars.frontend.components.eda.core import BaseEDATab


class SimulationTab(BaseEDATab):
    """
    Simulation tab for EDA module.

    Displays:
    - What-If Analysis / Decision Simulator
    - Advanced Target Analysis (Bivariate & Insights)
    """

    TAB_NAME = "Simulation"
    TAB_ICON = "🔮"

    def render(self) -> None:
        """Render the Simulation tab content."""
        df = self.get_data()
        if df is None:
            return

        # Mode selection
        with st.container(border=True):
            mode_sim = st.radio("Simulation Module", [
                "Decision Simulator", "Target Analysis"
            ], horizontal=True, label_visibility="collapsed")

        if mode_sim == "Decision Simulator":
            self.render_simulator(df)
        else:
            self.render_target_analysis(df)

    def render_simulator(self, df: pd.DataFrame) -> None:
        """Render the Decision Simulator."""
        st.write("#### 🎛️ What-If Analysis & Decision Intelligence")
        st.caption(
            "Train a predictive digital twin to simulate outcomes and evaluate scenarios.")

        engine = self.engine

        # Config Section
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            all_opts = self.ctx.num_cols + self.ctx.cat_cols
            def_idx = 0

            sim_target = c1.selectbox(
                "Target Outcome", all_opts, index=def_idx, key="sim_tgt")

            avail_drivers = [c for c in self.ctx.num_cols if c != sim_target]
            sim_feats = c2.multiselect(
                "Driver Features (Numeric)", avail_drivers,
                default=avail_drivers[:5] if len(
                    avail_drivers) > 5 else avail_drivers,
                key="sim_fts"
            )

            model_type = c3.selectbox(
                "Model Type", ["Random Forest", "Linear Model"], key="sim_model_type")

            if st.button("🚀 TRAIN SIMULATOR", type="primary", width="stretch"):
                if not sim_feats:
                    st.error("Select numeric driver features.")
                else:
                    with st.spinner("Training Model..."):
                        res = engine.analytics.ml.train_simulator_model(
                            df, sim_target, sim_feats, model_type
                        )

                        if res and "error" not in res:
                            self.state.set_value('sim_model', res['model'])
                            self.state.set_value('sim_feats', sim_feats)
                            self.state.set_value('sim_X', res['X_sample'])
                            self.state.set_value(
                                'sim_score', res.get('score', 0))
                            self.state.set_value(
                                'sim_metrics', res.get('metrics', {}))
                            self.state.set_value(
                                'sim_is_cat', res.get('is_categorical', False))
                            self.state.set_value('sim_target', sim_target)

                            explainer = engine.analytics.ml.train_surrogate_explainer(
                                res['model'], res['X_sample']
                            )
                            self.state.set_value('sim_explainer', explainer)
                            st.rerun()
                        else:
                            st.error(f"Train Error: {res.get('error')}")

        # Simulator Dashboard
        if self.state.has_value('sim_model'):
            if self.state.get_value('sim_target') != sim_target:
                st.info("Target changed. Please retrain.")
                return

            st.divider()

            model = self.state.get_value('sim_model')
            metrics = self.state.get_value('sim_metrics', {})
            is_cat = self.state.get_value('sim_is_cat', False)
            score = self.state.get_value('sim_score', 0)
            X_orig = self.state.get_value('sim_X')

            # A. Performance Dashboard
            self._render_sim_performance(score, metrics, is_cat, ctx=self.ctx)

            st.divider()

            # B. Simulation
            self._render_sim_scenarios(
                model, sim_feats, sim_target, is_cat, X_orig)

    def _render_sim_performance(self, score, metrics, is_cat, ctx):
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
                        fig_cm = px.imshow(cm, text_auto=True, title="Confusion Matrix (Test Set)",
                                           labels=dict(
                                               x="Predicted Class", y="Actual Class"),
                                           color_continuous_scale="Blues")
                        st.plotly_chart(fig_cm)
                    except:
                        st.write("CM Plot Error")
            elif not is_cat and 'residuals' in metrics:
                resid = metrics.get('residuals', [])
                y_p = metrics.get('y_pred', [])
                y_t = metrics.get('y_test', [])

                if len(resid) > 0 and len(y_p) > 0:
                    c_d1, c_d2 = st.columns(2)
                    fig_res = px.scatter(x=y_p, y=resid, labels={'x': "Predicted", 'y': "Residuals (Error)"},
                                         title="Residual Plot", template=ctx.theme, opacity=0.6)
                    fig_res.add_hline(y=0, line_dash="dash", line_color="red")
                    c_d1.plotly_chart(fig_res)

                    fig_avp = px.scatter(x=y_t, y=y_p, labels={'x': "Actual", 'y': "Predicted"},
                                         title="Actual vs Predicted", template=ctx.theme, opacity=0.6)
                    min_v = min(min(y_t), min(y_p))
                    max_v = max(max(y_t), max(y_p))
                    fig_avp.add_shape(type="line", x0=min_v, y0=min_v, x1=max_v, y1=max_v,
                                      line=dict(color="red", dash="dash"))
                    c_d2.plotly_chart(fig_avp)

    def _render_sim_scenarios(self, model, sim_feats, sim_target, is_cat, X_orig):
        st.subheader("🔮 Scenario Simulator")
        c_sim, c_res = st.columns([1, 1.5])

        user_inputs = {}
        with c_sim.container(border=True):
            st.write("#### 🎛️ Scenario Manager")

            if not self.state.has_value('sim_scenarios'):
                self.state.set_value('sim_scenarios', {})

            scen_name = st.text_input(
                "Scenario Name", placeholder="e.g. Best Case")
            if st.button("Save Scenario"):
                if not scen_name:
                    st.warning("Name required")

            st.divider()
            st.caption("Adjust Drivers (Levers)")

            for feat in sim_feats:
                if X_orig is None or feat not in X_orig.columns:
                    continue
                min_v = float(X_orig[feat].min())
                max_v = float(X_orig[feat].max())
                mean_v = float(X_orig[feat].mean())

                if min_v >= max_v:
                    min_v = mean_v - 1.0
                    max_v = mean_v + 1.0

                step = (max_v - min_v) / 100 if (max_v - min_v) != 0 else 0.1
                user_inputs[feat] = st.slider(
                    f"{feat}", min_v, max_v, mean_v, step=step)

        with c_res:
            try:
                input_df = pd.DataFrame([user_inputs])
                valid_cols = [c for c in sim_feats if c in user_inputs]
                input_df = input_df[valid_cols]

                pred = model.predict(input_df)[0]

                st.write("##### Outcome Analysis")
                if is_cat:
                    st.metric("Predicted Class", f"{pred}")
                else:
                    st.metric(f"Predicted {sim_target}", f"{pred:,.2f}")

                sim_mode = st.radio("Analysis Mode",
                                    ["Single Prediction",
                                        "Sensitivity (Tornado)", "Monte Carlo (Risk)"],
                                    horizontal=True, label_visibility="collapsed")
                st.divider()

                if sim_mode == "Single Prediction":
                    self._render_single_prediction_mode(user_inputs, is_cat)
                elif sim_mode == "Sensitivity (Tornado)":
                    self._render_sensitivity_mode(model, user_inputs, X_orig)
                elif sim_mode == "Monte Carlo (Risk)":
                    self._render_monte_carlo_mode(
                        model, user_inputs, X_orig, sim_target)

            except Exception as e:
                st.error(f"Prediction Error: {e}")

    def _render_single_prediction_mode(self, user_inputs, is_cat):
        explainer = self.state.get_value('sim_explainer')
        if explainer and not is_cat:
            contribs = self.engine.analytics.ml.get_prediction_contribution(
                explainer, user_inputs)
            if contribs:
                top_c = contribs[:8]
                wf_feats = [c['Feature'] for c in top_c]
                wf_vals = [c['Contribution'] for c in top_c]

                fig_wf = go.Figure(go.Waterfall(
                    orientation="v", measure=["relative"] * len(wf_vals),
                    x=wf_feats, y=wf_vals,
                    connector={"line": {"color": "rgb(63, 63, 63)"}}
                ))
                fig_wf.update_layout(
                    title="Feature Contribution", height=350, template=self.ctx.theme)
                st.plotly_chart(fig_wf)

    def _render_sensitivity_mode(self, model, user_inputs, X_orig):
        st.caption("How much does the output change if we tweak each input?")
        feat_stats = {}
        if X_orig is not None:
            for c in X_orig.columns:
                feat_stats[c] = {'std': X_orig[c].std()}

        sens_df = self.engine.analytics.ml.get_sensitivity(
            model, user_inputs, feat_stats)
        if not sens_df.empty:
            fig_tor = px.bar(sens_df, x="Spread", y="Feature", orientation='h',
                             title=f"Sensitivity: Output Range (+/- 1 Std Dev)",
                             template=self.ctx.theme, color="Spread")
            st.plotly_chart(fig_tor)

    def _render_monte_carlo_mode(self, model, user_inputs, X_orig, sim_target):
        st.caption("Simulating 1,000 scenarios with random noise.")
        feat_stats = {}
        if X_orig is not None:
            for c in X_orig.columns:
                feat_stats[c] = {'std': X_orig[c].std()}

        mc_res = self.engine.analytics.ml.run_monte_carlo(
            model, user_inputs, feat_stats)
        preds = mc_res['predictions']

        fig_dist = px.histogram(preds, nbins=30, title="Probability Distribution of Outcome",
                                labels={'value': f"Predicted {sim_target}"},
                                template=self.ctx.theme, opacity=0.7)

        p5, p95, mean_val = mc_res['p5'], mc_res['p95'], mc_res['mean']

        fig_dist.add_vline(x=mean_val, line_dash="dash",
                           line_color="white", annotation_text="Exp. Value")
        fig_dist.add_vrect(x0=p5, x1=p95, fillcolor="green",
                           opacity=0.1, annotation_text="90% Conf.")
        st.plotly_chart(fig_dist)

        c_r1, c_r2, c_r3 = st.columns(3)
        c_r1.metric("Optimistic (95th)", f"{p95:,.2f}")
        c_r2.metric("Expected", f"{mean_val:,.2f}")
        c_r3.metric("Pessimistic (5th)", f"{p5:,.2f}")

    def render_target_analysis(self, df: pd.DataFrame) -> None:
        """Render Advanced Target Analysis."""
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            target = c1.selectbox("🎯 Target Variable",
                                  self.ctx.all_cols, key="tgt_an_target")

            if not target:
                st.info("Select a target.")
                return

            is_num = target in self.ctx.num_cols
            t_type = "Numeric (Regression)" if is_num else "Categorical (Classification)"
            c2.info(f"Analysis Pattern: **{t_type}**")

        if st.button("Run Target Analysis", type="primary"):
            self.state.eda_tgt_run = True

        if self.state.eda_tgt_run:
            st.divider()
            if is_num:
                self._render_numeric_target_analysis(df, target)
            else:
                self._render_categorical_target_analysis(df, target)

            self._render_pdp_analysis(df, target)

    def _render_numeric_target_analysis(self, df, target):
        with st.spinner("Calculating Correlations..."):
            corr_df = self.engine.analytics.stats.get_target_correlations(
                df, target, self.ctx.num_cols
            )

        c_left, c_right = st.columns([1.2, 1])
        with c_left:
            st.subheader("📊 Driver Analysis (Correlation)")
            if not corr_df.empty:
                fig_corr = px.bar(corr_df.head(10), x="Correlation", y="Feature",
                                  color="Correlation", orientation="h",
                                  color_continuous_scale="RdBu", range_color=[-1, 1],
                                  title=f"Top 10 Correlated Features with {target}",
                                  template=self.ctx.theme)
                fig_corr.update_layout(height=400)
                st.plotly_chart(fig_corr)
            else:
                st.warning("No significant numeric correlations found.")

        with c_right:
            st.subheader("🔎 Bivariate Deep Dive")
            defaults = [c for c in self.ctx.num_cols if c != target]
            def_idx = 0
            if not corr_df.empty:
                top_f = corr_df.iloc[0]["Feature"]
                if top_f in defaults:
                    def_idx = defaults.index(top_f)

            feat_x = st.selectbox("Compare Feature (X)",
                                  defaults, index=def_idx, key="tgt_scat_x")
            if feat_x:
                fig_scat = px.scatter(df, x=feat_x, y=target, trendline="ols",
                                      trendline_color_override="red", opacity=0.6,
                                      title=f"{target} vs {feat_x}", template=self.ctx.theme)
                st.plotly_chart(fig_scat)

        if self.ctx.cat_cols:
            st.divider()
            st.subheader("📦 Categorical Impact")
            cat_feat = st.selectbox(
                "Group By Category", self.ctx.cat_cols, index=0, key="tgt_box_cat")
            if cat_feat:
                fig_box = px.box(df, x=cat_feat, y=target, color=cat_feat,
                                 title=f"{target} Distribution by {cat_feat}",
                                 template=self.ctx.theme)
                st.plotly_chart(fig_box)

    def _render_categorical_target_analysis(self, df, target):
        c_l, c_r = st.columns([1, 1.5])
        with c_l:
            st.subheader("🍰 Class Balance")
            counts = df[target].value_counts().reset_index()
            counts.columns = [target, "Count"]
            fig_pie = px.pie(counts, names=target, values="Count", hole=0.4,
                             template=self.ctx.theme, title=f"{target} Proportions")
            st.plotly_chart(fig_pie)

        with c_r:
            st.subheader("📐 Feature Separation")
            feat_sep = st.selectbox(
                "Inspect Feature", self.ctx.num_cols, key="tgt_sep_f")
            if feat_sep:
                fig_sep = px.box(df, x=target, y=feat_sep, color=target, points="outliers",
                                 title=f"Distribution of {feat_sep} by Class",
                                 template=self.ctx.theme)
                st.plotly_chart(fig_sep)

        if len(self.ctx.cat_cols) > 1:
            st.divider()
            st.subheader("🔗 Categorical Association")
            cat_assoc = st.selectbox(
                "Cross-Tab Feature", [c for c in self.ctx.cat_cols if c != target], key="tgt_ct")
            if cat_assoc:
                ct = pd.crosstab(df[target], df[cat_assoc], normalize='index')
                fig_hm = px.imshow(ct, text_auto=cast(Any, ".1%"), aspect="auto",
                                   labels=dict(
                                       x=cat_assoc, y=target, color="Pct"),
                                   title=f"Normalized Association: {target} vs {cat_assoc}",
                                   template=self.ctx.theme)
                st.plotly_chart(fig_hm)

    def _render_pdp_analysis(self, df, target):
        with st.expander("🤖 Advanced: Partial Dependence (PDP)"):
            st.caption(
                "Model-independent view of how a feature affects the target.")
            pdp_opts = [c for c in self.ctx.num_cols if c != target]
            pdp_f = st.selectbox("Select Feature for PDP",
                                 pdp_opts, key="tgt_pdp_f")

            if st.button("Run PDP Calculation"):
                with st.spinner("Calculating PDP..."):
                    res = self.engine.analytics.ml.get_partial_dependence(
                        df, target, pdp_f)
                    if "x" in res:
                        fig_pdp = px.line(x=res['x'], y=res['y'], markers=True,
                                          labels={'x': pdp_f,
                                                  'y': f"Predicted {target}"},
                                          title=f"Partial Dependence Plot: {pdp_f}")
                        st.plotly_chart(fig_pdp)
                    else:
                        st.warning("PDP Failed.")
