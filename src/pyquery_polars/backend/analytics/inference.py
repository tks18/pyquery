
from typing import List, Dict, Optional, Sequence, Any, Union

import polars as pl

from pyquery_polars.core.models import RecipeStep
from pyquery_polars.backend.processing import executor as execution


class TypeInferenceEngine:
    @staticmethod
    def infer_types(base_lf: Optional[pl.LazyFrame],
                    recipe: Sequence[Union[dict, RecipeStep]],
                    datasets_dict: Dict[str, pl.LazyFrame],
                    project_recipes: Optional[Dict[str, List[Any]]] = None,
                    columns: Optional[List[str]] = None,
                    sample_size: int = 1000) -> Dict[str, str]:
        """
        Infer data types for specific columns based on a sample of the transformed data.
        Returns a dictionary mapping column names to suggested PyQuery types (e.g. 'Int64', 'Date').
        """
        if base_lf is None:
            return {}

        # 1. Apply current recipe to get state
        try:
            transformed_lf = execution.apply_recipe(
                base_lf, recipe, datasets_dict, project_recipes)
        except Exception as e:
            # If pipeline breaks, fall back to base
            transformed_lf = base_lf

        # 2. Slice Sample
        try:
            sample_df = transformed_lf.slice(0, sample_size).collect()
        except Exception as e:
            return {}

        # 3. Determine columns to check
        if not columns:
            # Default: Inspect all String columns
            columns = [c for c, t in sample_df.schema.items() if t ==
                       pl.String]

        inferred = {}

        for col in columns:
            if col not in sample_df.columns:
                continue

            s = sample_df[col]
            # Skip if empty
            if s.len() == 0:
                continue

            # Only infer for strings (safest for now)
            if s.dtype != pl.String:
                continue

            non_null_s = s.drop_nulls()
            if non_null_s.len() == 0:
                continue

            # Helper to check success rate (STRICT)
            def check_cast(dtype):
                try:
                    casted = non_null_s.cast(dtype, strict=False)
                    # Count nulls that weren't null before (failure to cast)
                    new_nulls = casted.null_count()
                    return new_nulls == 0  # Strict success
                except:
                    return False

            # 1. Boolean (common strings)
            try:
                upper = non_null_s.str.to_uppercase()
                is_bool = upper.is_in(
                    ["TRUE", "FALSE", "T", "F", "1", "0", "YES", "NO"]).all()
                if is_bool:
                    inferred[col] = "Boolean"
                    continue
            except:
                pass

            # 2. Int64
            if check_cast(pl.Int64):
                inferred[col] = "Int64"
                continue

            # 3. Float64
            if check_cast(pl.Float64):
                inferred[col] = "Float64"
                continue

            # 4. Date (ISO)
            if check_cast(pl.Date):
                inferred[col] = "Date"
                continue

            # 5. Datetime (ISO)
            if check_cast(pl.Datetime):
                inferred[col] = "Datetime"
                continue

        return inferred
