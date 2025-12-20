import polars as pl
from typing import Optional, Any
from functools import reduce
import operator
from src.core.models import TransformContext
from src.core.params import (
    FillNullsParams, RegexExtractParams, StringCaseParams, StringReplaceParams,
    DropNullsParams, TextSliceParams, TextLengthParams
)


def fill_nulls_func(lf: pl.LazyFrame, params: FillNullsParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    cols = params.cols
    if not cols:
        return lf

    s = params.strategy

    # logic map
    if s == "forward":
        return lf.with_columns([pl.col(c).forward_fill() for c in cols])
    elif s == "backward":
        return lf.with_columns([pl.col(c).backward_fill() for c in cols])
    elif s == "zero":
        return lf.with_columns([pl.col(c).fill_null(0) for c in cols])
    elif s == "literal":
        val = params.literal_val if params.literal_val is not None else 0
        return lf.with_columns([pl.col(c).fill_null(val) for c in cols])
    elif s == "min":
        return lf.with_columns([pl.col(c).fill_null(pl.col(c).min()) for c in cols])
    elif s == "max":
        return lf.with_columns([pl.col(c).fill_null(pl.col(c).max()) for c in cols])
    elif s == "mean":
        return lf.with_columns([pl.col(c).fill_null(pl.col(c).mean()) for c in cols])
    elif s == "median":
        return lf.with_columns([pl.col(c).fill_null(pl.col(c).median()) for c in cols])

    return lf


def regex_extract_func(lf: pl.LazyFrame, params: RegexExtractParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    # default group index 1
    return lf.with_columns(
        pl.col(params.col).str.extract(params.pattern, 1).alias(params.alias)
    )


def string_case_func(lf: pl.LazyFrame, params: StringCaseParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    c = pl.col(params.col)
    expr = c
    if params.case == "upper":
        expr = c.str.to_uppercase()
    elif params.case == "lower":
        expr = c.str.to_lowercase()
    elif params.case == "title":
        expr = c.str.to_titlecase()
    elif params.case == "trim":
        expr = c.str.strip_chars()

    alias = params.alias or params.col
    return lf.with_columns(expr.alias(alias))


def string_replace_func(lf: pl.LazyFrame, params: StringReplaceParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    alias = params.alias or params.col
    return lf.with_columns(
        pl.col(params.col).str.replace_all(
            params.pat, params.val, literal=True).alias(alias)
    )


def drop_nulls_func(lf: pl.LazyFrame, params: DropNullsParams, context=None) -> pl.LazyFrame:
    # If no cols specified, use all
    subset = params.cols if params.cols else None

    if params.how == "any":
        return lf.drop_nulls(subset=subset)
    else:
        # ALL: Drop row only if ALL selected columns are null
        # Filter where NOT (c1.is_null & c2.is_null ...)
        if not subset:
            cols = lf.collect_schema().names()
        else:
            cols = subset

        exprs = [pl.col(c).is_null() for c in cols]
        all_null = reduce(operator.and_, exprs)
        return lf.filter(~all_null)


def text_slice_func(lf: pl.LazyFrame, params: TextSliceParams, context=None) -> pl.LazyFrame:
    new_name = params.alias if params.alias else f"{params.col}_slice"
    # Polars str.slice(offset, length)
    return lf.with_columns(
        pl.col(params.col).str.slice(
            params.start, params.length).alias(new_name)
    )


def text_length_func(lf: pl.LazyFrame, params: TextLengthParams, context=None) -> pl.LazyFrame:
    new_name = params.alias if params.alias else f"{params.col}_len"
    # str.len_chars() for character length
    return lf.with_columns(
        pl.col(params.col).str.len_chars().alias(new_name)
    )
