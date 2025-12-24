import polars as pl
from typing import Optional
from pyquery_polars.core.models import TransformContext
from pyquery_polars.core.params import (
    MathSciParams, ClipParams, DateOffsetParams, DateDiffParams
)


def math_sci_func(lf: pl.LazyFrame, params: MathSciParams, context=None) -> pl.LazyFrame:
    col_expr = pl.col(params.col)

    if params.op == "log":
        # Base e
        res = col_expr.log()
    elif params.op == "log10":
        res = col_expr.log10()
    elif params.op == "exp":
        res = col_expr.exp()
    elif params.op == "sqrt":
        res = col_expr.sqrt()
    elif params.op == "cbrt":
        res = col_expr.cbrt()
    elif params.op == "pow":
        res = col_expr.pow(params.arg)
    elif params.op == "mod":
        res = col_expr % params.arg
    # Trig
    elif params.op == "sin":
        res = col_expr.sin()
    elif params.op == "cos":
        res = col_expr.cos()
    elif params.op == "tan":
        res = col_expr.tan()
    elif params.op == "arcsin":
        res = col_expr.arcsin()
    elif params.op == "arccos":
        res = col_expr.arccos()
    elif params.op == "arctan":
        res = col_expr.arctan()
    elif params.op == "degrees":
        res = col_expr.degrees()
    elif params.op == "radians":
        res = col_expr.radians()
    elif params.op == "sign":
        res = col_expr.sign()
    else:
        res = col_expr

    return lf.with_columns(res)


def clip_func(lf: pl.LazyFrame, params: ClipParams, context=None) -> pl.LazyFrame:
    # Polars clip(min, max)
    # clip supports expressions or literals
    return lf.with_columns(
        pl.col(params.col).clip(
            lower_bound=params.min_val, upper_bound=params.max_val)
    )


def date_offset_func(lf: pl.LazyFrame, params: DateOffsetParams, context=None) -> pl.LazyFrame:
    # params.offset is string like "1d", "2h".

    offset = params.offset
    if params.action == "sub":
        if not offset.startswith("-"):
            offset = f"-{offset}"

    return lf.with_columns(
        pl.col(params.col).dt.offset_by(offset)
    )


def date_diff_func(lf: pl.LazyFrame, params: DateDiffParams, context=None) -> pl.LazyFrame:
    # diff between colA and colB
    diff = pl.col(params.end_col) - pl.col(params.start_col)

    new_name = params.alias if params.alias else f"diff_{params.start_col}_{params.end_col}"

    # Duration conversion
    if params.unit == "days":
        res = diff.dt.total_days()
    elif params.unit == "hours":
        res = diff.dt.total_hours()
    elif params.unit == "minutes":
        res = diff.dt.total_minutes()
    elif params.unit == "seconds":
        res = diff.dt.total_seconds()
    elif params.unit == "milliseconds":
        res = diff.dt.total_milliseconds()
    else:
        res = diff  # Keep as Duration type

    return lf.with_columns(res.alias(new_name))
