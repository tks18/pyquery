from typing import List, Dict, Any

import pandas as pd
import polars as pl
import numpy as np

# Stats & Scipy Imports
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
                    df_ts[val_col],
                    period=period,
                    model='additive',
                    extrapolate_trend='freq'  # type: ignore[arg-type]
                )
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
                    start=last_date + pd.Timedelta(
                        1,
                        unit=freq  # type: ignore[arg-type]
                    ),
                    periods=periods,
                    freq=freq
                )
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

    @staticmethod
    def get_kde_curve(series: pd.Series, x_range: np.ndarray, bandwidth: str = 'scott') -> Dict[str, Any]:
        """
        Calculate KDE (Kernel Density Estimation) curve for distribution overlay.

        Args:
            series: Data series to estimate density
            x_range: X-axis values to evaluate KDE at
            bandwidth: Bandwidth selection method ('scott', 'silverman', or float)

        Returns:
            Dictionary with x_values, y_values, and bandwidth used
        """
        try:
            # Drop NaN values
            clean_series = series.dropna()
            if len(clean_series) < 2:
                return {"error": "Need at least 2 data points for KDE"}

            # Calculate KDE using scipy
            kernel = sp_stats.gaussian_kde(clean_series, bw_method=bandwidth)
            y_values = kernel(x_range)

            return {
                "x_values": x_range.tolist() if isinstance(x_range, np.ndarray) else x_range,
                "y_values": y_values.tolist() if isinstance(y_values, np.ndarray) else y_values,
                "bandwidth": float(
                    kernel.factor  # type: ignore[arg-type]
                ) if hasattr(kernel, 'factor') else bandwidth
            }
        except ImportError:
            return {"error": "Scipy required for KDE calculation"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_normal_fit(series: pd.Series, x_range: np.ndarray) -> Dict[str, Any]:
        """
        Fit a normal distribution to data and generate curve points.

        Args:
            series: Data series to fit
            x_range: X-axis values to evaluate fit at

        Returns:
            Dictionary with x_values, y_values, mu (mean), and sigma (std dev)
        """
        try:
            # Drop NaN values
            clean_series = series.dropna()
            if len(clean_series) < 2:
                return {"error": "Need at least 2 data points for normal fit"}

            # Fit normal distribution
            mu, sigma = sp_stats.norm.fit(clean_series)

            # Calculate PDF values
            y_values = sp_stats.norm.pdf(x_range, mu, sigma)

            return {
                "x_values": x_range.tolist() if isinstance(x_range, np.ndarray) else x_range,
                "y_values": y_values.tolist() if isinstance(y_values, np.ndarray) else y_values,
                "mu": float(mu),
                "sigma": float(sigma)
            }
        except ImportError:
            return {"error": "Scipy required for normal fit"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_qq_plot_data(series: pd.Series, distribution: str = 'norm') -> Dict[str, Any]:
        """
        Generate QQ plot data (theoretical quantiles vs observed quantiles).

        Args:
            series: Data series to analyze
            distribution: Distribution to compare against (default: 'norm')

        Returns:
            Dictionary with theoretical quantiles, observed values, and correlation
        """
        try:
            # Drop NaN values
            clean_series = series.dropna()
            if len(clean_series) < 3:
                return {"error": "Need at least 3 data points for QQ plot"}

            # Generate QQ plot data
            # probplot returns ((theoretical_quantiles, ordered_values), (slope, intercept, r))
            (osm, osr), (slope, intercept, r) = sp_stats.probplot(
                clean_series, dist=distribution, fit=True)

            return {
                "theoretical": osm.tolist() if isinstance(osm, np.ndarray) else osm,
                "observed": osr.tolist() if isinstance(osr, np.ndarray) else osr,
                "slope": float(slope),  # type: ignore
                "intercept": float(intercept),  # type: ignore
                "correlation": float(r)  # type: ignore
            }
        except ImportError:
            return {"error": "Scipy required for QQ plot"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_rolling_stats(df: pd.DataFrame, date_col: str, value_col: str,
                          window: int, stat_type: str = 'mean', center: bool = True) -> pd.Series:
        """
        Calculate rolling window statistics for time series smoothing.

        Args:
            df: DataFrame with time series data
            date_col: Name of date/time column
            value_col: Name of value column
            window: Rolling window size
            stat_type: Type of statistic ('mean', 'median', 'std', 'min', 'max')
            center: Whether to center the window

        Returns:
            Pandas Series with rolling statistic values
        """
        try:
            # Ensure sorted by date
            df_sorted = df.sort_values(date_col).copy()

            # Get rolling window
            rolling = df_sorted[value_col].rolling(
                window=window, center=center, min_periods=1)

            # Apply requested statistic
            if stat_type == 'mean':
                result = rolling.mean()
            elif stat_type == 'median':
                result = rolling.median()
            elif stat_type == 'std':
                result = rolling.std()
            elif stat_type == 'min':
                result = rolling.min()
            elif stat_type == 'max':
                result = rolling.max()
            else:
                # Default to mean
                result = rolling.mean()

            return result
        except Exception as e:
            # Return empty series on error
            return pd.Series(dtype=float)

    @staticmethod
    def get_quantiles(series: pd.Series, quantile_list: List[float]) -> Dict[float, float]:
        """
        Calculate multiple quantiles at once.

        Args:
            series: Data series
            quantile_list: List of quantiles to calculate (e.g., [0.25, 0.5, 0.75])

        Returns:
            Dictionary mapping quantile to value
        """
        try:
            # Drop NaN values
            clean_series = series.dropna()
            if clean_series.empty:
                return {}

            # Calculate all quantiles at once (more efficient)
            quantiles = clean_series.quantile(quantile_list)

            # Convert to dictionary
            if isinstance(quantiles, pd.Series):
                return {
                    float(
                        q  # type: ignore[arg-type]
                    ): float(v) for q, v in quantiles.items()
                }
            else:
                # Single quantile
                return {float(quantile_list[0]): float(quantiles)}
        except Exception as e:
            return {}

    @staticmethod
    def get_group_contrast(df: pd.DataFrame, group_col: str, group_a: Any, group_b: Any,
                           num_cols: List[str], cat_cols: List[str]) -> pd.DataFrame:
        """
        Calculate statistical difference (Effect Size) between two groups for all features.

        Args:
            df: DataFrame
            group_col: Column to group by
            group_a: Value for Group A
            group_b: Value for Group B
            num_cols: List of numeric columns
            cat_cols: List of categorical columns

        Returns:
            DataFrame with 'Feature', 'Type', 'Effect_Size', 'P_Value', 'Metric_A', 'Metric_B'
        """
        try:
            # Filter Data
            df_a = df[df[group_col] == group_a]
            df_b = df[df[group_col] == group_b]

            if df_a.empty or df_b.empty:
                return pd.DataFrame()

            results = []

            # 1. Numeric Analysis (Cohen's D)
            for col in num_cols:
                if col == group_col:
                    continue

                try:
                    s_a = df_a[col].dropna()
                    s_b = df_b[col].dropna()

                    if len(s_a) < 2 or len(s_b) < 2:
                        continue

                    mean_a, mean_b = s_a.mean(), s_b.mean()
                    std_a, std_b = s_a.std(), s_b.std()

                    # Pooled Std Dev
                    n_a, n_b = len(s_a), len(s_b)
                    pooled_std = np.sqrt(
                        ((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))

                    if pooled_std == 0:
                        continue

                    cohens_d = (mean_a - mean_b) / pooled_std

                    # T-Test
                    _, p_val = sp_stats.ttest_ind(s_a, s_b, equal_var=False)

                    results.append({
                        "Feature": col,
                        "Type": "Numeric",
                        "Effect_Size": abs(cohens_d),  # Magnitude
                        # Sign indicates direction (A > B vs B > A)
                        "Direction": cohens_d,
                        "P_Value": p_val,
                        "Metric_A": f"{mean_a:.2f}",
                        "Metric_B": f"{mean_b:.2f}",
                        "Desc": f"Diff: {(mean_a - mean_b):.2f}"
                    })
                except:
                    continue

            # 2. Categorical Analysis (Cramer's V or TVD)
            # For simple contrast, Total Variation Distance (TVD) is intuitive: .5 * sum|prob_a - prob_b|
            for col in cat_cols:
                if col == group_col:
                    continue

                try:
                    vc_a = df_a[col].value_counts(normalize=True)
                    vc_b = df_b[col].value_counts(normalize=True)

                    # Align indexes
                    all_cats = set(vc_a.index) | set(vc_b.index)
                    tvd = 0
                    max_diff = 0
                    top_diff_cat = ""

                    for cat in all_cats:
                        p_a = vc_a.get(cat, 0)
                        p_b = vc_b.get(cat, 0)
                        diff = abs(p_a - p_b)
                        tvd += diff

                        if diff > max_diff:
                            max_diff = diff
                            top_diff_cat = cat

                    tvd = 0.5 * tvd

                    if tvd > 0:
                        results.append({
                            "Feature": col,
                            "Type": "Categorical",
                            # Scale to comparable roughly with Cohen's d (0-1 range typically, d can be >1) -> Heuristic
                            "Effect_Size": tvd * 2,
                            "Direction": 0,  # N/A
                            "P_Value": None,  # Chi2 could be done but complex for just row-subset
                            "Metric_A": f"Top: {vc_a.idxmax() if not vc_a.empty else ''}",
                            "Metric_B": f"Top: {vc_b.idxmax() if not vc_b.empty else ''}",
                            "Desc": f"Biggest Shift: '{top_diff_cat}' (Δ {max_diff:.1%})"
                        })
                except:
                    continue

            return pd.DataFrame(results).sort_values("Effect_Size", ascending=False)

        except Exception as e:
            return pd.DataFrame()

    @staticmethod
    def get_advanced_profile(df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """
        Deep profiling for any column type (Numeric or Categorical) with advanced metrics.
        """
        try:
            series = df[col]
            clean = series.dropna()

            stats = {
                "count": len(series),
                "missing": series.isna().sum(),
                "missing_p": series.isna().mean(),
                "unique": series.nunique(),
                "dtype": str(series.dtype)
            }

            if pd.api.types.is_numeric_dtype(series):
                # Numeric Metrics
                stats.update({
                    "mean": clean.mean(),
                    "median": clean.median(),
                    "std": clean.std(),
                    "min": clean.min(),
                    "max": clean.max(),
                    "skew": clean.skew(),
                    "kurtosis": clean.kurtosis(),
                    "zeros": (clean == 0).sum(),
                    "negatives": (clean < 0).sum(),
                    "type": "Numeric"
                })

                # Top Correlated Features (Correlation Scan)
                try:
                    # Select only numeric columns for correlation
                    num_df = df.select_dtypes(include=[np.number])
                    if num_df.shape[1] > 1:
                        # Corr with target
                        corrs = num_df.corrwith(
                            clean).abs().sort_values(ascending=False)
                        # Drop self
                        corrs = corrs.drop(col, errors='ignore').head(3)
                        stats["correlations"] = corrs.to_dict()
                except:
                    stats["correlations"] = {}

            else:
                # Categorical / Text Metrics
                clean_str = clean.astype(str)
                stats.update({
                    "mode": clean_str.mode()[0] if not clean_str.empty else "N/A",
                    "type": "Categorical"
                })

                # String Lengths
                lens = clean_str.str.len()
                stats.update({
                    "len_min": int(lens.min()) if not lens.empty else 0,
                    "len_max": int(lens.max()) if not lens.empty else 0,
                    "len_avg": float(lens.mean()) if not lens.empty else 0,
                })

                # Semantic Detection (Heuristic)
                patterns = {
                    "Email": r"[^@]+@[^@]+\.[^@]+",
                    "URL": r"http[s]?://",
                    "Phone": r"\+?[\d\s-]{10,}",
                    "Date": r"\d{4}-\d{2}-\d{2}",
                    "IP": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
                }

                # Sample for regex perf
                sample = clean_str if len(
                    clean_str) < 5000 else clean_str.sample(5000)
                detected = {}
                for name, pat in patterns.items():
                    matches = sample.str.contains(pat, regex=True).sum()
                    if matches > 0:
                        detected[name] = int(matches)
                stats["semantic_entities"] = detected

                # Top/Rare
                vc = clean_str.value_counts()
                stats["top_counts"] = vc.head(10).to_dict()
                stats["rare_count"] = (vc == 1).sum()

            return stats

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_comparative_stats(df: pd.DataFrame, group_col: str, group_a: Any, group_b: Any,
                              nums: List[str], cats: List[str]) -> pd.DataFrame:
        """
        Comparison with rigorous hypothesis testing (Mann-Whitney, Chi2).
        """
        try:
            df_a = df[df[group_col] == group_a]
            df_b = df[df[group_col] == group_b]

            if df_a.empty or df_b.empty:
                return pd.DataFrame()

            results = []

            # 1. Numeric (Mann-Whitney U + T-Test + Effect Size)
            for col in nums:
                if col == group_col:
                    continue
                try:
                    s_a = df_a[col].dropna()
                    s_b = df_b[col].dropna()
                    if len(s_a) < 5 or len(s_b) < 5:
                        continue

                    # Effect Size (Cohen's d)
                    m_a, m_b = s_a.mean(), s_b.mean()
                    sd_a, sd_b = s_a.std(), s_b.std()
                    pooled_sd = np.sqrt(
                        ((len(s_a)-1)*sd_a**2 + (len(s_b)-1)*sd_b**2) / (len(s_a)+len(s_b)-2))
                    cohen_d = (m_a - m_b) / pooled_sd if pooled_sd > 0 else 0

                    # Mann-Whitney U (Non-parametric test for difference in distribution)
                    u_stat, p_mw = sp_stats.mannwhitneyu(
                        s_a, s_b, alternative='two-sided')

                    # T-Test (Parametric)
                    t_stat, p_tt = sp_stats.ttest_ind(
                        s_a, s_b, equal_var=False)

                    results.append({
                        "Feature": col,
                        "Type": "Numeric",
                        "Effect_Size": abs(cohen_d),
                        "Direction": cohen_d,
                        "P_Value_MW": p_mw,
                        "P_Value_TT": p_tt,
                        "Mean_A": m_a,
                        "Mean_B": m_b,
                        "Median_A": s_a.median(),
                        "Median_B": s_b.median(),
                        "Desc": f"Diff: {m_a - m_b:.2f}"
                    })
                except:
                    continue

            # 2. Categorical (Chi-Square)
            for col in cats:
                if col == group_col:
                    continue
                try:
                    # Contingency Table
                    # We need full df filtered to just these two groups
                    sub = df[df[group_col].isin([group_a, group_b])]
                    contingency = pd.crosstab(sub[col], sub[group_col])

                    if contingency.empty:
                        continue

                    # Chi2 Test
                    chi2, p_chi2, dof, ex = sp_stats.chi2_contingency(
                        contingency)

                    # Cramer's V (Effect Size)
                    n = contingency.sum().sum()
                    min_dim = min(contingency.shape) - 1
                    cramers_v = np.sqrt(
                        chi2 / (n * min_dim)) if min_dim > 0 and n > 0 else 0

                    # Dominant category shift
                    # Get prop difference max
                    norm = pd.crosstab(
                        sub[col], sub[group_col], normalize='columns')
                    diffs = (norm[group_a] - norm[group_b]).abs()
                    max_diff = diffs.max()
                    top_cat = diffs.idxmax()

                    results.append({
                        "Feature": col,
                        "Type": "Categorical",
                        "Effect_Size": cramers_v,
                        "Direction": 0,  # N/A
                        "P_Value_MW": p_chi2,  # Map to same col for simpler processing
                        "P_Value_TT": None,
                        "Mean_A": 0, "Mean_B": 0,
                        "Desc": f"Shift: {top_cat} (Δ {max_diff:.1%})"
                    })
                except:
                    continue

            return pd.DataFrame(results).sort_values("Effect_Size", ascending=False)
        except:
            return pd.DataFrame()
