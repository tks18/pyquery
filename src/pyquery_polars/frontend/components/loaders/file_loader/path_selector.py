"""
PathSelectorComponent - Class-based path input UI.

Renders file/folder path selection based on import mode.
"""

from typing import Tuple, Optional

import os
import streamlit as st

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.frontend.utils.file_picker import pick_file, pick_folder
from pyquery_polars.frontend.components.loaders.file_loader.config import PATTERNS


class PathSelectorComponent(BaseComponent):
    """
    Path selection component for FileLoader.

    Handles:
    - Single file path input with browse button
    - Folder pattern input with glob pattern configuration
    - Recent paths management
    - Recursive directory search toggle
    """

    def __init__(self, ctx: AppContext, loader_name: str) -> None:
        """
        Initialize PathSelectorComponent.

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

    def render(self, mode: str, is_busy: bool) -> Tuple[str, Optional[str]]:
        """
        Render path selection UI.

        Args:
            mode: 'Single File' or 'Folder Pattern'
            is_busy: Whether the loader is currently processing

        Returns:
            Tuple of (effective_path, folder_input)
        """
        if mode == "Single File":
            return self._render_single_file_mode(is_busy)
        else:
            return self._render_folder_pattern_mode(is_busy)

    def _render_single_file_mode(self, is_busy: bool) -> Tuple[str, None]:
        """Render single file selection UI."""
        ln = self._ln
        path_key = f"dlg_{ln}_path"
        recent_key = f"dlg_{ln}_recent_paths"

        # Recent paths dropdown
        recents = self.state.get_loader_value(ln, "recent_paths", [])
        if recents:
            self._render_recent_paths(recents, path_key, recent_key)

        # File path input with browse button
        col_path, col_btn = st.columns([0.85, 0.15])
        path_input = col_path.text_input(
            "File Path",
            key=path_key,
            disabled=is_busy,
            help="Enter path to file."
        )

        def callback_pick_file():
            picked = pick_file("Select File")
            if picked:
                self.state.set_loader_value(ln, "path", picked)

        col_btn.button(
            "📂",
            on_click=callback_pick_file,
            key=f"btn_pick_file_{ln}",
            help="Browse Files",
            disabled=is_busy
        )

        return path_input, None

    def _render_folder_pattern_mode(self, is_busy: bool) -> Tuple[str, str]:
        """Render folder pattern selection UI."""
        ln = self._ln
        folder_key = f"dlg_{ln}_folder"

        # Folder input with browse button
        col_dir, col_btn = st.columns([0.85, 0.15])
        folder_input = col_dir.text_input(
            "Base Folder",
            key=folder_key,
            disabled=is_busy
        )

        def callback_pick_folder():
            picked = pick_folder("Select Folder")
            if picked:
                self.state.set_loader_value(ln, "folder", picked)

        col_btn.button(
            "📂",
            on_click=callback_pick_folder,
            key=f"btn_pick_folder_{ln}",
            help="Browse Folder",
            disabled=is_busy
        )

        # Pattern configuration
        final_pattern = self._render_pattern_config(is_busy)

        # Compose effective path
        effective_path = ""
        if folder_input and final_pattern:
            effective_path = os.path.join(folder_input, final_pattern)

        return effective_path, folder_input

    def _render_pattern_config(self, is_busy: bool) -> str:
        """Render glob pattern configuration."""
        ln = self._ln
        c1, c2, c_rec = st.columns([0.4, 0.35, 0.25])

        pat_key = f"dlg_{ln}_pat_type"
        sel_pat_label = c1.selectbox(
            "Pattern Type",
            list(PATTERNS.keys()),
            key=pat_key,
            disabled=is_busy
        )

        base_pattern = PATTERNS[sel_pat_label]
        is_custom = base_pattern == "custom"

        if is_custom:
            # Custom pattern input
            custom_key = f"dlg_{ln}_pat_custom"
            base_pattern = c2.text_input(
                "Custom Pattern",
                value="*.csv" if not self.state.has_loader_value(
                    ln, "pat_custom") else "",
                key=custom_key,
                disabled=is_busy
            )
            c_rec.caption("Recursive: N/A")
            return base_pattern
        else:
            # Standard pattern with recursive toggle
            recursive = c_rec.checkbox(
                "🔄 Recursive",
                key=f"dlg_{ln}_recursive",
                help="Search subdirectories (adds **/ prefix)",
                disabled=is_busy
            )

            if recursive and not base_pattern.startswith("**/"):
                final_pattern = f"**/{base_pattern}"
            else:
                final_pattern = base_pattern

            c2.text_input("Pattern Preview",
                          value=final_pattern, disabled=True)
            return final_pattern

    def _render_recent_paths(self, recents: list, path_key: str, recent_key: str) -> None:
        """Render recent paths dropdown."""
        ln = self._ln

        def on_recent_change():
            sel = self.state.get_value(f"{ln}_recent_sel")
            if sel and sel != "Select recent...":
                self.state.set_value(path_key, sel)

        c_rec, c_clr = st.columns([0.85, 0.15])
        c_rec.selectbox(
            "Recent Paths",
            ["Select recent..."] + recents,
            key=f"{ln}_recent_sel",
            on_change=on_recent_change,
            label_visibility="collapsed"
        )

        if c_clr.button("Clear", help="Clear History", key=f"btn_clear_recent_{ln}"):
            self.state.set_loader_value(ln, "recent_paths", [])
            st.rerun()
