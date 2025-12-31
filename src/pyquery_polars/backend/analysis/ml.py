import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union

# Sklearn Imports
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder, PolynomialFeatures
from sklearn.model_selection import train_test_split, cross_val_score, KFold, learning_curve
from sklearn.metrics import confusion_matrix, r2_score, mean_absolute_error, accuracy_score, silhouette_samples, silhouette_score, roc_curve, precision_recall_curve, auc
from sklearn.inspection import permutation_importance
from sklearn.utils import resample
from sklearn.inspection import partial_dependence

HAS_SKLEARN = True


class MLEngine:
    """Backend module for Machine Learning Operations."""

    @staticmethod
    def check_sklearn() -> bool:
        return HAS_SKLEARN

    @staticmethod
    def prepare_data(df: pd.DataFrame, features: List[str], target: Optional[str] = None) -> Tuple[pd.DataFrame, Any]:
        """Prepare X and y for modeling. Handles basic encoding/filling."""
        X = df[features].copy()
        X = X.fillna(0)

        # Simple Label Encoding for categoricals
        for c in X.select_dtypes(include=['object', 'category']).columns:
            X[c] = LabelEncoder().fit_transform(X[c].astype(str))

        y = None
        if target:
            y = df[target].copy().fillna(0)  # Basic fill
            # Encode target if categorical
            if y.dtype == 'object' or hasattr(y, 'cat'):
                y = LabelEncoder().fit_transform(y.astype(str))

        return X, y

    @staticmethod
    def run_diagnostic_model(df: pd.DataFrame, target: str, features: List[str], model_type: str, is_categorical: bool, use_poly: bool = False) -> Dict[str, Any]:
        """
        Run a diagnostic model (Regression or Classification) with advanced diagnostics.
        """
        if not HAS_SKLEARN:
            return {"error": "Scikit-Learn not installed"}

        X, y = MLEngine.prepare_data(df, features, target)
        if y is None:
            return {"error": "Target not found"}

        # Polynomial Features (Interactions)
        if use_poly:
            # Degree 2, Interaction Only to keep it sane
            poly = PolynomialFeatures(
                degree=2, interaction_only=True, include_bias=False)
            X_poly = poly.fit_transform(X)
            # Reconstruct DF for names
            new_feats = poly.get_feature_names_out(features)
            X = pd.DataFrame(X_poly, columns=new_feats)

        # Define Models
        models_to_run = []
        if model_type == "Auto-Pilot (Best Model)":
            if is_categorical:
                models_to_run = [
                    ("Logistic", LogisticRegression(max_iter=500)),
                    ("Random Forest", RandomForestClassifier(random_state=42))
                ]
            else:
                models_to_run = [
                    ("Linear", LinearRegression()),
                    ("Ridge", Ridge()),
                    ("Lasso", Lasso()),
                    ("Random Forest", RandomForestRegressor(random_state=42))
                ]
        else:
            # Single Model Mapping
            if "Linear" in model_type:
                models_to_run = [("Linear", LinearRegression())]
            elif "Ridge" in model_type:
                models_to_run = [("Ridge", Ridge())]
            elif "Lasso" in model_type:
                models_to_run = [("Lasso", Lasso())]
            elif "Logistic" in model_type:
                models_to_run = [
                    ("Logistic", LogisticRegression(max_iter=500))]
            else:
                models_to_run = [("Random Forest", RandomForestClassifier(
                    random_state=42) if is_categorical else RandomForestRegressor(random_state=42))]

        # Evaluation Loop
        best_model = None
        best_score = -999
        best_name = ""
        best_cv_results = []
        best_name = ""
        best_cv_results = []

        # 1. Train/Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        for name, model in models_to_run:
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            scores = cross_val_score(
                model, X, y, cv=kf, scoring='accuracy' if is_categorical else 'r2')
            mean_score = scores.mean()

            if mean_score > best_score:
                best_score = mean_score
                best_model = model
                best_name = name
                best_cv_results = scores

        if best_model is None:
            return {"error": "No suitable model found"}

        # 2. Final Fit
        best_model.fit(X_train, y_train)
        y_pred = best_model.predict(X_test)

        # 3. Advanced Diagnostics
        diagnostics = {}

        # Learning Curve (Bias/Variance)
        # Learning Curve (Bias/Variance)
        try:
            lc_res = learning_curve(
                best_model, X, y, cv=5, n_jobs=-1,
                train_sizes=np.linspace(0.1, 1.0, 5)
            )
            # Unpack first 3 safely (train_sizes, train_scores, test_scores)
            train_sizes, train_scores, test_scores = lc_res[:3]

            diagnostics['learning_curve'] = {
                "train_sizes": train_sizes,
                "train_mean": np.mean(train_scores, axis=1),
                "test_mean": np.mean(test_scores, axis=1)
            }
        except:
            pass

        metrics = {}
        if is_categorical:
            metrics['accuracy'] = accuracy_score(y_test, y_pred)
            metrics['confusion_matrix'] = confusion_matrix(y_test, y_pred)

            # ROC / PR
            if hasattr(best_model, "predict_proba"):
                y_prob = best_model.predict_proba(X_test)  # type: ignore
                # Handle multi-class vs binary
                if len(np.unique(y)) == 2:
                    fpr, tpr, _ = roc_curve(y_test, y_prob[:, 1])
                    precision, recall, _ = precision_recall_curve(
                        y_test, y_prob[:, 1])
                    diagnostics['roc'] = {"fpr": fpr,
                                          "tpr": tpr, "auc": auc(fpr, tpr)}
                    diagnostics['pr'] = {
                        "precision": precision, "recall": recall}
        else:
            metrics['r2'] = r2_score(y_test, y_pred)
            metrics['mae'] = mean_absolute_error(y_test, y_pred)
            metrics['residuals'] = y_test - y_pred
            diagnostics['residuals'] = metrics['residuals']
            diagnostics['actual'] = y_test
            diagnostics['predicted'] = y_pred

        return {
            "model_name": best_name,
            "best_score": best_score,
            "cv_scores": best_cv_results,
            "metrics": metrics,
            "model_obj": best_model,
            "train_cols": X.columns.tolist(),
            "diagnostics": diagnostics,
            "X_test": X_test,
            "y_test": y_test,
            "y_pred": y_pred
        }

    @staticmethod
    def get_permutation_importance(model, X, y):
        """Calculate permutation importance."""
        result = permutation_importance(
            model, X, y, n_repeats=10, random_state=42)
        return result['importances_mean']

    @staticmethod
    def cluster_data(df: pd.DataFrame, features: List[str], n_clusters: int = 3, algo: str = "K-Means", optimize_k: bool = False) -> Dict[str, Any]:
        """Run Clustering (KMeans/DBSCAN) with support for Elbow Method Optimization."""
        if not HAS_SKLEARN:
            return {"error": "Sklearn missing"}

        try:
            X, _ = MLEngine.prepare_data(df, features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Optimization: Elbow Method
            elbow_data = {}
            if optimize_k and algo == "K-Means":
                inertias = []
                ks = range(2, 11)
                for k in ks:
                    km = KMeans(n_clusters=k, random_state=42).fit(X_scaled)
                    inertias.append(km.inertia_)
                elbow_data = {"k": list(ks), "inertia": inertias}

            labels = None
            if algo == "K-Means":
                km = KMeans(n_clusters=n_clusters,
                            random_state=42).fit(X_scaled)
                labels = km.labels_
            elif algo == "DBSCAN":
                # Hardcoded eps/min_samples for now, or pass as kwargs?
                dbs = DBSCAN(eps=0.5, min_samples=5).fit(X_scaled)
                labels = dbs.labels_
            else:
                return {"error": "Unknown algo"}

            # Metrics
            sil_score = -1.0
            if len(set(labels)) > 1:
                sil_score = silhouette_score(X_scaled, labels)

            # Projection (PCA)
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(X_scaled)

            # Result DF
            res_df = df.copy()
            res_df['Cluster'] = labels.astype(str)
            res_df['PCA1'] = coords[:, 0]
            res_df['PCA2'] = coords[:, 1]

            # Cluster Profiles (Mean of features per cluster)
            # Need strict numeric DF
            num_df = res_df[features].select_dtypes(include=[np.number])
            num_df['Cluster'] = labels.astype(str)
            profiles = num_df.groupby('Cluster').mean().to_dict()

            return {
                "df": res_df,
                "silhouette_score": sil_score,
                "labels": labels,
                "elbow_data": elbow_data,
                "centroids": profiles
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def detect_anomalies(df: pd.DataFrame, features: List[str], contamination: float = 0.05) -> Dict[str, Any]:
        """Run Isolation Forest for anomalies."""
        if not HAS_SKLEARN:
            return {"error": "Sklearn missing"}

        try:
            X, _ = MLEngine.prepare_data(df, features)
            X_scaled = StandardScaler().fit_transform(X)

            iso = IsolationForest(contamination=contamination, random_state=42)
            preds = iso.fit_predict(X_scaled)

            res_df = df.copy()
            res_df['Type'] = np.where(preds == -1, 'Outlier', 'Normal')
            return {"df": res_df, "model": iso}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def train_simulator_model(df: pd.DataFrame, target: str, features: List[str], model_type: str = "Random Forest") -> Any:
        """Train a predictive model for the decision simulator with detailed metrics."""
        if not HAS_SKLEARN:
            return None
        try:
            X, y = MLEngine.prepare_data(df, features, target)
            if y is None:
                return {"error": "Target not found"}

            # Detect Type
            is_cat = False
            if y.dtype == 'object' or hasattr(y, 'cat') or pd.api.types.is_object_dtype(y):
                is_cat = True
            elif len(np.unique(y)) <= 20 and pd.api.types.is_integer_dtype(y):
                # Heuristic: <20 unique values might be categorical
                pass

            # Split for Evaluation
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)

            model = None
            if is_cat:
                if model_type == "Linear Model":
                    model = LogisticRegression(max_iter=1000)
                else:  # Default RF
                    model = RandomForestClassifier(
                        n_estimators=50, random_state=42)
            else:
                if model_type == "Linear Model":
                    model = LinearRegression()
                else:
                    model = RandomForestRegressor(
                        n_estimators=50, random_state=42)

            model.fit(X_train, y_train)

            # Metrics
            score = 0
            metrics = {}
            y_pred = model.predict(X_test)

            if is_cat:
                score = accuracy_score(y_test, y_pred)
                metrics['accuracy'] = score
                try:
                    metrics['confusion_matrix'] = confusion_matrix(
                        y_test, y_pred).tolist()
                except:
                    pass
            else:
                score = r2_score(y_test, y_pred)
                metrics['r2'] = score
                metrics['mae'] = mean_absolute_error(y_test, y_pred)
                # Sample residuals for plotting (limit size)
                residuals = (y_test - y_pred)
                # Keep top 200 for charts to be light
                limit = 200
                if len(residuals) > limit:
                    metrics['residuals'] = residuals[:limit].tolist()
                    metrics['y_test'] = y_test[:limit].tolist()
                    metrics['y_pred'] = y_pred[:limit].tolist()
                else:
                    metrics['residuals'] = residuals.tolist()
                    metrics['y_test'] = y_test.tolist()
                    metrics['y_pred'] = y_pred.tolist()

            # Note: We return the split-trained model so metrics align with its state.

            return {
                "model": model,
                # Return X (full) for slider bounds, but we know model is trained on subset.
                # This is acceptable for simulator range estimation.
                "X_sample": X,
                "score": score,
                "metrics": metrics,
                "is_categorical": is_cat
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def train_surrogate_explainer(blackbox_model, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Train a surrogate linear model (LIME-like) to explain the complex model globally/locally.
        Returns coefficients to allow "Contribution" analysis in frontend.
        """
        try:
            # 1. Get Predictions from Complex Model
            preds = blackbox_model.predict(X)

            # 2. Train Linear Surrogate
            # If classification, preds are class labels? No, use predict_proba for better explanation if possible.
            # But RandomForestClassifier.predict() returns classes.
            # Let's stick to Regressor always for Surrogate interpretation (interpreting the class label as 0/1 or probability).

            # If classifier, we fit on probability of class 1 if binary, or just class ID if multi?
            # Simplest for MVP: Fit on the output directly.

            surrogate = LinearRegression()
            surrogate.fit(X, preds)

            # 3. Store Explainer Data
            return {
                "coefs": dict(zip(X.columns, surrogate.coef_)),
                "intercept": surrogate.intercept_,
                "means": X.mean().to_dict(),
                "r2_surrogate": surrogate.score(X, preds)  # fidelity check
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_prediction_contribution(explainer_data: Dict[str, Any], input_row: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Compute feature contributions for a specific input row using Surrogate weights.
        Contribution = (Input_Val - Mean_Val) * Coeff
        """
        try:
            contributions = []
            means = explainer_data.get('means', {})
            coefs = explainer_data.get('coefs', {})

            for feat, val in input_row.items():
                if feat in coefs:
                    mean_val = means.get(feat, 0)
                    c = coefs[feat]
                    # Impact: How much did this deviate from average prediction?
                    impact = (val - mean_val) * c
                    contributions.append({
                        "Feature": feat,
                        "Input": val,
                        "Mean": mean_val,
                        "Contribution": impact,
                        "Coeff": c
                    })
            return sorted(contributions, key=lambda x: abs(x['Contribution']), reverse=True)
        except:
            return []

    @staticmethod
    def get_partial_dependence(df: pd.DataFrame, target: str, feature: str, features_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate Partial Dependence for a feature on target.
        Trains a temporary Random Forest to estimate the dependence.
        """
        if not HAS_SKLEARN:
            return {}
        try:

            # Use provided feature list or default to all numeric/categorical
            valid_feats = features_list if features_list else df.select_dtypes(
                include=[np.number, 'category', 'object']).columns.tolist()
            if target in valid_feats:
                valid_feats.remove(target)

            X, y = MLEngine.prepare_data(df, valid_feats, target)

            # Determine mode
            is_cat = y.nunique() < 10 or str(y.dtype) == 'object'

            # Quick Proxy Model
            model = RandomForestClassifier(n_estimators=20, max_depth=5, random_state=42) if is_cat \
                else RandomForestRegressor(n_estimators=20, max_depth=5, random_state=42)
            model.fit(X, y)

            # Calculate PDP
            # Note: feature must be in X.columns
            if feature not in X.columns:
                return {"error": f"Feature {feature} not found in model input."}

            pdp_res = partial_dependence(
                # type: ignore
                model, X, [feature], grid_resolution=50, kind='average')

            return {
                "x": pdp_res['grid_values'][0],
                "y": pdp_res['average'][0]
            }
        except Exception as e:
            return {"error": f"PDP Error: {str(e)}"}

    @staticmethod
    def get_silhouette_samples(df: pd.DataFrame, features: List[str], labels: Any) -> Dict[str, Any]:
        """Calculate Silhouette Coefficient for each sample."""
        if not HAS_SKLEARN:
            return {}
        try:
            X, _ = MLEngine.prepare_data(df, features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            if len(set(labels)) < 2:
                return {"error": "Need > 1 cluster"}

            sample_scores = silhouette_samples(X_scaled, labels)

            return {
                "scores": sample_scores,
                "mean_score": float(sample_scores.mean())  # type: ignore
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_clustering_optimization(df: pd.DataFrame, features: List[str], max_k: int = 8) -> Dict[str, Any]:
        """Run K-Means for K=2..max_k and return Inertia + Silhouette."""
        if not HAS_SKLEARN:
            return {}
        try:
            X, _ = MLEngine.prepare_data(df, features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            wcss = []
            sil = []
            ks = range(2, max_k + 1)

            for k in ks:
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                km.fit(X_scaled)
                wcss.append(km.inertia_)
                if len(X) > k:
                    # Silhouette is expensive for large data, sample if needed
                    if len(X) > 2000:
                        # Sample for speed
                        X_samp, labels_samp = resample(
                            X_scaled, km.labels_, n_samples=1000, random_state=42)  # type: ignore
                        sil.append(silhouette_score(X_samp, labels_samp))
                    else:
                        sil.append(silhouette_score(X_scaled, km.labels_))
                else:
                    sil.append(0)

            return {
                "k": list(ks),
                "wcss": wcss,
                "silhouette": sil
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_classification_curves(model, X_test, y_test) -> Dict[str, Any]:
        """Compute ROC and PR Curve data."""
        if not HAS_SKLEARN:
            return {}
        try:
            res = {}
            # ROC requires probabilities
            if hasattr(model, "predict_proba"):
                # Check classes
                if len(np.unique(y_test)) == 2:
                    y_prob = model.predict_proba(
                        X_test)[:, 1]  # Positive class

                    fpr, tpr, _ = roc_curve(y_test, y_prob)
                    roc_auc = auc(fpr, tpr)

                    res['roc'] = {
                        'fpr': fpr.tolist(),
                        'tpr': tpr.tolist(),
                        'auc': roc_auc
                    }

            return res
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_sensitivity(model: Any, base_inputs: Dict[str, float], feature_stats: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Calculate local sensitivity (Tornado Data).
        Perturbs each feature by +/- 1 Std Dev (or 10% range) and measures output change.
        """
        results = []
        base_df = pd.DataFrame([base_inputs])
        # Ensure correct column order
        cols = model.feature_names_in_ if hasattr(
            model, "feature_names_in_") else list(base_inputs.keys())
        base_df = base_df[cols]

        base_pred = model.predict(base_df)[0]

        for feat, val in base_inputs.items():
            if feat not in cols:
                continue

            # Determine perturbation size
            std = feature_stats.get(feat, {}).get(
                'std', abs(val)*0.1 if val != 0 else 1.0)
            if std == 0:
                std = 1.0

            # Low Case
            low_input = base_df.copy()
            low_input[feat] = val - std
            low_pred = model.predict(low_input)[0]

            # High Case
            high_input = base_df.copy()
            high_input[feat] = val + std
            high_pred = model.predict(high_input)[0]

            # Impact
            change = abs(high_pred - low_pred)

            results.append({
                "Feature": feat,
                "Base": base_pred,
                "Low_Val": val - std,
                "High_Val": val + std,
                "Low_Pred": low_pred,
                "High_Pred": high_pred,
                "Spread": high_pred - low_pred,
                "Impact_Abs": change
            })

        return pd.DataFrame(results).sort_values("Impact_Abs", ascending=True)

    @staticmethod
    def run_monte_carlo(model: Any, base_inputs: Dict[str, float], feature_stats: Dict[str, Dict[str, float]], n_sims: int = 1000) -> Dict[str, Any]:
        """
        Run Monte Carlo Simulation for Risk Analysis.
        Injects Gaussian noise into inputs based on their historical Std Dev.
        """
        # 1. Generate Inputs
        cols = model.feature_names_in_ if hasattr(
            model, "feature_names_in_") else list(base_inputs.keys())
        sim_data = {}

        for col in cols:
            base_val = base_inputs.get(col, 0)
            # Default noise: 10% of std dev (small uncertainty) or 5% of value
            std = feature_stats.get(col, {}).get('std', abs(base_val)*0.1)
            if std == 0:
                std = 0.01

            # Random samples
            # 0.5 factor to keep it realistic
            noise = np.random.normal(0, std * 0.5, n_sims)
            sim_data[col] = base_val + noise

        sim_df = pd.DataFrame(sim_data)

        # 2. Predict
        preds = model.predict(sim_df)

        # 3. Analyze Results
        return {
            "predictions": preds,
            "mean": np.mean(preds),
            "p5": np.percentile(preds, 5),
            "p95": np.percentile(preds, 95),
            "std": np.std(preds),
            "sim_df": sim_df  # Return inputs too if needed for detailed analysis
        }
