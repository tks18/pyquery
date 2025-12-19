import polars as pl

def build_filter_expr(col_name, op, val_str, schema):
    if op == "is_null":
        return pl.col(col_name).is_null()
    if op == "is_not_null":
        return pl.col(col_name).is_not_null()
    if not val_str:
        return None
    dtype = schema.get(col_name, pl.Utf8)
    try:
        rhs = None
        if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]:
            clean_val = val_str.strip()
            rhs = pl.lit(int(float(clean_val))
                         ) if "." in clean_val else pl.lit(int(clean_val))
        elif dtype in [pl.Float32, pl.Float64]:
            rhs = pl.lit(float(val_str.strip()))
        elif dtype == pl.Date:
            rhs = pl.lit(val_str.strip()).str.to_date()
        elif dtype == pl.Datetime:
            rhs = pl.lit(val_str.strip()).str.to_datetime()
        elif dtype == pl.Time:
            rhs = pl.lit(val_str.strip()).str.to_time()
        elif dtype == pl.Boolean:
            rhs = pl.lit(val_str.lower() in ['true', '1', 'yes'])
        else:
            rhs = pl.lit(val_str)

        if op == "==":
            return pl.col(col_name) == rhs
        elif op == "!=":
            return pl.col(col_name) != rhs
        elif op == ">":
            return pl.col(col_name) > rhs
        elif op == "<":
            return pl.col(col_name) < rhs
        elif op == ">=":
            return pl.col(col_name) >= rhs
        elif op == "<=":
            return pl.col(col_name) <= rhs
        elif op == "contains":
            return pl.col(col_name).str.contains(val_str)
    except:
        return None
    return None
