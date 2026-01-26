"""
Profile component module.

Provides dataset profiling functionality.
"""

import streamlit as st
import polars as pl
import pandas as pd

from pyquery_polars.frontend.base import BaseComponent


class ProfileComponent(BaseComponent):
    """
    Component for rendering dataset profiling analysis.
    """

    def render(self, dataset_name: str) -> None:
        """
        Render the profile tab.

        Args:
            dataset_name: Name of the dataset to profile
        """
        if st.button("Generate Profile", type="primary"):
            if not self.engine:
                return

            recipe = self.state.recipe_steps

            with st.spinner("Analyzing data..."):
                lf = self.engine.datasets.get(dataset_name)
                if lf is not None:
                    result = self.engine.processing.get_profile(lf, recipe)
                else:
                    result = None

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

            self._render_overview(shape, nulls)
            st.divider()

            st.subheader("Statistical Summary")
            st.dataframe(summary, width="stretch")
            st.divider()

            self._render_column_analysis(df_sample, dtypes, nulls, shape)

    def _render_overview(self, shape, nulls):
        st.subheader("Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows (Sampled)", shape[0])
        c2.metric("Columns", shape[1])

        total_cells = shape[0] * shape[1]
        total_nulls = sum(nulls.values())
        null_pct = (total_nulls / total_cells * 100) if total_cells > 0 else 0
        c3.metric("Missing Values", f"{total_nulls} ({null_pct:.1f}%)")

    def _render_column_analysis(self, df_sample, dtypes, nulls, shape):
        st.subheader("Column Analysis")
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

                is_numeric = "Int" in col_type or "Float" in col_type
                if is_numeric and shape[0] > 0:
                    st.caption("Distribution (Sample)")
                    st.bar_chart(df_sample[col].to_list())
                elif "Date" in col_type or "Time" in col_type:
                    st.caption("Temporal Distribution (Sample)")
                    st.line_chart(df_sample[col].to_list())
