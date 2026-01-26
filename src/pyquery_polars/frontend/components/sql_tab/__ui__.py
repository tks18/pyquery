"""
SQL Tab component module.

Provides SQL query editor and execution functionality.
"""

import time
import os
import pandas as pd
import streamlit as st

from pyquery_polars.frontend.base import BaseComponent
from pyquery_polars.frontend.utils.dynamic_ui import render_schema_fields
from pyquery_polars.frontend.utils.io_schemas import get_exporter_schema
from pyquery_polars.frontend.utils.file_picker import pick_folder
from pyquery_polars.frontend.elements import sql_editor


class SQLTabComponent(BaseComponent):
    """
    SQL Query interface component.
    """

    def render(self) -> None:
        """Render the SQL Editor tab."""
        st.subheader("SQL Editor")

        if not self.engine:
            st.error("Engine not initialized.")
            return

        self._render_schema_explorer()
        self._render_query_editor()

        if self.state.sql_run_trigger:
            self._render_results()

        st.divider()
        self._render_export_section()

    def _render_schema_explorer(self):
        with st.expander("📚 Schema Explorer (Tables & Columns)", expanded=False):
            tables = self.engine.datasets.list_names()
            if not tables:
                st.warning("No datasets loaded.")
                return

            selected_table = st.selectbox(
                "Select Table to Inspect:", tables, key="schema_table_selector")
            if selected_table:
                lf = self.engine.datasets.get(selected_table)
                schema = None
                if lf is not None:
                    recipe = self.engine.recipes.get(selected_table)
                    schema = self.engine.processing.get_transformed_schema(
                        lf, recipe)

                if schema:
                    schema_df = pd.DataFrame([
                        {"Column": col, "Type": str(dtype)} for col, dtype in schema.items()
                    ])
                    st.dataframe(schema_df, width="stretch", height="auto", hide_index=True,
                                 column_config={
                                     "Column": st.column_config.TextColumn("Column Name", width="medium"),
                                     "Type": st.column_config.TextColumn("Data Type", width="small")
                                 })

    def _render_query_editor(self):
        active_ds_name = self.state.active_dataset
        default_query = "SELECT * FROM " + \
            (active_ds_name if active_ds_name else "table_name") + " LIMIT 10"

        if not self.state.sql_query or self.state.sql_query.strip() == "DS_DELETED":
            self.state.sql_query = default_query

        st.write("###### Write Query")

        def on_hist_change():
            val = self.state.get_value("hist_picker")
            if val and val != "Recall recent query...":
                self.state.sql_query = val

        st.selectbox("Recent Queries", ["Recall recent query..."] + self.state.sql_history,
                     key="hist_picker", label_visibility="collapsed",
                     on_change=on_hist_change, placeholder="Recall recent query...")

        st.info("💡 Tip: You can write standard SQL queries here.")

        query_result = sql_editor(
            code=self.state.sql_query, key="sql_query_editor", height=[15, 25], state=self.state)

        if query_result is not None:
            self.state.sql_query = query_result
            self.state.sql_run_trigger = True

            q = query_result
            if q and q.strip():
                hist = self.state.sql_history
                if q in hist:
                    hist.remove(q)
                hist.insert(0, q)
                if len(hist) > 10:
                    hist.pop()
            st.rerun()

    def _render_results(self):
        try:
            if self.state.sql_run_trigger:
                with st.spinner("Executing SQL (Preview)..."):
                    preview_lf = self.engine.processing.execute_sql(
                        self.state.sql_query, preview=True, preview_limit=1000)
                    preview_df = preview_lf.collect() if preview_lf is not None else pd.DataFrame()

                    any_folder = any((meta := self.engine.datasets.get_metadata(t)) and meta.process_individual
                                     for t in self.engine.datasets.list_names())
                    warn_msg = "⚠️ **Preview Mode**: Results based on top 1,000 rows only."
                    if any_folder:
                        warn_msg += " (Note: Folder datasets preview **First File Only**)."
                    warn_msg += " Export uses full dataset."

                    st.warning(warn_msg)
                    st.dataframe(preview_df, width="stretch")
                    st.caption(f"Shape: {preview_df.shape}")

                    with st.expander("📊 Analyze Result Quality"):
                        if st.button("Run Profile", key="btn_sql_profile"):
                            self._render_result_profile(preview_df)

                    with st.expander("💾 Save as Dataset (Materialize)"):
                        self._render_materialize_option()

        except Exception as e:
            st.error(f"SQL Error: {e}")

    def _render_result_profile(self, df):
        profile_data = []
        for col in df.columns:
            s = df[col]
            profile_data.append({
                "Column": col, "Type": str(s.dtype),
                "Nulls": s.null_count(),
                "Null %": f"{s.null_count() / len(s):.1%}" if len(s) > 0 else "0%",
                "Unique": s.n_unique()
            })
        st.dataframe(profile_data, width="stretch")

    def _render_materialize_option(self):
        st.caption(
            "Save the result of this query as a reusable dataset in the main pipeline.")
        c1, c2 = st.columns([3, 1])
        new_ds_name = c1.text_input(
            "New Dataset Name", placeholder="e.g. filtered_sales", label_visibility="collapsed")

        if c2.button("Save to Pipeline", type="primary", disabled=not new_ds_name):
            try:
                with st.spinner("Materializing..."):
                    lf = self.engine.processing.execute_sql(
                        self.state.sql_query)
                    temp_name = f"___temp_sql_{new_ds_name}"
                    self.engine.datasets.add(temp_name, lf, metadata={
                                             "input_type": "sql", "source_path": None})

                    if self.engine.processing.materialize_dataset(temp_name, new_ds_name, recipe=[]):
                        self.engine.datasets.remove(temp_name)
                        st.success(f"Saved '{new_ds_name}'!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        self.engine.datasets.remove(temp_name)
                        st.error("Failed to save dataset.")
            except Exception as e:
                st.error(f"Error: {e}")

    def _render_export_section(self):
        st.subheader("📤 Export SQL Results")
        with st.expander("Export Options", expanded=False):
            exporters = self.engine.io.get_exporters()
            if not exporters:
                st.warning("No exporters available.")
                return

            exporter_map = {e.name: e for e in exporters}
            selected_exporter_name = st.selectbox("Format", list(
                exporter_map.keys()), key="sql_export_format")
            selected_exporter = exporter_map[selected_exporter_name]

            base_schema = get_exporter_schema(selected_exporter.name)
            ui_schema = [f for f in base_schema if f.name != "path"]

            st.write("###### Output Destination")
            folder_key = f"sql_exp_{selected_exporter_name}_folder"
            filename_key = f"sql_exp_{selected_exporter_name}_filename"

            dataset_meta = self.engine.datasets.get_metadata(
                self.state.active_dataset) if self.state.active_dataset else None
            source_path = dataset_meta.source_path if dataset_meta else None
            default_folder = os.getcwd()
            if source_path:
                if os.path.isfile(source_path):
                    default_folder = os.path.dirname(source_path)
                else:
                    default_folder = source_path

            # Defaults logic
            if not self.state.has_value(folder_key):
                self.state.set_value(
                    folder_key, default_folder)
            if not self.state.has_value(filename_key):
                self.state.set_value(
                    filename_key, f"sql_export_{int(time.time())}")

            c1, c2 = st.columns([0.85, 0.15])
            folder_path = c1.text_input("Destination Folder", key=folder_key)

            def on_pick_sql_folder():
                picked = pick_folder(title="Select SQL Export Folder")
                if picked:
                    self.state.set_value(folder_key, picked)

            c2.markdown("<div style='height: 28px'></div>",
                        unsafe_allow_html=True)
            c2.button(
                "📂", key=f"btn_browse_sql_{selected_exporter_name}", on_click=on_pick_sql_folder)

            filename_val = st.text_input("Filename", key=filename_key)
            ext = ".parquet" if selected_exporter_name == "Parquet" else f".{selected_exporter_name.lower()}"
            if selected_exporter_name == "Arrow IPC":
                ext = ".arrow"
            if selected_exporter_name == "Excel":
                ext = ".xlsx"

            full_path = os.path.join(folder_path, f"{filename_val}{ext}")
            st.caption(f"📝 **Target:** `{full_path}`")
            st.divider()

            params = render_schema_fields(
                ui_schema, key_prefix=f"sql_exp_{selected_exporter_name}", columns=2)
            params["path"] = full_path

            if st.button("Export SQL Result", type="primary"):
                self._run_export_job(selected_exporter, params)

    def _run_export_job(self, exporter, params):
        final_params = params
        if exporter.params_model:
            try:
                final_params = exporter.params_model.model_validate(params)
            except Exception as e:
                st.error(f"Invalid Params: {e}")
                return

        try:
            job_id = self.engine.jobs.start_export_job(
                dataset_name="SQL_RESULT",
                recipe=[],
                exporter_name=exporter.name,
                params=final_params,
                project_recipes=self.state.all_recipes,
                precomputed_lf=self.engine.processing.execute_sql(
                    self.state.sql_query, preview=False)
            )

            status_placeholder = st.empty()
            start_ts = time.time()
            with st.spinner(f"Exporting SQL Result..."):
                while True:
                    elapsed = time.time() - start_ts
                    status_placeholder.info(f"⏳ Exporting... ({elapsed:.2f}s)")

                    job_info = self.engine.jobs.get_job_status(job_id)
                    if not job_info:
                        time.sleep(0.5)
                        continue

                    if job_info.status == "COMPLETED":
                        size = getattr(job_info, 'size_str', "Unknown")
                        status_placeholder.success(
                            f"✅ Export Complete! Time: {job_info.duration:.2f}s | Size: {size}")
                        break
                    elif job_info.status == "FAILED":
                        status_placeholder.error(
                            f"❌ Failed: {getattr(job_info, 'error', 'Unknown')}")
                        break
                    else:
                        time.sleep(0.5)
        except Exception as e:
            st.error(f"Failed to start export: {e}")
