"""
StateManager - Centralized session state management for the frontend.
"""

from typing import List, Optional, Dict, Any
import streamlit as st
import json
import copy
from datetime import datetime

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.registry import StepRegistry


class StateManager:
    """
    Manages Streamlit session state for the application.

    Handles:
    - Recipe state management (per dataset)
    - Undo/redo history
    - Synchronization with backend engine
    - EDA state initialization

    This class encapsulates all session state operations that were
    previously scattered across module-level functions.

    Attributes:
        engine: PyQueryEngine instance for backend operations
    """

    def __init__(self, engine: PyQueryEngine) -> None:
        """
        Initialize StateManager with engine reference.

        Args:
            engine: PyQueryEngine instance for backend operations
        """
        self._engine = engine
        self._init_session_state()

    @property
    def engine(self) -> PyQueryEngine:
        """Get the PyQueryEngine instance."""
        return self._engine

    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    def _init_session_state(self) -> None:
        """Initialize all session state variables with defaults."""
        # Core state
        if 'all_recipes' not in st.session_state:
            st.session_state.all_recipes = {}

        if 'recipe_steps' not in st.session_state:
            st.session_state.recipe_steps = []

        # Undo/Redo stacks
        if 'history_stack' not in st.session_state:
            st.session_state.history_stack = []
        if 'redo_stack' not in st.session_state:
            st.session_state.redo_stack = []

        # UI state
        if 'last_added_id' not in st.session_state:
            st.session_state.last_added_id = None
        if 'active_base_dataset' not in st.session_state:
            st.session_state.active_base_dataset = None
        if 'file_path_buffer' not in st.session_state:
            st.session_state.file_path_buffer = ""
        if 'view_at_step_id' not in st.session_state:
            st.session_state.view_at_step_id = None

        # Loader & Dialog State
        if 'show_loader_file' not in st.session_state:
            st.session_state.show_loader_file = False
        if 'show_loader_sql' not in st.session_state:
            st.session_state.show_loader_sql = False
        if 'show_loader_api' not in st.session_state:
            st.session_state.show_loader_api = False
        if 'edit_mode_dataset' not in st.session_state:
            st.session_state.edit_mode_dataset = None
        if 'show_project_export' not in st.session_state:
            st.session_state.show_project_export = False
        if 'show_project_import' not in st.session_state:
            st.session_state.show_project_import = False
        if 'dlg_just_opened' not in st.session_state:
            st.session_state.dlg_just_opened = False
        if 'last_dlg_hash' not in st.session_state:
            st.session_state.last_dlg_hash = ""

        # New UI & Project flags
        if 'just_added_step' not in st.session_state:
            st.session_state.just_added_step = False
        if 'cleanup_done' not in st.session_state:
            st.session_state.cleanup_done = False
        if 'proj_export_base_dir' not in st.session_state:
            st.session_state.proj_export_base_dir = ""
        if 'proj_export_path' not in st.session_state:
            st.session_state.proj_export_path = ""
        if 'export_folder' not in st.session_state:
            st.session_state.export_folder = ""
        if 'export_filename' not in st.session_state:
            st.session_state.export_filename = ""

        # Initialize EDA state
        self.init_eda_state()

    def init_eda_state(self) -> None:
        """Initialize EDA-specific session state variables."""
        if 'eda_ready' not in st.session_state:
            st.session_state.eda_ready = False
        if 'eda_show_labels' not in st.session_state:
            st.session_state.eda_show_labels = False

        # Simulation state
        if 'sim_model' not in st.session_state:
            st.session_state.sim_model = None
        if 'sim_feats' not in st.session_state:
            st.session_state.sim_feats = []
        if 'sim_X' not in st.session_state:
            st.session_state.sim_X = None
        if 'sim_score' not in st.session_state:
            st.session_state.sim_score = 0
        if 'sim_metrics' not in st.session_state:
            st.session_state.sim_metrics = {}
        if 'sim_is_cat' not in st.session_state:
            st.session_state.sim_is_cat = False
        if 'sim_target' not in st.session_state:
            st.session_state.sim_target = None
        if 'sim_explainer' not in st.session_state:
            st.session_state.sim_explainer = None
        if 'sim_scenarios' not in st.session_state:
            st.session_state.sim_scenarios = {}
        if 'eda_tgt_run' not in st.session_state:
            st.session_state.eda_tgt_run = False
        if 'eda_ts_run' not in st.session_state:
            st.session_state.eda_ts_run = False
        if 'eda_dist_run' not in st.session_state:
            st.session_state.eda_dist_run = False
        if 'eda_hier_run' not in st.session_state:
            st.session_state.eda_hier_run = False
        if 'eda_rel_scatter_run' not in st.session_state:
            st.session_state.eda_rel_scatter_run = False

        # Config
        if 'eda_sample_limit' not in st.session_state:
            st.session_state.eda_sample_limit = 5000
        if 'eda_theme' not in st.session_state:
            st.session_state.eda_theme = "plotly"
        if 'eda_sql_query' not in st.session_state:
            st.session_state.eda_sql_query = ""

        # SQL State
        if 'sql_query' not in st.session_state:
            st.session_state.sql_query = ""
        if 'sql_history' not in st.session_state:
            st.session_state.sql_history = []
        if 'sql_run_trigger' not in st.session_state:
            st.session_state.sql_run_trigger = False
        if 'sql_export_folder' not in st.session_state:
            st.session_state.sql_export_folder = ""

    # =========================================================================
    # TYPED PROPERTY ACCESSORS (Type-Safe State Access)
    # =========================================================================

    @property
    def active_dataset(self) -> Optional[str]:
        """Get the currently active dataset name."""
        return st.session_state.get("active_base_dataset")

    @active_dataset.setter
    def active_dataset(self, value: Optional[str]) -> None:
        """Set the currently active dataset name."""
        st.session_state["active_base_dataset"] = value

    @property
    def recipe_steps(self) -> List[RecipeStep]:
        """Get the current recipe steps for active dataset."""
        return st.session_state.get("recipe_steps", [])

    @recipe_steps.setter
    def recipe_steps(self, value: List[RecipeStep]) -> None:
        """Set the current recipe steps."""
        st.session_state["recipe_steps"] = value

    @property
    def all_recipes(self) -> Dict[str, List[RecipeStep]]:
        """Get all recipes dictionary."""
        return st.session_state.get("all_recipes", {})

    @all_recipes.setter
    def all_recipes(self, value: Dict[str, List[RecipeStep]]) -> None:
        """Set all recipes dictionary."""
        st.session_state["all_recipes"] = value

    @property
    def edit_mode_dataset(self) -> Optional[str]:
        """Get the dataset currently being edited (if any)."""
        return st.session_state.get("edit_mode_dataset")

    @edit_mode_dataset.setter
    def edit_mode_dataset(self, value: Optional[str]) -> None:
        """Set the dataset to edit."""
        st.session_state["edit_mode_dataset"] = value

    @property
    def last_added_id(self) -> Optional[str]:
        """Get the ID of the last added step."""
        return st.session_state.get("last_added_id")

    @last_added_id.setter
    def last_added_id(self, value: Optional[str]) -> None:
        """Set the ID of the last added step."""
        st.session_state["last_added_id"] = value

    @property
    def view_at_step_id(self) -> Optional[str]:
        """Get the step ID currently being previewed."""
        return st.session_state.get("view_at_step_id")

    @view_at_step_id.setter
    def view_at_step_id(self, value: Optional[str]) -> None:
        """Set the step ID to preview."""
        st.session_state["view_at_step_id"] = value

    @property
    def sql_query(self) -> str:
        """Get current SQL query."""
        return st.session_state.get("sql_query", "")

    @sql_query.setter
    def sql_query(self, value: str) -> None:
        """Set current SQL query."""
        st.session_state["sql_query"] = value

    @property
    def sql_history(self) -> List[str]:
        """Get SQL query history."""
        return st.session_state.get("sql_history", [])

    @sql_history.setter
    def sql_history(self, value: List[str]) -> None:
        """Set SQL query history."""
        st.session_state["sql_history"] = value

    @property
    def sql_run_trigger(self) -> bool:
        """Get SQL run trigger status."""
        return st.session_state.get("sql_run_trigger", False)

    @sql_run_trigger.setter
    def sql_run_trigger(self, value: bool) -> None:
        """Set SQL run trigger status."""
        st.session_state["sql_run_trigger"] = value

    @property
    def just_added_step(self) -> bool:
        """Flag indicating a step was just added to focus UI."""
        return st.session_state.get("just_added_step", False)

    @just_added_step.setter
    def just_added_step(self, value: bool) -> None:
        st.session_state["just_added_step"] = value

    @property
    def cleanup_done(self) -> bool:
        """Flag indicating session cleanup has been performed."""
        return st.session_state.get("cleanup_done", False)

    @cleanup_done.setter
    def cleanup_done(self, value: bool) -> None:
        st.session_state["cleanup_done"] = value

    @property
    def proj_export_base_dir(self) -> str:
        """Base directory for relative project exports."""
        return st.session_state.get("proj_export_base_dir", "")

    @proj_export_base_dir.setter
    def proj_export_base_dir(self, value: str) -> None:
        st.session_state["proj_export_base_dir"] = value

    @property
    def proj_export_path(self) -> str:
        """Last used project export path."""
        return st.session_state.get("proj_export_path", "")

    @proj_export_path.setter
    def proj_export_path(self, value: str) -> None:
        st.session_state["proj_export_path"] = value

    @property
    def eda_sample_limit(self) -> int:
        """Maximum rows for EDA analysis."""
        return st.session_state.get("eda_sample_limit", 5000)

    @eda_sample_limit.setter
    def eda_sample_limit(self, value: int) -> None:
        st.session_state["eda_sample_limit"] = value

    @property
    def eda_show_labels(self) -> bool:
        """Whether to show data labels in EDA plots."""
        return st.session_state.get("eda_show_labels", False)

    @eda_show_labels.setter
    def eda_show_labels(self, value: bool) -> None:
        st.session_state["eda_show_labels"] = value

    @property
    def eda_sql_query(self) -> str:
        """Current custom SQL query for EDA."""
        return st.session_state.get("eda_sql_query", "")

    @eda_sql_query.setter
    def eda_sql_query(self, value: str) -> None:
        st.session_state["eda_sql_query"] = value

    @property
    def eda_theme(self) -> str:
        """Plotting theme for EDA."""
        return st.session_state.get("eda_theme", "plotly")

    @eda_theme.setter
    def eda_theme(self, value: str) -> None:
        st.session_state["eda_theme"] = value

    @property
    def sql_export_folder(self) -> str:
        """Last used SQL export folder."""
        return st.session_state.get("sql_export_folder", "")

    @sql_export_folder.setter
    def sql_export_folder(self, value: str) -> None:
        st.session_state["sql_export_folder"] = value

    @property
    def export_folder(self) -> str:
        """Last used general export folder."""
        return st.session_state.get("export_folder", "")

    @export_folder.setter
    def export_folder(self, value: str) -> None:
        st.session_state["export_folder"] = value

    @property
    def export_filename(self) -> str:
        """Last used general export filename."""
        return st.session_state.get("export_filename", "")

    @export_filename.setter
    def export_filename(self, value: str) -> None:
        st.session_state["export_filename"] = value

    # ==========================================
    # GENERIC VALUE ACCESSORS
    # ==========================================

    def get_value(self, key: str, default: Any = None) -> Any:
        """Generic session state getter."""
        return st.session_state.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """Generic session state setter."""
        st.session_state[key] = value

    def has_value(self, key: str) -> bool:
        """Generic session state key check."""
        return key in st.session_state

    def delete_value(self, key: str) -> None:
        """Generic session state key deletion."""
        if key in st.session_state:
            del st.session_state[key]

    def get_all_keys(self) -> List[str]:
        """Get all keys in session state."""
        return [str(k) for k in st.session_state.keys()]

    # =========================================================================
    # DIALOG STATE METHODS (Type-Safe Dialog Access)
    # =========================================================================

    def is_dialog_open(self, dialog_type: str) -> bool:
        """
        Check if a dialog is currently open.

        Args:
            dialog_type: One of 'file', 'sql', 'api', 'project_export', 'project_import'

        Returns:
            True if the dialog is open
        """
        key = f"show_loader_{dialog_type}" if dialog_type in (
            'file', 'sql', 'api') else f"show_{dialog_type}"
        return st.session_state.get(key, False)

    def open_dialog(self, dialog_type: str) -> None:
        """
        Open a dialog.

        Args:
            dialog_type: One of 'file', 'sql', 'api', 'project_export', 'project_import'
        """
        key = f"show_loader_{dialog_type}" if dialog_type in (
            'file', 'sql', 'api') else f"show_{dialog_type}"
        st.session_state[key] = True
        st.session_state.dlg_just_opened = True

    def close_dialog(self, dialog_type: str) -> None:
        """
        Close a dialog.

        Args:
            dialog_type: One of 'file', 'sql', 'api', 'project_export', 'project_import'
        """
        key = f"show_loader_{dialog_type}" if dialog_type in (
            'file', 'sql', 'api') else f"show_{dialog_type}"
        st.session_state[key] = False

    @property
    def eda_tgt_run(self) -> bool:
        """Flag to run target analysis."""
        return st.session_state.get("eda_tgt_run", False)

    @eda_tgt_run.setter
    def eda_tgt_run(self, value: bool) -> None:
        st.session_state["eda_tgt_run"] = value

    @property
    def eda_ts_run(self) -> bool:
        """Flag to run time series analysis."""
        return st.session_state.get("eda_ts_run", False)

    @eda_ts_run.setter
    def eda_ts_run(self, value: bool) -> None:
        st.session_state["eda_ts_run"] = value

    @property
    def eda_dist_run(self) -> bool:
        """Flag to run distribution analysis."""
        return st.session_state.get("eda_dist_run", False)

    @eda_dist_run.setter
    def eda_dist_run(self, value: bool) -> None:
        st.session_state["eda_dist_run"] = value

    @property
    def eda_hier_run(self) -> bool:
        """Flag to run hierarchy analysis."""
        return st.session_state.get("eda_hier_run", False)

    @eda_hier_run.setter
    def eda_hier_run(self, value: bool) -> None:
        st.session_state["eda_hier_run"] = value

    @property
    def eda_rel_scatter_run(self) -> bool:
        """Flag to run scatter plot analysis."""
        return st.session_state.get("eda_rel_scatter_run", False)

    @eda_rel_scatter_run.setter
    def eda_rel_scatter_run(self, value: bool) -> None:
        st.session_state["eda_rel_scatter_run"] = value

    def close_all_dialogs(self) -> None:
        """Close all loader and project dialogs."""
        st.session_state["show_loader_file"] = False
        st.session_state["show_loader_sql"] = False
        st.session_state["show_loader_api"] = False
        st.session_state["show_project_export"] = False
        st.session_state["show_project_import"] = False
        st.session_state["edit_mode_dataset"] = None

    # =========================================================================
    # LOADER-SPECIFIC STATE METHODS (For Dialog Components)
    # =========================================================================

    def get_loader_value(self, loader_name: str, key: str, default: Any = None) -> Any:
        """
        Get a loader-specific session state value.

        Args:
            loader_name: Loader identifier (e.g., 'File', 'SQL', 'API')
            key: State key suffix (e.g., 'alias', 'path', 'busy')
            default: Default value if key doesn't exist

        Returns:
            The stored value or default
        """
        full_key = f"dlg_{loader_name}_{key}"
        return st.session_state.get(full_key, default)

    def set_loader_value(self, loader_name: str, key: str, value: Any) -> None:
        """
        Set a loader-specific session state value.

        Args:
            loader_name: Loader identifier (e.g., 'File', 'SQL', 'API')
            key: State key suffix (e.g., 'alias', 'path', 'busy')
            value: Value to store
        """
        full_key = f"dlg_{loader_name}_{key}"
        st.session_state[full_key] = value

    def has_loader_value(self, loader_name: str, key: str) -> bool:
        """
        Check if a loader-specific session state key exists.

        Args:
            loader_name: Loader identifier
            key: State key suffix

        Returns:
            True if the key exists
        """
        full_key = f"dlg_{loader_name}_{key}"
        return full_key in st.session_state

    def delete_loader_value(self, loader_name: str, key: str) -> None:
        """
        Delete a loader-specific session state value.

        Args:
            loader_name: Loader identifier
            key: State key suffix
        """
        full_key = f"dlg_{loader_name}_{key}"
        if full_key in st.session_state:
            del st.session_state[full_key]

    def clear_loader_state(self, loader_name: str, prefix: str = "dlg_") -> None:
        """
        Clear all session state keys for a specific loader.

        Args:
            loader_name: Loader identifier
            prefix: Key prefix to match (default: 'dlg_')
        """
        pattern = f"{prefix}{loader_name}_"
        keys_to_remove = [k for k in st.session_state.keys()
                          if isinstance(k, str) and k.startswith(pattern)]
        for key in keys_to_remove:
            del st.session_state[key]

    def reset_dialog_state(self) -> None:
        """Reset all dialog-related state (keys starting with 'dlg_')."""
        keys_to_remove = [k for k in st.session_state.keys()
                          if isinstance(k, str) and k.startswith("dlg_")]
        for key in keys_to_remove:
            del st.session_state[key]

    # =========================================================================
    # BACKEND SYNC
    # =========================================================================

    def sync_to_backend(self, dataset_name: str, recipe: List[RecipeStep]) -> None:
        """
        Sync recipe to backend engine for persistence.

        Args:
            dataset_name: Name of the dataset
            recipe: List of recipe steps to sync
        """
        if self._engine and dataset_name:
            try:
                self._engine.recipes.update(dataset_name, recipe)
            except Exception as e:
                print(f"Backend sync warning: {e}")

    def sync_from_backend(self, dataset_name: str) -> List[RecipeStep]:
        """
        Sync recipe FROM backend to frontend for given dataset.

        Called after project import or other backend-initiated changes.

        Args:
            dataset_name: Name of the dataset to sync

        Returns:
            The synced recipe steps
        """
        if self._engine and dataset_name:
            try:
                backend_recipe = self._engine.recipes.get(dataset_name)
                st.session_state.all_recipes[dataset_name] = backend_recipe
                if st.session_state.active_base_dataset == dataset_name:
                    st.session_state.recipe_steps = backend_recipe
                return backend_recipe
            except Exception as e:
                print(f"Backend sync warning: {e}")
        return []

    def sync_all_from_backend(self) -> None:
        """
        Sync ALL recipes from backend to frontend.

        Called after project import or initial load.
        """
        if self._engine:
            try:
                all_backend_recipes = self._engine.recipes.get_all()
                st.session_state.all_recipes = all_backend_recipes

                # Update active recipe_steps if applicable
                active_ds = st.session_state.active_base_dataset
                if active_ds and active_ds in all_backend_recipes:
                    st.session_state.recipe_steps = all_backend_recipes[active_ds]
            except Exception as e:
                st.toast(f"Backend sync warning: {e}", icon="⚠️")
                print(f"Backend sync all warning: {e}")

    # =========================================================================
    # RECIPE ACCESS
    # =========================================================================

    def get_active_recipe(self) -> List[RecipeStep]:
        """
        Get recipe for currently active dataset.

        Returns:
            List of recipe steps for active dataset, or empty list
        """
        active_ds = st.session_state.active_base_dataset
        if active_ds and active_ds in st.session_state.all_recipes:
            return st.session_state.all_recipes[active_ds]
        return []

    def get_all_recipes(self) -> Dict[str, List[RecipeStep]]:
        """
        Get all recipes.

        Returns:
            Dictionary mapping dataset names to recipe steps
        """
        return st.session_state.all_recipes

    # =========================================================================
    # UNDO/REDO
    # =========================================================================

    @property
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(st.session_state.get('history_stack', [])) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(st.session_state.get('redo_stack', [])) > 0

    def save_checkpoint(self) -> None:
        """
        Save current state to undo stack before making changes.

        Call this before any mutation to enable undo.
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds:
            return

        current_steps = st.session_state.all_recipes.get(active_ds, [])
        snapshot = copy.deepcopy(current_steps)

        # Cap history stack
        if len(st.session_state.history_stack) > 20:
            st.session_state.history_stack.pop(0)

        st.session_state.history_stack.append(snapshot)
        # Clear redo stack on new branch
        st.session_state.redo_stack = []

    def undo(self) -> bool:
        """
        Undo last action.

        Returns:
            True if undo was performed, False if nothing to undo
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds or not st.session_state.history_stack:
            return False

        # Push current to redo
        current = st.session_state.all_recipes.get(active_ds, [])
        st.session_state.redo_stack.append(copy.deepcopy(current))

        # Pop from history
        prev_state = st.session_state.history_stack.pop()

        # Regenerate IDs to force widget reset
        ts = int(datetime.now().timestamp() * 10000)
        for i, step in enumerate(prev_state):
            step.id = f"{ts}_{i}"

        # Apply
        st.session_state.all_recipes[active_ds] = prev_state
        st.session_state.recipe_steps = prev_state

        # Sync to backend
        self.sync_to_backend(active_ds, prev_state)
        return True

    def redo(self) -> bool:
        """
        Redo last undone action.

        Returns:
            True if redo was performed, False if nothing to redo
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds or not st.session_state.redo_stack:
            return False

        # Push current to history
        current = st.session_state.all_recipes.get(active_ds, [])
        st.session_state.history_stack.append(copy.deepcopy(current))

        # Pop from redo
        next_state = st.session_state.redo_stack.pop()

        # Regenerate IDs
        ts = int(datetime.now().timestamp() * 10000)
        for i, step in enumerate(next_state):
            step.id = f"{ts}_{i}"

        # Apply
        st.session_state.all_recipes[active_ds] = next_state
        st.session_state.recipe_steps = next_state

        # Sync to backend
        self.sync_to_backend(active_ds, next_state)
        return True

    # =========================================================================
    # STEP OPERATIONS
    # =========================================================================

    def add_step(self, step_type: str, default_label: str) -> Optional[str]:
        """
        Add a new step to the active recipe.

        Args:
            step_type: Type of step (e.g., 'fill_nulls', 'filter_rows')
            default_label: Human-readable label for the step

        Returns:
            The new step's ID, or None if failed
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds:
            st.error("No active dataset selected to add step to.")
            return None

        # Use Registry to get default params
        definition = StepRegistry.get(step_type)
        if not definition:
            st.error(f"Unknown step type: {step_type}")
            return None

        # Instantiate params model for defaults
        try:
            if definition.params_model:
                default_params_obj = definition.params_model()
                default_params_dict = default_params_obj.model_dump()
            else:
                default_params_dict = {}
        except Exception as e:
            st.error(f"Failed to init params: {e}")
            return None

        self.save_checkpoint()

        new_id = str(datetime.now().timestamp())

        new_step = RecipeStep(
            id=new_id,
            type=step_type,
            label=default_label,
            params=default_params_dict
        )

        if active_ds not in st.session_state.all_recipes:
            st.session_state.all_recipes[active_ds] = []

        st.session_state.all_recipes[active_ds].append(new_step)
        st.session_state.last_added_id = new_id
        st.session_state.recipe_steps = st.session_state.all_recipes[active_ds]
        st.session_state.just_added_step = True

        # Sync to backend
        self.sync_to_backend(
            active_ds, st.session_state.all_recipes[active_ds])

        return new_id

    def delete_step(self, index: int) -> bool:
        """
        Delete step at given index.

        Args:
            index: Index of step to delete

        Returns:
            True if deleted, False otherwise
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds:
            return False

        self.save_checkpoint()

        st.session_state.all_recipes[active_ds].pop(index)
        st.session_state.recipe_steps = st.session_state.all_recipes[active_ds]

        # Sync to backend
        self.sync_to_backend(
            active_ds, st.session_state.all_recipes[active_ds])
        return True

    def move_step(self, index: int, direction: int) -> bool:
        """
        Move step up (-1) or down (+1).

        Args:
            index: Current index of step
            direction: -1 for up, +1 for down

        Returns:
            True if moved, False otherwise
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds:
            return False

        self.save_checkpoint()

        steps = st.session_state.all_recipes[active_ds]

        if direction == -1 and index > 0:
            steps[index], steps[index-1] = steps[index-1], steps[index]
            st.session_state.last_added_id = steps[index-1].id
        elif direction == 1 and index < len(steps) - 1:
            steps[index], steps[index+1] = steps[index+1], steps[index]
            st.session_state.last_added_id = steps[index+1].id
        else:
            return False

        st.session_state.recipe_steps = steps

        # Sync to backend
        self.sync_to_backend(active_ds, steps)
        return True

    def update_step_params(self, step_id: str, new_params: dict,
                           create_checkpoint: bool = True) -> bool:
        """
        Update params for a specific step.

        Args:
            step_id: ID of step to update
            new_params: New parameter dictionary
            create_checkpoint: Whether to create undo checkpoint

        Returns:
            True if updated, False otherwise
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds:
            return False

        if create_checkpoint:
            self.save_checkpoint()

        steps = st.session_state.all_recipes.get(active_ds, [])
        for step in steps:
            if step.id == step_id:
                step.params = new_params
                st.session_state.recipe_steps = steps
                st.session_state.all_recipes[active_ds] = steps

                # Sync to backend
                self.sync_to_backend(active_ds, steps)
                return True

        return False

    def clear_active_recipe(self) -> None:
        """Clear all steps from the active recipe."""
        active_ds = self.active_dataset
        if active_ds:
            self.save_checkpoint()
            st.session_state.all_recipes[active_ds] = []
            st.session_state.recipe_steps = []
            self.sync_to_backend(active_ds, [])

    # =========================================================================
    # RECIPE I/O
    # =========================================================================

    def load_recipe_from_json(self, uploaded_file) -> bool:
        """
        Load recipe from uploaded JSON file.

        Args:
            uploaded_file: Streamlit uploaded file object

        Returns:
            True if loaded successfully, False otherwise
        """
        active_ds = st.session_state.active_base_dataset
        if not active_ds:
            st.error("No active dataset to load recipe into.")
            return False

        try:
            data = json.load(uploaded_file)
            steps = []
            for s in data:
                steps.append(RecipeStep(**s))

            self.save_checkpoint()

            st.session_state.all_recipes[active_ds] = steps
            st.session_state.recipe_steps = steps

            # Sync to backend
            self.sync_to_backend(active_ds, steps)

            st.success("Recipe loaded!")
            return True
        except Exception as e:
            st.error(f"Invalid JSON or Schema Mismatch: {e}")
            return False

    # =========================================================================
    # WIDGET STATE UTILITIES
    # =========================================================================

    def cleanup_widget_state(self, steps: List[RecipeStep]) -> None:
        """
        Clear Streamlit widget state for given steps to force UI refresh.

        Args:
            steps: List of steps whose widget state should be cleared
        """
        step_ids = {s.id for s in steps}

        keys_to_remove = []
        for key in st.session_state.keys():
            key_str = str(key)
            for sid in step_ids:
                if sid in key_str:
                    keys_to_remove.append(key)
                    break

        for k in keys_to_remove:
            del st.session_state[k]

        if keys_to_remove:
            st.toast(f"Cleared {len(keys_to_remove)} widget states.")

    def hard_reset(self) -> None:
        """Clear all session state and cache resource."""
        st.cache_resource.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
