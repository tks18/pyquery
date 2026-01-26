"""
SQL Loader - Database connection dialog component.

This module provides the SQL loader dialog for connecting to databases
via SQLAlchemy connection strings.
"""

from typing import Optional, Any

import streamlit as st

from pyquery_polars.frontend.components.loaders.base import BaseLoader


class SQLLoader(BaseLoader):
    """
    SQL Loader dialog for database connections.

    Provides UI for:
    - Connection string input
    - SQL query input
    - Dataset alias
    - Auto-inference option
    """

    LOADER_NAME = "SQL"
    LOADER_TYPE = "SQL"
    STATE_KEY = "show_loader_sql"

    def render(self, edit_mode: bool = False,
               edit_dataset_name: Optional[str] = None) -> Any:
        """Render SQL loader dialog content (called within @st.dialog)."""
        st.caption(
            f"{'Modify SQL query settings' if edit_mode else 'Connect to SQL Databases via SQLAlchemy'}")

        # Pre-fill for edit mode
        ln = self.LOADER_NAME
        edit_init_key = self._get_edit_init_key()
        if edit_mode and edit_dataset_name and not self.state.has_loader_value(ln, "edit_initialized"):
            params = self._load_edit_params(edit_dataset_name)
            if params:
                self.state.set_loader_value(ln, "conn", params.get("conn", ""))
                self.state.set_loader_value(
                    ln, "query", params.get("query", ""))
                self.state.set_loader_value(ln, "alias", edit_dataset_name)
                self.state.set_loader_value(
                    ln, "infer", params.get("auto_infer", False))
            self.state.set_loader_value(ln, "edit_initialized", True)

        # Input fields
        conn = st.text_input(
            "Connection String",
            placeholder="postgresql://user:pass@host:port/dbname",
            key="dlg_sql_conn"
        )
        query = st.text_area(
            "SQL Query",
            height=150,
            placeholder="SELECT * FROM table_name LIMIT 1000",
            key="dlg_sql_query"
        )

        alias_val = st.text_input(
            "Dataset Alias",
            value=f"sql_data_{len(self.state.all_recipes) + 1}",
            key="dlg_sql_alias"
        )
        auto_infer = st.checkbox(
            "✨ Auto Detect & Clean Types",
            value=False,
            key="dlg_sql_infer"
        )

        # Action buttons
        c_cancel, c_submit = st.columns([0.3, 0.7])

        if c_cancel.button("Cancel", key="dlg_btn_sql_cancel"):
            self._hide_dialog()

        btn_label = "Update Dataset" if edit_mode else "Execute Query"
        if c_submit.button(btn_label, type="primary", width="stretch", key="dlg_btn_sql_load"):
            if not conn or not query:
                st.error("Connection string and query are required.")
                return

            params = {
                "conn": conn,
                "query": query,
                "alias": alias_val,
                "auto_infer": auto_infer
            }

            with st.spinner("Executing query & loading..."):
                res = self.engine.io.run_loader("Sql", params)
                if res:
                    lf_or_lfs, meta = res

                    success = self._register_dataset(
                        alias=alias_val,
                        lf_or_lfs=lf_or_lfs,
                        meta=meta,
                        loader_params=params,
                        auto_infer=auto_infer,
                        edit_mode=edit_mode,
                        edit_dataset_name=edit_dataset_name
                    )

                    if success:
                        self._hide_dialog()
                else:
                    st.error("SQL Load Failed.")
