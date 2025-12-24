import polars as pl
from typing import Type
import datetime


def robust_numeric_cleaner(col_name: str, dtype: Type[pl.DataType] = pl.Float64):
    # Remove currency symbols ($, €, £), grouping separators (,, _), and extra whitespace
    # Regex: [,$€£_\s] -> remove these.
    return (pl.col(col_name).str.strip_chars()
            .str.replace_all(r"[,$€£_\s]", "")
            .cast(dtype, strict=False))


def robust_date_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_date(strict=False),                      # ISO (YYYY-MM-DD)
        c.str.to_date("%d/%m/%Y", strict=False),          # DMY (/)
        c.str.to_date("%m/%d/%Y", strict=False),          # MDY (/)
        c.str.to_date("%d-%m-%Y", strict=False),          # DMY (-)
        c.str.to_date("%m-%d-%Y", strict=False),          # MDY (-)
    ])


def robust_datetime_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    # OPTIMIZATION: Top 5 Formats
    return pl.coalesce([
        c.str.to_datetime(strict=False),                           # ISO
        c.str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False),    # DMY /
        c.str.to_datetime("%m/%d/%Y %H:%M:%S", strict=False),    # MDY /
        c.str.to_datetime("%d-%m-%Y %H:%M:%S", strict=False),    # DMY -
        c.str.to_datetime("%m-%d-%Y %H:%M:%S", strict=False),    # MDY -
    ])


def robust_time_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    # OPTIMIZATION: Top 3 Formats
    return pl.coalesce([
        c.str.to_time(strict=False),
        c.str.to_time("%H:%M", strict=False),
        c.str.to_time("%H:%M:%S", strict=False),
    ])


def robust_excel_date_parser(col_name):
    # 1899-12-30 epoch
    # Hybrid Strategy:
    # 1. Fast Path: Direct cast to Float64 (Properties: Fast, handles Int/Float/CleanStr, Returns Null on Fail)
    # 2. Robust Path: Cast to String -> Strip -> Float64 (Properties: Slower, handles " 123 ", Mixed Types)
    days_expr = pl.coalesce([
        pl.col(col_name).cast(pl.Float64, strict=False),
        pl.col(col_name).cast(pl.String).str.strip_chars().cast(
            pl.Float64, strict=False)
    ])
    return (pl.datetime(1899, 12, 30) + pl.duration(days=days_expr)).cast(pl.Date)


def robust_excel_datetime_parser(col_name):
    days_expr = pl.coalesce([
        pl.col(col_name).cast(pl.Float64, strict=False),
        pl.col(col_name).cast(pl.String).str.strip_chars().cast(
            pl.Float64, strict=False)
    ])
    return (pl.datetime(1899, 12, 30) + pl.duration(days=days_expr))


def robust_excel_time_parser(col_name):
    days_expr = pl.coalesce([
        pl.col(col_name).cast(pl.Float64, strict=False),
        pl.col(col_name).cast(pl.String).str.strip_chars().cast(
            pl.Float64, strict=False)
    ])
    return (pl.datetime(1899, 12, 30) + pl.duration(days=days_expr)).dt.time()
