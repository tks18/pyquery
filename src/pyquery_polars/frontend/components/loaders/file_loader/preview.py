"""
PreviewComponent - Class-based file/sheet preview UI.

Renders preview tabs for matched files and selected sheets/tables.
"""

from typing import List, Optional

import os
import streamlit as st
import pandas as pd

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.frontend.utils.cache_utils import (
    get_cached_resolved_files,
    get_cached_table_names,
    get_cached_sheet_names
)
from pyquery_polars.frontend.components.loaders.utils import filter_sheet_names
from pyquery_polars.frontend.components.loaders.file_loader.filters import convert_filters_from_state


class PreviewComponent(BaseComponent):
    """
    Preview component for FileLoader.

    Handles:
    - Matched files preview
    - Selected sheets preview
    - Selected tables preview
    - Dynamic filter preview
    """

    def __init__(self, ctx: AppContext, loader_name: str) -> None:
        """
        Initialize PreviewComponent.

        Args:
            ctx: AppContext with engine and state_manager
            loader_name: Identifier for this loader (e.g., 'File')
        """
        super().__init__(ctx)
        self._loader_name = loader_name

    @property
    def _ln(self) -> str:
        """Shortcut for loader name."""
        return self._loader_name

    def render(
        self,
        effective_path: str,
        effective_filters: List,
        is_excel: bool,
        sheet_source_file: Optional[str]
    ) -> None:
        """
        Render preview expander with file/sheet tabs.

        Args:
            effective_path: Current file path or glob pattern
            effective_filters: List of file filters
            is_excel: Whether this is an Excel file
            sheet_source_file: File to use for sheet/table names
        """
        with st.expander("🔎 Preview & Review", expanded=True):
            # Build tab labels
            tabs_labels = ["📂 Matched Files"]
            if is_excel and effective_path:
                target_mode = self.state.get_loader_value(
                    self._ln, "excel_target", "Sheet")
                if target_mode == "Table":
                    tabs_labels.append("📑 Selected Tables")
                else:
                    tabs_labels.append("📑 Selected Sheets")

            tabs = st.tabs(tabs_labels)

            # Tab 1: Files
            with tabs[0]:
                self._render_files_preview(effective_path, effective_filters)

            # Tab 2: Sheets/Tables
            if len(tabs) > 1 and is_excel:
                with tabs[1]:
                    self._render_excel_preview(sheet_source_file)

    def _render_files_preview(self, effective_path: str, effective_filters: List) -> None:
        """Render matched files preview."""
        ln = self._ln

        if not effective_path:
            st.info("Select a path to preview files.")
            return

        if st.button("Load File Preview", key=f"btn_{ln}_preview"):
            try:
                found_files = get_cached_resolved_files(
                    self.engine, effective_path, effective_filters, limit=1000
                )

                data = []
                for f in found_files[:1000]:
                    data.append({
                        "File Name": os.path.basename(f),
                        "Type": os.path.splitext(f)[1],
                        "Path": f
                    })

                if found_files:
                    st.success(f"Found {len(found_files)} files.")

                    # Check for split mode
                    is_splitting = (
                        self.state.get_loader_value(ln, "split_files") or
                        self.state.get_loader_value(ln, "split_sheets")
                    )
                    if is_splitting:
                        st.info(
                            "ℹ️ Split Mode Enabled: Files will be loaded as individual datasets.")

                    st.dataframe(pd.DataFrame(data))
                else:
                    st.warning("No files found matching the pattern.")

            except Exception as e:
                st.error(f"Error previewing files: {e}")
        else:
            st.caption("Click to preview matched files.")

    def _render_excel_preview(self, sheet_source_file: Optional[str]) -> None:
        """Render Excel sheets/tables preview."""
        ln = self._ln

        target_mode = self.state.get_loader_value(ln, "excel_target", "Sheet")
        src_fname = os.path.basename(
            sheet_source_file) if sheet_source_file else "Multiple/Pattern"

        final_table = self.state.get_loader_value(ln, "final_table")

        # Check for ALL tables/sheets selections
        if target_mode == "Table":
            if final_table == "__ALL_TABLES__":
                st.info(f"✅ All Tables in {src_fname} will be loaded.")
                return
            elif isinstance(final_table, list) and final_table:
                st.dataframe(pd.DataFrame({
                    "Table Name": final_table,
                    "Source Type": ["Manual Selection"] * len(final_table),
                    "Source File": [src_fname] * len(final_table)
                }), hide_index=True)
                return

        # Check for dynamic filter mode
        is_table_dynamic = (
            target_mode == "Table" and
            self.state.get_loader_value(
                ln, "table_mode_selection") == "Dynamic Filter"
        )
        is_sheet_dynamic = (
            target_mode == "Sheet" and
            self.state.get_loader_value(
                ln, "sheet_mode_selection") == "Dynamic Filter"
        )

        if is_table_dynamic:
            self._render_dynamic_preview(
                "Table",
                f"dlg_{ln}_table_filters",
                sheet_source_file,
                src_fname
            )
        elif is_sheet_dynamic:
            self._render_dynamic_preview(
                "Sheet",
                f"dlg_{ln}_sheet_filters",
                sheet_source_file,
                src_fname
            )
        else:
            # Manual sheet selection fallback
            self._render_sheet_manual_preview(src_fname)

    def _render_sheet_manual_preview(self, src_fname: str) -> None:
        """Render manual sheet selection preview."""
        ln = self._ln

        selected_sheets = self.state.get_loader_value(ln, "final_sheets_list")
        if selected_sheets is None:
            selected_sheets = self.state.get_loader_value(ln, "sel_sheet", [])

        if selected_sheets == "__ALL_SHEETS__":
            st.info(f"✅ All Sheets in {src_fname} will be loaded.")
        elif selected_sheets:
            st.dataframe(pd.DataFrame({
                "Sheet Name": selected_sheets,
                "Source Type": ["Manual Selection"] * len(selected_sheets),
                "Source File": [src_fname] * len(selected_sheets)
            }), hide_index=True)

    def _render_dynamic_preview(
        self,
        item_type: str,
        filter_key: str,
        sheet_source_file: Optional[str],
        src_fname: str
    ) -> None:
        """Render dynamic filter preview."""
        filts = self.state.get_value(filter_key, [])

        if not filts:
            st.info("No filters defined.")
            return

        st.info(f"Filters check against template: {src_fname}")

        try:
            preview_filters = convert_filters_from_state(filts)

            base_items = []
            if sheet_source_file:
                if item_type == "Table":
                    base_items = get_cached_table_names(
                        self.engine, sheet_source_file)
                else:
                    base_items = get_cached_sheet_names(
                        self.engine, sheet_source_file)

            matched = filter_sheet_names(base_items, preview_filters)

            st.dataframe(pd.DataFrame({
                f"Matched {item_type} Name": matched,
                "Match Rule": ["Dynamic Filter"] * len(matched),
                "Source File": [src_fname] * len(matched)
            }), hide_index=True)

            if not matched:
                st.warning(
                    f"No {item_type.lower()}s match these filters in the template.")

        except Exception as e:
            st.error(f"Error generating preview: {e}")
