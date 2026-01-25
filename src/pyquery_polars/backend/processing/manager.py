"""
ProcessingManager

Provides a unified interface for:
- Recipe application (transformations)
- SQL execution
- View preparation (preview, full, EDA)
- Materialization

"""
from typing import Any, Dict, List, Optional, Sequence, Union

import polars as pl

from pyquery_polars.core.models import RecipeStep, DatasetMetadata
from pyquery_polars.backend.processing.executor import (
    apply_step as _apply_step,
    apply_recipe as _apply_recipe,
    prepare_view as _prepare_view,
    execute_sql as _execute_sql,
    get_profile as _get_profile
)
from pyquery_polars.backend.datasets import DatasetManager
from pyquery_polars.backend.recipes import RecipeManager
from pyquery_polars.backend.io import IOManager
from pyquery_polars.backend.processing.materializer import Materializer


class ProcessingManager:
    """
    Manages all data processing operations.

    Dependencies:
    - DatasetManager: To resolve datasets for execution context
    - RecipeManager: To resolve recipes for nested operations
    - IOManager: To stage data to staging directory

    This class provides a unified interface for:
    - Applying recipe steps and full recipes
    - Preparing views for preview, export, EDA
    - Executing SQL queries
    - Materializing datasets
    - Getting dataset profiles
    """

    def __init__(self, io_manager: IOManager, dataset_manager: DatasetManager, recipe_manager: RecipeManager):
        self._io = io_manager
        self._datasets = dataset_manager
        self._recipes = recipe_manager
        self._materializer = Materializer(self._io)

    # ========== Context Helpers ==========

    def _get_context(self) -> Dict[str, pl.LazyFrame]:
        """Get execution context (all datasets) from DatasetManager."""
        return self._datasets.get_all_for_context()

    def _get_project_recipes(self) -> Dict[str, List[RecipeStep]]:
        """Get all recipes from RecipeManager."""
        return self._recipes.get_all()

    # ========== Recipe Application ==========

    def apply_step(
        self,
        lf: pl.LazyFrame,
        step: RecipeStep
    ) -> pl.LazyFrame:
        """Apply a single recipe step to a LazyFrame."""
        return _apply_step(
            lf,
            step,
            self._get_context(),
            self._get_project_recipes()
        )

    def apply_recipe(
        self,
        lf: pl.LazyFrame,
        recipe: Sequence[Union[dict, RecipeStep]]
    ) -> pl.LazyFrame:
        """Apply a full recipe to a LazyFrame."""
        return _apply_recipe(
            lf,
            recipe,
            self._get_context(),
            self._get_project_recipes()
        )

    # ========== View Preparation ==========

    def prepare_view(
        self,
        meta: DatasetMetadata,
        recipe: Sequence[Union[dict, RecipeStep]],
        mode: str = "preview",
        preview_limit: int = 1000,
        collection_limit: Optional[int] = None
    ) -> Optional[pl.LazyFrame]:
        """
        Prepare a dataset view for usage (Preview, SQL, Export).
        """
        return _prepare_view(
            meta,
            recipe,
            self._get_context(),
            self._get_project_recipes(),
            mode=mode,
            preview_limit=preview_limit,
            collection_limit=collection_limit
        )

    def get_preview(
        self,
        meta: DatasetMetadata,
        recipe: Sequence[Union[dict, RecipeStep]],
        limit: int = 1000
    ) -> Optional[pl.DataFrame]:
        """Get an eager DataFrame preview."""
        lf = self.prepare_view(
            meta,
            recipe,
            mode="preview",
            preview_limit=limit
        )
        if lf is None:
            return None
        return lf.collect()

    def get_eda_view(
        self,
        meta: DatasetMetadata,
        recipe: Sequence[Union[dict, RecipeStep]],
        strategy: str = "preview",
        limit: int = 5000
    ) -> Optional[pl.LazyFrame]:
        """
        Get a view for EDA with specific strategy.
        """
        # Hard cap for browser safety
        limit = min(limit, 100000)

        if strategy == "preview":
            return self.prepare_view(
                meta, recipe, mode="preview", preview_limit=limit
            )

        elif strategy == "full_head":
            return self.prepare_view(
                meta, recipe, mode="full", collection_limit=limit
            )

        elif strategy == "full_sample":
            HARD_LIMIT = 100000
            lf = self.prepare_view(
                meta, recipe, mode="full", collection_limit=HARD_LIMIT
            )

            if lf is not None:
                df = lf.collect()
                if len(df) <= limit:
                    return df.lazy()
                return df.sample(n=limit, seed=42).lazy()

        return None

    def get_dataset_view(self, name: str) -> Optional[pl.LazyFrame]:
        """Get a specific dataset view with its recipe applied."""
        meta = self._datasets.get_metadata(name)
        if not meta:
            return None

        recipe = self._recipes.get(name)
        return self.prepare_view(meta, recipe, mode="full")

    # ========== SQL Execution ==========

    def execute_sql(
        self,
        query: str,
        preview: bool = False,
        preview_limit: int = 1000,
        collection_limit: Optional[int] = None
    ) -> pl.LazyFrame:
        """Execute a SQL query against datasets."""
        # Prepare all dataset views
        final_datasets = {}
        datasets_dict = self._get_context()
        recipe_dict = self._get_project_recipes()

        mode = "preview" if preview else "full"

        # We construct views from dataset manager metadata
        # (This duplicates logic in prepare_view somewhat but is needed for SQL context)
        # Ideally we iterating over DatasetManager keys

        for name in self._datasets.list_names():
            meta = self._datasets.get_metadata(name)
            recipe = recipe_dict.get(name, [])

            if meta:
                view = _prepare_view(
                    meta, recipe, datasets_dict, recipe_dict,
                    mode=mode, preview_limit=preview_limit,
                    collection_limit=collection_limit
                )
                if view is not None:
                    final_datasets[name] = view

        return _execute_sql(query, final_datasets, recipe_dict)

    # ========== Profiling ==========

    def get_profile(
        self,
        base_lf: pl.LazyFrame,
        recipe: Sequence[Union[dict, RecipeStep]]
    ) -> Dict[str, Any]:
        """Get dataset profile (schema, nulls, summary stats)."""
        return _get_profile(base_lf, recipe, self._get_context())

    # ========== Materialization ==========

    def materialize_dataset(
        self,
        dataset_name: str,
        new_name: str,
        recipe: Sequence[Union[dict, RecipeStep]]
    ) -> bool:
        """Materialize a dataset to a new dataset."""
        # Wrapper to get LF view
        def _get_lf(name, r, pr):
            return self.get_dataset_view(name)

        # Wrapper to add dataset
        def _add_ds(name, lf, meta, **kwargs):
            self._datasets.add(name, lf, meta, **kwargs)
            self._recipes.ensure_exists(name)

        return self._materializer.materialize_dataset(
            get_lf_func=_get_lf,
            add_dataset_func=_add_ds,
            dataset_name=dataset_name,
            new_name=new_name,
            recipe=recipe,
            project_recipes=self._get_project_recipes()
        )

    # ========== Schema Operations ==========

    def get_schema(self, lf: pl.LazyFrame) -> Optional[pl.Schema]:
        """Get schema of a LazyFrame."""
        try:
            return lf.collect_schema()
        except:
            return None

    def get_transformed_schema(
        self,
        lf: pl.LazyFrame,
        recipe: Sequence[Union[dict, RecipeStep]]
    ) -> Optional[pl.Schema]:
        """Get schema after applying a recipe."""
        try:
            transformed = self.apply_recipe(lf, recipe)
            return transformed.collect_schema()
        except:
            return None
