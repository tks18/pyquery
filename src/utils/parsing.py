import polars as pl

def robust_numeric_cleaner(col_name, dtype=pl.Float64):
    return (pl.col(col_name).str.strip_chars().str.replace_all(",", "").str.replace_all(r"[^\d\.\-]", "").cast(dtype, strict=False))


def robust_date_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_date(strict=False),
        c.str.to_date("%d/%m/%Y", strict=False),
        c.str.to_date("%m/%d/%Y", strict=False),
        c.str.to_date("%d-%m-%Y", strict=False),
        c.str.to_date("%Y/%m/%d", strict=False),
        c.str.to_date("%d-%b-%Y", strict=False),
    ])


def robust_datetime_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_datetime(strict=False),
        c.str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False),
        c.str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False),
        c.str.to_datetime("%m/%d/%Y %H:%M:%S", strict=False),
        c.str.to_datetime("%d-%m-%Y %H:%M:%S", strict=False),
    ])


def robust_time_parser(col_name):
    c = pl.col(col_name).str.strip_chars()
    return pl.coalesce([
        c.str.to_time(strict=False),
        c.str.to_time("%H:%M", strict=False),
        c.str.to_time("%I:%M %p", strict=False),
        c.str.to_time("%I:%M:%S %p", strict=False)
    ])


def robust_excel_date_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False))).cast(pl.Date)


def robust_excel_datetime_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False)))


def robust_excel_time_parser(col_name):
    return (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col_name).str.strip_chars().cast(pl.Float64, strict=False))).dt.time()
