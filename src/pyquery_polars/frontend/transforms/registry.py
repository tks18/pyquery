"""
Frontend Registry Initialization.

Registers all step renderers using their class definitions.
"""
from typing import Type

from pyquery_polars.core.registry import StepRegistry

from pyquery_polars.frontend.transforms.base import BaseStepRenderer

# Import all step classes
from pyquery_polars.frontend.transforms.pipeline import (
    # Columns
    SelectColsStep, DropColsStep, RenameColStep, KeepColsStep,
    AddColStep, CleanCastStep, PromoteHeaderStep, SplitColStep,
    CombineColsStep, AddRowNumberStep, ExplodeStep, CoalesceStep,
    OneHotEncodeStep, SanitizeColsStep,

    # Rows
    FilterRowsStep, SortRowsStep, DeduplicateStep, SampleStep,
    SliceRowsStep, ShiftStep, DropEmptyRowsStep, RemoveOutliersStep,

    # Combine
    JoinDatasetStep, AggregateStep, WindowFuncStep,
    ReshapeStep, ConcatDatasetsStep,

    # Cleaning
    FillNullsStep, DropNullsStep, RegexExtractStep, TextSliceStep,
    TextLengthStep, StringCaseStep, StringReplaceStep, StringPadStep,
    TextExtractDelimStep, RegexToolStep, NormalizeSpacesStep, SmartExtractStep,
    CleanTextStep, MaskPIIStep, AutoImputeStep, CheckBoolStep,

    # Analytics
    TimeBinStep, RollingAggStep, NumericBinStep, MathOpStep,
    DateExtractStep, CumulativeStep, RankStep, DiffStep,
    ZScoreStep, SkewKurtStep,

    # Scientific / Math
    MathSciStep, ClipStep, DateOffsetStep, DateDiffStep,

    # Advanced
    CustomScriptStep
)


def create_renderer(cls: Type[BaseStepRenderer]):
    """
    Factory function to create a renderer callable from a StepRenderer class.

    Args:
        cls: The StepRenderer class (e.g. FilterRowsStep)

    Returns:
        A callable matching the FrontendFunc signature.
    """
    def renderer(step_id: str, params, schema=None, ctx=None):
        if not ctx:
            import streamlit as st
            st.error("Application Context not initialized.")
            return params

        instance = cls(ctx)
        return instance.render(step_id, params, schema)
    return renderer


def register_frontend():
    """
    Register all step renderers with the frontend registry.
    use the stepregistry to get the renderers and register them later
    """
    R = StepRegistry

    # Helper to clean up registration syntax
    def reg(step_type: str, cls: Type[BaseStepRenderer]):
        R.register_renderer(step_type, create_renderer(cls))

    # Columns
    reg("select_cols", SelectColsStep)
    reg("drop_cols", DropColsStep)
    reg("rename_col", RenameColStep)
    reg("keep_cols", KeepColsStep)
    reg("add_col", AddColStep)
    reg("clean_cast", CleanCastStep)
    reg("promote_header", PromoteHeaderStep)
    reg("split_col", SplitColStep)
    reg("combine_cols", CombineColsStep)
    reg("add_row_number", AddRowNumberStep)
    reg("explode", ExplodeStep)
    reg("coalesce", CoalesceStep)
    reg("one_hot_encode", OneHotEncodeStep)
    reg("sanitize_cols", SanitizeColsStep)

    # Rows
    reg("filter_rows", FilterRowsStep)
    reg("sort_rows", SortRowsStep)
    reg("deduplicate", DeduplicateStep)
    reg("sample", SampleStep)
    reg("slice_rows", SliceRowsStep)
    reg("shift", ShiftStep)
    reg("drop_empty_rows", DropEmptyRowsStep)
    reg("remove_outliers", RemoveOutliersStep)

    # Combine
    reg("join_dataset", JoinDatasetStep)
    reg("aggregate", AggregateStep)
    reg("window_func", WindowFuncStep)
    reg("reshape", ReshapeStep)
    reg("concat_datasets", ConcatDatasetsStep)

    # Clean
    reg("fill_nulls", FillNullsStep)
    reg("drop_nulls", DropNullsStep)
    reg("regex_extract", RegexExtractStep)
    reg("text_slice", TextSliceStep)
    reg("text_length", TextLengthStep)
    reg("string_case", StringCaseStep)
    reg("string_replace", StringReplaceStep)
    reg("string_pad", StringPadStep)
    reg("text_extract_delim", TextExtractDelimStep)
    reg("regex_tool", RegexToolStep)
    reg("normalize_spaces", NormalizeSpacesStep)
    reg("smart_extract", SmartExtractStep)
    reg("clean_text", CleanTextStep)
    reg("mask_pii", MaskPIIStep)
    reg("auto_impute", AutoImputeStep)
    reg("check_bool", CheckBoolStep)

    # Analytics
    reg("time_bin", TimeBinStep)
    reg("rolling_agg", RollingAggStep)
    reg("numeric_bin", NumericBinStep)
    reg("cumulative", CumulativeStep)
    reg("rank", RankStep)
    reg("diff", DiffStep)
    reg("z_score", ZScoreStep)
    reg("skew_kurt", SkewKurtStep)

    # Math & Date
    reg("math_op", MathOpStep)
    reg("math_sci", MathSciStep)
    reg("clip", ClipStep)
    reg("date_extract", DateExtractStep)
    reg("date_offset", DateOffsetStep)
    reg("date_diff", DateDiffStep)

    # Advanced
    reg("custom_script", CustomScriptStep)
