from typing import cast
import streamlit as st
import polars as pl
import pandas as pd  # Streamlit charts often work effectively with pandas or native lists
from pyquery_polars.backend.engine import PyQueryEngine


def render_profile_tab(dataset_name):  # Takes name
    if st.button("Generate Profile", type="primary"):
        engine = cast(PyQueryEngine, st.session_state.get('engine'))
        if not engine:
            return

        recipe = st.session_state.recipe_steps

        with st.spinner("Analyzing data..."):
            result = engine.get_profile(dataset_name, recipe)

        if not result:
            st.error("Failed to generate profile.")
            return

        if "error" in result:
            st.error(f"Profiling Error: {result['error']}")
            return

        # Unpack
        df_sample = result['sample']
        summary = result['summary']
        dtypes = result['dtypes']
        nulls = result['nulls']
        shape = result['shape']

        # --- 1. OVERVIEW TILES ---
        st.subheader("Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows (Sampled)", shape[0])
        c2.metric("Columns", shape[1])

        # Total cells
        total_cells = shape[0] * shape[1]
        total_nulls = sum(nulls.values())
        null_pct = (total_nulls / total_cells * 100) if total_cells > 0 else 0
        c3.metric("Missing Values", f"{total_nulls} ({null_pct:.1f}%)")

        st.divider()

        # --- 2. SUMMARY TABLE ---
        st.subheader("Statistical Summary")
        st.dataframe(summary, width="stretch")

        st.divider()

        # --- 3. COLUMN DETAILS ---
        st.subheader("Column Analysis")

        # Convert Polars numeric columns to Pandas for simple charting if needed
        # Or just use list of values

        cols = df_sample.columns
        for col in cols:
            with st.expander(f"📍 {col}", expanded=False):
                col_type = dtypes[col]
                n_null = nulls[col]
                n_unique = df_sample[col].n_unique()

                mc1, mc2, mc3 = st.columns(3)
                mc1.info(f"Type: **{col_type}**")
                mc2.warning(f"Nulls: **{n_null}**")
                mc3.success(f"Unique: **{n_unique}**")

                # Distribution Chart for Numerics
                # Check if slightly numeric (Int/Float)
                is_numeric = "Int" in col_type or "Float" in col_type
                if is_numeric and shape[0] > 0:
                    st.caption("Distribution (Sample)")
                    st.bar_chart(df_sample[col].to_list())
                elif "Date" in col_type or "Time" in col_type:
                    st.caption("Temporal Distribution (Sample)")
                    # Simple line chart of counts probably better? or just values?
                    # Let's just dump values for now
                    st.line_chart(df_sample[col].to_list())
