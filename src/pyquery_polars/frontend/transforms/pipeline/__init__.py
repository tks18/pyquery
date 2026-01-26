"""
Step renderers module - Class-based UI components for transformation steps.

This module exports all step renderer classes and the base class.
Each step type has a corresponding class that inherits from BaseStepRenderer.

Usage:
    from pyquery_polars.frontend.steps import BaseStepRenderer, FillNullsStep
    
    class MyStep(BaseStepRenderer[MyParams]):
        def render(self, step_id, params, schema):
            # Render UI
            return params
"""

# Base class
from pyquery_polars.frontend.transforms.base import BaseStepRenderer

# Cleaning steps
from pyquery_polars.frontend.transforms.pipeline.cleaning import (
    FillNullsStep, RegexExtractStep, StringCaseStep, StringReplaceStep,
    DropNullsStep, TextSliceStep, TextLengthStep, StringPadStep,
    TextExtractDelimStep, RegexToolStep, NormalizeSpacesStep, SmartExtractStep,
    CleanTextStep, MaskPIIStep, AutoImputeStep, CheckBoolStep
)

# Column steps
from pyquery_polars.frontend.transforms.pipeline.columns import (
    SanitizeColsStep, SelectColsStep, DropColsStep, KeepColsStep,
    RenameColStep, AddColStep, CleanCastStep, PromoteHeaderStep,
    SplitColStep, CombineColsStep, AddRowNumberStep,
    ExplodeStep, CoalesceStep, OneHotEncodeStep
)

# Row steps
from pyquery_polars.frontend.transforms.pipeline.rows import (
    FilterRowsStep, SortRowsStep, DeduplicateStep, SampleStep,
    SliceRowsStep, ShiftStep, DropEmptyRowsStep, RemoveOutliersStep
)

# Combine steps
from pyquery_polars.frontend.transforms.pipeline.combine import (
    JoinDatasetStep, AggregateStep, WindowFuncStep,
    ReshapeStep, ConcatDatasetsStep
)

# Analytics steps
from pyquery_polars.frontend.transforms.pipeline.analytics import (
    TimeBinStep, RollingAggStep, NumericBinStep, MathOpStep,
    DateExtractStep, CumulativeStep, RankStep, DiffStep,
    ZScoreStep, SkewKurtStep
)

# Scientific steps
from pyquery_polars.frontend.transforms.pipeline.scientific import (
    MathSciStep, ClipStep, DateOffsetStep, DateDiffStep
)

# Advanced steps
from pyquery_polars.frontend.transforms.pipeline.advanced import CustomScriptStep


__all__ = [
    # Base
    "BaseStepRenderer",

    # Cleaning
    "FillNullsStep", "RegexExtractStep", "StringCaseStep", "StringReplaceStep",
    "DropNullsStep", "TextSliceStep", "TextLengthStep", "StringPadStep",
    "TextExtractDelimStep", "RegexToolStep", "NormalizeSpacesStep", "SmartExtractStep",
    "CleanTextStep", "MaskPIIStep", "AutoImputeStep", "CheckBoolStep",

    # Columns
    "SanitizeColsStep", "SelectColsStep", "DropColsStep", "KeepColsStep",
    "RenameColStep", "AddColStep", "CleanCastStep", "PromoteHeaderStep",
    "SplitColStep", "CombineColsStep", "AddRowNumberStep",
    "ExplodeStep", "CoalesceStep", "OneHotEncodeStep",

    # Rows
    "FilterRowsStep", "SortRowsStep", "DeduplicateStep", "SampleStep",
    "SliceRowsStep", "ShiftStep", "DropEmptyRowsStep", "RemoveOutliersStep",

    # Combine
    "JoinDatasetStep", "AggregateStep", "WindowFuncStep",
    "ReshapeStep", "ConcatDatasetsStep",

    # Analytics
    "TimeBinStep", "RollingAggStep", "NumericBinStep", "MathOpStep",
    "DateExtractStep", "CumulativeStep", "RankStep", "DiffStep",
    "ZScoreStep", "SkewKurtStep",

    # Scientific
    "MathSciStep", "ClipStep", "DateOffsetStep", "DateDiffStep",

    # Advanced
    "CustomScriptStep",
]
