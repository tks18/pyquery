import polars as pl
from src.backend.utils.parsing import (
    robust_numeric_cleaner, robust_date_parser, robust_datetime_parser, 
    robust_time_parser, robust_excel_date_parser, robust_excel_datetime_parser, 
    robust_excel_time_parser
)

def select_cols_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    cols = params.get('cols', [])
    if cols:
        return lf.select(cols)
    return lf

def drop_cols_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    cols = params.get('cols', [])
    if cols:
        return lf.drop(cols)
    return lf

def rename_col_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    old = params.get('old')
    new = params.get('new')
    if old and new:
        return lf.rename({old: new})
    return lf

def keep_cols_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    cols = params.get('cols', [])
    if cols:
        return lf.select(cols)
    return lf

def add_col_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    name = params.get('name')
    expr_str = params.get('expr')
    if name and expr_str:
        try:
            computed_expr = eval(expr_str)
            return lf.with_columns(computed_expr.alias(name))
        except Exception:
            pass
    return lf

def clean_cast_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    changes = params.get('changes', [])
    if not changes:
        return lf
    
    exprs = []
    for change in changes:
        t_col = change['col']
        act = change['action']
        
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
