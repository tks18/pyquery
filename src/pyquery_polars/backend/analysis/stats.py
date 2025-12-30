import pandas as pd
import polars as pl
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from statsmodels.tsa.seasonal import seasonal_decompose
from scipy import stats as sp_stats
from scipy.stats import pearsonr
from scipy.stats import chi2_contingency
from scipy.stats import f_oneway
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression


class StatsEngine:
    """Backend module for Statistical Analysis."""

    @staticmethod
    def analyze_correlations(df: pd.DataFrame, num_cols: List[str], threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Scan for strong correlations in numeric columns.
        Returns a list of insights.
        """
        insights = []
        if len(num_cols) < 2:
            return insights

        try:
            # Use Pandas for correlation matrix (NumPy backend is fast enough for sampled data)
            corr_matrix = df[num_cols].corr().abs()
            np.fill_diagonal(corr_matrix.values, 0)

            # Find top correlations
            # Unstack to get pairs
            pairs = corr_matrix.unstack().sort_values(ascending=False)  # type: ignore

            # De-duplicate pairs (A-B is same as B-A) by keeping index where A < B
            # Or just take top N unique?
            # Simple approach: Top N largest values
            top_corrs = pairs.nlargest(5)  # Look at top 5

            seen = set()
            for idx, score in top_corrs.items():
                if not isinstance(idx, tuple):
                    continue
                f1, f2 = idx
                if score > threshold:
                    # Dedupe key
                    key = tuple(sorted((f1, f2)))
                    if key in seen:
                        continue
                    seen.add(key)

                    insights.append({
                        "type": "Correlation",
                        "score": float(score),
                        "title": f"Strong Link: {f1} & {f2}",
                        "desc": f"These variables move together ({score:.2f}).",
                        "action": f"👉 **Now What**: Investigate if '{f1}' drives '{f2}'. Influencing one may control the other.",
                        "vars": (f1, f2)
                    })
        except Exception as e:
            print(f"Correlation Error: {e}")

        return insights

    @staticmethod
    def analyze_trends(df: pd.DataFrame, date_cols: List[str], num_cols: List[str]) -> List[Dict[str, Any]]:
        """
        Scan for significant growth or decline trends over time.
        """
        insights = []
        if not date_cols or df.empty:
            return insights

        dt = date_cols[0]
        try:
            # Sort by date
            df_sorted = df.sort_values(dt)

            for val in num_cols[:3]:  # Limit scan to top 3 numeric cols for performance
                try:
                    first = df_sorted[val].iloc[0]
                    last = df_sorted[val].iloc[-1]

                    if first != 0:
                        change = (last - first) / first
                        if abs(change) > 0.15:  # 15% threshold
                            direction = "Growth" if change > 0 else "Decline"
                            insights.append({
                                "type": "Trend",
                                "score": abs(change),
                                "title": f"{direction} Alert: {val}",
                                "desc": f"{val} has {direction.lower()}d by {abs(change):.1%} over the period.",
                                "action": f"👉 **Now What**: {'Capitalize on momentum' if change > 0 else 'Diagnose the drop'} in {val}."
                            })
                except:
                    continue
        except Exception:
            pass

        # Sort by magnitude
        insights.sort(key=lambda x: x['score'], reverse=True)
        return insights

    @staticmethod
    def get_pivot_summary(df: pd.DataFrame, index_col: str, value_col: str, agg_func: str) -> pd.DataFrame:
        """
        Generate a quick pivot summary (Top 20).
        """
        try:
            pivot = df.groupby(index_col)[value_col].agg(
                agg_func).reset_index()
            pivot = pivot.sort_values(value_col, ascending=False).head(20)
            return pivot
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def perform_ts_decomposition(df: pd.DataFrame, date_col: str, val_col: str, freq_str: str = "D") -> Dict[str, Any]:
        """
        Perform basic Time Series Decomposition (Trend, Seasonality, Residual).
        Uses simple Moving Average + Detrending if statsmodels is missing.
        """
        try:
            # Ensure Sorted & Clean
            df_ts = df.dropna(subset=[date_col, val_col]
                              ).sort_values(date_col).copy()
            df_ts.set_index(date_col, inplace=True)

            # Heuristic Period based on user freq selection (e.g. 'D' -> 7 for weekly pattern, or 30?)
            # Let's guess: 'D' -> 7, 'M' -> 12, 'H' -> 24
            period = 7
            if freq_str in ['M', 'MS', 'ME']:
                period = 12
            elif freq_str in ['H', 'h']:
                period = 24
            elif freq_str in ['Q', 'QS']:
                period = 4

            if len(df_ts) < period * 2:
                return {"error": "Not enough data for decomposition"}

            # Try Statsmodels
            try:
                res = seasonal_decompose(
                    df_ts[val_col], period=period, model='additive', extrapolate_trend='freq') # type: ignore
                return {
                    "dates": df_ts.index,
                    "trend": res.trend,
                    "seasonal": res.seasonal,
                    "resid": res.resid,
                    "observed": res.observed,
                    "success": True
                }
            except ImportError:
                # Fallback: Simple Moving Average Decomposition
                trend = df_ts[val_col].rolling(
                    window=period, center=True).mean()
                detrended = df_ts[val_col] - trend
                # Naive seasonal: just 0 for now or average of detrended?
                # Let's just return Trend to avoid misleading seasonality
                return {
                    "dates": df_ts.index,
                    "trend": trend,
                    "seasonal": pd.Series(0, index=df_ts.index),
                    "resid": df_ts[val_col] - trend.fillna(0),
                    "observed": df_ts[val_col],
                    "success": True,
                    "note": "Statsmodels not found, using Moving Average."
                }
            except Exception as e:
                return {"error": str(e)}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def detect_ts_outliers(df: pd.DataFrame, date_col: str, val_col: str, sensitivity: float = 3.0) -> pd.DataFrame:
        """
        Detect anomalies using Z-Score on Rolling Residuals.
        """
        try:
            df_ts = df.sort_values(date_col).copy()

            # 1. Calculate Trend (Rolling Median is robust)
            rolling_med = df_ts[val_col].rolling(
                window=7, center=True, min_periods=1).median()

            # 2. Residuals
            resid = df_ts[val_col] - rolling_med

            # 3. Z-Score of Resid
            resid_mean = resid.mean()
            resid_std = resid.std()

            if resid_std == 0:
                return pd.DataFrame()

            z_score = (resid - resid_mean).abs() / resid_std

            outliers = df_ts[z_score > sensitivity]
            return outliers
        except:
            return pd.DataFrame()

    @staticmethod
    def get_distribution_stats(df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Calculates advanced distribution metrics and normality tests."""
        try:
            series = df[col].dropna()
            if series.empty:
                return {}

            stats = {
                "Mean": series.mean(),
                "Median": series.median(),
                "Std Dev": series.std(),
                "Skewness": series.skew(),
                "Kurtosis": series.kurtosis(),
                "Min": series.min(),
                "Max": series.max(),
                "Count": len(series)
            }

            # Normality Test
            try:
                # Shapiro is robust for N < 5000.
                # If sample size is exactly 5000, it might warn, but usually fine.
                if len(series) <= 5000:
                    stat, p = sp_stats.shapiro(series)
                    stats["Normality_Test"] = "Shapiro-Wilk"
                else:
                    stat, p = sp_stats.normaltest(series)
                    stats["Normality_Test"] = "D'Agostino's K^2"

                stats["Normality_p"] = p
                stats["Is_Normal"] = p > 0.05

            except ImportError:
                stats["Normality_Test"] = "Not Available (No Scipy)"

            return stats
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_outliers_iqr(df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Get outliers via IQR method."""
        try:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            return df[(df[col] < lower) | (df[col] > upper)]
        except:
            return pd.DataFrame()

    @staticmethod
    def get_target_correlations(df: pd.DataFrame, target: str, num_cols: List[str]) -> pd.DataFrame:
        """Calculate correlation of all numeric cols against a target."""
        try:
            if target not in df.columns:
                return pd.DataFrame()

            # Ensure target is treated as numeric for correlation
            cols = [c for c in num_cols if c in df.columns]
            if target not in cols:
                # If target is not in num_cols list but is in df, check if we can append it
                if pd.api.types.is_numeric_dtype(df[target]):
                    cols.append(target)
                else:
                    return pd.DataFrame()  # Can't correlate categorical

            if len(cols) < 2:
                return pd.DataFrame()

            # Calculate Correlation
            # dropna to avoid errors
            corr = df[cols].corrwith(
                df[target], numeric_only=True).reset_index()
            corr.columns = ["Feature", "Correlation"]
            corr["AbsCorr"] = corr["Correlation"].abs()

            # Sort by absolute strength, but drop the target itself (corr=1.0)
            corr = corr[corr["Feature"] != target]
            return corr.sort_values("AbsCorr", ascending=False)
        except Exception as e:
            return pd.DataFrame()

    @staticmethod
    def get_concentration_metrics(df: pd.DataFrame, group_col: str, val_col: str) -> Dict[str, Any]:
        """Calculate market concentration metrics (Gini, HHI) for a hierarchy."""
        try:
            if df.empty or val_col not in df.columns or group_col not in df.columns:
                return {}

            # Aggregate to get total value per group
            gdf = df.groupby(group_col)[val_col].sum().reset_index()
            values = gdf[val_col].values.astype(float)

            # cleanup
            values = values[values > 0]
            if len(values) == 0:
                return {}

            # Sort desc
            values = np.sort(values.astype(float))[::-1]
            total = values.sum()
            if total == 0:
                return {}

            # Shares
            shares = values / total

            # 1. HHI (Herfindahl-Hirschman Index) -> Sum of squared shares * 10000
            # Range 0 to 10,000. <1500 competitive, >2500 concentrated.
            hhi = (shares ** 2).sum() * 10000

            # 2. Gini importance (Inequality)
            # Standard Gini calculation
            vals_asc = np.sort(values)
            n = len(vals_asc)
            index = np.arange(1, n + 1)
            gini = ((2 * np.sum(index * vals_asc)) /
                    (n * total)) - ((n + 1) / n)

            # 3. Top N Share
            top_3 = shares[:3].sum()

            return {
                "HHI": hhi,
                "Gini": gini,
                "Top_3_Share": top_3,
                "Total_Groups": n,
                "Total_Value": total
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_pairwise_association(df: pd.DataFrame, col1: str, col2: str) -> Dict[str, Any]:
        """Calculate association between two columns dynamically."""
        try:
            # Check cols exist
            if col1 not in df.columns or col2 not in df.columns:
                return {}

            # Drop NA
            sub = df[[col1, col2]].dropna()
            if sub.empty:
                return {}

            c1_num = pd.api.types.is_numeric_dtype(sub[col1])
            c2_num = pd.api.types.is_numeric_dtype(sub[col2])

            res = {"method": "Unknown", "score": 0.0,
                   "p_value": None, "note": ""}

            if c1_num and c2_num:
                # Pearson
                corr = sub[col1].corr(sub[col2])
                res["method"] = "Pearson Correlation"
                res["score"] = corr
                res["note"] = "Linear Relationship (-1 to +1)"
                # P-value for Pearson?
                try:
                    s, p = pearsonr(sub[col1], sub[col2])
                    res["p_value"] = p
                except:
                    pass

            elif not c1_num and not c2_num:
                # Cat-Cat: Cramer's V or Chi2
                try:
                    contingency = pd.crosstab(sub[col1], sub[col2])
                    # Remove low freq?
                    chi2, p, dof, ex = chi2_contingency(contingency)

                    # Cramer's V calculation
                    n = contingency.sum().sum()
                    min_dim = min(contingency.shape) - 1
                    if min_dim == 0:
                        min_dim = 1  # Avoid div by 0

                    cv = np.sqrt(chi2 / (n * min_dim))

                    res["method"] = "Cramer's V (Chi²)"
                    res["score"] = cv
                    res["p_value"] = p
                    res["note"] = "Association Strength (0 to 1)"
                except:
                    res["note"] = "Chi2 Failed (Scipy missing?)"

            else:
                # Mixed: One-Way ANOVA (Num by Cat)
                num_c, cat_c = (col1, col2) if c1_num else (col2, col1)

                # Enforce minimal groups
                if sub[cat_c].nunique() < 2:
                    return {"note": "Categorical column needs >1 group"}

                try:
                    groups = [group[num_c].values for name,
                              group in sub.groupby(cat_c)]
                    if len(groups) > 1:
                        f_stat, p = f_oneway(*groups)
                        res["method"] = "ANOVA (F-Test)"
                        res["score"] = f_stat
                        res["p_value"] = p
                        res["note"] = "Difference in Means (Higher F = More Different)"
                    else:
                        res["note"] = "Not enough groups"
                except:
                    res["note"] = "ANOVA Failed"

            return res
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_dataset_health(df: pd.DataFrame) -> Dict[str, Any]:
        """Compute dataset health metadata: shape, nulls, dupes, memory."""
        try:
            health = {
                "rows": len(df),
                "cols": len(df.columns),
                "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                "duplicates": df.duplicated().sum(),
                "total_cells": df.size,
                "total_nulls": df.isna().sum().sum(),
            }
            health["null_pct"] = (
                health["total_nulls"] / health["total_cells"]) if health["total_cells"] > 0 else 0

            # Type Breakdown
            types = df.dtypes.value_counts().astype(str).to_dict()
            # Clean keys
            health["types"] = {str(k): v for k, v in types.items()}

            return health
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_feature_summary(df: pd.DataFrame) -> pd.DataFrame:
        """Generate a summary dataframe for all columns."""
        try:
            summary_data = []
            for col in df.columns:
                series = df[col]
                dtype = str(series.dtype)
                n_unique = series.nunique()
                n_null = series.isna().sum()

                # Examples
                examples = series.dropna().unique()[:3].tolist()
                ex_str = ", ".join(map(str, examples))

                entry = {
                    "Feature": col,
                    "Type": dtype,
                    "Nulls": n_null,
                    "Missing %": (n_null / len(df)),  # ratio 0-1
                    "Unique": n_unique,
                    "Examples": ex_str
                }

                # Stats if numeric
                if pd.api.types.is_numeric_dtype(series):
                    entry["Min"] = float(series.min()) if not pd.isna(
                        series.min()) else None
                    entry["Max"] = float(series.max()) if not pd.isna(
                        series.max()) else None
                    entry["Mean"] = float(series.mean()) if not pd.isna(
                        series.mean()) else None
                else:
                    entry["Min"] = None
                    entry["Max"] = None
                    entry["Mean"] = None

                summary_data.append(entry)

            return pd.DataFrame(summary_data)
        except Exception as e:
            return pd.DataFrame()

    @staticmethod
    def get_ts_forecast(df: pd.DataFrame, date_col: str, val_col: str, periods: int = 30, freq: str = "D") -> Dict[str, Any]:
        """
        Generate time series forecast using Holt-Winters (Exponential Smoothing) or Linear Fallback.
        Returns dictionary with historical and forecast data.
        """
        try:
            # Prepare Series
            ts = df.set_index(pd.to_datetime(df[date_col]))[
                [val_col]].sort_index()
            # Resample to ensure regularity
            ts = ts.resample(freq).mean().interpolate()

            # Require minimum data points
            if len(ts) < 10:
                return {"error": "Not enough data points (need 10+)"}

            # 1. Try Holt-Winters (Exponential Smoothing) - Good for Seasonality
            try:
                # Simple heuristic: additive trend/seasonality
                # If series has negatives or zeros, multiplicative fails. Safe default = additive.
                model = ExponentialSmoothing(
                    ts[val_col], seasonal=None, trend='add', seasonal_periods=None).fit()

                # Forecast
                pred = model.forecast(periods)

                # Confidence Intervals (Simulated for ES as statsmodels simple API doesn't always return them easily for ES)
                # Or switch to ARIMA?
                # Let's use simple residue-based CI for robustness without heavy ARIMA deps.
                resid_std = model.resid.std()
                lower = pred - 1.96 * resid_std
                upper = pred + 1.96 * resid_std

                method = "Exponential Smoothing (Holt-Winters)"

            except ImportError:
                # Fallback to Linear Regression if statsmodels missing
                method = "Linear Trend (Fallback)"

                # Create ordinal X
                ts['ordinal'] = ts.index.map(pd.Timestamp.toordinal)
                X = ts[['ordinal']]
                y = ts[val_col]

                lr = LinearRegression()
                lr.fit(X, y)

                # Future Dates
                last_date = ts.index[-1]
                future_dates = pd.date_range(
                    start=last_date + pd.Timedelta(1, unit=freq), periods=periods, freq=freq) # type: ignore
                X_future = pd.DataFrame(
                    {'ordinal': future_dates.map(pd.Timestamp.toordinal)})

                pred_vals = lr.predict(X_future)
                pred = pd.Series(pred_vals, index=future_dates)

                # CI (Prediction Interval approximate)
                # Calcluate std of residuals
                y_pred_hist = lr.predict(X)
                resid_std = (y - y_pred_hist).std()
                lower = pred - 1.96 * resid_std
                upper = pred + 1.96 * resid_std

            except Exception as e:
                # Generic Fallback
                return {"error": f"Model Fit Failed: {e}"}

            return {
                "method": method,
                "history_dates": ts.index.tolist(),
                "history_values": ts[val_col].tolist(),
                "forecast_dates": pred.index.tolist(),
                "forecast_values": pred.tolist(),
                "lower_bound": lower.tolist(),
                "upper_bound": upper.tolist()
            }

        except Exception as e:
            return {"error": str(e)}
