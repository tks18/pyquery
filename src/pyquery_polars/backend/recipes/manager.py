"""
RecipeManager

Manages the storage and retrieval of recipes (transformation steps) for datasets.
"""
from typing import Dict, List, Optional

import uuid

from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.params import CastChange, CleanCastParams


class RecipeManager:
    """
    Manage recipe lifecycle (CRUD).

    This class handles:
    - Adding/replacing recipes for datasets
    - Getting recipes for datasets
    - Adding individual steps to recipes
    - Clearing recipes
    - Bulk get/set operations for project import/export
    """

    def __init__(self):
        self._recipes: Dict[str, List[RecipeStep]] = {}

    def add(self, dataset_name: str, recipe: List[RecipeStep]) -> None:
        """Add or replace recipe for a dataset."""
        self._recipes[dataset_name] = recipe

    def get(self, dataset_name: str) -> List[RecipeStep]:
        """Get recipe for a dataset. Returns empty list if none."""
        return self._recipes.get(dataset_name, [])

    def update(self, dataset_name: str, recipe: List[RecipeStep]) -> None:
        """Update (replace) recipe for a dataset."""
        self._recipes[dataset_name] = recipe

    def add_step(self, dataset_name: str, step: RecipeStep) -> None:
        """Add a single step to a dataset's recipe."""
        if dataset_name not in self._recipes:
            self._recipes[dataset_name] = []
        self._recipes[dataset_name].append(step)

    def clear(self, dataset_name: str) -> None:
        """Clear all recipe steps for a dataset."""
        self._recipes[dataset_name] = []

    def remove(self, dataset_name: str) -> bool:
        """Remove recipe for a dataset entirely."""
        if dataset_name in self._recipes:
            del self._recipes[dataset_name]
            return True
        return False

    def rename(self, old_name: str, new_name: str) -> bool:
        """Rename a dataset's recipe (when dataset is renamed)."""
        if old_name in self._recipes:
            self._recipes[new_name] = self._recipes.pop(old_name)
            return True
        return False

    def remove_step(self, dataset_name: str, step_id: str) -> bool:
        """Remove a specific step from a recipe."""
        if dataset_name in self._recipes:
            original_len = len(self._recipes[dataset_name])
            self._recipes[dataset_name] = [
                s for s in self._recipes[dataset_name] if s.id != step_id
            ]
            return len(self._recipes[dataset_name]) < original_len
        return False

    def get_all(self) -> Dict[str, List[RecipeStep]]:
        """Get all recipes as a dict (for project export and frontend sync)."""
        return self._recipes.copy()

    def set_all(self, recipes: Dict[str, List[RecipeStep]]) -> None:
        """Set all recipes at once (for project import)."""
        self._recipes = recipes.copy()

    def clear_all(self) -> None:
        """Clear all recipes."""
        self._recipes.clear()

    def ensure_exists(self, dataset_name: str) -> None:
        """Ensure a recipe exists for a dataset (initialize if not)."""
        if dataset_name not in self._recipes:
            self._recipes[dataset_name] = []

    def exists(self, dataset_name: str) -> bool:
        """Check if a recipe exists for a dataset."""
        return dataset_name in self._recipes

    def __contains__(self, dataset_name: str) -> bool:
        """Support 'in' operator."""
        return self.exists(dataset_name)

    def __iter__(self):
        """Iterate over dataset names that have recipes."""
        return iter(self._recipes.keys())

    def items(self):
        """Iterate over (dataset_name, recipe) pairs."""
        return self._recipes.items()

    def apply_inferred_types(self, dataset_name: str, inferred_types: Dict[str, str], merge_step_id: Optional[str] = None, prepend: bool = False, label: Optional[str] = None) -> None:
        """
        Create or update a CleanCast step based on inferred types.

        Args:
           dataset_name: Target dataset
           inferred_types: Dict of {column: type_str}
           merge_step_id: Optional, if provided, updates this step instead of creating new
           prepend: If True, insert new step at the start (if creating new)
           label: Optional custom label for the step
        """
        if not inferred_types:
            return

        # Map types to actions
        TYPE_ACTION_MAP = {
            "Int64": "To Int",
            "Float64": "To Float",
            "Date": "To Date",
            "Datetime": "To Datetime",
            "Boolean": "To Boolean"
        }

        changes = []
        for col, dtype in inferred_types.items():
            action = TYPE_ACTION_MAP.get(dtype)
            if action:
                changes.append(CastChange(col=col, action=action))

        if changes:
            self.apply_cast_changes(
                dataset_name, changes, merge_step_id, prepend, label)

    def apply_cast_changes(self, dataset_name: str, changes: List["CastChange"], merge_step_id: Optional[str] = None, prepend: bool = False, label: Optional[str] = None) -> None:
        """
        Apply a list of CastChanges to a dataset recipe (merge or new).

        Args:
            dataset_name: Target dataset
            changes: List of CastChange objects
            merge_step_id: Optional step ID to merge into
            prepend: If True, insert new step at start
            label: Optional custom label for the step
        """
        if not changes:
            return

        # Handle Merge vs New
        target_step = None
        if merge_step_id:
            # Find existing step
            steps = self.get(dataset_name)
            for s in steps:
                if s.id == merge_step_id:
                    target_step = s
                    break

        if target_step and target_step.type == "clean_cast":
            # Merge params
            current_params = CleanCastParams(**target_step.params)

            # Remove existing changes for these columns (overlap)
            new_cols = {c.col for c in changes}
            kept = [c for c in current_params.changes if c.col not in new_cols]

            # Combine
            current_params.changes = kept + changes

            # Update step params
            target_step.params = current_params.model_dump()
        else:
            # Create NEW Step
            step_id = str(uuid.uuid4())
            params = CleanCastParams(changes=changes)

            step = RecipeStep(
                id=step_id,
                type="clean_cast",
                label=label or "Auto Clean Types",
                params=params.model_dump()
            )

            if prepend:
                if dataset_name not in self._recipes:
                    self._recipes[dataset_name] = []
                self._recipes[dataset_name].insert(0, step)
            else:
                self.add_step(dataset_name, step)
