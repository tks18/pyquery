"""
FilterComponent - Class-based file filtering UI.

Renders advanced file/path filters and dynamic item filters (sheets/tables).
"""

from typing import List, Dict, Optional

import streamlit as st

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.core.io import FileFilter, FilterType, ItemFilter
from pyquery_polars.frontend.components.loaders.file_loader.config import FILTER_TYPE_MAP


class FilterComponent(BaseComponent):
    """
    Filter component for FileLoader.

    Handles:
    - Advanced file path filters (contains, startswith, etc.)
    - Dynamic item filters for sheets/tables
    - Filter state management via StateManager
    """

    def __init__(self, ctx: AppContext, loader_name: str) -> None:
        """
        Initialize FilterComponent.

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

    def render(self, mode: str, is_busy: bool, session_key: Optional[str] = None) -> List[FileFilter]:
        """
        Render advanced file path filters.

        Args:
            mode: 'Single File' or 'Folder Pattern'
            is_busy: Whether the loader is currently processing
            session_key: Optional session state key override

        Returns:
            List of FileFilter objects
        """
        ln = self._ln
        if session_key is None:
            session_key = f"dlg_{ln}_filters"

        effective_filters = []

        # Initialize state
        if not self.state.has_loader_value(ln, "filters"):
            self.state.set_loader_value(ln, "filters", [])

        if mode != "Folder Pattern":
            return effective_filters

        with st.expander("🔍 Advanced File & Path Filters", expanded=False):
            st.caption("Apply additional filters to file paths & file names.")

            filters_list = self.state.get_loader_value(ln, "filters", [])

            # Show existing filters
            for i, f in enumerate(filters_list):
                self._render_filter_row(f, i, session_key, is_busy)

            # Add new filter
            st.divider()
            self._render_add_filter_ui(session_key, is_busy)

            # Refresh filters list after potential modifications
            filters_list = self.state.get_loader_value(ln, "filters", [])

        # Convert to FileFilter objects
        # Convert to FileFilter objects
        effective_filters = convert_file_filters_from_state(filters_list)
        return effective_filters

    def _render_filter_row(self, f: Dict, idx: int, session_key: str, is_busy: bool) -> None:
        """Render a single filter row with delete button."""
        c1, c2, c3, c4 = st.columns([0.25, 0.25, 0.4, 0.1])
        c1.markdown(f"**{f['type']}**")
        c2.caption(f"Apply to: {f.get('target', 'filename')}")
        c3.text(f['value'])

        def delete_filter(i: int):
            filters = self.state.get_value(session_key, [])
            if 0 <= i < len(filters):
                filters.pop(i)
                self.state.set_value(session_key, filters)

        c4.button(
            "✕",
            key=f"dlg_btn_del_filt_{self._ln}_{idx}",
            on_click=delete_filter,
            args=(idx,),
            disabled=is_busy
        )

    def _render_add_filter_ui(self, session_key: str, is_busy: bool) -> None:
        """Render UI to add a new filter."""
        ln = self._ln
        c_add_1, c_add_2, c_add_3, c_add_4 = st.columns([0.25, 0.25, 0.4, 0.1])

        new_f_type = c_add_1.selectbox(
            "Type",
            list(FILTER_TYPE_MAP.keys()),
            key=f"dlg_new_filt_type_{ln}",
            disabled=is_busy
        )
        new_f_target = c_add_2.selectbox(
            "Target",
            ["filename", "path"],
            key=f"dlg_new_filt_target_{ln}",
            disabled=is_busy
        )
        new_f_val = c_add_3.text_input(
            "Value",
            key=f"dlg_new_filt_val_{ln}",
            disabled=is_busy
        )

        def add_filter():
            val = self.state.get_value(f"dlg_new_filt_val_{ln}", "")
            if val:
                filters = self.state.get_value(session_key, [])
                filters.append({
                    "type": self.state.get_value(f"dlg_new_filt_type_{ln}"),
                    "value": val,
                    "target": self.state.get_value(f"dlg_new_filt_target_{ln}")
                })
                self.state.set_value(session_key, filters)
                self.state.set_value(f"dlg_new_filt_val_{ln}", "")

        c_add_4.button(
            "➕",
            on_click=add_filter,
            key=f"dlg_btn_add_filt_{ln}",
            disabled=is_busy
        )

    def render_items(
        self,
        item_type: str,
        session_key: str,
        is_busy: bool,
        key_suffix: str = ""
    ) -> None:
        """
        Render dynamic item filters (for sheets/tables).

        Args:
            item_type: 'Sheet' or 'Table'
            session_key: Session state key for storing filters
            is_busy: Whether the loader is currently processing
            key_suffix: Suffix for widget keys to ensure uniqueness
        """
        # Initialize state
        if not self.state.has_value(session_key):
            self.state.set_value(session_key, [])

        filters_list = self.state.get_value(session_key, [])

        # Show existing filters
        for i, f in enumerate(filters_list):
            c1, c2, c3 = st.columns([0.3, 0.6, 0.1])
            c1.markdown(f"**{f['type']}**")
            c2.text(f['value'])

            def del_filter(idx: int):
                current = self.state.get_value(session_key, [])
                if 0 <= idx < len(current):
                    current.pop(idx)
                    self.state.set_value(session_key, current)

            c3.button(
                "✕",
                key=f"dlg_btn_del_{key_suffix}_{i}_{self._ln}",
                on_click=del_filter,
                args=(i,),
                disabled=is_busy
            )

        # Add new filter
        with st.container(border=True):
            c_add_1, c_add_2, c_add_3 = st.columns([0.4, 0.5, 0.1])

            new_type = c_add_1.selectbox(
                "Type",
                list(FILTER_TYPE_MAP.keys()),
                key=f"dlg_new_{key_suffix}_type_{self._ln}",
                disabled=is_busy
            )
            new_val = c_add_2.text_input(
                "Pattern",
                key=f"dlg_new_{key_suffix}_val_{self._ln}",
                disabled=is_busy
            )

            def add_filter():
                val_key = f"dlg_new_{key_suffix}_val_{self._ln}"
                type_key = f"dlg_new_{key_suffix}_type_{self._ln}"
                val = self.state.get_value(val_key, "")
                if val:
                    current = self.state.get_value(session_key, [])
                    current.append({
                        "type": self.state.get_value(type_key),
                        "value": val
                    })
                    self.state.set_value(session_key, current)
                    self.state.set_value(val_key, "")

            c_add_3.button(
                "➕",
                on_click=add_filter,
                key=f"dlg_btn_add_{key_suffix}_{self._ln}",
                disabled=is_busy
            )


# =============================================================================
# FILTER CONVERSION UTILITIES
# =============================================================================

def convert_filters_from_state(state_filters: List[Dict]) -> List[ItemFilter]:
    """Convert state dictionary filters to ItemFilter objects."""
    result = []
    if not state_filters:
        return result

    for f in state_filters:
        if f['type'] in FILTER_TYPE_MAP:
            result.append(ItemFilter(
                type=FILTER_TYPE_MAP[f['type']],
                value=f['value']
            ))
    return result


def convert_file_filters_from_state(filters_list: List[Dict]) -> List[FileFilter]:
    """Convert state dictionary filters to FileFilter objects."""
    result = []
    if not filters_list:
        return result

    for f in filters_list:
        if f['type'] in FILTER_TYPE_MAP:
            result.append(FileFilter(
                type=FILTER_TYPE_MAP[f['type']],
                value=f['value'],
                target=f.get('target', 'filename')
            ))
    return result


def convert_filters_for_display(filter_list) -> List[Dict]:
    """Convert ItemFilters to dictionary format for state."""
    result = []
    if filter_list:
        for f in filter_list:
            if hasattr(f, 'type') and hasattr(f, 'value'):
                # Pydantic model
                f_type = f.type.value if hasattr(
                    f.type, 'value') else str(f.type)
                result.append({
                    "type": f_type,
                    "value": f.value,
                    "target": getattr(f, 'target', 'name')
                })
            elif isinstance(f, dict):
                f_type = f.get('type', '')
                if hasattr(f_type, 'value'):
                    f_type = f_type.value
                result.append({
                    "type": str(f_type),
                    "value": f.get('value', ''),
                    "target": f.get('target', 'name')
                })
    return result
