import polars as pl
from typing import Optional, Any
from pyquery_polars.core.models import TransformContext
from pyquery_polars.core.params import (
    TimeBinParams, RollingAggParams, NumericBinParams, MathOpParams, DateExtractParams,
    CumulativeParams, RankParams, DiffParams, ZScoreParams, SkewKurtParams
)


def time_bin_func(lf: pl.LazyFrame, params: TimeBinParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    return lf.with_columns(
        pl.col(params.col).dt.truncate(params.interval).alias(
            f"{params.col}_{params.interval}")
    )


def rolling_agg_func(lf: pl.LazyFrame, params: RollingAggParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    # window_size, op, center
    c = pl.col(params.target)
    w = params.window_size

    expr = None
    if params.op == "mean":
        expr = c.rolling_mean(w, center=params.center)
    elif params.op == "sum":
        expr = c.rolling_sum(w, center=params.center)
    elif params.op == "min":
        expr = c.rolling_min(w, center=params.center)
    elif params.op == "max":
        expr = c.rolling_max(w, center=params.center)
    elif params.op == "std":
        expr = c.rolling_std(w, center=params.center)

    if expr is not None:
        return lf.with_columns(expr.alias(f"{params.target}_rolling_{params.op}_{w}"))
    return lf


def numeric_bin_func(lf: pl.LazyFrame, params: NumericBinParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:

    return lf.with_columns(
        pl.col(params.col).qcut(params.bins, labels=params.labels).alias(
            f"{params.col}_binned")
    )


def math_op_func(lf: pl.LazyFrame, params: MathOpParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    c = pl.col(params.col)
    expr = c
    if params.op == "round":
        expr = c.round(params.precision)
    elif params.op == "abs":
        expr = c.abs()
    elif params.op == "ceil":
        expr = c.ceil()
    elif params.op == "floor":
        expr = c.floor()
    elif params.op == "sqrt":
        expr = c.sqrt()

    alias = params.alias or f"{params.col}_{params.op}"
    return lf.with_columns(expr.alias(alias))


def date_extract_func(lf: pl.LazyFrame, params: DateExtractParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    c = pl.col(params.col)
    expr = c
    p = params.part
    if p == "year":
        expr = c.dt.year()
    elif p == "month":
        expr = c.dt.month()
    elif p == "day":
        expr = c.dt.day()
    elif p == "hour":
        expr = c.dt.hour()
    elif p == "weekday":
        expr = c.dt.weekday()
    elif p == "minute":
        expr = c.dt.minute()
    elif p == "second":
        expr = c.dt.second()

    alias = params.alias or f"{params.col}_{p}"
    return lf.with_columns(expr.alias(alias))


def cumulative_func(lf: pl.LazyFrame, params: CumulativeParams, context=None) -> pl.LazyFrame:
    op_map = {
        "cumsum": "cum_sum", "cummin": "cum_min", "cummax": "cum_max", "cumprod": "cum_prod"
    }
    method = op_map.get(params.op, "cum_sum")
    new_name = params.alias if params.alias else f"{params.col}_{params.op}"

    # Polars cum_sum(reverse=False)
    expr = getattr(pl.col(params.col), method)(reverse=params.reverse)
    return lf.with_columns(expr.alias(new_name))


def rank_func(lf: pl.LazyFrame, params: RankParams, context=None) -> pl.LazyFrame:
    new_name = params.alias if params.alias else f"{params.col}_rank"
    return lf.with_columns(
        pl.col(params.col).rank(method=params.method,
                                descending=params.descending).alias(new_name)
    )


def diff_func(lf: pl.LazyFrame, params: DiffParams, context=None) -> pl.LazyFrame:
    new_name = params.alias if params.alias else f"{params.col}_{params.method}"
    if params.method == "pct_change":
        return lf.with_columns(pl.col(params.col).pct_change(n=params.n).alias(new_name))
    else:
        return lf.with_columns(pl.col(params.col).diff(n=params.n).alias(new_name))


def z_score_func(lf: pl.LazyFrame, params: ZScoreParams, context=None) -> pl.LazyFrame:
    # (x - mean) / std
    # Supports 'over' if params.by is set

    col = pl.col(params.col)

    if params.by:
        mean_expr = col.mean().over(params.by)
        std_expr = col.std().over(params.by)
    else:
        mean_expr = col.mean()
        std_expr = col.std()

    expr = (col - mean_expr) / std_expr

    new_name = params.alias if params.alias else f"{params.col}_zscore"
    return lf.with_columns(expr.alias(new_name))


def skew_kurt_func(lf: pl.LazyFrame, params: SkewKurtParams, context=None) -> pl.LazyFrame:

    col = pl.col(params.col)
    if params.measure == "skew":
        expr = col.skew()
    else:
        expr = col.kurtosis()

    new_name = params.alias if params.alias else f"{params.col}_{params.measure}"
    return lf.with_columns(expr.alias(new_name))
