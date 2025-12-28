import streamlit as st
import polars as pl
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import cast, Any, List, Dict, Optional, Tuple
from pyquery_polars.backend.engine import PyQueryEngine

# Required ML Imports
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import confusion_matrix, r2_score, mean_absolute_error, accuracy_score, silhouette_score, roc_curve, auc, precision_recall_curve, brier_score_loss
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance, partial_dependence
from sklearn.calibration import calibration_curve

HAS_SKLEARN = True

# --- CONFIG ---
EDA_SAMPLE_LIMIT = 5000


def render_eda_tab():
    st.subheader("📊 EDA: The Decision Engine 🚀")

    # 1. Get Engine & Active Dataset
    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        st.error("Engine not initialized.")
        return

    active_ds = st.session_state.get('active_base_dataset')
    if not active_ds:
        st.info("👈 Please select a dataset in the Sidebar to analyze.")
        return

    # 2. Prepare Data (Sampled) - LOAD FIRST to get columns for settings
    df = None
    num_cols = []
    cat_cols = []
    date_cols = []
    all_cols = []

    with st.spinner(f"Preparing '{active_ds}'..."):
        try:
            project_recipes = st.session_state.get('all_recipes', {}) or {}
            current_recipe = project_recipes.get(active_ds, [])

            base_lf = engine.get_dataset(active_ds)
            if base_lf is None:
                st.error("Dataset not found.")
                return

            transformed_lf = engine.apply_recipe(
                base_lf, current_recipe, project_recipes)
            df = transformed_lf.head(EDA_SAMPLE_LIMIT).collect().to_pandas()

            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            cat_cols = df.select_dtypes(
                include=['object', 'category', 'string', 'bool']).columns.tolist()
            date_cols = df.select_dtypes(
                include=['datetime', 'datetimetz']).columns.tolist()
            all_cols = df.columns.tolist()

        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if df is None:
        return

    # 3. Global Settings (Sidebar or Top)
    # 3. Global Settings (Sidebar or Top)
    with st.expander("⚙️ Analysis Settings", expanded=True):
        c1, c2, c3 = st.columns(3)
        show_labels = c1.toggle("🔠 Show Data Labels", value=False)
        theme = c2.selectbox(
            "Theme", ["plotly", "plotly_dark", "seaborn", "ggplot2"], index=0)

        # SMART FILTERING: Exclude columns
        excluded_cols = st.multiselect(
            "🚫 Exclude Columns from Analysis (All Types)", all_cols)

    # Apply Exclusion Logic
    if excluded_cols:
        all_cols = [c for c in all_cols if c not in excluded_cols]
        num_cols = [c for c in num_cols if c not in excluded_cols]
        cat_cols = [c for c in cat_cols if c not in excluded_cols]
        date_cols = [c for c in date_cols if c not in excluded_cols]
        df = df[all_cols]
        st.caption(f"Excluding {len(excluded_cols)} columns from analysis.")

    # LAZY LOAD BUFFER
    if 'eda_ready' not in st.session_state:
        st.session_state['eda_ready'] = False

    col_gen, _ = st.columns([1, 2])
    if col_gen.button("🚀 Generate Insights & Charts", type="primary"):
        st.session_state['eda_ready'] = True
        st.rerun()

    if not st.session_state.get('eda_ready', False):
        st.info("👆 Click 'Generate' to initialize the charts and analysis engine.")
        return

    # --- TABS ---
    tabs = st.tabs([
        "📋 Overview",
        "🤖 Decision ML",
        "🎛️ Simulation",  # NEW
        "🎯 Target Analysis",
        "⏳ Time Series",
        "📊 Distributions",
        "🧱 Hierarchy",
        "🕸️ Relationships"
    ])

    (tab_overview, tab_ml, tab_sim, tab_target,
     tab_time, tab_dist, tab_hier, tab_rel) = tabs

    # ==========================
    # 1. OVERVIEW (Autopilot Insights)
    # ==========================
    with tab_overview:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{len(df):,}")
        c2.metric("Columns", len(all_cols))
        missing = df.isna().sum().sum()
        c3.metric("Null Values", f"{missing:,}")
        dupes = df.duplicated().sum()
        c4.metric("Duplicates", f"{dupes:,}")

        st.divider()

        # --- EDA 10.0: STRATEGIC BRIEF (Insight Prioritization) ---
        if len(num_cols) > 0:
            st.write("#### 🚀 Strategic Brief (Top Insights)")

            insights = []

            # 1. Correlation Scanning
            corr_matrix = df[num_cols].corr().abs()
            np.fill_diagonal(corr_matrix.values, 0)
            top_corrs = cast(pd.Series, corr_matrix.unstack()).nlargest(3)

            for idx, score in top_corrs.items():
                f1, f2 = cast(Tuple[str, str], idx)
                if score > 0.6:  # Threshold
                    insights.append({
                        "type": "Correlation",
                        "score": score,
                        "title": f"Strong Link: {f1} & {f2}",
                        "desc": f"These variables move together ({score:.2f}).",
                        "action": f"👉 **Now What**: Investigate if '{f1}' drives '{f2}'. Influencing one may control the other."
                    })

            # 2. Trend Scanning (Action Engine)
            if date_cols and not df.empty:
                dt = date_cols[0]
                # Sort by date for trend calc
                df_sorted = df.sort_values(dt)
                for val in num_cols[:3]:  # Scan top 3 numeric
                    try:
                        first = df_sorted[val].iloc[0]
                        last = df_sorted[val].iloc[-1]
                        if first != 0:
                            change = (last - first) / first
                            if abs(change) > 0.15:  # 15% threshold
                                direction = "Growth" if change > 0 else "Decline"
                                insights.append({
                                    "type": "Trend",
                                    "score": abs(change),  # Rank by magnitude
                                    "title": f"{direction} Alert: {val}",
                                    "desc": f"{val} has {direction.lower()}d by {abs(change):.1%} over the period.",
                                    "action": f"👉 **Now What**: {'Capitalize on momentum' if change > 0 else 'Diagnose the drop'} in {val}."
                                })
                    except:
                        pass

            # 3. Rank & Display
            insights.sort(key=lambda x: x['score'], reverse=True)

            if insights:
                top_3 = insights[:3]
                cols = st.columns(len(top_3))
                for i, insight in enumerate(top_3):
                    with cols[i]:
                        with st.container(border=True):
                            st.metric(insight['title'], f"{insight['score']:.2f}",
                                      delta="High Impact" if insight['score'] > 0.7 else None)
                            st.caption(insight['desc'])
                            st.markdown(insight['action'])
            else:
                st.info(
                    "No significant strategic insights detected yet. Try filtering columns or adding more data.")

            st.divider()

        # A. Pivot Table (Quick Summary)
        if len(cat_cols) > 0 and len(num_cols) > 0:
            st.write("###### 🔢 Quick Pivot Summary")
            p_row = st.selectbox("Pivot Rows", cat_cols, key="p_row")
            p_val = st.selectbox("Summarize Value", num_cols, key="p_val")
            p_agg = st.selectbox(
                "Agg Func", ["mean", "sum", "count", "min", "max"], key="p_agg")

            pivot_df = df.groupby(p_row)[p_val].agg(
                p_agg).reset_index().sort_values(p_val, ascending=False).head(20)

            fig = px.bar(pivot_df, x=p_row, y=p_val, template=theme,
                         text=p_val if show_labels else None,
                         title=f"Top 20 {p_row} by {p_agg} {p_val}")

            if show_labels:
                fig.update_traces(
                    texttemplate='%{text:.2s}', textposition='outside')
            st.plotly_chart(fig, width="stretch")

        # B. Null Matrix
        if missing > 0:
            st.write("###### 🚧 Null Matrix")
            hm_df = df.isna().replace(
                {True: 1, False: 0}).sample(min(len(df), 1000))
            fig = px.imshow(hm_df, color_continuous_scale=[
                            '#f0f2f6', '#ff4b4b'], template=theme)
            fig.update_layout(coloraxis_showscale=False,
                              height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, width="stretch")

    # ==========================
    # 2. DECISION GRADE ML
    # ==========================
    with tab_ml:
        if not HAS_SKLEARN:
            st.warning("⚠️ Scikit-Learn not installed.")
            return

        mode_ml = st.radio("Intelligence Module", [
                           "Diagnostic Model Sandbox", "Advanced Clustering", "Explainable Anomalies"], horizontal=True)

        if len(num_cols) < 2 and mode_ml not in ["Explainable Anomalies"]:
            st.warning("Need features to run ML.")
        else:
            # A. DIAGNOSTIC SANDBOX
            if mode_ml == "Diagnostic Model Sandbox":
                st.write("#### 🧪 Robust Modeling & Calibration")

                c1, c2 = st.columns(2)
                target = c1.selectbox(
                    "Target Variable", all_cols, key="qm_target")
                model_type = c2.selectbox("Model Type", ["Linear Regression (OLS)", "Ridge (L2)", "Lasso (L1)",
                                                         "Logistic Regression", "Random Forest", "Auto-Pilot (Best Model)"], key="qm_type")

                def_chk = [c for c in (num_cols[:5] if len(
                    num_cols) >= 5 else num_cols) if c != target]
                feats = st.multiselect(
                    "Features", [c for c in all_cols if c != target], default=def_chk, key="qm_feats")

                if st.button("RUN DECISION MODEL"):
                    if not feats:
                        st.error("Select features.")
                    else:
                        with st.spinner("Executing Analysis..."):
                            try:
                                X = df[feats].copy()
                                y = df[target].copy()
                                X = X.fillna(0)
                                for c in X.select_dtypes(include=['object']).columns:
                                    X[c] = LabelEncoder().fit_transform(
                                        X[c].astype(str))

                                is_cat = target in cat_cols or df[target].nunique(
                                ) < 10

                                # AUTO-PILOT LOGIC
                                best_model = None
                                best_score = -999
                                best_name = ""
                                best_cv_scores = np.array([])

                                models_to_run = []
                                if model_type == "Auto-Pilot (Best Model)":
                                    if is_cat:
                                        models_to_run = [("Logistic", LogisticRegression(
                                            max_iter=500)), ("Random Forest", RandomForestClassifier(random_state=42))]
                                    else:
                                        models_to_run = [("Linear", LinearRegression()), ("Ridge", Ridge(
                                        )), ("Lasso", Lasso()), ("Random Forest", RandomForestRegressor(random_state=42))]
                                else:
                                    # Single model logic
                                    if "Linear" in model_type:
                                        models_to_run = [
                                            ("Linear", LinearRegression())]
                                    elif "Ridge" in model_type:
                                        models_to_run = [("Ridge", Ridge())]
                                    elif "Lasso" in model_type:
                                        models_to_run = [("Lasso", Lasso())]
                                    elif "Logistic" in model_type:
                                        models_to_run = [
                                            ("Logistic", LogisticRegression(max_iter=500))]
                                    else:
                                        models_to_run = [("Random Forest", RandomForestClassifier(
                                            random_state=42) if is_cat else RandomForestRegressor(random_state=42))]

                                # PREP Y
                                if is_cat:
                                    y = y.astype(str).fillna("Unknown")
                                else:
                                    y = y.fillna(0)

                                # Eval Loop
                                score_metric = 'accuracy' if is_cat else 'r2'

                                st.write("###### 🏆 Model Leaderboard")
                                results_md = []

                                for name, m in models_to_run:
                                    cv_scores = cross_val_score(
                                        m, X, y, cv=5, scoring=score_metric)
                                    mean_sc = cv_scores.mean()
                                    results_md.append(
                                        f"- **{name}**: {mean_sc:.3f} (± {cv_scores.std()*2:.3f})")
                                    if mean_sc > best_score:
                                        best_score = mean_sc
                                        best_model = m
                                        best_name = name
                                        best_cv_scores = cv_scores

                                for line in results_md:
                                    st.write(line)
                                st.success(
                                    f"**Winner:** {best_name} (Score: {best_score:.3f})")

                                if best_model is None:
                                    st.error("No model could be trained.")
                                    return

                                # EDA 10.0: Model Rationale
                                rationale = "Model selected based on overall performance."
                                if "Random Forest" in best_name:
                                    rationale = "Selected for its ability to handle **complex, non-linear relationships** and feature interactions."
                                elif "Linear" in best_name or "Ridge" in best_name:
                                    rationale = "Selected because **linear relationships** dominate. Simpler models prevent overfitting here."
                                elif "Lasso" in best_name:
                                    rationale = "Selected for its ability to **eliminate noisy features** (sparse selection)."
                                elif "Logistic" in best_name:
                                    rationale = "Selected as a robust baseline for binary classification."

                                st.info(f"💡 **Why this model?** {rationale}")

                                # Final Fit & Diagnostics on Winner
                                model = best_model
                                X_train, X_test, y_train, y_test = train_test_split(
                                    X, y, test_size=0.2, random_state=42)
                                model.fit(X_train, y_train)
                                y_pred = model.predict(X_test)

                                # SCORECARD with Confidence Badges
                                st.write("#### 📝 Diagnostic Scorecard")

                                confidence_level = "Medium"
                                if best_score > 0.8 and len(df) > 100:
                                    confidence_level = "High 🛡️"
                                elif best_score < 0.5 or len(df) < 50:
                                    confidence_level = "Low ⚠️"

                                col_s1, col_s2, col_s3 = st.columns(3)
                                col_s1.metric(
                                    "Validation Score", f"{best_score:.3f}", delta=confidence_level)
                                col_s2.metric("Uncertainty (CI)",
                                              f"± {best_cv_scores.std()*2:.3f}")
                                col_s3.metric("Model Type", best_name)

                                # 2. Calibration / Residuals
                                c1, c2 = st.columns(2)
                                with c1:
                                    if is_cat:
                                        # Use getattr or cast to Any to avoid Pylance error
                                        if hasattr(model, "predict_proba") and len(np.unique(y)) == 2:
                                            prob_pos = cast(Any, model).predict_proba(
                                                X_test)[:, 1]
                                            lb = LabelEncoder().fit(y)
                                            y_test_bin = lb.transform(y_test)
                                            fraction_of_positives, mean_predicted_value = calibration_curve(
                                                y_test_bin, prob_pos, n_bins=10)
                                            fig_cal = px.line(x=mean_predicted_value, y=fraction_of_positives, markers=True,
                                                              labels={
                                                                  'x': "Predicted Probability", 'y': "Actual Fraction"},
                                                              title="Calibration Curve", template=theme)
                                            fig_cal.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(
                                                dash="dash", color="grey"))
                                            st.plotly_chart(
                                                fig_cal, width="stretch")
                                        else:
                                            cm = confusion_matrix(
                                                y_test, y_pred)
                                            st.plotly_chart(px.imshow(
                                                cm, text_auto=True, title="Confusion Matrix", color_continuous_scale="Blues", template=theme), width="stretch")
                                    else:
                                        residuals = y_test - y_pred
                                        st.plotly_chart(px.histogram(
                                            residuals, nbins=30, title="Residual Histogram", template=theme, text_auto=show_labels), width="stretch")

                                # 3. Permutation Importance
                                with c2:
                                    perm_imp = permutation_importance(
                                        model, X_test, y_test, n_repeats=5, random_state=42)
                                    # Use dictionary access for Bunch
                                    importances = perm_imp['importances_mean']
                                    perm_df = pd.DataFrame({'Feature': feats, 'Importance': importances}).sort_values(
                                        'Importance', ascending=True)
                                    fig_perm = px.bar(perm_df, x='Importance', y='Feature', orientation='h', title="Key Drivers (Permutation)", template=theme, text_auto=cast(
                                        Any, '.4f' if show_labels else False))
                                    st.plotly_chart(fig_perm, width="stretch")

                            except Exception as e:
                                st.error(f"Error: {e}")

            # B. CLUSTERING
            elif mode_ml == "Advanced Clustering":
                st.write("#### 🧬 Clustering Laboratory")
                algo = st.selectbox("Algorithm", ["K-Means", "DBSCAN"])
                feats = st.multiselect(
                    "Features", num_cols, default=num_cols[:4] if len(num_cols) >= 4 else num_cols)
                if st.button("RUN CLUSTERING"):
                    try:
                        X = df[feats].dropna()
                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)
                        labels = None
                        if algo == "K-Means":
                            k = st.slider("K", 2, 8, 3)
                            km = KMeans(n_clusters=k, random_state=42).fit(
                                X_scaled)
                            labels = km.labels_
                        else:
                            dbs = DBSCAN(eps=0.5, min_samples=5).fit(X_scaled)
                            labels = dbs.labels_

                        df_clus = X.copy()
                        df_clus['Cluster'] = labels.astype(str)
                        if len(set(labels)) > 1:
                            st.metric("Silhouette Score",
                                      f"{silhouette_score(X_scaled, labels):.3f}")

                        c1, c2 = st.columns([2, 1])
                        with c1:
                            st.dataframe(df_clus.groupby('Cluster').mean(
                            ).style.background_gradient(cmap='RdBu'), width="stretch")
                        with c2:
                            st.plotly_chart(
                                px.pie(df_clus, names='Cluster', title="Size"), width="stretch")

                        pca = PCA(n_components=2).fit_transform(X_scaled)
                        df_clus['PCA1'], df_clus['PCA2'] = pca[:, 0], pca[:, 1]
                        st.plotly_chart(px.scatter(
                            df_clus, x='PCA1', y='PCA2', color='Cluster', title="PCA Projection"), width="stretch")
                    except Exception as e:
                        st.error(f"Cluster Error: {e}")

            # C. EXPLAINABLE ANOMALIES
            elif mode_ml == "Explainable Anomalies":
                st.write("#### 🚨 Explainable Outlier Detection")
                contam = st.slider("Contamination", 0.01, 0.15, 0.05)
                cols_anom = st.multiselect(
                    "Features", num_cols, default=num_cols[:3] if len(num_cols) >= 3 else num_cols)
                if st.button("DETECT & EXPLAIN"):
                    try:
                        X_a = df[cols_anom].dropna()
                        clf = IsolationForest(
                            contamination=contam, random_state=42)
                        preds = clf.fit_predict(X_a)
                        X_a['Type'] = np.where(
                            preds == -1, 'Outlier', 'Normal')
                        st.plotly_chart(px.scatter(X_a, x=cols_anom[0], y=cols_anom[1] if len(cols_anom) > 1 else cols_anom[0], color='Type', color_discrete_map={
                                        'Normal': 'blue', 'Outlier': 'red'}, title="Outlier Map"), width="stretch")

                        outliers = X_a[X_a['Type'] == 'Outlier']
                        if not outliers.empty:
                            global_median = X_a[cols_anom].median()
                            outlier_mean = outliers[cols_anom].mean()
                            dev_df = pd.DataFrame({'Feature': cols_anom, 'Deviation %': (
                                (outlier_mean - global_median) / global_median) * 100}).sort_values('Deviation %', key=abs, ascending=False)
                            st.plotly_chart(px.bar(dev_df, x='Deviation %', y='Feature', orientation='h', title="Avg Deviation of Outliers vs Median",
                                            color='Deviation %', color_continuous_scale='RdBu_r', text_auto=cast(Any, '.1f' if show_labels else False)), width="stretch")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ... (Sim section is next, skipping) ...

    # ==========================
    # 4. TARGET ANALYSIS
    # ==========================

    # ==========================
    # 3. DECISION SIMULATOR (NEW)
    # ==========================
    with tab_sim:
        st.write("#### 🎛️ What-If Analysis (Decision Simulator)")
        st.caption(
            "Train a model, then adjust sliders to see predicted outcomes.")

        c1, c2 = st.columns(2)
        sim_target = c1.selectbox("Target Outcome", num_cols, key="sim_tgt")
        sim_feats = c2.multiselect("Driver Features", [c for c in num_cols if c != sim_target], default=[
                                   c for c in num_cols if c != sim_target][:5], key="sim_fts")

        if st.button("INITIALIZE SIMULATOR"):
            if not sim_feats:
                st.error("Select features.")
            else:
                with st.spinner("Training Simulator Model..."):
                    try:
                        # Train RF Regressor for versatility
                        X = df[sim_feats].fillna(0)
                        y = df[sim_target].fillna(0)
                        sim_model = RandomForestRegressor(
                            n_estimators=50, random_state=42)
                        sim_model.fit(X, y)
                        st.session_state['sim_model'] = sim_model
                        st.session_state['sim_feats'] = sim_feats
                        st.session_state['sim_X'] = X  # Save for ranges
                        st.success("Simulator Ready!")
                    except Exception as e:
                        st.error(f"Train Error: {e}")

        # RENDER SLIDERS if model ready
        if 'sim_model' in st.session_state and st.session_state.get('sim_feats') == sim_feats:
            st.divider()
            model = st.session_state['sim_model']
            X_orig = st.session_state['sim_X']

            # User Input Dict
            user_inputs = {}
            cols = st.columns(3)
            for i, feat in enumerate(sim_feats):
                min_v = float(X_orig[feat].min())
                max_v = float(X_orig[feat].max())
                mean_v = float(X_orig[feat].mean())
                step = (max_v - min_v) / 100 if max_v != min_v else 0.1
                with cols[i % 3]:
                    if min_v < max_v:
                        user_inputs[feat] = st.slider(
                            f"{feat}", min_value=min_v, max_value=max_v, value=mean_v, step=step)
                    else:
                        st.caption(f"🔒 {feat} (Constant)")
                        st.number_input(f"{feat}", value=min_v,
                                        disabled=True, key=f"fix_{feat}")
                        user_inputs[feat] = min_v

            # Predict
            input_df = pd.DataFrame([user_inputs])
            pred = model.predict(input_df)[0]

            # Strategy Tip (Action Engine)
            if hasattr(model, 'feature_importances_'):
                imp = model.feature_importances_
                # Safety check
                if len(imp) == len(sim_feats):
                    top_idx = np.argmax(imp)
                    top_feat = sim_feats[top_idx]
                    st.success(
                        f"🚀 **Strategy Tip**: **{top_feat}** is the strongest lever in this model. Small changes here will have the biggest impact on **{sim_target}**.")

            st.metric(f"Predicted {sim_target}", f"{pred:,.2f}")

    # ==========================
    # 4. TARGET ANALYSIS
    # ==========================
    with tab_target:
        target = st.selectbox("Select Target Variable",
                              all_cols, key="target_col2")
        if target:
            if target in num_cols:
                if len(num_cols) > 1:
                    pdp_feat = st.selectbox("Partial Dependence Feature", [
                                            c for c in num_cols if c != target], index=0)
                    if pdp_feat:
                        try:
                            X = df[[pdp_feat]].dropna()
                            y = df.loc[X.index, target]
                            rf = RandomForestRegressor(
                                n_estimators=10, max_depth=3).fit(X, y)
                            x_grid = np.linspace(
                                X[pdp_feat].min(), X[pdp_feat].max(), 50).reshape(-1, 1)
                            y_grid = rf.predict(x_grid)
                            st.plotly_chart(px.line(x=x_grid.flatten(), y=y_grid, labels={
                                            'x': pdp_feat, 'y': f"Pred {target}"}, title="Partial Dependence (Impact Curve)"), width="stretch")
                        except:
                            pass

                if len(num_cols) > 1:
                    c1, c2 = st.columns(2)
                    ia_x = c1.selectbox(
                        "Interaction X", num_cols, index=0 if num_cols[0] != target else 1, key="ia_x")
                    ia_y = c2.selectbox(
                        "Interaction Y", num_cols, index=1 if num_cols[1] != target else 0, key="ia_y")
                    if ia_x != ia_y:
                        df['x_bin'] = pd.cut(df[ia_x], bins=10).astype(str)
                        df['y_bin'] = pd.cut(df[ia_y], bins=10).astype(str)
                        pivot_ia = df.groupby(['x_bin', 'y_bin'], observed=True)[
                            target].mean().unstack()
                        st.plotly_chart(px.imshow(pivot_ia, title=f"Mean {target} by {ia_x} & {ia_y}", labels=dict(
                            x=ia_y, y=ia_x)), width="stretch")

    # ==========================
    # 5. TIME SERIES
    # ==========================
    with tab_time:
        if date_cols:
            dt_col = st.selectbox("Time Column", date_cols, key="time_col")
            y_col = st.selectbox("Value", num_cols, key="time_val")
            cat_split = st.selectbox(
                "Stack/Split By", ["None"] + cat_cols, key="time_stack")
            ts_df = df.copy().set_index(pd.to_datetime(df[dt_col]))
            if y_col:
                if cat_split != "None":
                    agg_df = df.groupby([dt_col, cat_split])[
                        y_col].sum().reset_index()
                    st.plotly_chart(px.area(agg_df, x=dt_col, y=y_col,
                                    color=cat_split, title="Stacked Area"), use_container_width=True)
                else:
                    agg_df = df.groupby(dt_col)[y_col].sum().reset_index()
                    st.plotly_chart(px.line(agg_df, x=dt_col, y=y_col,
                                    title="Trend Line"), use_container_width=True)
            else:
                st.warning("Please select a Value column.")
        else:
            st.info("No DateTime columns found.")

    # ==========================
    # 6. DISTRIBUTIONS
    # ==========================
    with tab_dist:
        col = st.selectbox("Column", num_cols, key="dist_col2")
        if col:
            st.caption(
                "💡 **Chart Advisor**: For distributions, Histogram is best for overview, and Box Plot for outliers.")
            type_ = st.radio("Chart Type", [
                             "Histogram", "ECDF", "Box Plot", "Ridgeline"], horizontal=True, key="dist_type")
            if type_ == "Histogram":
                fig = px.histogram(df, x=col, marginal="box",
                                   text_auto=show_labels)
            elif type_ == "ECDF":
                fig = px.ecdf(df, x=col)
            elif type_ == "Box Plot":
                fig = px.box(df, y=col, points="outliers")
            else:
                cat = st.selectbox("Split By", cat_cols, key="ridge_cat_2")
                if cat:
                    fig = px.violin(df, x=col, color=cat, box=True)
                else:
                    fig = px.violin(df, x=col)
            fig.update_layout(template=theme)
            st.plotly_chart(fig, width="stretch")

    # ==========================
    # 7. HIERARCHY
    # ==========================
    with tab_hier:
        type_ = st.radio("Hierarchical Info", [
                         "Sunburst", "Treemap", "Funnel"], horizontal=True)
        if type_ == "Funnel":
            stage_col = st.selectbox("Stage", cat_cols, key="funnel_stage")
            val_col = st.selectbox("Value", num_cols, key="funnel_val")
            if val_col:
                funnel_data = df.groupby(stage_col)[val_col].sum(
                ).reset_index().sort_values(val_col, ascending=False)
                st.plotly_chart(px.funnel(funnel_data, x=val_col, y=stage_col,
                                text=val_col if show_labels else None, template=theme), width="stretch")
            else:
                st.warning("Select Value column.")
        else:
            path = st.multiselect("Hierarchy Path", cat_cols, default=cat_cols[:2] if len(
                cat_cols) >= 2 else cat_cols)
            val = st.selectbox(
                "Size By", ["Count"] + num_cols, index=0, key="hier_val")
            v_arg = val if val != "Count" else None
            if type_ == "Sunburst":
                fig = px.sunburst(df, path=path, values=v_arg)
            else:
                fig = px.treemap(df, path=path, values=v_arg)
            fig.update_layout(template=theme)
            st.plotly_chart(fig, width="stretch")

    # ==========================
    # 8. RELATIONSHIPS PRO
    # ==========================
    with tab_rel:
        mode = st.radio("View Mode", ["Facet Grid", "Sankey Flow",
                        "Animated Bubble", "Contour", "Parallel Coords"], horizontal=True)

        if mode == "Facet Grid":
            c1, c2, c3, c4 = st.columns(4)
            x = c1.selectbox("X Axis", num_cols, index=0, key="fg_x")
            y = c2.selectbox("Y Axis", num_cols, index=1 if len(
                num_cols) > 1 else 0, key="fg_y")
            row = c3.selectbox("Row Split", ["None"] + cat_cols, key="fg_row")
            col = c4.selectbox("Col Split", ["None"] + cat_cols, key="fg_col")
            trend = st.checkbox("Show Trendline (OLS)", value=False)

            if row != "None" and df[row].nunique() > 10:
                st.warning(
                    "⚠️ High cardinality on Row Split! Chart may be crowded.")

            row_arg = row if row != "None" else None
            col_arg = col if col != "None" else None

            # Fix: Ensure logic handles None correctly for Plotly
            if x and y:
                if row_arg or col_arg:
                    # Check for None explicitly to avoid Plotly errors
                    st.plotly_chart(px.scatter(df, x=x, y=y, facet_row=row_arg, facet_col=col_arg, trendline="ols" if trend else None,
                                    template=theme, title=f"Facet: {x} vs {y}"), use_container_width=True, height=600 if row_arg else 450)
                else:
                    st.plotly_chart(px.scatter(df, x=x, y=y, trendline="ols" if trend else None,
                                    template=theme, title=f"Scatter: {x} vs {y}"), use_container_width=True)
            else:
                st.warning("Please select X and Y variables.")

        elif mode == "Sankey Flow":
            if len(cat_cols) < 2:
                st.warning("Need at least 2 categorical columns.")
            else:
                src = st.selectbox("Source", cat_cols, index=0, key="sank_src")
                tgt = st.selectbox("Target", cat_cols, index=1, key="sank_tgt")
                if src != tgt:
                    st.plotly_chart(px.parallel_categories(
                        df, dimensions=[src, tgt], template=theme), use_container_width=True)
                else:
                    st.warning("Select distinct columns.")

        elif mode == "Animated Bubble":
            if not date_cols:
                st.warning("Need Time column.")
            else:
                time = st.selectbox("Time Axis", date_cols, key="anim_time")
                x = st.selectbox("X", num_cols, index=0, key="anim_x")
                y = st.selectbox("Y", num_cols, index=1, key="anim_y")
                sz = st.selectbox("Size", num_cols, index=2 if len(
                    num_cols) > 2 else 0, key="anim_sz")
                clr = st.selectbox("Color", cat_cols, key="anim_c")

                df['Frame'] = df[time].dt.strftime('%Y-%m')
                anim_df = df.groupby(['Frame', clr])[
                    [x, y, sz]].mean().reset_index().sort_values('Frame')
                st.plotly_chart(px.scatter(anim_df, x=x, y=y, animation_frame='Frame', animation_group=clr, size=sz, color=clr, hover_name=clr, range_x=[
                                df[x].min(), df[x].max()], range_y=[df[y].min(), df[y].max()], template=theme, title="Evolution"), use_container_width=True)

        elif mode == "Contour":
            x = st.selectbox("X", num_cols, index=0, key="cnt_x")
            y = st.selectbox("Y", num_cols, index=1, key="cnt_y")
            if x and y:
                st.plotly_chart(px.density_contour(df, x=x, y=y, marginal_x="histogram",
                                marginal_y="histogram", template=theme), use_container_width=True)

        elif mode == "Parallel Coords":
            dims = st.multiselect("Dimensions", num_cols, default=num_cols[:5])
            c = st.selectbox("Color Scale", num_cols, index=0, key="par_c")
            if dims and c:
                st.plotly_chart(px.parallel_coordinates(
                    df, dimensions=dims, color=c, template=theme), use_container_width=True)
