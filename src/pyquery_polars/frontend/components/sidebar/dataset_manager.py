"""
Sidebar Dataset Manager component.

Handles dataset import, listing, and lifecycle management.
"""

import streamlit as st
import hashlib

from pyquery_polars.frontend.base import BaseComponent
from pyquery_polars.frontend.components.loaders import FileLoader, SQLLoader, APILoader
from pyquery_polars.frontend.components.project_dialog import ProjectDialogComponent


@st.dialog("Import Data", width="large")
def _show_file_loader_dialog(ctx, edit_ds):
    """Display File Loader dialog using class-based component."""
    FileLoader(ctx).render(
        edit_mode=bool(edit_ds),
        edit_dataset_name=edit_ds
    )


@st.dialog("SQL Connection", width="large")
def _show_sql_loader_dialog(ctx, edit_ds):
    """Display SQL Loader dialog using class-based component."""
    SQLLoader(ctx).render(
        edit_mode=bool(edit_ds),
        edit_dataset_name=edit_ds
    )


@st.dialog("API Import", width="large")
def _show_api_loader_dialog(ctx, edit_ds):
    """Display API Loader dialog using class-based component."""
    APILoader(ctx).render(
        edit_mode=bool(edit_ds),
        edit_dataset_name=edit_ds
    )


