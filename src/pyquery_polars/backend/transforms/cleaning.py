import polars as pl
from typing import Optional, Any
from functools import reduce
import operator
from pyquery_polars.core.models import TransformContext
from pyquery_polars.core.params import (
    FillNullsParams, RegexExtractParams, StringCaseParams, StringReplaceParams,
    DropNullsParams, TextSliceParams, TextLengthParams, StringPadParams,
    TextExtractDelimParams, RegexToolParams,
    NormalizeSpacesParams, SmartExtractParams
)
import re


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


def string_pad_func(lf: pl.LazyFrame, params: StringPadParams, context=None) -> pl.LazyFrame:
    col = pl.col(params.col)
    fill = params.fill_char or " "
    ln = params.length
    
    if params.side == "left":
        expr = col.str.pad_start(ln, fill)
    elif params.side == "right":
        expr = col.str.pad_end(ln, fill)
    else:  # Center
        len_expr = col.str.len_chars()
        pad_needed = pl.lit(ln) - len_expr
        pad_left = (pad_needed / 2).floor().cast(pl.Int64)
        pad_right = (pad_needed - pad_left).cast(pl.Int64)
        expr = col.str.pad_start(ln, fill)
        
    new_name = params.alias if params.alias else params.col
    return lf.with_columns(expr.alias(new_name))


def text_extract_delim_func(lf: pl.LazyFrame, params: TextExtractDelimParams, context=None) -> pl.LazyFrame:
    col_name = params.col
    start = params.start_delim
    end = params.end_delim
    
    # Construct Regex
    # We use re.escape to handle special characters in delimiters safely
    # Pattern logic:
    # 1. Start & End: (?<=start).*?(?=end)  (Lookbehind, Non-greedy match, Lookahead)
    # 2. Start only: (?<=start).*           (Lookbehind, match rest)
    # 3. End only: ^.*?(?=end)              (Start of string, non-greedy, lookahead)
    
    pattern = ""
    if start and end:
        pattern = f"(?<={re.escape(start)}).*?(?={re.escape(end)})"
    elif start:
        pattern = f"(?<={re.escape(start)}).*"
    elif end:
        pattern = f"^.*?(?={re.escape(end)})"
    else:
        # No delimiters? Return original? Or error?
        # Let's return as is but maybe warn log.
        return lf
        
    new_name = params.alias if params.alias else f"{col_name}_extract"
    return lf.with_columns(
        pl.col(col_name).str.extract(pattern, 1).alias(new_name)
    )


def regex_tool_func(lf: pl.LazyFrame, params: RegexToolParams, context=None) -> pl.LazyFrame:
    col = pl.col(params.col)
    pat = params.pattern
    action = params.action
    val = params.replacement
    
    alias = params.alias if params.alias else f"{params.col}_{action}"
    
    expr = col
    if action == "replace_all":
        expr = col.str.replace_all(pat, val, literal=False)
    elif action == "replace_one":
        expr = col.str.replace(pat, val, literal=False)
    elif action == "extract":
        # Group 1 extraction
        expr = col.str.extract(pat, 1)
    elif action == "count":
        expr = col.str.count_matches(pat)
    elif action == "contains":
        expr = col.str.contains(pat)
        
    return lf.with_columns(expr.alias(alias))


def normalize_spaces_func(lf: pl.LazyFrame, params: NormalizeSpacesParams, context=None) -> pl.LazyFrame:
    col = pl.col(params.col)
    expr = col.str.replace_all(r"\s+", " ").str.strip_chars()
    
    alias = params.alias if params.alias else params.col
    return lf.with_columns(expr.alias(alias))


def smart_extract_func(lf: pl.LazyFrame, params: SmartExtractParams, context=None) -> pl.LazyFrame:
    col = pl.col(params.col)
    ptype = params.type
    
    pattern = ""
    if ptype == "email_user":
        pattern = r"^([^@]+)@"
    elif ptype == "email_domain":
        pattern = r"@([\w\.-]+)"
    elif ptype == "url_domain":
        pattern = r"://([\w\.-]+)"
    elif ptype == "url_path":
        pattern = r"://[\w\.-]+(/.*)"
    elif ptype == "ipv4":
        pattern = r"(\b(?:\d{1,3}\.){3}\d{1,3}\b)"
        
    alias = params.alias if params.alias else f"{params.col}_{ptype}"
    return lf.with_columns(
        col.str.extract(pattern, 1).alias(alias)
    )
