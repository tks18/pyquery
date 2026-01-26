"""
ExcelSettingsComponent - Class-based Excel configuration UI.

Renders Excel-specific settings for sheet/table selection.
"""

from typing import Optional

import streamlit as st

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.frontend.components.loaders.utils import filter_list_by_regex
from pyquery_polars.frontend.utils.cache_utils import (
    get_cached_resolved_files,
    get_cached_table_names,
    get_cached_sheet_names
)
from pyquery_polars.frontend.components.loaders.file_loader.filters import FilterComponent


class ExcelSettingsComponent(BaseComponent):
    """
    Excel settings component for FileLoader.

    Handles:
    - Sheet/Table selection mode
    - Manual selection with search/filter
    - Dynamic filters for bulk selection
    - Template file selection for glob patterns
    """

    def __init__(self, ctx: AppContext, loader_name: str) -> None:
        """
        Initialize ExcelSettingsComponent.

        Args:
            ctx: AppContext with engine and state_manager
            loader_name: Identifier for this loader (e.g., 'File')
        """
        super().__init__(ctx)
        self._loader_name = loader_name
        self._filter_component = FilterComponent(ctx, loader_name)

    @property
    def _ln(self) -> str:
        """Shortcut for loader name."""
        return self._loader_name

    def render(
        self,
        effective_path: str,
        effective_filters: list,
        is_busy: bool
    ) -> Optional[str]:
        """
        Render Excel settings expander.

        Args:
            effective_path: Current effective path (file or glob pattern)
            effective_filters: List of file filters
            is_busy: Whether the loader is currently processing

        Returns:
            The sheet source file path
        """
        sheet_source_file = effective_path

        with st.expander("📊 Excel Settings", expanded=True):
            try:
                # Handle glob pattern - select template file
                if "*" in effective_path:
                    sheet_source_file = self._render_template_selection(
                        effective_path, effective_filters, is_busy
                    )

                if sheet_source_file:
                    self._render_target_selection(sheet_source_file, is_busy)

            except Exception as e:
                st.warning(f"Excel scan error: {e}")

        return sheet_source_file

    def _render_template_selection(
        self,
        effective_path: str,
        effective_filters: list,
        is_busy: bool
    ) -> Optional[str]:
        """Render template file selection for glob patterns."""
        ln = self._ln
        matches = []

        try:
            resolved = get_cached_resolved_files(
                self.engine, effective_path, effective_filters, limit=50
            )
            for f in resolved:
                if f.lower().endswith(('.xlsx', '.xls', '.xlsm')):
                    matches.append(f)
        except:
            pass

        if not matches:
            st.warning("No Excel files found matching pattern.")
            return None

        tpl_key = f"dlg_{ln}_template_file"

        # Validate current template
        if self.state.has_loader_value(ln, "template_file"):
            curr_tpl = self.state.get_loader_value(ln, "template_file")
            if curr_tpl and curr_tpl not in matches:
                self.state.set_loader_value(ln, "template_file", matches[0])

        def _on_template_change():
            self._handle_template_change(matches)

        base_selection = st.selectbox(
            "Select Base File (Template)",
            matches,
            key=tpl_key,
            on_change=_on_template_change,
            help="Choose a file to populate values from.",
            disabled=is_busy
        )

        return base_selection

    def _handle_template_change(self, matches: list) -> None:
        """Handle template file change - preserve valid selections."""
        ln = self._ln
        tpl_key = f"dlg_{ln}_template_file"
        new_tpl = self.state.get_value(tpl_key)

        if not new_tpl:
            return

        # Handle sheets
        self._preserve_or_reset_selection(
            new_tpl, "sel_sheet", get_cached_sheet_names, "Sheet1"
        )

        # Handle tables
        self._preserve_or_reset_selection(
            new_tpl, "sel_table", get_cached_table_names, None
        )

        # Clear derived keys
        for suffix in ["final_table", "final_sheets_list"]:
            self.state.delete_loader_value(ln, suffix)

    def _preserve_or_reset_selection(
        self,
        new_tpl: str,
        selection_key: str,
        get_available_func,
        default_fallback: Optional[str]
    ) -> None:
        """Try to preserve selection, or reset to default."""
        ln = self._ln
        current = self.state.get_loader_value(ln, selection_key, [])

        try:
            available = get_available_func(self.engine, new_tpl)
            valid = [item for item in current if item in available]

            if valid:
                self.state.set_loader_value(ln, selection_key, valid)
            elif default_fallback and default_fallback in available:
                self.state.set_loader_value(
                    ln, selection_key, [default_fallback])
            elif available:
                self.state.set_loader_value(ln, selection_key, [available[0]])
            else:
                self.state.set_loader_value(ln, selection_key, [])
        except:
            self.state.set_loader_value(ln, selection_key, [])

    def _render_target_selection(self, sheet_source_file: str, is_busy: bool) -> None:
        """Render Sheet/Table target selection."""
        ln = self._ln

        c_target, c_mode_sel = st.columns(2)

        excel_load_target = c_target.radio(
            "Load Target",
            ["Sheet", "Table"],
            horizontal=True,
            key=f"dlg_{ln}_excel_target",
            disabled=is_busy
        )

        if excel_load_target == "Table":
            self._render_table_mode(sheet_source_file, c_mode_sel, is_busy)
        else:
            self._render_sheet_mode(sheet_source_file, c_mode_sel, is_busy)

    def _render_table_mode(self, sheet_source_file: str, c_mode_sel, is_busy: bool) -> None:
        """Render table selection mode."""
        ln = self._ln

        table_mode = c_mode_sel.radio(
            "Selection Mode",
            ["Manual Selection", "Dynamic Filter"],
            horizontal=True,
            key=f"dlg_{ln}_table_mode",
            disabled=is_busy
        )
        self.state.set_loader_value(ln, "table_mode_selection", table_mode)
        st.divider()

        if table_mode == "Manual Selection":
            self._render_manual_table_selection(sheet_source_file, is_busy)
        else:
            self._render_dynamic_table_filters(sheet_source_file, is_busy)

    def _render_manual_table_selection(self, sheet_source_file: str, is_busy: bool) -> None:
        """Render manual table multiselect."""
        ln = self._ln

        tables = get_cached_table_names(self.engine, sheet_source_file)

        if not tables:
            st.warning("No named tables found in this file.")
            self.state.set_loader_value(ln, "final_table", None)
            return

        t_col_f, t_col_act = st.columns([0.6, 0.4])

        table_filter = t_col_f.text_input(
            "Filter Tables",
            "",
            placeholder="e.g. Table.*",
            key=f"dlg_{ln}_tbl_regex"
        )

        filtered_tables = tables
        if table_filter:
            filtered_tables = filter_list_by_regex(tables, table_filter)
            # Ensure selected are kept
            current_sel = self.state.get_loader_value(ln, "sel_table", [])
            for t in current_sel:
                if t in tables and t not in filtered_tables:
                    filtered_tables.append(t)

        c_all, c_vis = t_col_act.columns(2)
        sel_all_global = c_all.checkbox(
            "All",
            key=f"dlg_{ln}_tbl_all_g",
            help="Select all tables in file"
        )
        sel_all_vis = c_vis.checkbox(
            "Filtered",
            key=f"dlg_{ln}_tbl_all_v",
            disabled=not table_filter
        )

        if sel_all_global:
            self.state.set_loader_value(ln, "final_table", tables)
            st.caption(f"Selected all {len(tables)} tables.")
        elif sel_all_vis:
            self.state.set_loader_value(ln, "final_table", filtered_tables)
            st.caption(f"Selected {len(filtered_tables)} filtered tables.")
        else:
            self._render_table_multiselect(filtered_tables, is_busy)

    def _render_table_multiselect(self, filtered_tables: list, is_busy: bool) -> None:
        """Render table multiselect with smart defaults."""
        ln = self._ln
        prefill_key = f"dlg_{ln}_sel_table"
        prefilled = self.state.get_loader_value(ln, "sel_table", [])

        # Force default if needed
        # Force default if KEY MISSING
        if not self.state.has_loader_value(ln, "sel_table"):
            if filtered_tables:
                self.state.set_loader_value(
                    ln, "sel_table", [filtered_tables[0]])
        elif not all(t in filtered_tables for t in prefilled):
            valid = [t for t in prefilled if t in filtered_tables]
            if valid:
                self.state.set_loader_value(ln, "sel_table", valid)
            elif filtered_tables:
                self.state.set_loader_value(
                    ln, "sel_table", [filtered_tables[0]])

        selected_table = st.multiselect(
            "Select Table(s)",
            filtered_tables,
            key=prefill_key,
            disabled=is_busy
        )
        self.state.set_loader_value(ln, "final_table", selected_table)

    def _render_dynamic_table_filters(self, sheet_source_file: str, is_busy: bool) -> None:
        """Render dynamic table filter rules."""
        ln = self._ln

        st.caption("Define rules to select tables automatically from ALL files.")
        self.state.set_loader_value(ln, "final_table", [])

        self._filter_component.render_items(
            "Table",
            f"dlg_{ln}_table_filters",
            is_busy,
            key_suffix="tfilt"
        )

        # Preview
        if self.state.get_loader_value(ln, "table_filters"):
            try:
                base_tables = get_cached_table_names(
                    self.engine, sheet_source_file)
                st.caption(
                    f"Filters check against template (Base has {len(base_tables)} tables)")
            except:
                pass

    def _render_sheet_mode(self, sheet_source_file: str, c_mode_sel, is_busy: bool) -> None:
        """Render sheet selection mode."""
        ln = self._ln

        sheet_mode = c_mode_sel.radio(
            "Selection Mode",
            ["Manual Selection", "Dynamic Filter"],
            horizontal=True,
            key=f"dlg_{ln}_sheet_mode",
            disabled=is_busy
        )
        self.state.set_loader_value(ln, "sheet_mode_selection", sheet_mode)
        st.divider()

        # Clear table selection
        self.state.set_loader_value(ln, "final_table", None)

        if sheet_mode == "Manual Selection":
            self._render_manual_sheet_selection(sheet_source_file, is_busy)
        else:
            self._render_dynamic_sheet_filters(sheet_source_file, is_busy)

    def _render_manual_sheet_selection(self, sheet_source_file: str, is_busy: bool) -> None:
        """Render manual sheet multiselect."""
        ln = self._ln

        sheets = get_cached_sheet_names(self.engine, sheet_source_file)

        col_filter, col_act = st.columns([0.6, 0.4])

        sheet_filter = col_filter.text_input(
            "Filter Sheets",
            "",
            key=f"dlg_{ln}_sheet_regex",
            placeholder="e.g. Sheet.*",
            disabled=is_busy
        )

        filtered_sheets = sheets
        if sheet_filter:
            filtered_sheets = filter_list_by_regex(sheets, sheet_filter)
            # Ensure selected are kept
            current_sel = self.state.get_loader_value(ln, "sel_sheet", [])
            for s in current_sel:
                if s in sheets and s not in filtered_sheets:
                    filtered_sheets.append(s)

        c_all_s, c_vis_s = col_act.columns(2)
        all_sheets_global = c_all_s.checkbox(
            "All",
            key=f"dlg_{ln}_sht_all_g",
            disabled=is_busy
        )
        all_sheets_vis = c_vis_s.checkbox(
            "Filtered",
            value=False,
            key=f"dlg_{ln}_sht_all_v",
            disabled=not sheet_filter
        )

        if all_sheets_global:
            self.state.set_loader_value(ln, "final_sheets_list", sheets)
            st.caption(f"Selected all {len(sheets)} sheets.")
        elif all_sheets_vis:
            self.state.set_loader_value(
                ln, "final_sheets_list", filtered_sheets)
            st.caption(f"Selected {len(filtered_sheets)} filtered sheets.")
        else:
            self._render_sheet_multiselect(filtered_sheets, is_busy)

    def _render_sheet_multiselect(self, filtered_sheets: list, is_busy: bool) -> None:
        """Render sheet multiselect with smart defaults."""
        ln = self._ln
        prefill_key = f"dlg_{ln}_sel_sheet"
        prefilled = self.state.get_loader_value(ln, "sel_sheet", [])

        # Force default if needed
        # Force default if KEY MISSING
        if not self.state.has_loader_value(ln, "sel_sheet"):
            if "Sheet1" in filtered_sheets:
                self.state.set_loader_value(ln, "sel_sheet", ["Sheet1"])
            elif filtered_sheets:
                self.state.set_loader_value(
                    ln, "sel_sheet", [filtered_sheets[0]])
        elif not all(s in filtered_sheets for s in prefilled):
            valid = [s for s in prefilled if s in filtered_sheets]
            if valid:
                self.state.set_loader_value(ln, "sel_sheet", valid)
            elif "Sheet1" in filtered_sheets:
                self.state.set_loader_value(ln, "sel_sheet", ["Sheet1"])
            elif filtered_sheets:
                self.state.set_loader_value(
                    ln, "sel_sheet", [filtered_sheets[0]])

        selected_sheets = st.multiselect(
            "Select Sheets",
            filtered_sheets,
            key=prefill_key,
            disabled=is_busy
        )
        self.state.set_loader_value(ln, "final_sheets_list", selected_sheets)

    def _render_dynamic_sheet_filters(self, sheet_source_file: str, is_busy: bool) -> None:
        """Render dynamic sheet filter rules."""
        ln = self._ln

        st.caption("Define rules to select sheets automatically from ALL files.")

        self._filter_component.render_items(
            "Sheet",
            f"dlg_{ln}_sheet_filters",
            is_busy,
            key_suffix="sfilt"
        )

        # Preview
        if self.state.get_loader_value(ln, "sheet_filters"):
            try:
                base_sheets = get_cached_sheet_names(
                    self.engine, sheet_source_file)
                st.caption(
                    f"Filters check against template (Base has {len(base_sheets)} sheets)")
            except:
                pass
