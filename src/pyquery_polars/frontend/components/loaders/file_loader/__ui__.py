"""
File Loader Component - Class-based implementation.

This module provides the FileLoader class for importing data from local files
(CSV, Excel, Parquet, JSON, IPC).
"""

from typing import Optional, Any, List, Dict

import streamlit as st
import os
import glob as glob_module

from pyquery_polars.frontend.base import AppContext
from pyquery_polars.frontend.components.loaders.base import BaseLoader
from pyquery_polars.frontend.utils.cache_utils import get_cached_encoding_scan
from pyquery_polars.frontend.components.loaders.utils import handle_auto_inference, remove_auto_inference_step

from pyquery_polars.frontend.components.loaders.file_loader.config import PATTERNS
from pyquery_polars.frontend.components.loaders.file_loader.filters import convert_filters_for_display, convert_file_filters_from_state, convert_filters_from_state

from pyquery_polars.frontend.components.loaders.file_loader.path_selector import PathSelectorComponent
from pyquery_polars.frontend.components.loaders.file_loader.filters import FilterComponent
from pyquery_polars.frontend.components.loaders.file_loader.excel_settings import ExcelSettingsComponent
from pyquery_polars.frontend.components.loaders.file_loader.preview import PreviewComponent


class FileLoader(BaseLoader):
    """
    File Loader dialog for local file imports.

    Provides UI for:
    - Single file or folder pattern selection
    - Advanced file filtering
    - Excel sheet/table selection
    - Data loading options (split files/sheets, auto-infer, etc.)
    - Live preview

    Inherits from BaseLoader and implements the render() method.
    """

    LOADER_NAME = "File"
    LOADER_TYPE = "File"
    STATE_KEY = "show_loader_file"

    def __init__(self, ctx: AppContext) -> None:
        """Initialize FileLoader with app context and sub-components."""
        super().__init__(ctx)
        self._init_state_keys()

        # Initialize sub-components with shared context
        self._path_selector = PathSelectorComponent(ctx, self.LOADER_NAME)
        self._filter_component = FilterComponent(ctx, self.LOADER_NAME)
        self._excel_settings = ExcelSettingsComponent(ctx, self.LOADER_NAME)
        self._preview = PreviewComponent(ctx, self.LOADER_NAME)

    def _init_state_keys(self) -> None:
        """Initialize all required session state keys using StateManager."""
        ln = self.LOADER_NAME
        defaults = {
            "busy": False,
            "action": None,
            "job_params": {},
            "mode": "Single File",
            "path": "",
            "folder": "",
            "recent_paths": [],
        }
        for key, default in defaults.items():
            if not self.state.has_loader_value(ln, key):
                self.state.set_loader_value(ln, key, default)

    @property
    def _ln(self) -> str:
        """Shortcut for loader name prefix."""
        return self.LOADER_NAME

    @property
    def _is_busy(self) -> bool:
        """Check if loader is currently processing."""
        return self.state.get_loader_value(self._ln, "busy", False)

    def render(self, edit_mode: bool = False,
               edit_dataset_name: Optional[str] = None) -> Any:
        """
        Render the file loader dialog content.

        Args:
            edit_mode: If True, pre-fill inputs from existing dataset
            edit_dataset_name: Name of dataset to edit
        """
        st.caption(
            f"{'Modify settings for existing dataset' if edit_mode else 'Load data from local files (CSV, Excel, Parquet, JSON, IPC)'}"
        )

        ln = self._ln
        is_busy = self._is_busy

        # Pre-fill for edit mode
        if edit_mode and edit_dataset_name and not self.state.has_loader_value(ln, "edit_initialized"):
            self._prefill_edit_mode(edit_dataset_name)
            self.state.set_loader_value(ln, "edit_initialized", True)

        # Alias initialization
        alias_key = f"dlg_{ln}_alias"
        if not self.state.has_loader_value(ln, "alias"):
            self.state.set_loader_value(
                ln, "alias", f"data_{len(self.state.all_recipes) + 1}")

        # Header: Alias & Mode
        c_alias, c_mode = st.columns([0.65, 0.35])
        alias_val = c_alias.text_input(
            "Dataset Alias", key=alias_key, disabled=is_busy)
        mode = c_mode.radio(
            "Import Mode",
            ["Single File", "Folder Pattern"],
            horizontal=True,
            key=f"dlg_{ln}_mode",
            disabled=is_busy
        )

        # Source & Settings Expander
        effective_path, folder_input, is_excel, sheet_source_file = self._render_source_section(
            mode, is_busy
        )

        # Settings Section
        self._render_settings_section(mode, is_excel, is_busy, edit_mode)

        # Preview Tab
        effective_filters = convert_file_filters_from_state(
            self.state.get_loader_value(ln, "filters", [])
        )
        self._preview.render(
            effective_path, effective_filters, is_excel, sheet_source_file
        )

        # Action Buttons
        self._render_actions(
            is_busy, edit_mode, alias_val, mode, effective_path, folder_input,
            effective_filters, edit_dataset_name
        )

        # Execution Visualization
        if is_busy:
            self._render_execution(mode)

    def _render_source_section(self, mode: str, is_busy: bool) -> tuple:
        """
        Render the source & settings expander.

        Returns:
            Tuple of (effective_path, folder_input, is_excel, sheet_source_file)
        """
        ln = self._ln

        with st.expander("📂 Source & Settings", expanded=not is_busy):
            # Path Selector
            effective_path, folder_input = self._path_selector.render(
                mode, is_busy
            )

            # Path change detection for Excel reset
            self._handle_path_change(effective_path)

            # Advanced Filters
            self._filter_component.render(mode, is_busy)

            # Excel Detection & Settings
            is_excel = False
            sheet_source_file = effective_path

            if effective_path:
                lower = effective_path.lower()
                if lower.endswith(('.xlsx', '.xls', '.xlsm')) or ("*" in effective_path and ".xls" in lower):
                    is_excel = True

            if is_excel:
                effective_filters = convert_file_filters_from_state(
                    self.state.get_loader_value(ln, "filters", [])
                )
                sheet_source_file = self._excel_settings.render(
                    effective_path, effective_filters, is_busy
                )

        return effective_path, folder_input, is_excel, sheet_source_file

    def _handle_path_change(self, effective_path: str) -> None:
        """Detect path changes and reset Excel selections."""
        ln = self._ln
        prev_path_key = f"dlg_{ln}_prev_path"

        curr_p = os.path.normcase(os.path.normpath(
            effective_path)) if effective_path else None

        stored_prev = self.state.get_loader_value(ln, "prev_path")
        prev_p = os.path.normcase(os.path.normpath(
            stored_prev)) if stored_prev else None

        if curr_p != prev_p:
            # Clear Excel widget keys
            keys_to_clear = [
                "sel_sheet", "sht_all_g", "sht_all_v",
                "sel_table", "tbl_all_g", "tbl_all_v",
                "final_table", "final_sheets_list"
            ]
            for key_suffix in keys_to_clear:
                self.state.delete_loader_value(ln, key_suffix)
            self.state.set_loader_value(ln, "prev_path", effective_path)

    def _render_settings_section(self, mode: str, is_excel: bool, is_busy: bool, edit_mode: bool) -> None:
        """Render the loading settings expander."""
        ln = self._ln

        with st.expander("⚙️ Loading Settings", expanded=not is_busy):
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Extraction Behavior**")
                # Set defaults
                for k in ["process_individual", "split_sheets", "clean_headers", "include_src", "auto_infer"]:
                    if not self.state.has_loader_value(ln, k):
                        self.state.set_loader_value(ln, k, False)

                if mode == "Folder Pattern":
                    st.toggle("Process Individually",
                              key=f"dlg_{ln}_process_individual", disabled=is_busy)
                    st.toggle(
                        "Split Files", key=f"dlg_{ln}_split_files", disabled=is_busy or edit_mode)
                else:
                    self.state.set_loader_value(ln, "split_files", False)

                if is_excel:
                    st.toggle(
                        "Split Sheets", key=f"dlg_{ln}_split_sheets", disabled=is_busy or edit_mode)
                else:
                    self.state.set_loader_value(ln, "split_sheets", False)

            with c2:
                st.markdown("**Schema & Metadata**")
                st.toggle("Clean Headers",
                          key=f"dlg_{ln}_clean_headers", disabled=is_busy)
                st.toggle("Include Source Path",
                          key=f"dlg_{ln}_include_src", disabled=is_busy)
                st.toggle("Auto Infer Types",
                          key=f"dlg_{ln}_auto_infer", disabled=is_busy)

    def _render_actions(self, is_busy: bool, edit_mode: bool, alias_val: str,
                        mode: str, effective_path: str, folder_input: str,
                        effective_filters: List, edit_dataset_name: Optional[str]) -> None:
        """Render action buttons (Cancel/Load)."""
        ln = self._ln
        job_params_key = f"dlg_{ln}_job_params"
        busy_key = f"dlg_{ln}_busy"
        action_key = f"dlg_{ln}_action"

        c_cancel, c_submit = st.columns([0.3, 0.7])

        if c_cancel.button("Cancel", key=f"dlg_btn_{ln}_cancel", disabled=is_busy):
            self._hide_dialog()

        btn_label = "Update Dataset" if edit_mode else "Load Data"
        if c_submit.button(btn_label, type="primary", width="stretch", key=f"dlg_btn_{ln}_load", disabled=is_busy):
            # Validation
            if not alias_val:
                st.error("Alias is required.")
                return
            if mode == "Single File" and (not effective_path or not os.path.exists(effective_path)):
                st.error("Invalid file path.")
                return

            # Build params
            params = self._build_load_params(
                effective_path, effective_filters, alias_val, edit_dataset_name, edit_mode
            )

            self.state.set_loader_value(ln, "job_params", params)
            self.state.set_loader_value(ln, "busy", True)
            self.state.set_loader_value(ln, "action", "check_and_load")
            st.rerun()

    def _build_load_params(self, effective_path: str, effective_filters: List,
                           alias_val: str, edit_dataset_name: Optional[str],
                           edit_mode: bool) -> Dict:
        """Build the parameters dict for loading."""
        ln = self._ln

        # Excel logic: Exclusive parameter mapping
        excel_target = self.state.get_loader_value(ln, "excel_target", "Sheet")

        effective_sheets = None
        effective_sheet_filters = None
        final_table = None
        effective_table_filters = None

        if excel_target == "Table":
            table_mode = self.state.get_loader_value(
                ln, "table_mode", "Manual Selection")
            if table_mode == "Dynamic Filter":
                effective_table_filters = convert_filters_from_state(
                    self.state.get_loader_value(ln, "table_filters", [])
                )
            else:
                final_table = self.state.get_loader_value(ln, "final_table")
                if final_table is None:
                    final_table = self.state.get_loader_value(ln, "sel_table")
                if self.state.get_loader_value(ln, "tbl_all_g"):
                    final_table = "__ALL_TABLES__"
        else:
            sheet_mode = self.state.get_loader_value(
                ln, "sheet_mode", "Manual Selection")
            if sheet_mode == "Dynamic Filter":
                effective_sheet_filters = convert_filters_from_state(
                    self.state.get_loader_value(ln, "sheet_filters", [])
                )
            else:
                if self.state.get_loader_value(ln, "sht_all_g"):
                    effective_sheets = "__ALL_SHEETS__"
                else:
                    effective_sheets = self.state.get_loader_value(
                        ln, "final_sheets_list")
                    if effective_sheets is None:
                        effective_sheets = self.state.get_loader_value(
                            ln, "sel_sheet")

        return {
            "path": effective_path,
            "filters": effective_filters,
            "sheet": effective_sheets,
            "sheet_filters": effective_sheet_filters,
            "table": final_table,
            "table_filters": effective_table_filters,
            "alias": alias_val,
            "process_individual": self.state.get_loader_value(ln, "process_individual", False),
            "include_source_info": self.state.get_loader_value(ln, "include_src", False),
            "clean_headers": self.state.get_loader_value(ln, "clean_headers", False),
            "auto_infer": self.state.get_loader_value(ln, "auto_infer", False),
            "split_sheets": self.state.get_loader_value(ln, "split_sheets", False),
            "split_files": self.state.get_loader_value(ln, "split_files", False),
            "template_file": self.state.get_loader_value(ln, "template_file"),
            "edit_dataset_name": edit_dataset_name if edit_mode else None
        }

    def _render_execution(self, mode: str) -> None:
        """Render execution progress and handle loading workflow."""
        ln = self._ln
        job_params_key = f"dlg_{ln}_job_params"
        busy_key = f"dlg_{ln}_busy"
        action_key = f"dlg_{ln}_action"
        recent_paths_key = f"dlg_{ln}_recent_paths"

        action = self.state.get_loader_value(ln, "action")
        job_params = self.state.get_loader_value(ln, "job_params")

        with st.status("Processing...", expanded=True) as status:
            try:
                # STEP 1: RESOLVE
                if action == "check_and_load":
                    st.write("🔍 Checking files...")
                    all_files = self.engine.io.resolve_files(
                        job_params["path"], job_params["filters"]
                    )
                    if not all_files:
                        raise Exception("No files match.")

                    # Encoding scan for CSVs
                    issues = {}
                    if any(f.endswith(".csv") for f in all_files[:5]):
                        issues = get_cached_encoding_scan(
                            self.engine, all_files)

                    if issues:
                        job_params["issues"] = issues
                        job_params["all_files"] = all_files
                        self.state.set_loader_value(
                            ln, "action", "convert_and_load")
                        st.rerun()
                    else:
                        job_params["all_files"] = all_files
                        self.state.set_loader_value(ln, "action", "load")
                        st.rerun()

                # STEP 2: CONVERT
                if action == "convert_and_load":
                    st.info("Converting encodings...")
                    issues = job_params["issues"]
                    for f in issues:
                        self.engine.io.convert_encoding(f, issues[f])
                    self.state.set_loader_value(ln, "action", "load")
                    st.rerun()

                # STEP 3: LOAD
                if action == "load":
                    st.info("Reading data...")
                    self._execute_load(job_params)

                    status.update(label="✅ Success!",
                                  state="complete", expanded=False)

                    # Cleanup
                    self.state.set_loader_value(ln, "busy", False)
                    self.state.set_loader_value(ln, "action", None)

                    # Recent path
                    if mode == "Single File" and job_params.get("path"):
                        rp = job_params["path"]
                        recent = self.state.get_loader_value(
                            ln, "recent_paths", [])
                        if rp not in recent:
                            recent.insert(0, rp)
                            self.state.set_loader_value(
                                ln, "recent_paths", recent)

                    self._hide_dialog()

            except Exception as e:
                status.update(label="❌ Failed", state="error")
                st.error(f"Error: {e}")
                if st.button("Reset"):
                    self.state.set_loader_value(ln, "busy", False)
                    st.rerun()

    def _execute_load(self, params: Dict) -> None:
        """Execute the actual data loading."""
        split_files = params.get("split_files", False)
        split_sheets = params.get("split_sheets", False)
        target_files = params.get("all_files", [params["path"]])
        edit_name = params.get("edit_dataset_name")

        # Standard load (no splitting)
        if not split_files and not split_sheets:
            self._execute_standard_load(params, edit_name)
            return

        # Splitting logic
        loaded_aliases = []
        base_alias = params["alias"]

        if split_files:
            loaded_aliases = self._execute_split_files_load(
                params, target_files, base_alias, edit_name)
        elif split_sheets:
            loaded_aliases = self._execute_split_sheets_load(
                params, target_files, base_alias, edit_name)

        # Set active to last loaded
        if loaded_aliases:
            if edit_name:
                try:
                    self.engine.datasets.remove(edit_name)
                    if edit_name in self.state.all_recipes:
                        del self.state.all_recipes[edit_name]
                except:
                    pass
            self.state.active_dataset = loaded_aliases[-1]

    def _execute_standard_load(self, params: Dict, edit_name: Optional[str]) -> None:
        """Execute standard (non-split) load."""
        res = self.engine.io.run_loader("File", params)
        if res:
            name = params["alias"]

            # Remove old dataset if editing
            if edit_name:
                try:
                    self.engine.datasets.remove(edit_name)
                    if edit_name != name:
                        self.engine.recipes.rename(edit_name, name)
                except:
                    pass

            self.engine.datasets.add(
                name, res[0], res[1], loader_type="File", loader_params=params
            )

            if params.get("auto_infer"):
                handle_auto_inference(self.engine, name, state=self.state)
            elif edit_name:
                remove_auto_inference_step(self.engine, name, state=self.state)

            self.state.active_dataset = name

    def _execute_split_files_load(self, params: Dict, target_files: List[str],
                                  base_alias: str, edit_name: Optional[str]) -> List[str]:
        """Execute split-by-files load."""
        loaded_aliases = []
        split_sheets = params.get("split_sheets", False)

        for f in target_files:
            fname = os.path.basename(f)

            if split_sheets:
                # Split both files AND sheets
                target_sheets = params.get("sheet")
                if target_sheets == "__ALL_SHEETS__" or not target_sheets:
                    try:
                        target_sheets = self.engine.io.get_sheet_names(f)
                    except:
                        target_sheets = ["Sheet1"]

                if isinstance(target_sheets, str) and target_sheets != "__ALL_SHEETS__":
                    target_sheets = [target_sheets]

                if isinstance(target_sheets, list):
                    for s in target_sheets:
                        curr = self._build_child_params(params, f, s)
                        alias = f"{base_alias}_{fname}_{s}"
                        self._load_child_dataset(
                            curr, alias, bool(params.get("auto_infer", False)), edit_name)
                        loaded_aliases.append(alias)
            else:
                # Just split files
                curr = self._build_child_params(params, f, None)
                alias = f"{base_alias}_{fname}"
                self._load_child_dataset(
                    curr, alias, bool(params.get("auto_infer", False)), edit_name)
                loaded_aliases.append(alias)

        return loaded_aliases

    def _execute_split_sheets_load(self, params: Dict, target_files: List[str],
                                   base_alias: str, edit_name: Optional[str]) -> List[str]:
        """Execute split-by-sheets load (files merged)."""
        loaded_aliases = []
        target_sheets = params.get("sheet")

        if target_sheets == "__ALL_SHEETS__" or not target_sheets:
            first_file = target_files[0]
            try:
                target_sheets = self.engine.io.get_sheet_names(first_file)
            except:
                target_sheets = ["Sheet1"]

        if isinstance(target_sheets, list):
            for s in target_sheets:
                curr = params.copy()
                curr["sheet"] = s
                curr["split_sheets"] = False
                curr["sheet_filters"] = None
                curr["table_filters"] = None

                alias = f"{base_alias}_{s}"
                res = self.engine.io.run_loader("File", curr)
                if res:
                    self.engine.datasets.add(
                        alias, res[0], res[1], loader_type="File", loader_params=curr
                    )
                    if params.get("auto_infer"):
                        handle_auto_inference(
                            self.engine, alias, state=self.state)
                    elif edit_name:
                        remove_auto_inference_step(
                            self.engine, alias, state=self.state)
                    loaded_aliases.append(alias)

        return loaded_aliases

    def _build_child_params(self, params: Dict, file_path: str, sheet: Optional[str]) -> Dict:
        """Build parameters for a child dataset (split loading)."""
        curr = params.copy()
        curr["path"] = file_path
        curr.pop("all_files", None)
        curr.pop("files", None)
        curr["filters"] = []
        curr["sheet_filters"] = None
        curr["table_filters"] = None
        curr["process_individual"] = False
        curr["split_sheets"] = False
        curr["split_files"] = False

        if sheet:
            curr["sheet"] = sheet

        return curr

    def _load_child_dataset(self, params: Dict, alias: str,
                            auto_infer: bool, edit_name: Optional[str]) -> None:
        """Load a single child dataset."""
        res = self.engine.io.run_loader("File", params)
        if res:
            self.engine.datasets.add(
                alias, res[0], res[1], loader_type="File", loader_params=params
            )
            if auto_infer:
                handle_auto_inference(self.engine, alias, state=self.state)
            elif edit_name:
                remove_auto_inference_step(
                    self.engine, alias, state=self.state)

    def _prefill_edit_mode(self, dataset_name: str) -> None:
        """Pre-fill dialog state from existing dataset metadata."""
        ln = self._ln
        meta = self.engine.datasets.get_metadata(dataset_name)
        if meta and meta.loader_params:
            params = meta.loader_params
        else:
            params = {}

        self.state.set_loader_value(ln, "alias", dataset_name)

        # Determine mode
        path = params.get("path", "")
        is_folder = (
            os.path.isdir(path) or
            glob_module.has_magic(path) or
            (params.get("filters") and not os.path.isfile(path))
        )

        if is_folder:
            self.state.set_loader_value(ln, "mode", "Folder Pattern")

            # Check for recursive
            if path.endswith("**") or (os.path.sep + "**" in path):
                self.state.set_loader_value(ln, "recursive", True)
                clean_path = path.replace(
                    os.path.sep + "**", "").replace("/**", "")
            else:
                self.state.set_loader_value(ln, "recursive", False)
                clean_path = path

            if os.path.isdir(clean_path):
                self.state.set_loader_value(ln, "folder", clean_path)
                self.state.set_loader_value(ln, "pat_type", "Custom")
            else:
                self.state.set_loader_value(ln, "folder", os.path.dirname(
                    clean_path))
                basename = os.path.basename(clean_path)

                # Reverse lookup pattern
                found_type = "Custom"
                for k, v in PATTERNS.items():
                    if v == basename:
                        found_type = k
                        break

                self.state.set_loader_value(ln, "pat_type", found_type)
                if found_type == "Custom":
                    self.state.set_loader_value(ln, "pat_custom", basename)
        else:
            self.state.set_loader_value(ln, "mode", "Single File")
            self.state.set_loader_value(ln, "path", path)

        # Restore settings
        self.state.set_loader_value(ln, "process_individual", params.get(
            "process_individual", False))
        self.state.set_loader_value(ln, "clean_headers", params.get(
            "clean_headers", False))
        self.state.set_loader_value(ln, "include_src", params.get(
            "include_source_info", False))
        self.state.set_loader_value(ln, "auto_infer", params.get(
            "auto_infer", False))
        self.state.set_loader_value(ln, "split_files", params.get(
            "split_files", False))
        self.state.set_loader_value(ln, "split_sheets", params.get(
            "split_sheets", False))

        # Restore filters
        self.state.set_loader_value(ln, "filters", convert_filters_for_display(
            params.get("filters", [])))
        self.state.set_loader_value(ln, "sheet_filters", convert_filters_for_display(
            params.get("sheet_filters", [])))
        self.state.set_loader_value(ln, "table_filters", convert_filters_for_display(
            params.get("table_filters", [])))

        # Restore sheet selection
        sheet_param = params.get("sheet")
        if sheet_param == "__ALL_SHEETS__":
            self.state.set_loader_value(ln, "sht_all_g", True)
        elif isinstance(sheet_param, str):
            self.state.set_loader_value(ln, "sel_sheet", [sheet_param])
        elif isinstance(sheet_param, list):
            self.state.set_loader_value(ln, "sel_sheet", sheet_param)

        # Restore table selection
        table_param = params.get("table")
        if table_param == "__ALL_TABLES__":
            self.state.set_loader_value(ln, "tbl_all_g", True)
        elif isinstance(table_param, str):
            self.state.set_loader_value(ln, "sel_table", [table_param])
        elif isinstance(table_param, list):
            self.state.set_loader_value(ln, "sel_table", table_param)

        # Restore Excel UI state
        if params.get("table") or params.get("table_filters") or params.get("table") == "__ALL_TABLES__":
            self.state.set_loader_value(ln, "excel_target", "Table")
            if params.get("table_filters"):
                self.state.set_loader_value(ln, "table_mode", "Dynamic Filter")
            else:
                self.state.set_loader_value(
                    ln, "table_mode", "Manual Selection")
                self.state.set_loader_value(
                    ln, "final_table", self.state.get_loader_value(ln, "sel_table"))
        else:
            self.state.set_loader_value(ln, "excel_target", "Sheet")
            if params.get("sheet_filters"):
                self.state.set_loader_value(ln, "sheet_mode", "Dynamic Filter")
            else:
                self.state.set_loader_value(
                    ln, "sheet_mode", "Manual Selection")
                self.state.set_loader_value(
                    ln, "final_sheets_list", self.state.get_loader_value(ln, "sel_sheet"))

        # Restore template file
        tpl_param = params.get("template_file")
        if tpl_param:
            self.state.set_loader_value(
                ln, "template_file", os.path.normpath(tpl_param))
        elif not is_folder and path and path.lower().endswith(('.xlsx', '.xls', '.xlsm')):
            self.state.set_loader_value(
                ln, "template_file", os.path.normpath(path))

        # Initialize prev_path
        self.state.set_loader_value(
            ln, "prev_path", os.path.normpath(path) if path else None)
