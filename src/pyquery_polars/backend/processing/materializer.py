
import os
import polars as pl
from typing import Callable, Optional, Sequence, Union, Dict, List, Any
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.backend.io.files import get_staging_dir


class StorageManager:
    @staticmethod
    def materialize_dataset(
        get_lf_func: Callable[..., Optional[pl.LazyFrame]],
        add_dataset_func: Callable[[str, pl.LazyFrame, Optional[Dict]], None],
        dataset_name: str,
        new_name: str,
        recipe: Sequence[Union[dict, RecipeStep]],
        project_recipes: Optional[Dict[str, List[RecipeStep]]] = None
    ) -> bool:
        """
        Materializes a dataset with optional recipe to a new parquet file in staging.

        Args:
            get_lf_func: Callback to get the source LazyFrame (e.g. engine.get_dataset_for_export)
            add_dataset_func: Callback to register the new dataset (e.g. engine.add_dataset)
            dataset_name: Source dataset name
            new_name: Target dataset name
            recipe: Recipe to apply
            project_recipes: Context for recipe
        """
        try:
            # 1. Get the dataset LazyFrame (use export version to handle individual processing)
            if recipe is None:
                recipe = []

            # Call the getter with (name, recipe, project_recipes)
            lf = get_lf_func(dataset_name, recipe, project_recipes)
            if lf is None:
                raise ValueError(f"Dataset '{dataset_name}' not found")

            # 2. Get Centralized Staging Dir
            staging_dir = get_staging_dir()

            # 3. Sanitize Name (Basic)
            safe_name = "".join(
                x for x in new_name if x.isalnum() or x in " _-").strip()
            if not safe_name:
                raise ValueError("Invalid dataset name")

            file_path = os.path.join(staging_dir, f"{safe_name}.parquet")

            # 4. Write (always LazyFrame from backend)
            lf.sink_parquet(file_path)

            # 5. Register as new dataset
            new_lf = pl.scan_parquet(file_path)
            add_dataset_func(safe_name, new_lf, {
                "source_path": file_path,
                "input_type": "file",
                "input_format": ".parquet"
            })
            return True
        except Exception as e:
            print(f"Materialization Error: {e}")
            return False
