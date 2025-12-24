import polars as pl
from typing import List, Union, Dict, Optional, Any, Tuple
from pydantic import BaseModel

from pyquery_polars.core.models import RecipeStep, TransformContext
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
    def bound_apply_recipe(lf: pl.LazyFrame, recipe: List[Any], project_recipes: Optional[Dict] = None) -> pl.LazyFrame:
        return apply_recipe(lf, recipe, datasets, project_recipes)

    context = TransformContext(
        datasets=datasets,
        project_recipes=project_recipes,
        apply_recipe_callback=bound_apply_recipe
    )

    return definition.backend_func(lf, validated_params, context)


def apply_recipe(lf: pl.LazyFrame, recipe: List[Union[dict, RecipeStep]],
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


def get_preview(base_lf: pl.LazyFrame, recipe: List[Union[dict, RecipeStep]],
                datasets: Dict[str, pl.LazyFrame],
                project_recipes: Optional[Dict[str, List[RecipeStep]]] = None) -> pl.DataFrame:

    # MIDDLE GROUND STRATEGY: 1k Input Limit
    PREVIEW_INPUT_LIMIT = 1000

    sample_lf = base_lf.limit(PREVIEW_INPUT_LIMIT)

    transformed_lf = apply_recipe(sample_lf, recipe, datasets, project_recipes)

    return transformed_lf.collect()


def get_profile(base_lf: pl.LazyFrame, recipe: List[Union[dict, RecipeStep]],
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
