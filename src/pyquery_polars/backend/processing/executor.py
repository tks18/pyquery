from typing import List, Union, Dict, Optional, Any, Tuple, Sequence
from pydantic import BaseModel

import polars as pl

from pyquery_polars.core.models import RecipeStep, TransformContext, DatasetMetadata
from pyquery_polars.core.registry import StepRegistry


def apply_step(lf: pl.LazyFrame, step: RecipeStep, datasets: Dict[str, pl.LazyFrame],
               project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
    step_type = step.type
    definition = StepRegistry.get(step_type)
    if not definition:
        raise ValueError(f"Unknown step type: {step_type}")

    try:
        if isinstance(step.params, BaseModel):
            validated_params = step.params
        else:
            validated_params = definition.params_model.model_validate(
                step.params)
    except Exception as e:
        raise ValueError(f"Parameters invalid for step {step_type}: {e}")

    # Build Context
    def bound_apply_recipe(lf: pl.LazyFrame, recipe: Sequence[Any], project_recipes: Optional[Dict] = None) -> pl.LazyFrame:
        return apply_recipe(lf, recipe, datasets, project_recipes)

    context = TransformContext(
        datasets=datasets,
        project_recipes=project_recipes,
        apply_recipe_callback=bound_apply_recipe
    )

    return definition.backend_func(lf, validated_params, context)


def apply_recipe(lf: pl.LazyFrame, recipe: Sequence[Union[dict, RecipeStep]],
                 datasets: Dict[str, pl.LazyFrame],
                 project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
    current_lf = lf

    for step in recipe:
        if isinstance(step, dict):
            if 'type' not in step:
                continue
            step_obj = RecipeStep(**step)
        else:
            step_obj = step

        current_lf = apply_step(current_lf, step_obj,
                                datasets, project_recipes)

    return current_lf


def get_profile(base_lf: pl.LazyFrame, recipe: Sequence[Union[dict, RecipeStep]],
                datasets: Dict[str, pl.LazyFrame]) -> Dict[str, Any]:

    # Sample for speed
    SAMPLE_COUNT = 10000

    sample_lf = base_lf.limit(SAMPLE_COUNT)

    lf = apply_recipe(sample_lf, recipe, datasets)

    # 1. Collect Schema/Shape (on sample for speed)
    sample_df = lf.collect()

    rows, cols = sample_df.shape

    # nulls
    null_counts = {c: sample_df[c].null_count() for c in sample_df.columns}

    # dtypes logic
    dtypes = {c: str(sample_df[c].dtype) for c in sample_df.columns}

    # summary (describe)
    summary = sample_df.describe().to_pandas()

    return {
        "sample": sample_df,
        "shape": (rows, cols),
        "nulls": null_counts,
        "dtypes": dtypes,
        "summary": summary
    }


def prepare_view(
        meta: DatasetMetadata,
        recipe: Sequence[Union[dict, RecipeStep]],
        datasets: Dict[str, pl.LazyFrame],  # Context for lookups
        project_recipes: Optional[Dict[str, List[RecipeStep]]] = None,
        mode: str = "preview",  # 'preview' or 'full'
        preview_limit: int = 1000,
        collection_limit: Optional[int] = None
) -> Optional[pl.LazyFrame]:
    """
    Centralized logic to prepare a dataset for usage (Preview, SQL, Export).
    Handles 'Process Individual' logic + 'Preview Limits'.
    """
    # 1. Input Selection & Limiting
    if mode == "preview":
        if meta.process_individual and meta.base_lfs:
            # Individual Mode + Preview -> First File Only + Limit
            base = meta.base_lfs[0].limit(preview_limit)
        elif meta.base_lf is not None:
            # Normal Mode + Preview -> Base + Limit
            base = meta.base_lf.limit(preview_limit)
        else:
            return None

        # 2. Apply Recipe (Single Object)
        return apply_recipe(base, recipe, datasets, project_recipes)

    elif mode == "full":
        if meta.process_individual and meta.base_lfs and len(meta.base_lfs) > 1:
            # Individual Mode + Full -> Apply to ALL files + Concat
            processed_lfs = []
            for f in meta.base_lfs:
                try:
                    # Apply collection limit BEFORE recipe if requested
                    if collection_limit:
                        f = f.limit(collection_limit)

                    # Apply recipe to each file with full context
                    processed = apply_recipe(
                        f, recipe, datasets, project_recipes)
                    processed_lfs.append(processed)
                except Exception as e:
                    print(
                        f"Warning: skipped file in individual processing: {e}")

            if not processed_lfs:
                return None

            return pl.concat(processed_lfs, how="diagonal")

        elif meta.base_lf is not None:
            # Normal Mode + Full -> Apply to Base
            base = meta.base_lf
            if collection_limit:
                base = base.limit(collection_limit)

            return apply_recipe(base, recipe, datasets, project_recipes)

    return None


def execute_sql(query: str, datasets: Dict[str, pl.LazyFrame],
                project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.LazyFrame:
    """
    Executes a SQL query against reduced/prepared datasets.

    Args:
        query: SQL query string
        datasets: Dictionary of {name: LazyFrame} to register in SQL context
        project_recipes: (Optional) Unused in new logic if datasets are pre-processed, 
                         kept for signature compatibility or future use.
    """
    ctx = pl.SQLContext()

    for name, lf in datasets.items():
        # If recipes were NOT pre-applied (legacy path), we might apply them here.
        # But 'core.py' now guarantees they are pre-applied.
        # We'll just register the LF.
        ctx.register(name, lf)

    return ctx.execute(query, eager=False)
