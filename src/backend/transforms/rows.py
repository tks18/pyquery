import polars as pl
from src.backend.utils.helpers import build_filter_expr

def filter_rows_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    conditions = params.get('conditions', [])
    logic = params.get('logic', 'AND')
    
    if not conditions:
        return lf
    
    try:
        schema = lf.collect_schema()
    except:
        return lf

    exprs = [build_filter_expr(c['col'], c['op'], c['val'], schema) for c in conditions]
    exprs = [e for e in exprs if e is not None]
    
    if not exprs:
        return lf
        
    if logic == "AND":
        final_expr = exprs[0]
        for e in exprs[1:]:
            final_expr = final_expr & e
    else:
        final_expr = exprs[0]
        for e in exprs[1:]:
            final_expr = final_expr | e
            
    return lf.filter(final_expr)

def sort_rows_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    cols = params.get('cols', [])
    desc = params.get('desc', False)
    if cols:
        return lf.sort(cols, descending=desc)
    return lf

def deduplicate_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    subset = params.get('subset', [])
    if subset:
        return lf.unique(subset=subset)
    return lf.unique()

def sample_func(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    method = params.get('method', 'Fraction')
    val = params.get('val', 0.1)
    
    if method == "Fraction":
        try:
            return lf.collect().sample(fraction=val, shuffle=True).lazy()
        except:
            return lf.filter(pl.int_range(0, pl.count()) < (pl.count() * val))
    else:
        return lf.limit(int(val))
