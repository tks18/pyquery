import polars as pl
from typing import Dict, Any, List, Optional
from pyquery_polars.core.models import TransformContext
from pyquery_polars.core.params import (
    SelectColsParams, DropColsParams, RenameColParams, KeepColsParams, AddColParams, CleanCastParams,
    PromoteHeaderParams, SplitColParams, CombineColsParams, AddRowNumberParams, ExplodeParams, CoalesceParams, OneHotEncodeParams
)
from pyquery_polars.backend.utils.parsing import (
    robust_numeric_cleaner, robust_date_parser, robust_datetime_parser,
    robust_time_parser, robust_excel_date_parser, robust_excel_datetime_parser,
    robust_excel_time_parser
)


def select_cols_func(lf: pl.LazyFrame, params: SelectColsParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.cols:
        return lf.select(params.cols)
    return lf


def drop_cols_func(lf: pl.LazyFrame, params: DropColsParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.cols:
        return lf.drop(params.cols)
    return lf


def rename_col_func(lf: pl.LazyFrame, params: RenameColParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.old and params.new:
        return lf.rename({params.old: params.new})
    return lf


def keep_cols_func(lf: pl.LazyFrame, params: KeepColsParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.cols:
        return lf.select(params.cols)
    return lf


def add_col_func(lf: pl.LazyFrame, params: AddColParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if params.name and params.expr:
        # Allow errors to propagate so UI shows them
        computed_expr = eval(params.expr)
        return lf.with_columns(computed_expr.alias(params.name))
    return lf


def clean_cast_func(lf: pl.LazyFrame, params: CleanCastParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.changes:
        return lf

    exprs = []
    for change in params.changes:
        t_col = change.col
        act = change.action

        if act == "To String":
            exprs.append(pl.col(t_col).cast(pl.Utf8))
        elif act == "To Int":
            exprs.append(pl.col(t_col).cast(pl.Int64, strict=False))
        elif act == "To Float":
            exprs.append(pl.col(t_col).cast(pl.Float64, strict=False))
        elif act == "To Boolean":
            exprs.append(pl.col(t_col).cast(pl.Boolean, strict=False))
        elif act == "To Date":
            exprs.append(pl.col(t_col).cast(pl.Date, strict=False))
        elif act == "To Datetime":
            exprs.append(pl.col(t_col).cast(pl.Datetime, strict=False))
        elif act == "To Time":
            exprs.append(pl.col(t_col).cast(pl.Time, strict=False))
        elif act == "To Date (Format)":
            exprs.append(pl.col(t_col).str.to_date(format=change.fmt, strict=False))
        elif act == "To Datetime (Format)":
            exprs.append(pl.col(t_col).str.to_datetime(format=change.fmt, strict=False))
        elif act == "To Time (Format)":
            exprs.append(pl.col(t_col).str.to_time(format=change.fmt, strict=False))
        elif act == "To Duration":
            exprs.append(pl.col(t_col).cast(pl.Duration, strict=False))
        elif act == "To Int (Robust)":
            exprs.append(robust_numeric_cleaner(t_col, pl.Int64))
        elif act == "To Float (Robust)":
            exprs.append(robust_numeric_cleaner(t_col, pl.Float64))
        elif act == "To Date (Robust)":
            exprs.append(robust_date_parser(t_col))
        elif act == "To Datetime (Robust)":
            exprs.append(robust_datetime_parser(t_col))
        elif act == "To Time (Robust)":
            exprs.append(robust_time_parser(t_col))
        elif act == "Trim Whitespace":
            exprs.append(pl.col(t_col).str.strip_chars())
        elif act == "Standardize NULLs":
            null_vals = ["NA", "na", "nan", "NULL", "null", ""]
            exprs.append(pl.when(pl.col(t_col).is_in(null_vals)).then(
                None).otherwise(pl.col(t_col)).alias(t_col))
        elif act == "Fix Excel Serial Date":
            exprs.append(robust_excel_date_parser(t_col))
        elif act == "Fix Excel Serial Datetime":
            exprs.append(robust_excel_datetime_parser(t_col))
        elif act == "Fix Excel Serial Time":
            exprs.append(robust_excel_time_parser(t_col))

    if exprs:
        return lf.with_columns(exprs)
    return lf


def promote_header_func(lf: pl.LazyFrame, params: "PromoteHeaderParams", context: Optional[TransformContext] = None) -> pl.LazyFrame:
    # 1. Peek at first row (LIMIT 1) eagerly
    try:
        # We need to collect 1 row to get values
        first_row_df = lf.limit(1).collect()
        if first_row_df.height == 0:
            return lf
        
        # 2. Get new column names from the first row values
        # Assume all values are strings or convert them
        new_cols = []
        for val in first_row_df.row(0):
            new_cols.append(str(val) if val is not None else "col_null")
            
        # 3. Rename columns
        # Current columns
        old_cols = lf.collect_schema().names()
        
        # Mapping
        rename_map = {}
        for old, new in zip(old_cols, new_cols):
            rename_map[old] = new
            
        # 4. Apply rename and Remove first row
        # using slice(1, None) to skip first row
        return lf.rename(rename_map).slice(1)
        
    except Exception:
        return lf


def split_col_func(lf: pl.LazyFrame, params: "SplitColParams", context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.col:
        return lf
    
    try:
        tmp_alias = f"__split_{params.col}"
        # using split_exact(pat, n)
        return lf.with_columns(
            pl.col(params.col).str.split_exact(params.pat, params.n)
            .alias(tmp_alias)
        ).unnest(tmp_alias)
    except Exception:
        return lf


def combine_cols_func(lf: pl.LazyFrame, params: "CombineColsParams", context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.cols or not params.new_name:
        return lf
        
    return lf.with_columns(
        pl.concat_str(params.cols, separator=params.separator).alias(params.new_name)
    )


def add_row_number_func(lf: pl.LazyFrame, params: "AddRowNumberParams", context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.name:
        return lf
    return lf.with_row_index(params.name)


def explode_func(lf: pl.LazyFrame, params: ExplodeParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.cols:
        return lf
    return lf.explode(params.cols)


def coalesce_func(lf: pl.LazyFrame, params: CoalesceParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    if not params.cols or not params.new_name:
        return lf
    return lf.with_columns(
        pl.coalesce(params.cols).alias(params.new_name)
    )


def one_hot_encode_func(lf: pl.LazyFrame, params: OneHotEncodeParams, context=None) -> pl.LazyFrame:
    col_name = params.col
    try:
        # Collect distinct values
        uniques = lf.select(col_name).unique().collect().get_column(col_name).to_list()
        uniques = [u for u in uniques if u is not None] # filter nulls
        uniques.sort()
    except Exception:
        # Fallback or error if too distinct
        return lf
        
    prefix = params.prefix if params.prefix else col_name
    sep = params.separator
    
    exprs = []
    for val in uniques:
        safe_val = str(val)
        out_col = f"{prefix}{sep}{safe_val}"
        exprs.append(
            pl.when(pl.col(col_name) == val).then(pl.lit(1)).otherwise(pl.lit(0)).alias(out_col)
        )
        
    if not exprs:
        return lf
        
    return lf.with_columns(exprs)
