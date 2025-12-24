from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union, Any


class FilterCondition(BaseModel):
    col: str
    op: str
    val: Any


class AggDef(BaseModel):
    col: str
    op: str
    alias: str = ""


class CastChange(BaseModel):
    col: str
    action: str
    fmt: Optional[str] = None


class SelectColsParams(BaseModel):
    cols: List[str] = Field(default_factory=list)


class DropColsParams(BaseModel):
    cols: List[str] = Field(default_factory=list)


class RenameColParams(BaseModel):
    old: str = ""
    new: str = ""


class KeepColsParams(BaseModel):
    cols: List[str] = Field(default_factory=list)


class AddColParams(BaseModel):
    name: str = ""
    expr: str = "1"


class CleanCastParams(BaseModel):
    changes: List[CastChange] = Field(default_factory=list)


class FilterRowsParams(BaseModel):
    logic: Literal["AND", "OR"] = "AND"
    conditions: List[FilterCondition] = Field(default_factory=list)


class SortRowsParams(BaseModel):
    cols: List[str] = Field(default_factory=list)
    desc: bool = False


class DeduplicateParams(BaseModel):
    subset: List[str] = Field(default_factory=list)


class SampleParams(BaseModel):
    method: Literal["Fraction", "N"] = "Fraction"
    val: float = 0.1


class JoinDatasetParams(BaseModel):
    alias: str = ""
    how: Literal["inner", "left", "outer", "cross", "semi", "anti"] = "left"
    left_on: List[str] = Field(default_factory=list)
    right_on: List[str] = Field(default_factory=list)


class AggregateParams(BaseModel):
    keys: List[str] = Field(default_factory=list)
    aggs: List[AggDef] = Field(default_factory=list)


class WindowFuncParams(BaseModel):
    target: str = ""
    name: str = ""
    op: str = "sum"
    over: List[str] = Field(default_factory=list)
    sort: List[str] = Field(default_factory=list)


class ReshapeParams(BaseModel):
    mode: Literal["Pivot", "Unpivot"] = "Pivot"
    # Pivot
    idx: List[str] = Field(default_factory=list)
    col: str = ""
    val: str = ""
    agg: str = "first"
    # Unpivot
    id_vars: List[str] = Field(default_factory=list)
    val_vars: List[str] = Field(default_factory=list)


class FillNullsParams(BaseModel):
    cols: List[str] = Field(default_factory=list)
    strategy: Literal["forward", "backward", "mean",
                      "median", "min", "max", "zero", "literal"] = "forward"
    literal_val: Optional[Union[str, float, int]] = None


class RegexExtractParams(BaseModel):
    col: str = ""
    pattern: str = ""
    alias: str = ""


class TimeBinParams(BaseModel):
    col: str = ""
    interval: str = "1h"


class RollingAggParams(BaseModel):
    target: str = ""
    window_size: int = 3
    op: Literal["mean", "sum", "min", "max", "std"] = "mean"
    center: bool = False


class NumericBinParams(BaseModel):
    col: str = ""
    bins: int = 5
    labels: Optional[List[str]] = None


class StringCaseParams(BaseModel):
    col: str = ""
    case: Literal["upper", "lower", "title", "trim"] = "upper"
    alias: str = ""


class StringReplaceParams(BaseModel):
    col: str = ""
    pat: str = ""
    val: str = ""
    alias: str = ""


class MathOpParams(BaseModel):
    col: str = ""
    op: Literal["round", "abs", "ceil", "floor", "sqrt"] = "round"
    precision: int = 2
    alias: str = ""


class DateExtractParams(BaseModel):
    col: str = ""
    part: Literal["year", "month", "day", "hour", "minute",
                  "second", "weekday", "minute", "second"] = "year"
    alias: str = ""


class DropNullsParams(BaseModel):
    cols: List[str] = Field(default_factory=list)
    how: Literal["any", "all"] = "any"


class TextSliceParams(BaseModel):
    col: str = ""
    start: int = 0
    length: Optional[int] = None
    alias: str = ""


class TextLengthParams(BaseModel):
    col: str = ""
    alias: str = ""


class CumulativeParams(BaseModel):
    col: str = ""
    op: Literal["cumsum", "cummin", "cummax", "cumprod"] = "cumsum"
    alias: str = ""
    reverse: bool = False


class RankParams(BaseModel):
    col: str = ""
    method: Literal["average", "min", "max",
                    "dense", "ordinal", "random"] = "dense"
    descending: bool = False
    alias: str = ""


class DiffParams(BaseModel):
    col: str = ""
    method: Literal["diff", "pct_change"] = "diff"
    n: int = 1
    alias: str = ""


