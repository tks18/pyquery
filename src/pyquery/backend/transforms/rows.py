import polars as pl
from typing import Dict, Any, List, Optional
from pyquery.core.models import TransformContext
from pyquery.core.params import FilterRowsParams, SortRowsParams, DeduplicateParams, SampleParams
from pyquery.backend.utils.helpers import build_filter_expr


def filter_rows_func(lf: pl.LazyFrame, params: FilterRowsParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.conditions:
        return lf

    try:
        schema = lf.collect_schema()
    except Exception:
        return lf

    exprs = [build_filter_expr(c.col, c.op, c.val, schema)
             for c in params.conditions]
    exprs = [e for e in exprs if e is not None]

    if not exprs:
        return lf

    if params.logic == "AND":
        final_expr = exprs[0]
        for e in exprs[1:]:
            final_expr = final_expr & e
    else:
        final_expr = exprs[0]
        for e in exprs[1:]:
            final_expr = final_expr | e

    return lf.filter(final_expr)


def sort_rows_func(lf: pl.LazyFrame, params: SortRowsParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.cols:
        return lf.sort(params.cols, descending=params.desc)
    return lf


def deduplicate_func(lf: pl.LazyFrame, params: DeduplicateParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.subset:
        return lf.unique(subset=params.subset)
    return lf.unique()


def sample_func(lf: pl.LazyFrame, params: SampleParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.method == "Fraction":
        try:
            return lf.collect().sample(fraction=params.val, shuffle=True).lazy()
        except Exception:
            # Fallback for lazy sample if supported or alternative
            return lf.filter(pl.int_range(0, pl.count()) < (pl.count() * params.val))
    else:
        return lf.limit(int(params.val))
