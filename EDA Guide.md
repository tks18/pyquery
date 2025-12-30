# 📘 PyQuery EDA Field Manual & Reference Guide

This document is the definitive reference for the Exploratory Data Analysis (EDA) module. It details every Tab, Chart, and Metric accessible in the application.

---

## 🏗️ 1. Overview Tab
**Purpose**: Initial health check and strategic scan of the entire dataset.

### A. 🧬 Dataset DNA (Dashboard)
A high-level summary of data quality and structure.

| Metric/Visual | Definition | Interpretation Guide |
| :--- | :--- | :--- |
| **Rows** | Total count of records. | N/A |
| **Columns** | Total count of features. | N/A |
| **Missing Cells** | Percentage of cells with `null` or `NaN` values. | **< 1%**: Excellent.<br>**1-5%**: Standard.<br>**> 10%**: Requires cleaning (imputation). |
| **Duplicates** | Count of perfectly identical rows. | **> 0**: Potential data quality issue. Duplicates distort statistical tests. Remove them if accidental. |
| **Data Types (Donut)** | Ratio of Numeric vs. Categorical vs. Date columns. | Helps identifying if columns were loaded incorrectly (e.g., "Sales" loaded as Text). |
| **Missing Breakdown (Bar)** | Counts of missing values per column. | Identifies specific "dirty" columns. |

### B. 🚀 Strategic Brief
An automated scan that finds the strongest linear relationships and trends without any user input.

*   **Logic**: Calculates Correlation Coefficient ($r$) between all pairs of numeric columns.
*   **High Impact Cards**: Displays the top 3 pairs with $|r| > 0.6$.
    *   **Score**: The absolute correlation coefficient ($0.0 - 1.0$).
    *   **Delta**: "High Impact" if score > 0.7.

### C. 📸 Feature Snapshot
Detailed descriptive statistics for every column in a table format.

| Column | Definition |
| :--- | :--- |
| **Missing %** | Progress bar of missing data. |
| **Unique** | Cardinality (count of distinct values). High cardinality = continuous; Low = categorical. |
| **Min/Max/Mean** | Basic distribution stats (Numeric only). |
| **Examples** | 3 non-null sample values. Useful to spot formatting errors (e.g., "$100" vs "100"). |

### D. 📐 Multidimensional Pivot
A flexible tool to aggregate data across two dimensions.

*   **Heatmap View**: Visualizes the aggregated value (e.g., Sum of Sales) as color intensity.
    *   **X-Axis**: Column Group.
    *   **Y-Axis**: Row Group.
    *   **Color**: Value (Darker = Higher).

---

## 🧠 2. ML Laboratory
**Purpose**: Use machine learning algorithms to uncover patterns invisible to the naked eye.

### Module A: Diagnostic Model Sandbox
Trains an interpretable model to quantify relationship strengths between a **Target** and **Features**.

**1. Model Performance Metrics:**
| Metric | Definition | Good vs Bad |
| :--- | :--- | :--- |
| **Test Score** | $R^2$ (Regression) or Accuracy (Classification) on unseen test data. | **> 0.7** is strong. **< 0.3** implies the features don't explain the target. |
| **Confusion Matrix** | (Classification Only) Heatmap of Actual vs. Predicted classes. | Diagonal cells = Correct.<br>Off-diagonal = Errors. High values off-diagonal indicate specific class confusion. |
| **ROC Curve** | (Classification Only) Trade-off between True Positive and False Positive rate. | **AUC (Area Under Curve)**:<br>**0.5**: Random guessing.<br>**1.0**: Perfect.<br>**> 0.75**: Reliable model. |
| **Residuals** | (Regression Only) Difference between Actual and Predicted values. | **Shape**: Should look like a normal bell curve centered at 0.<br>**Skewed**: Model is biased (under/over-predicting). |

