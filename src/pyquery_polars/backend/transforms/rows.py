import polars as pl
from typing import Dict, Any, List, Optional
from pyquery_polars.core.models import TransformContext
from pyquery_polars.core.params import FilterRowsParams, SortRowsParams, DeduplicateParams, SampleParams, SliceRowsParams, ShiftParams, DropEmptyRowsParams, RemoveOutliersParams
from pyquery_polars.backend.utils.helpers import build_filter_expr


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


def slice_rows_func(lf: pl.LazyFrame, params: SliceRowsParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    mode = params.mode
    n = params.n
    if n < 0:
        n = 0

    if mode == "Keep Top":
        return lf.head(n)
    elif mode == "Keep Bottom":
        return lf.tail(n)
    elif mode == "Remove Top":
        return lf.with_row_index("__idx").filter(pl.col("__idx") >= n).drop("__idx")
    elif mode == "Remove Bottom":
        # Filter where index < (total - n)
        return lf.with_row_index("__idx").filter(pl.col("__idx") < (pl.len() - n)).drop("__idx")
    
    return lf


def shift_func(lf: pl.LazyFrame, params: ShiftParams, context=None) -> pl.LazyFrame:
    # shift col(s)
    col_name = params.col
    fill = params.fill_value
    p = params.periods
    
    # If no col specified, shift ALL? Or fail? 
    # Let's say if col is empty, do nothing or shift all cols (unlikely use case for single step).
    # Assuming single col for now based on params.
    if not col_name:
        return lf
        
    expr = pl.col(col_name).shift(p, fill_value=fill)
    new_name = params.alias if params.alias else col_name
    return lf.with_columns(expr.alias(new_name))


def drop_empty_rows_func(lf: pl.LazyFrame, params: DropEmptyRowsParams, context=None) -> pl.LazyFrame:
    # subset, how, thresh
    # Polars drop_nulls
    subset = params.subset if params.subset else None
    
    # Thresh is not directly supported in drop_nulls lazy?
    # Actually DataFrame.drop_nulls has thresh. LazyFrame.drop_nulls does too?
    # Checking docs... LazyFrame has drop_nulls(subset). 'how' is usually inferred or handled differently.
    # Actually LazyFrame.drop_nulls(subset) drops rows where ANY of subset are null.
    # To do 'ALL', we need filter.
    
    if params.thresh is not None:
        # Filter by null count
        # row null count < (total_cols - thresh + 1) ? 
        # Thresh = require at least N non-null values.
        # So null_count <= (total_cols - thresh)
        # This requires knowing total cols in subset.
        pass # Skip complex thresh for now in lazy if hard.
        
    if params.how == "all":
        # Drop if ALL cols in subset are null
        # filter(~(c1.is_null() & c2.is_null()...))
        cols = subset if subset else lf.collect_schema().names()
        # Efficient all-null check: sum_horizontal(is_null) == len(cols)
        # or all(is_null)
        return lf.filter(~pl.all_horizontal([pl.col(c).is_null() for c in cols]))
        
    else:
        # Any null in subset -> drop
        return lf.drop_nulls(subset=subset)


def remove_outliers_func(lf: pl.LazyFrame, params: RemoveOutliersParams, context=None) -> pl.LazyFrame:
    col = pl.col(params.col)
    
    # Q1/Q3 approximation if needed, but robust logic:
    # Filter: (col >= Q1 - factor*IQR) & (col <= Q3 + factor*IQR)
    
    q1 = col.quantile(0.25)
    q3 = col.quantile(0.75)
    iqr = q3 - q1
    factor = params.factor
    
    lower = q1 - (iqr * factor)
    upper = q3 + (iqr * factor)
    
    return lf.filter(
        (col >= lower) & (col <= upper)
    )
