"""
Base loader class for data import dialogs.

This module provides the abstract base class for all data loaders (File, SQL, API).
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, cast

import streamlit as st

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.frontend.components.loaders.utils import handle_auto_inference


class BaseLoader(BaseComponent):
    """
    Abstract base class for data loader dialogs.

    Each loader type (File, SQL, API) should inherit from this class and
    implement the render() method to display the loader dialog UI.

    This class provides common functionality:
    - Edit mode initialization
    - Dataset registration after load
    - Auto-inference handling

    Example:
        class SQLLoader(BaseLoader):
            def render(self, edit_mode=False, edit_dataset_name=None):
                # Show SQL connection dialog
                pass
    """

    # Override in subclasses
    LOADER_NAME: str = "Base"
    LOADER_TYPE: str = "base"
    STATE_KEY: str = "show_loader_base"

    def __init__(self, ctx: AppContext) -> None:
        """Initialize loader with app context."""
        super().__init__(ctx)

    def _get_edit_init_key(self) -> str:
        """Get session state key for edit init flag."""
        return f"dlg_{self.LOADER_NAME}_edit_initialized"

    def _load_edit_params(self, edit_dataset_name: str) -> dict:
        """
        Load parameters from existing dataset metadata for edit mode.

        Args:
            edit_dataset_name: Name of dataset being edited

        Returns:
            Dict of loader parameters from metadata
        """
        meta = self.engine.datasets.get_metadata(edit_dataset_name)
        if meta and meta.loader_params:
            return meta.loader_params
        return {}

    def _register_dataset(self, alias: str, lf_or_lfs, meta,
                          loader_params: dict, auto_infer: bool = False,
                          edit_mode: bool = False,
                          edit_dataset_name: Optional[str] = None) -> bool:
        """
        Common logic for registering a loaded dataset.

        Handles:
        - Edit mode (removing old dataset if renamed)
        - Adding to engine.datasets
        - Initializing recipe
        - Auto-inference if requested

        Args:
            alias: Dataset alias/name
            lf_or_lfs: LazyFrame or dict of LazyFrames
            meta: Dataset metadata
            loader_params: Parameters used by loader
            auto_infer: Whether to run auto type inference
            edit_mode: If editing existing dataset
            edit_dataset_name: Original dataset name if editing

        Returns:
            True if registration successful
        """
        try:
            # Handle edit mode - remove old if renamed
            if edit_mode and edit_dataset_name:
                if alias != edit_dataset_name:
                    if edit_dataset_name in self.state.all_recipes:
                        self.state.all_recipes[alias] = self.state.all_recipes.pop(
                            edit_dataset_name)
                    self.engine.datasets.remove(edit_dataset_name)
                else:
                    self.engine.datasets.remove(alias)

            # Add to engine
            self.engine.datasets.add(
                alias, lf_or_lfs, meta,
                loader_type=cast(Any, self.LOADER_TYPE),
                loader_params=loader_params
            )

            # Initialize recipe if new
            if alias not in self.state.all_recipes:
                self.state.all_recipes[alias] = []

            # Set as active
            self.state.active_dataset = alias
            self.state.recipe_steps = []

            # Run auto inference if requested
            if auto_infer:
                handle_auto_inference(self.engine, alias, state=self.state)

            return True

        except Exception as e:
            st.error(f"Failed to register dataset: {e}")
            return False

    def _hide_dialog(self) -> None:
        """Hide this loader's dialog and rerun."""
        self.state.set_value(self.STATE_KEY, False)
        st.rerun()

    @abstractmethod
    def render(self, edit_mode: bool = False,
               edit_dataset_name: Optional[str] = None) -> Any:
        """
        Render the loader dialog.

        Args:
            edit_mode: If True, pre-fill inputs from existing dataset
            edit_dataset_name: Name of dataset to edit

        Returns:
            Implementation-specific return value
        """
        pass