**2. Feature Importance:**
*   **Permutation Importance**: Shows how much the model's error increases if a feature is shuffled (randomized). Long bar = Critical feature.
*   **Coefficients (Linear Models)**:
    *   **Positive (+)**: As feature increases, Target increases.
    *   **Negative (-)**: As feature increases, Target decreases.
    *   **Magnitude**: Size of impact (per unit change).

### Module B: Advanced Clustering (Segmentation)
Groups similar data points into "Clusters".

**1. Optimization (Elbow & Silhouette):**
*   **Elbow Plot (Inertia)**: Shows error vs. Number of Clusters ($K$). Look for the "bend" or "elbow" point where improvement slows down.
*   **Silhouette Score**: Measures cluster separation (-1 to 1).
    *   **> 0.5**: Dense, distinct clusters.
    *   **~ 0.2**: Weak/Overlapping structure.
    *   **< 0**: Wrong assignment.

**2. Visuals:**
*   **2D Cluster Map (PCA)**: Result projected onto 2 dimensions. Points with same color should roughly group together.
*   **Cluster DNA (Profile)**: Heatmap of *average feature values* per cluster. Use this to name the segments (e.g., "Cluster 1 = High Spend, Low Age").

### Module C: Explainable Anomalies
Detects outliers using Isolation Forest.

*   **Contamination**: Expected percentage of outliers (Sensitivity).
*   **Outlier Map**: Scatter plot highlighting normal (Grey) vs. anomalous (Red) points.
*   **Contextual Profiler**: Compares the average values of Outliers vs. Normal data to explain *why* they are weird (e.g. "Outliers have 300% higher Income").

---

## 🔮 3. Decision Simulator
**Purpose**: "What-If" Analysis using a predictive Digital Twin.

### 🎮 Scenario Simulator
*   **Sliders**: Allow you to manipulate input variables (Drivers) within their real-world range.
*   **Predicted Outcome**: Real-time updated prediction based on the slider positions.
*   **Feature Contribution (Waterfall)**: Break down of the prediction.
    *   **Green Bar**: This factor pushed the prediction *up* (relative to average).
    *   **Red Bar**: This factor pushed the prediction *down*.
    *   **Base Value**: The average outcome if nothing is known.

### 🩺 Model Diagnostics
*   **Actual vs Predicted Plot**:
    *   **Red Dashed Line**: Perfect prediction ($y=x$).
    *   **Points**: Should cluster tightly around the line. Points far from line are errors.

---

## 🎯 4. Target Analysis
**Purpose**: Deep-dive analysis of a single variable's dependencies.

### Mode: Numeric Target
*   **Drivers (Correlation Bar)**: Features most strongly correlated with the target.
*   **Bivariate Scatter**: Plot of Target ($Y$) vs. Top Driver ($X$). red line indicates the trend direction.

### Mode: Categorical Target
*   **Class Balance**: Pie chart showing distribution of classes (e.g. "Churned" vs "Retained"). Imbalance (>80/20) can hurt ML models.
*   **Feature Separation (Box Plots)**: Checks if a numeric feature helps distinguish classes.
    *   *Good Separation*: The numeric ranges (boxes) for each class do **not** overlap.
    *   *Bad Separation*: Boxes are at the same level (feature provides no info).

---

## 📈 5. Time Series
**Purpose**: Trends, Seasonality, and Forecasting.

### Analysis Modes
1.  **📈 Trend Tracker**:
    *   **Actual Line**: Raw data.
    *   **Smoothed Line**: Moving average (removing noise).
    *   **Total Growth**: % change from start to end.
