import polars as pl

# Pure Backend Transform Logic
# All state/datasets are passed via context

def join_dataset_func(lf: pl.LazyFrame, params: dict, context: dict = None) -> pl.LazyFrame:
    alias = params.get('alias')
    left_on = params.get('left_on')
    right_on = params.get('right_on')
    how = params.get('how', 'left')
    
    if not (alias and left_on and right_on):
        return lf
    
    datasets = context.get('datasets', {}) if context else {}
    if alias in datasets:
        other_lf = datasets[alias]
        return lf.join(other_lf, left_on=left_on, right_on=right_on, how=how)
    
    return lf

def aggregate_func(lf: pl.LazyFrame, params: dict, context: dict = None) -> pl.LazyFrame:
    keys = params.get('keys', [])
    aggs = params.get('aggs', [])
    
    if not keys or not aggs:
        return lf
        
    agg_exprs = []
    for agg in aggs:
        col_expr = pl.col(agg['col'])
        op = agg['op']
        if op == "sum": agg_exprs.append(col_expr.sum())
        elif op == "mean": agg_exprs.append(col_expr.mean())
        elif op == "min": agg_exprs.append(col_expr.min())
        elif op == "max": agg_exprs.append(col_expr.max())
        elif op == "count": agg_exprs.append(col_expr.count())
        elif op == "n_unique": agg_exprs.append(col_expr.n_unique())
        elif op == "first": agg_exprs.append(col_expr.first())
        elif op == "last": agg_exprs.append(col_expr.last())
        elif op == "median": agg_exprs.append(col_expr.median())
            
    return lf.group_by(keys).agg(agg_exprs)

def window_func_func(lf: pl.LazyFrame, params: dict, context: dict = None) -> pl.LazyFrame:
    target = params.get('target')
    op = params.get('op')
    over = params.get('over', [])
    sort = params.get('sort', [])
    name = params.get('name')
    
    if not (target and name and op):
        return lf
        
    expr = pl.col(target)
    if op == "sum": expr = expr.sum()
    elif op == "mean": expr = expr.mean()
    elif op == "min": expr = expr.min()
    elif op == "max": expr = expr.max()
    elif op == "count": expr = expr.count()
    elif op == "cum_sum": expr = expr.cum_sum()
    elif op == "rank_dense": expr = expr.rank("dense")
    elif op == "rank_ordinal": expr = expr.rank("ordinal")
    elif op == "lag": expr = expr.shift(1)
    elif op == "lead": expr = expr.shift(-1)
    
    if over:
        expr = expr.over(over)
        
    if sort:
        lf = lf.sort(sort)
        
    return lf.with_columns(expr.alias(name))

def reshape_func(lf: pl.LazyFrame, params: dict, context: dict = None) -> pl.LazyFrame:
    mode = params.get('mode', 'Unpivot')
    
    if mode == "Unpivot":
        id_vars = params.get('id_vars', [])
        val_vars = params.get('val_vars', [])
        if id_vars and val_vars:
            return lf.melt(id_vars=id_vars, value_vars=val_vars)
            
    else: # Pivot
        idx = params.get('idx', [])
        col = params.get('col')
        val = params.get('val')
        agg = params.get('agg', 'first')
        
        if idx and col and val:
            # Pivot requires eager execution -> Collect inside backend?
            # Yes, backend does the compute.
            return lf.collect().pivot(
                index=idx, on=col, values=val, aggregate_function=agg
            ).lazy()
            
    return lf
