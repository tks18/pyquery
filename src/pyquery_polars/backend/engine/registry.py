from pyquery_polars.core.models import StepMetadata
from pyquery_polars.core.registry import StepRegistry

# Import Params
from pyquery_polars.core.params import (
    SelectColsParams, DropColsParams, RenameColParams, KeepColsParams, AddColParams, CleanCastParams,
    FilterRowsParams, SortRowsParams, DeduplicateParams, SampleParams,
    JoinDatasetParams, AggregateParams, WindowFuncParams, ReshapeParams,
    FillNullsParams, RegexExtractParams, TimeBinParams, RollingAggParams, NumericBinParams,
    StringCaseParams, StringReplaceParams, MathOpParams, DateExtractParams,
    DropNullsParams, TextSliceParams, TextLengthParams,
    CumulativeParams, RankParams, DiffParams,
    MathSciParams, ClipParams, DateOffsetParams, DateDiffParams,
    SliceRowsParams, PromoteHeaderParams,
    SplitColParams, CombineColsParams, AddRowNumberParams,
    ExplodeParams, CoalesceParams,
    ZScoreParams, SkewKurtParams, StringPadParams, ConcatParams,
    ShiftParams, DropEmptyRowsParams,
    TextExtractDelimParams, RegexToolParams,
    RemoveOutliersParams, NormalizeSpacesParams, SmartExtractParams, OneHotEncodeParams,
    CleanTextParams, MaskPIIParams, AutoImputeParams, CheckBoolParams
)

# Import Transforms (Backend Logic)
from pyquery_polars.backend.transforms.columns import (
    select_cols_func, drop_cols_func, rename_col_func,
    keep_cols_func, add_col_func, clean_cast_func, promote_header_func,
    split_col_func, combine_cols_func, add_row_number_func,
    explode_func, coalesce_func, one_hot_encode_func
)
from pyquery_polars.backend.transforms.rows import (
    filter_rows_func, sort_rows_func, deduplicate_func, sample_func, slice_rows_func,
    shift_func, drop_empty_rows_func, remove_outliers_func
)
from pyquery_polars.backend.transforms.combine import (
    join_dataset_func, aggregate_func, window_func_func, reshape_func, concat_datasets_func
)
from pyquery_polars.backend.transforms.cleaning import (
    fill_nulls_func, regex_extract_func, string_case_func, string_replace_func,
    drop_nulls_func, text_slice_func, text_length_func, string_pad_func,
    text_extract_delim_func, regex_tool_func,
    normalize_spaces_func, smart_extract_func,
    clean_text_func, mask_pii_func, auto_impute_func, check_bool_func
)
from pyquery_polars.backend.transforms.analytics import (
    time_bin_func, rolling_agg_func, numeric_bin_func, math_op_func, date_extract_func,
    cumulative_func, rank_func, diff_func, z_score_func, skew_kurt_func
)
from pyquery_polars.backend.transforms.scientific import (
    math_sci_func, clip_func, date_offset_func, date_diff_func
)


