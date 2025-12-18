import streamlit as st
import polars as pl
import time

def render_profile_tab(current_lf):
    st.header("🔍 Dataset Health Check")

    # Analyze the CURRENT transformed state
    if st.button("Generate Profile (Takes time for large data)"):
        with st.spinner("Profiling..."):
            try:
                # We only take a sample for profiling to be fast
                sample_df = current_lf.limit(10000).collect()

                # Metrics
                st.markdown(
                    f"**Rows:** {sample_df.height} (Sampled) | **Columns:** {sample_df.width}")

                # Column Details
                for col in sample_df.columns:
                    with st.expander(f"Column: **{col}** ({sample_df[col].dtype})"):
                        c1, c2, c3, c4 = st.columns(4)
                        n_null = sample_df[col].null_count()
                        pct_null = (n_null / sample_df.height) * 100
                        n_unique = sample_df[col].n_unique()

                        c1.metric("Nulls", f"{n_null} ({pct_null:.1f}%)")
                        c2.metric("Unique", n_unique)

                        # Type specific stats
                        if sample_df[col].dtype in [pl.Float64, pl.Int64]:
                            c3.metric("Min", f"{sample_df[col].min()}")
                            c4.metric("Max", f"{sample_df[col].max()}")
                            st.bar_chart(sample_df[col].value_counts().sort(
                                "count", descending=True).limit(20))
                        elif sample_df[col].dtype == pl.Utf8:
                            st.write("Top Values:")
                            st.dataframe(sample_df[col].value_counts().sort(
                                "count", descending=True).limit(5))

            except Exception as e:
                st.error(f"Profiling Failed: {e}")