class MathSciParams(BaseModel):
    col: str = ""
    op: Literal["log", "log10", "exp", "pow", "sqrt", "cbrt", "mod",
                "sin", "cos", "tan", "arcsin", "arccos", "arctan",
                "degrees", "radians", "sign"] = "log"
    arg: float = 2.0


class ClipParams(BaseModel):
    col: str = ""
    min_val: Optional[float] = None
    max_val: Optional[float] = None


class DateOffsetParams(BaseModel):
    col: str = ""
    offset: str = "1d"
    action: Literal["add", "sub"] = "add"


class DateDiffParams(BaseModel):
    start_col: str = ""
    end_col: str = ""
    unit: Literal["days", "hours", "minutes",
                  "seconds", "milliseconds"] = "days"
    alias: str = ""


class SliceRowsParams(BaseModel):
    mode: Literal["Keep Top", "Keep Bottom",
                  "Remove Top", "Remove Bottom"] = "Keep Top"
    n: int = 10


class PromoteHeaderParams(BaseModel):
    pass


class SplitColParams(BaseModel):
    col: str = ""
    pat: str = ","
    n: int = 2


class CombineColsParams(BaseModel):
    cols: List[str] = Field(default_factory=list)
    separator: str = " "
    new_name: str = "combined_col"


class AddRowNumberParams(BaseModel):
    name: str = "row_nr"


class ExplodeParams(BaseModel):
    cols: List[str] = Field(default_factory=list)


class CoalesceParams(BaseModel):
    cols: List[str] = Field(default_factory=list)
    new_name: str = "coalesced"


class ZScoreParams(BaseModel):
    col: str = ""
    by: List[str] = Field(default_factory=list)
    alias: str = ""


class SkewKurtParams(BaseModel):
    col: str = ""
    measure: Literal["skew", "kurtosis"] = "skew"
    alias: str = ""


class StringPadParams(BaseModel):
    col: str = ""
    length: int = 10
    fill_char: str = ""
    side: Literal["left", "right", "center"] = "left"
    alias: str = ""


class TextExtractDelimParams(BaseModel):
    col: str = ""
    start_delim: str = ""
    end_delim: str = ""
    alias: str = ""


class RegexToolParams(BaseModel):
    col: str = ""
    pattern: str = ""
    action: Literal["replace_all", "replace_one",
                    "extract", "count", "contains"] = "replace_all"
    replacement: str = ""
    alias: str = ""


class RemoveOutliersParams(BaseModel):
    col: str = ""
    method: Literal["IQR"] = "IQR"
    factor: float = 1.5
    alias: str = ""


class NormalizeSpacesParams(BaseModel):
    col: str = ""
    alias: str = ""


class SmartExtractParams(BaseModel):
    col: str = ""
    type: Literal["email_user", "email_domain",
                  "url_domain", "url_path", "ipv4"] = "email_domain"
    alias: str = ""


class OneHotEncodeParams(BaseModel):
    col: str = ""
    prefix: str = ""
    separator: str = "_"


class ConcatParams(BaseModel):
    other_dataset: str = ""  # ID/Name of the other dataset


class ShiftParams(BaseModel):
    # If empty, apply to all applicable? Or just single col. Let's support single for now or list.
    col: str = ""
    periods: int = 1
    fill_value: Optional[Union[float, int, str]] = None
    alias: str = ""


class DropEmptyRowsParams(BaseModel):
    subset: List[str] = Field(default_factory=list)
    how: Literal["any", "all"] = "any"
    thresh: Optional[int] = None


class AutoImputeParams(BaseModel):
    col: str = ""
    strategy: Literal["mean", "median", "mode",
                      "ffill", "bfill", "zero"] = "mean"
    alias: str = ""


class ClipValuesParams(BaseModel):
    col: str = ""
    lower_percentile: float = 0.01
    upper_percentile: float = 0.99
    alias: str = ""


class MaskPIIParams(BaseModel):
    col: str = ""
    type: Literal["email", "credit_card",
                  "phone", "ssn", "ip", "custom"] = "email"
    mask_char: str = "*"
    alias: str = ""


class CleanTextParams(BaseModel):
    col: str = ""
    lowercase: bool = True
    remove_punctuation: bool = True
    remove_digits: bool = False
    ascii_only: bool = True
    alias: str = ""


class QuantileBinsParams(BaseModel):
    col: str = ""
    n_bins: int = 4
    labels: Optional[List[str]] = None
    alias: str = ""


class CheckBoolParams(BaseModel):
    col: str = ""
    true_values: List[str] = Field(default_factory=lambda: [
                                   "yes", "y", "true", "1", "on"])
    false_values: List[str] = Field(default_factory=lambda: [
                                    "no", "n", "false", "0", "off"])
    alias: str = ""


class RoundSmartParams(BaseModel):
    col: str = ""
    decimals: int = 2
    alias: str = ""
