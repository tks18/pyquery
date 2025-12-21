from pyquery_polars.core.registry import StepRegistry

# Frontend Renderers
from pyquery_polars.frontend.steps.columns import (
    render_select_cols, render_drop_cols, render_rename_col,
    render_keep_cols, render_add_col, render_clean_cast
)
from pyquery_polars.frontend.steps.rows import (
    render_filter_rows, render_sort_rows, render_deduplicate, render_sample
)
from pyquery_polars.frontend.steps.combine import (
    render_join_dataset, render_aggregate, render_window_func, render_reshape
)
from pyquery_polars.frontend.steps.cleaning import (
    render_fill_nulls, render_regex_extract, render_string_case, render_string_replace,
    render_drop_nulls, render_text_slice, render_text_length
)
from pyquery_polars.frontend.steps.analytics import (
    render_time_bin, render_rolling_agg, render_numeric_bin, render_math_op, render_date_extract,
    render_cumulative, render_rank, render_diff
)
from pyquery_polars.frontend.steps.scientific import (
    render_math_sci, render_clip, render_date_offset, render_date_diff
)


def register_frontend():
    R = StepRegistry

    # Columns
    R.register_renderer("select_cols", render_select_cols)
    R.register_renderer("drop_cols", render_drop_cols)
    R.register_renderer("rename_col", render_rename_col)
    R.register_renderer("keep_cols", render_keep_cols)
    R.register_renderer("add_col", render_add_col)
    R.register_renderer("clean_cast", render_clean_cast)

    # Rows
    R.register_renderer("filter_rows", render_filter_rows)
    R.register_renderer("sort_rows", render_sort_rows)
    R.register_renderer("deduplicate", render_deduplicate)
    R.register_renderer("sample", render_sample)

    # Combine
    R.register_renderer("join_dataset", render_join_dataset)
    R.register_renderer("aggregate", render_aggregate)
    R.register_renderer("window_func", render_window_func)
    R.register_renderer("reshape", render_reshape)

    # Clean
    R.register_renderer("fill_nulls", render_fill_nulls)
    R.register_renderer("drop_nulls", render_drop_nulls)
    R.register_renderer("regex_extract", render_regex_extract)
    R.register_renderer("text_slice", render_text_slice)
    R.register_renderer("text_length", render_text_length)
    R.register_renderer("string_case", render_string_case)
    R.register_renderer("string_replace", render_string_replace)

    # Analytics
    R.register_renderer("time_bin", render_time_bin)
    R.register_renderer("rolling_agg", render_rolling_agg)
    R.register_renderer("numeric_bin", render_numeric_bin)
    R.register_renderer("cumulative", render_cumulative)
    R.register_renderer("rank", render_rank)
    R.register_renderer("diff", render_diff)

    # Math & Date
    R.register_renderer("math_op", render_math_op)
    R.register_renderer("math_sci", render_math_sci)
    R.register_renderer("clip", render_clip)
    R.register_renderer("date_extract", render_date_extract)
    R.register_renderer("date_offset", render_date_offset)
    R.register_renderer("date_diff", render_date_diff)
