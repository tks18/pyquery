import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
from .core import EDAContext


def render_overview(ctx: EDAContext):
    """Render the Overview Tab (Strategic Brief, Pivot, etc.)"""

    # st.caption("Review dataset health and generate strategic insights.") # Too simple

    # 1. Data Collection (Auto-Run if possible, or Button)
    # Ideally Overview should be fast and auto-load. 5k rows is trivial.
    if ctx.df is None:
        try:
            df = ctx.lf.collect().to_pandas()
        except:
            return
    else:
        df = ctx.df

    engine = ctx.engine

    # --- A. DATASET DNA (Dashboard) ---
    with st.container(border=True):
        st.write("#### 🧬 Dataset DNA")

        # Compute Health
        health = engine.analysis.stats.get_dataset_health(df)
        if "error" in health:
            st.error(health['error'])
            return

        # Metrics Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{health.get('rows', 0):,}")
        c2.metric("Columns", health.get('cols', 0))
        c3.metric("Missing Cells", f"{health.get('null_pct', 0):.1%}",
                  delta="Critical" if health.get('null_pct', 0) > 0.2 else "Healthy", delta_color="inverse")
        c4.metric("Duplicates", f"{health.get('duplicates', 0):,}",
                  delta="Clean" if health.get('duplicates', 0) == 0 else "Warning", delta_color="inverse")

        # Visuals Row
        c_v1, c_v2 = st.columns([1, 2])

        # 1. Type Distribution (Donut)
        types = health.get('types', {})
        if types:
            type_df = pd.DataFrame(list(types.items()),
                                   columns=['Type', 'Count'])
            fig_types = px.pie(type_df, names='Type', values='Count',
                               hole=0.4, title="Data Types", template=ctx.theme)
            fig_types.update_traces(textinfo='value+label')
            c_v1.plotly_chart(fig_types)

        # 2. Missing Values (Bar)
        null_counts = df.isnull().sum()
        null_counts = null_counts[null_counts > 0].sort_values(ascending=False)
        if not null_counts.empty:
            null_df = pd.DataFrame(
                {'Feature': null_counts.index, 'Missing Count': null_counts.values})
            fig_null = px.bar(null_df, x='Feature', y='Missing Count', title="Missing Values Breakdown",
                              color='Missing Count', color_continuous_scale='Reds', template=ctx.theme)
            c_v2.plotly_chart(fig_null)
        else:
            c_v2.info("✨ No missing values detected in this sample.")

    # --- B. STRATEGIC BRIEF ---
    if len(ctx.num_cols) > 0:
        st.write("#### 🚀 Strategic Brief")

        insights = []
        insights.extend(
            ctx.engine.analysis.stats.analyze_correlations(df, ctx.num_cols))
        if ctx.date_cols:
            insights.extend(ctx.engine.analysis.stats.analyze_trends(
                df, ctx.date_cols, ctx.num_cols))

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
        else:
            st.info("No dominant linear relationships or trends found.")

    # --- C. FEATURE SNAPSHOT ---
    with st.expander("📸 Feature Snapshot (Detailed Stats)", expanded=False):
        summ = engine.analysis.stats.get_feature_summary(df)
        if not summ.empty:
            st.dataframe(summ, hide_index=True, column_config={
                "Missing %": st.column_config.ProgressColumn(
                    "Missing %", format="%.1f%%", min_value=0, max_value=1,
                    help="Percentage of missing values"
                ),
                "Mean": st.column_config.NumberColumn("Mean", format="%.2f"),
                "Min": st.column_config.NumberColumn("Min", format="%.2f"),
                "Max": st.column_config.NumberColumn("Max", format="%.2f"),
            })

    # --- D. SMART PIVOT ---
    st.divider()
    st.write("#### 📐 Multidimensional Pivot")
    st.caption("Aggregate and visualize relationships between dimensions.")

    if len(ctx.cat_cols) > 0 and len(ctx.num_cols) > 0:
        c1, c2, c3, c4 = st.columns(4)
        p_row = c1.selectbox("Row Group", ctx.cat_cols, index=0, key="p_row_n")

        # Optional Col Group
        rem_cats = [c for c in ctx.cat_cols if c != p_row]
        p_col = c2.selectbox("Column Group (Optional)", [
                             "(None)"] + rem_cats, key="p_col_n")

        p_val = c3.selectbox("Value", ctx.num_cols, index=0, key="p_val_n")
        p_agg = c4.selectbox(
            "Aggregation", ["mean", "sum", "count", "min", "max", "median"], key="p_agg_n")

        if st.button("Generate Pivot Analysis", type="primary"):
            try:
                # Use Pandas for flexible pivot (since data is collected)
                if p_col != "(None)":
                    pivot_res = df.pivot_table(
                        index=p_row, columns=p_col, values=p_val, aggfunc=p_agg)
                    # Heatmap
                    st.plotly_chart(px.imshow(pivot_res, text_auto=True, aspect="auto",
                                              title=f"{p_agg.title()} of {p_val} by {p_row} & {p_col}",
                                              color_continuous_scale="Viridis", template=ctx.theme))
                else:
                    pivot_res = df.groupby(p_row)[p_val].agg(
                        p_agg).reset_index().sort_values(p_val, ascending=False).head(20)
                    st.plotly_chart(px.bar(pivot_res, x=p_row, y=p_val, text_auto=True,
                                           title=f"Top {p_row} by {p_agg} {p_val}",
                                           template=ctx.theme, color=p_val))

            except Exception as e:
                st.error(f"Pivot Error: {e}")
    else:
        st.warning("Need both numeric and categorical columns for pivot.")