2.  **🔍 Decomposition**: Splits the series into 3 parts:
    *   **Trend**: Long-term direction.
    *   **Seasonal**: Repeating cyclic pattern (e.g., Weekly/Yearly).
    *   **Residual**: Random noise (what's left).
3.  **🔮 Future Forecast**:
    *   **Method**: Uses Holt-Winters Exponential Smoothing (or Linear Trend fallback).
    *   **Confidence Interval (Shaded)**: The range where 95% of future values are expected to fall. Wider shading = Lower confidence.
4.  **🌡️ Heatmap View**: X-Axis = Month, Y-Axis = Year. Great for visualizing seasonality (e.g., dark columns in December).
5.  **⚠️ Anomaly Detection**:
    *   **Z-Score**: Number of standard deviations from the rolling mean.
    *   **Red Dots**: Points that deviate significantly (>3 Sigma) from the local trend.

---

## 📊 6. Distributions
**Purpose**: Understanding the shape and spread of data.

### Statistical Metrics Panel
| Metric | Definition | Decision Guide |
| :--- | :--- | :--- |
| **Skewness** | Measure of asymmetry. | **0**: Symmetric.<br>**> 1**: Right-skewed (Long tail of high values). Use Log Transform.<br>**< -1**: Left-skewed (Long tail of low values). |
| **Kurtosis** | "Tail heaviness" (Outliers). | **> 3**: Heavy tails (More extreme outliers than Normal).<br>**< 3**: Light tails (Fewer outliers). |
| **Normality Test** | (Shapiro/K^2) Tests if data is Gaussian. | **p-value < 0.05**: Not Normal. <br>**p-value > 0.05**: Likely Normal (Bell Curve). |

### Charts
*   **Histogram**: Frequency bars.
    *   **KDE Curve**: Smooth probability density estimate.
    *   **Normal Fit (Red)**: What the curve *would* look like if it were perfectly normal.
*   **QQ Plot**: Plot of Data Quantiles vs. Theoretical Normal Quantiles.
    *   **Interpretation**: If dots fall on the red line, data is Normal. Curvature indicates Skewness/Kurtosis.
*   **ECDF**: Cumulative percentage plot. Reading: "Y% of data is less than X".

---

## 🕸️ 7. Hierarchy & Concentration
**Purpose**: Analyzing market structure, inequality, and nested categories.

### Concentration Metrics
Used for analyzing Market Share, Wealth Distribution, or Portfolio Concentration.

| Metric | Definition | Thresholds (Standard) |
| :--- | :--- | :--- |
| **HHI (Herfindahl-Hirschman)** | Market Concentration Index. | **< 1,500**: Competitive (fragmented).<br>**1,500 - 2,500**: Moderately concentrated.<br>**> 2,500**: Highly concentrated (Oligopoly/Monopoly). |
| **Gini Coefficient** | Inequality Score. | **0.0**: Perfect Equality.<br>**1.0**: Perfect Inequality.<br>**> 0.5**: Very high disparity (Pareto principle active). |
| **Top 3 Share** | % held by top 3 groups. | simple dominance metric. |

### Visuals
*   **Sunburst**: Multi-level pie chart (Center = Root).
*   **Treemap**: Nested rectangles. Usage: Comparing relative sizes of categories.

---

## 🔗 8. Relationships
**Purpose**: Multivariate Analysis and Correlation.

### Association Metrics
Automatically selects the right test based on data types.

| Data Types | Method Used | Metric Range | Interpretation |
| :--- | :--- | :--- | :--- |
| **Num vs Num** | **Pearson Correlation** | -1.0 to +1.0 | **>0.7**: Strong Positive.<br>**<-0.7**: Strong Negative. |
| **Cat vs Cat** | **Cramér's V** (Chi-Square) | 0.0 to 1.0 | **>0.5**: Strong Association.<br>**<0.1**: No Association. |
| **Num vs Cat** | **ANOVA (F-Test)** | F-Stat | **High F**: The numeric mean is significantly different across categories. |

### Visuals
*   **Scatter Matrix (SPLOM)**: Grid of all-pairs scatter plots. Good for spotting patterns across 3-4 variables simultaneously.
*   **Sankey Diagram** (Future): Flow visualization.
*   **3D Scatter**: Rotatable 3D plot. Useful for finding separation planes in clusters.
*   **Heatmap (Density)**: colored 2D grid. Uses density instead of points to handle overplotting.
