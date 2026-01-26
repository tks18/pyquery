"""
API Loader - REST API import dialog component.

This module provides the API loader dialog for importing JSON data from REST APIs.
"""

from typing import Optional, Any

import streamlit as st

from pyquery_polars.frontend.components.loaders.base import BaseLoader


class APILoader(BaseLoader):
    """
    API Loader dialog for REST API data import.

    Provides UI for:
    - API endpoint URL input
    - Dataset alias
    - Auto-inference option
    """

    LOADER_NAME = "API"
    LOADER_TYPE = "API"
    STATE_KEY = "show_loader_api"

    def render(self, edit_mode: bool = False,
               edit_dataset_name: Optional[str] = None) -> Any:
        """Render API loader dialog content (called within @st.dialog)."""
        st.caption(
            f"{'Modify API endpoint settings' if edit_mode else 'Import JSON/Data from REST API'}")

        # Pre-fill for edit mode
        ln = self.LOADER_NAME
        if edit_mode and edit_dataset_name and not self.state.has_loader_value(ln, "edit_initialized"):
            params = self._load_edit_params(edit_dataset_name)
            if params:
                self.state.set_loader_value(ln, "url", params.get("url", ""))
                self.state.set_loader_value(ln, "alias", edit_dataset_name)
                self.state.set_loader_value(
                    ln, "infer", params.get("auto_infer", False))
            self.state.set_loader_value(ln, "edit_initialized", True)

        # Input fields
        url = st.text_input("API Endpoint URL", key="dlg_api_url")
        alias_val = st.text_input(
            "Dataset Alias",
            value=f"api_data_{len(self.state.all_recipes) + 1}",
            key="dlg_api_alias"
        )
        auto_infer = st.checkbox(
            "✨ Auto Detect & Clean Types",
            value=False,
            key="dlg_api_infer"
        )

        # Action buttons
        c_cancel, c_submit = st.columns([0.3, 0.7])

        if c_cancel.button("Cancel", key="dlg_btn_api_cancel"):
            self._hide_dialog()

        btn_label = "Update Dataset" if edit_mode else "Fetch Data"
        if c_submit.button(btn_label, type="primary", width="stretch", key="dlg_btn_api_load"):
            params = {
                "url": url,
                "alias": alias_val,
                "auto_infer": auto_infer
            }

            with st.spinner("Fetching data..."):
                res = self.engine.io.run_loader("Api", params)
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
                    st.error("API Load Failed.")
