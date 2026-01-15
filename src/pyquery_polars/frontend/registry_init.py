from pyquery_polars.core.registry import StepRegistry

# Frontend Renderers
from pyquery_polars.frontend.steps.columns import (
    render_select_cols, render_drop_cols, render_rename_col,
    render_keep_cols, render_add_col, render_clean_cast, render_promote_header,
    render_split_col, render_combine_cols, render_add_row_number,
    render_explode, render_coalesce, render_one_hot_encode, render_sanitize_cols
)
from pyquery_polars.frontend.steps.rows import (
    render_filter_rows, render_sort_rows, render_deduplicate, render_sample, render_slice_rows,
    render_shift, render_drop_empty_rows, render_remove_outliers
)
from pyquery_polars.frontend.steps.combine import (
    render_join_dataset, render_aggregate, render_window_func, render_reshape, render_concat_datasets
)
from pyquery_polars.frontend.steps.cleaning import (
    render_fill_nulls, render_regex_extract, render_string_case, render_string_replace,
    render_drop_nulls, render_text_slice, render_text_length, render_string_pad,
    render_text_extract_delim, render_regex_tool,
    render_normalize_spaces, render_smart_extract,
    render_clean_text, render_mask_pii, render_auto_impute, render_check_bool
)
from pyquery_polars.frontend.steps.analytics import (
    render_time_bin, render_rolling_agg, render_numeric_bin, render_math_op, render_date_extract,
    render_cumulative, render_rank, render_diff, render_z_score, render_skew_kurt
)
from pyquery_polars.frontend.steps.scientific import (
    render_math_sci, render_clip, render_date_offset, render_date_diff
)
from pyquery_polars.frontend.steps.advanced import render_custom_script


def register_frontend():
    R = StepRegistry

    # Columns
    R.register_renderer("select_cols", render_select_cols)
    R.register_renderer("drop_cols", render_drop_cols)
    R.register_renderer("rename_col", render_rename_col)
    R.register_renderer("keep_cols", render_keep_cols)
    R.register_renderer("add_col", render_add_col)
    R.register_renderer("clean_cast", render_clean_cast)
    R.register_renderer("promote_header", render_promote_header)
    R.register_renderer("split_col", render_split_col)
    R.register_renderer("combine_cols", render_combine_cols)
    R.register_renderer("add_row_number", render_add_row_number)
    R.register_renderer("explode", render_explode)
    R.register_renderer("coalesce", render_coalesce)
    R.register_renderer("one_hot_encode", render_one_hot_encode)
    R.register_renderer("sanitize_cols", render_sanitize_cols)

    # Rows
    R.register_renderer("filter_rows", render_filter_rows)
    R.register_renderer("sort_rows", render_sort_rows)
    R.register_renderer("deduplicate", render_deduplicate)
    R.register_renderer("sample", render_sample)
    R.register_renderer("slice_rows", render_slice_rows)
    R.register_renderer("shift", render_shift)
    R.register_renderer("drop_empty_rows", render_drop_empty_rows)
    R.register_renderer("remove_outliers", render_remove_outliers)

    # Combine
    R.register_renderer("join_dataset", render_join_dataset)
    R.register_renderer("aggregate", render_aggregate)
    R.register_renderer("window_func", render_window_func)
    R.register_renderer("reshape", render_reshape)
    R.register_renderer("concat_datasets", render_concat_datasets)

    # Clean
    R.register_renderer("fill_nulls", render_fill_nulls)
    R.register_renderer("drop_nulls", render_drop_nulls)
    R.register_renderer("regex_extract", render_regex_extract)
    R.register_renderer("text_slice", render_text_slice)
    R.register_renderer("text_length", render_text_length)
    R.register_renderer("string_case", render_string_case)
    R.register_renderer("string_replace", render_string_replace)
    R.register_renderer("string_pad", render_string_pad)
    R.register_renderer("text_extract_delim", render_text_extract_delim)
    R.register_renderer("regex_tool", render_regex_tool)
    R.register_renderer("normalize_spaces", render_normalize_spaces)
    R.register_renderer("smart_extract", render_smart_extract)
    R.register_renderer("clean_text", render_clean_text)
    R.register_renderer("mask_pii", render_mask_pii)
    R.register_renderer("auto_impute", render_auto_impute)
    R.register_renderer("check_bool", render_check_bool)

    # Analytics
    R.register_renderer("time_bin", render_time_bin)
    R.register_renderer("rolling_agg", render_rolling_agg)
    R.register_renderer("numeric_bin", render_numeric_bin)
    R.register_renderer("cumulative", render_cumulative)
    R.register_renderer("rank", render_rank)
    R.register_renderer("diff", render_diff)
    R.register_renderer("z_score", render_z_score)
    R.register_renderer("skew_kurt", render_skew_kurt)

    # Math & Date
    R.register_renderer("math_op", render_math_op)
    R.register_renderer("math_sci", render_math_sci)
    R.register_renderer("clip", render_clip)
    R.register_renderer("date_extract", render_date_extract)
    R.register_renderer("date_offset", render_date_offset)
    R.register_renderer("date_diff", render_date_diff)

    # Advanced
    R.register_renderer("custom_script", render_custom_script)
