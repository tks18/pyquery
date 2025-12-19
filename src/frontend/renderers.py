from src.frontend.steps.columns import (
    render_select_cols, render_drop_cols, render_rename_col, 
    render_keep_cols, render_add_col, render_clean_cast
)
from src.frontend.steps.rows import (
    render_filter_rows, render_sort_rows, render_deduplicate, render_sample
)
from src.frontend.steps.combine import (
    render_join_dataset, render_aggregate, render_window_func, render_reshape
)

RENDERER_MAP = {
    # Columns
    "select_cols": render_select_cols,
    "drop_cols": render_drop_cols,
    "rename_col": render_rename_col,
    "keep_cols": render_keep_cols,
    "add_col": render_add_col,
    "clean_cast": render_clean_cast,
    
    # Rows
    "filter_rows": render_filter_rows,
    "sort_rows": render_sort_rows,
    "deduplicate": render_deduplicate,
    "sample": render_sample,
    
    # Combine
    "join_dataset": render_join_dataset,
    "aggregate": render_aggregate,
    "window_func": render_window_func,
    "reshape": render_reshape,
}