class SidebarDatasetManager(BaseComponent):
    """
    Manages dataset operations in the sidebar: import, list, delete, settings.
    Also handles the dialog lifecycle for loaders.
    """

    def render(self) -> None:
        """Render the dataset manager section."""
        self._handle_dialog_auto_close()

        st.subheader("🗂️ Datasets")
        st.write("###### Import Data")

        # Import Buttons
        c1, c2, c3 = st.columns(3)
        if c1.button("📂 File", help="Import Local Files", width="stretch", on_click=self._open_file_loader):
            pass
        if c2.button("🛢️ SQL", help="Connect Database", width="stretch", on_click=self._open_sql_loader):
            pass
        if c3.button("🌐 API", help="REST API Import", width="stretch", on_click=self._open_api_loader):
            pass

        self._render_active_dialogs()

        # Dataset List
        dataset_names = self.engine.datasets.list_names()
        if dataset_names:
            st.divider()
            st.caption("Available Projects")
            for name in dataset_names:
                self._render_dataset_item(name)

    def _render_dataset_item(self, name: str):
        c1, c_settings, c_delete = st.columns([0.7, 0.15, 0.15])
        active_ds = self.state.active_dataset
        label = f"📂 {name}" if name != active_ds else f"🟢 **{name}**"

        if c1.button(label, key=f"sel_{name}", width="stretch"):
            self.state.active_dataset = name
            self.state.recipe_steps = self.state.all_recipes.get(name, [])
            st.rerun()

        if c_settings.button("⚙️", key=f"settings_{name}", help="Edit dataset settings",
                             on_click=self._open_dataset_settings, args=(name,)):
            pass

        if c_delete.button("🗑️", key=f"del_{name}"):
            self._delete_dataset(name)
            st.rerun()

    def _delete_dataset(self, name):
        self.engine.datasets.remove(name)
        active_datasets = self.engine.datasets.list_names()

        self.state.sql_history = [q for q in self.state.sql_history if any(
            name in q for name in active_datasets)] if active_datasets else []

        self.state.sql_query = "DS_DELETED"

        all_recipes = self.state.all_recipes
        if name in all_recipes:
            del all_recipes[name]
            self.state.all_recipes = all_recipes
        if self.state.active_dataset == name:
            self.state.active_dataset = None
            self.state.recipe_steps = []

    def _reset_dialog_state(self):
        """Clear all dialog-specific session state."""
        self.state.reset_dialog_state()

    def _open_file_loader(self):
        self._set_loader_state(file=True)

    def _open_sql_loader(self):
        self._set_loader_state(sql=True)

    def _open_api_loader(self):
        self._set_loader_state(api=True)

    def _set_loader_state(self, file=False, sql=False, api=False):
        self.state.close_all_dialogs()
        self._reset_dialog_state()
        self.state.edit_mode_dataset = None
        if file:
            self.state.open_dialog("file")
        elif sql:
            self.state.open_dialog("sql")
        elif api:
            self.state.open_dialog("api")

    def _open_dataset_settings(self, name):
        meta = self.engine.datasets.get_metadata(name)
        loader_type = meta.loader_type if meta and meta.loader_type else "File"

        self._reset_dialog_state()

        self._set_loader_state(
            file=(loader_type == "File" or loader_type not in ["SQL", "API"]),
            sql=(loader_type == "SQL"),
            api=(loader_type == "API")
        )

        # Set AFTER resetting state
        self.state.edit_mode_dataset = name

    def _render_active_dialogs(self):
        edit_ds = self.state.edit_mode_dataset

        if self.state.is_dialog_open("project_export"):
            # ProjectDialogComponent handles rendering based on state, but we ensure it's called
            ProjectDialogComponent(self.ctx).render(show_buttons=False)

        elif self.state.is_dialog_open("project_import"):
            ProjectDialogComponent(self.ctx).render(show_buttons=False)

        elif self.state.is_dialog_open("file"):
            _show_file_loader_dialog(self.ctx, edit_ds)
        elif self.state.is_dialog_open("sql"):
            _show_sql_loader_dialog(self.ctx, edit_ds)
        elif self.state.is_dialog_open("api"):
            _show_api_loader_dialog(self.ctx, edit_ds)

        self._update_dialog_hash()

    def _handle_dialog_auto_close(self):
        """Detect external dialog closure (Click outside or 'X') and sync state."""
        # 1. Skip if no dialog is supposed to be open according to our state
        any_open = any([
            self.state.is_dialog_open("file"),
            self.state.is_dialog_open("sql"),
            self.state.is_dialog_open("api"),
            self.state.is_dialog_open("project_export"),
            self.state.is_dialog_open("project_import")
        ])
        if not any_open:
            return

        # 2. Check for 'Just Opened' flag
        if self.state.get_value("dlg_just_opened"):
            self.state.set_value("dlg_just_opened", False)
            return

        # 3. Compute Current State Hash (Interaction Detection)
        try:
            dlg_keys = [k for k in self.state.get_all_keys() if isinstance(
                k, str) and k.startswith("dlg_")]
            # Exclude buttons and internal trackers from hash
            trackers = ["dlg_just_opened",
                        "dlg_last_hash", "dlg_action", "dlg_busy"]
            input_values = {k: self.state.get_value(k) for k in dlg_keys
                            if not k.startswith("dlg_btn") and k not in trackers}

            input_str = str(sorted(input_values.items()))
            current_hash = hashlib.md5(input_str.encode()).hexdigest()

            # 4. Check for button clicks
            btn_clicked = any(self.state.get_value(k)
                              for k in dlg_keys if k.startswith("dlg_btn"))

            last_hash = self.state.get_value("last_dlg_hash", "")
            is_interaction = btn_clicked or (current_hash != last_hash)

            # 5. Auto-Close if no interaction detected
            if not is_interaction:
                self.state.close_all_dialogs()
                self.state.reset_dialog_state()
                self.state.set_value("last_dlg_hash", "")  # Reset hash
        except Exception:
            pass

    def _update_dialog_hash(self):
        """Update the last known dialog state hash at the end of render."""
        try:
            dlg_keys = [k for k in self.state.get_all_keys() if isinstance(
                k, str) and k.startswith("dlg_")]
            trackers = ["dlg_just_opened",
                        "dlg_last_hash", "dlg_action", "dlg_busy"]
            input_values = {k: self.state.get_value(k) for k in dlg_keys
                            if not k.startswith("dlg_btn") and k not in trackers}

            input_str = str(sorted(input_values.items()))
            self.state.set_value("last_dlg_hash", hashlib.md5(
                input_str.encode()).hexdigest())
        except Exception:
            pass
