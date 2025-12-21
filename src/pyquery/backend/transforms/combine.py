import polars as pl
from typing import Dict, Any, Optional
from pyquery.core.models import TransformContext
from pyquery.core.params import JoinDatasetParams, AggregateParams, WindowFuncParams, ReshapeParams

# Pure Backend Transform Logic
# All state/datasets are passed via context


def join_dataset_func(lf: pl.LazyFrame, params: JoinDatasetParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not (params.alias and params.left_on and params.right_on):
        return lf

    # Context usage
    datasets = context.datasets if context else {}
    if params.alias in datasets:
        other_lf = datasets[params.alias]
        return lf.join(other_lf, left_on=params.left_on, right_on=params.right_on, how=params.how)

    return lf


def aggregate_func(lf: pl.LazyFrame, params: AggregateParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.keys or not params.aggs:
        return lf

    agg_exprs = []
    for agg in params.aggs:
        col_expr = pl.col(agg.col)
        op = agg.op
        if op == "sum":
            agg_exprs.append(col_expr.sum())
        elif op == "mean":
            agg_exprs.append(col_expr.mean())
        elif op == "min":
            agg_exprs.append(col_expr.min())
        elif op == "max":
            agg_exprs.append(col_expr.max())
        elif op == "count":
            agg_exprs.append(col_expr.count())
        elif op == "n_unique":
            agg_exprs.append(col_expr.n_unique())
        elif op == "first":
            agg_exprs.append(col_expr.first())
        elif op == "last":
            agg_exprs.append(col_expr.last())
        elif op == "median":
            agg_exprs.append(col_expr.median())

    return lf.group_by(params.keys).agg(agg_exprs)


def window_func_func(lf: pl.LazyFrame, params: WindowFuncParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not (params.target and params.name and params.op):
        return lf

    expr = pl.col(params.target)
    op = params.op
    if op == "sum":
        expr = expr.sum()
    elif op == "mean":
        expr = expr.mean()
    elif op == "min":
        expr = expr.min()
    elif op == "max":
        expr = expr.max()
    elif op == "count":
        expr = expr.count()
    elif op == "cum_sum":
        expr = expr.cum_sum()
    elif op == "rank_dense":
        expr = expr.rank("dense")
    elif op == "rank_ordinal":
        expr = expr.rank("ordinal")
    elif op == "lag":
        expr = expr.shift(1)
    elif op == "lead":
        expr = expr.shift(-1)

    if params.over:
        expr = expr.over(params.over)

    if params.sort:
        lf = lf.sort(params.sort)

    return lf.with_columns(expr.alias(params.name))


def reshape_func(lf: pl.LazyFrame, params: ReshapeParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.mode == "Unpivot":
        if params.id_vars and params.val_vars:
            return lf.melt(id_vars=params.id_vars, value_vars=params.val_vars)

    else:  # Pivot
        if params.idx and params.col and params.val:
            from typing import cast, Any
            agg_func = params.agg or "first"
            # Explicitly cast to Any to bypass strict type checking for Polars pivot
            return lf.collect().pivot(
                index=params.idx, on=params.col, values=params.val, aggregate_function=cast(
                    Any, agg_func)
            ).lazy()

    return lf