def register_all_steps():
    """Register all available steps to the StepRegistry."""
    # Bootstrap the StepRegistry
    if StepRegistry.get_supported_steps():
        return

    R = StepRegistry

    # Columns
    R.register("select_cols", StepMetadata(label="Select Columns",
               group="Columns"), SelectColsParams, select_cols_func)
    R.register("drop_cols", StepMetadata(label="Drop Columns",
               group="Columns"), DropColsParams, drop_cols_func)
    R.register("rename_col", StepMetadata(label="Rename Column",
               group="Columns"), RenameColParams, rename_col_func)
    R.register("keep_cols", StepMetadata(label="Keep Specific (Finalize)",
               group="Columns"), KeepColsParams, keep_cols_func)
    R.register("add_col", StepMetadata(label="Add New Column",
               group="Columns"), AddColParams, add_col_func)
    R.register("clean_cast", StepMetadata(label="Clean / Cast Types",
               group="Columns"), CleanCastParams, clean_cast_func)
    R.register("promote_header", StepMetadata(label="First Row as Header", 
               group="Columns"), PromoteHeaderParams, promote_header_func)
    R.register("split_col", StepMetadata(label="Split Column", 
               group="Columns"), SplitColParams, split_col_func)
    R.register("combine_cols", StepMetadata(label="Combine Columns", 
               group="Columns"), CombineColsParams, combine_cols_func)
    R.register("add_row_number", StepMetadata(label="Add Row Number", 
               group="Columns"), AddRowNumberParams, add_row_number_func)
    R.register("explode", StepMetadata(label="Explode (Flatten List)", 
               group="Columns"), ExplodeParams, explode_func)
    R.register("coalesce", StepMetadata(label="Coalesce (Fill Nulls)", 
               group="Columns"), CoalesceParams, coalesce_func)
    R.register("one_hot_encode", StepMetadata(label="One-Hot Encode", 
               group="Columns"), OneHotEncodeParams, one_hot_encode_func)

    # Rows
    R.register("filter_rows", StepMetadata(label="Filter Rows", group="Rows"),
               FilterRowsParams, filter_rows_func)
    R.register("sort_rows", StepMetadata(label="Sort Rows", group="Rows"),
               SortRowsParams, sort_rows_func)
    R.register("deduplicate", StepMetadata(label="Deduplicate", group="Rows"),
               DeduplicateParams, deduplicate_func)
    R.register("sample", StepMetadata(label="Sample Data",
               group="Rows"), SampleParams, sample_func)
    R.register("slice_rows", StepMetadata(label="Keep / Remove Rows (Slice)",
               group="Rows"), SliceRowsParams, slice_rows_func)
    R.register("remove_outliers", StepMetadata(label="Remove Outliers (IQR)",
               group="Rows"), RemoveOutliersParams, remove_outliers_func)

    # Combine
    R.register("join_dataset", StepMetadata(label="Join Dataset", group="Combine"),
               JoinDatasetParams, join_dataset_func)
    R.register("aggregate", StepMetadata(label="Group By (Aggregate)",
               group="Combine"), AggregateParams, aggregate_func)
    R.register("window_func", StepMetadata(label="Window Function",
               group="Combine"), WindowFuncParams, window_func_func)
    R.register("reshape", StepMetadata(label="Reshape (Pivot/Melt)",
               group="Combine"), ReshapeParams, reshape_func)

    # Clean
    R.register("fill_nulls", StepMetadata(label="Fill NULLs", group="Clean"),
               FillNullsParams, fill_nulls_func)
    R.register("drop_nulls", StepMetadata(label="Drop NULL Rows",
               group="Clean"), DropNullsParams, drop_nulls_func)
    R.register("regex_extract", StepMetadata(label="Regex Extract", group="Clean"),
               RegexExtractParams, regex_extract_func)
    R.register("text_slice", StepMetadata(label="Text Slice (Substring)",
               group="Clean"), TextSliceParams, text_slice_func)
    R.register("text_length", StepMetadata(label="Text Length", group="Clean"),
               TextLengthParams, text_length_func)
    R.register("string_case", StepMetadata(label="String Case/Trim",
               group="Clean"), StringCaseParams, string_case_func)
    R.register("string_replace", StepMetadata(label="String Replace", group="Clean"),
               StringReplaceParams, string_replace_func)

    R.register("text_extract_delim", StepMetadata(label="Text Extract (Delimiter)",
               group="Clean"), TextExtractDelimParams, text_extract_delim_func)
    R.register("regex_tool", StepMetadata(label="Advanced Regex Tool",
               group="Clean"), RegexToolParams, regex_tool_func)
    R.register("normalize_spaces", StepMetadata(label="Normalize Whitespace",
               group="Clean"), NormalizeSpacesParams, normalize_spaces_func)
    R.register("smart_extract", StepMetadata(label="Smart Extract (Email/URL)",
               group="Clean"), SmartExtractParams, smart_extract_func)
    R.register("clean_text", StepMetadata(label="Smart Text Clean",
               group="Clean"), CleanTextParams, clean_text_func)
    R.register("mask_pii", StepMetadata(label="Mask PII (Redact)",
               group="Clean"), MaskPIIParams, mask_pii_func)
    R.register("auto_impute", StepMetadata(label="Auto Impute (Fill)",
               group="Clean"), AutoImputeParams, auto_impute_func)
    R.register("check_bool", StepMetadata(label="Smart Boolean (Yes/No)",
               group="Clean"), CheckBoolParams, check_bool_func)

    # Analytics
    R.register("time_bin", StepMetadata(label="Time Truncate (Bin)",
               group="Analytics"), TimeBinParams, time_bin_func)
    R.register("rolling_agg", StepMetadata(label="Rolling Aggregate",
               group="Analytics"), RollingAggParams, rolling_agg_func)
    R.register("numeric_bin", StepMetadata(label="Numeric Binning",
               group="Analytics"), NumericBinParams, numeric_bin_func)
    R.register("cumulative", StepMetadata(label="Cumulative (Running)",
               group="Analytics"), CumulativeParams, cumulative_func)
    R.register("rank", StepMetadata(label="Ranking",
               group="Analytics"), RankParams, rank_func)
    R.register("diff", StepMetadata(label="Pct Change / Diff",
               group="Analytics"), DiffParams, diff_func)

    # Math & Date
    R.register("math_op", StepMetadata(label="Math Operation",
               group="Math & Date"), MathOpParams, math_op_func)
    R.register("math_sci", StepMetadata(label="Scientific Math",
               group="Math & Date"), MathSciParams, math_sci_func)
    R.register("clip", StepMetadata(label="Clip / Clamp Values",
               group="Math & Date"), ClipParams, clip_func)

    R.register("date_extract", StepMetadata(label="Date Extraction", group="Math & Date"),
               DateExtractParams, date_extract_func)
    R.register("date_offset", StepMetadata(label="Date Offset (Add/Sub)",
               group="Math & Date"), DateOffsetParams, date_offset_func)
    R.register("date_diff", StepMetadata(label="Date Duration (Diff)",
               group="Math & Date"), DateDiffParams, date_diff_func)

    # Extended Operations (Phase 3)
    R.register("z_score", StepMetadata(label="Z-Score (Standardize)",
               group="Analytics"), ZScoreParams, z_score_func)
    R.register("skew_kurt", StepMetadata(label="Skew / Kurtosis",
               group="Analytics"), SkewKurtParams, skew_kurt_func)
               
    R.register("string_pad", StepMetadata(label="String Pad",
               group="Clean"), StringPadParams, string_pad_func)
               
    R.register("concat_datasets", StepMetadata(label="Concat Dataset (Vertical)",
               group="Combine"), ConcatParams, concat_datasets_func)
               
    R.register("shift", StepMetadata(label="Shift (Lead/Lag)",
               group="Rows"), ShiftParams, shift_func)
    R.register("drop_empty_rows", StepMetadata(label="Drop Empty Rows",
               group="Rows"), DropEmptyRowsParams, drop_empty_rows_func)
