import polars as pl
from typing import Type
import datetime


def robust_numeric_cleaner(col_name: str, dtype: Type[pl.DataType] = pl.Float64):
    # Remove currency symbols ($, €, £), grouping separators (,, _), and extra whitespace
    # We consciously DO NOT remove 'e' or 'E' to preserve scientific notation support.
    # Regex: [,$€£_\s] -> remove these.
    return (pl.col(col_name).str.strip_chars()
            .str.replace_all(r"[,$€£_\s]", "")
            .cast(dtype, strict=False))


def robust_date_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    # Optimization: Normalize separators (/ and .) to hyphens (-) to reduce permutation checks
    c_norm = c.str.replace_all(r"[/\.]", "-")
    
    return pl.coalesce([
        c.str.to_date(strict=False),                      # Standard ISO
        c_norm.str.to_date("%d-%m-%Y", strict=False),     # DMY (Normalized)
        c_norm.str.to_date("%m-%d-%Y", strict=False),     # MDY (Normalized)
        c.str.to_date("%d %b %Y", strict=False),          # 01 Jan 2023
        c.str.to_date("%d-%b-%Y", strict=False),          # 01-Jan-2023
    ])


def robust_datetime_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    # Normalize date separators to hyphens
    c_norm = c.str.replace_all(r"[/\.]", "-")
    
    return pl.coalesce([
        c.str.to_datetime(strict=False),
        c.str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False),
        # Normalized DMY variants
        c_norm.str.to_datetime("%d-%m-%Y %H:%M:%S", strict=False),
        c_norm.str.to_datetime("%m-%d-%Y %H:%M:%S", strict=False),
    ])


def robust_time_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_time(strict=False),
        c.str.to_time("%H:%M", strict=False),
        c.str.to_time("%H:%M:%S", strict=False),
        c.str.to_time("%I:%M %p", strict=False),
        c.str.to_time("%I:%M:%S %p", strict=False)
    ])


def robust_excel_date_parser(col_name):
    # 1899-12-30 epoch
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False))).cast(pl.Date)


def robust_excel_datetime_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False)))


def robust_excel_time_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False))).dt.time()
