from typing import Any, Optional, cast

import streamlit as st
import polars as pl

from pyquery_polars.core.params import (
    FillNullsParams, RegexExtractParams, StringCaseParams, StringReplaceParams,
    DropNullsParams, TextSliceParams, TextLengthParams, StringPadParams,
    TextExtractDelimParams, RegexToolParams,
    NormalizeSpacesParams, SmartExtractParams,
    CleanTextParams, MaskPIIParams, AutoImputeParams, CheckBoolParams
)


def render_fill_nulls(step_id: str, params: FillNullsParams, schema: Optional[pl.Schema]) -> FillNullsParams:
    # Simple form
    c1, c2 = st.columns([0.5, 0.5])

    params.strategy = c1.selectbox(
        "Strategy",
        ["forward", "backward", "mean", "median", "min", "max", "zero", "literal"],
        index=["forward", "backward", "mean", "median", "min",
               "max", "zero", "literal"].index(params.strategy),
        key=f"fn_s_{step_id}"
    )

    if params.strategy == "literal":
        lit = c2.text_input("Literal Value", value=str(
            params.literal_val or ""), key=f"fn_l_{step_id}")
        try:
            params.literal_val = float(lit)
        except:
            params.literal_val = lit

    # Columns
    current_cols = schema.names() if schema else []
    # If we have schema, use multiselect
    if current_cols:
        default_cols = [c for c in params.cols if c in current_cols]
        selected_cols = st.multiselect(
            "Columns", current_cols, default=default_cols, key=f"fn_c_{step_id}")
        params.cols = selected_cols
    else:
        # Fallback to text input
        cols_str = st.text_input("Columns (comma separated)", value=", ".join(
            params.cols), key=f"fn_c_{step_id}")
        if cols_str:
            params.cols = [c.strip() for c in cols_str.split(",") if c.strip()]
        else:
            params.cols = []

    return params


def render_regex_extract(step_id: str, params: RegexExtractParams, schema: Optional[pl.Schema]) -> RegexExtractParams:
    current_cols = schema.names() if schema else []

    c1, c2 = st.columns(2)

    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Target Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"re_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Target Column", value=params.col, key=f"re_c_{step_id}")

    params.alias = c2.text_input(
        "Output Name", value=params.alias, key=f"re_a_{step_id}")
    params.pattern = st.text_input(
        "Regex Pattern", value=params.pattern, key=f"re_p_{step_id}")
    return params


def render_string_case(step_id: str, params: StringCaseParams, schema: Optional[pl.Schema]) -> StringCaseParams:
    current_cols = schema.names() if schema else []

    c1, c2 = st.columns(2)

    # String Case

    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Target Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"sc_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Target Column", value=params.col, key=f"sc_c_{step_id}")

    params.case = c2.selectbox("Operation", ["upper", "lower", "title", "trim"],
                               index=["upper", "lower", "title",
                                      "trim"].index(params.case),
                               key=f"sc_o_{step_id}")

    params.alias = st.text_input("Output Name (Optional)", value=params.alias,
                                 key=f"sc_a_{step_id}", help="Leave empty to overwrite")
    return params


def render_string_replace(step_id: str, params: StringReplaceParams, schema: Optional[pl.Schema]) -> StringReplaceParams:
    current_cols = schema.names() if schema else []

    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = st.selectbox("Target Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"sr_c_{step_id}")
    else:
        params.col = st.text_input(
            "Target Column", value=params.col, key=f"sr_c_{step_id}")

    c1, c2 = st.columns(2)
    params.pat = c1.text_input("Find", value=params.pat, key=f"sr_p_{step_id}")
    params.val = c2.text_input(
        "Replace With", value=params.val, key=f"sr_v_{step_id}")

    params.alias = st.text_input("Output Name (Optional)", value=params.alias,
                                 key=f"sr_a_{step_id}", help="Leave empty to overwrite")
    return params


def render_drop_nulls(step_id: str, params: DropNullsParams, schema: Optional[pl.Schema]) -> DropNullsParams:
    c1, c2 = st.columns([0.2, 0.8])
    params.how = c1.selectbox("Criteria", ["any", "all"], index=[
                              "any", "all"].index(params.how), key=f"dn_h_{step_id}")

    current_cols = schema.names() if schema else []
    default = [c for c in params.cols if c in current_cols]
    params.cols = c2.multiselect(
        "Check Columns (Empty = All)", current_cols, default=default, key=f"dn_c_{step_id}")
    return params


def render_text_slice(step_id: str, params: TextSliceParams, schema: Optional[pl.Schema]) -> TextSliceParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")

    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"ts_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"ts_c_{step_id}")

    params.alias = c2.text_input(
        "New Name (Optional)", value=params.alias, key=f"ts_a_{step_id}")

    c3, c4 = st.columns(2)
    params.start = c3.number_input(
        "Start Index", value=params.start, key=f"ts_s_{step_id}")
    # Slice to end if checkbox
    slice_to_end = c4.checkbox("Slice to End", value=(
        params.length is None), key=f"ts_e_{step_id}")
    if not slice_to_end:
        val = params.length if params.length else 1
        params.length = c4.number_input(
            "Length", value=val, min_value=1, key=f"ts_l_{step_id}")
    else:
        params.length = None

    return params


def render_text_length(step_id: str, params: TextLengthParams, schema: Optional[pl.Schema]) -> TextLengthParams:
    current_cols = schema.names() if schema else []
    c1, c2 = st.columns(2)
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"tl_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"tl_c_{step_id}")

    params.alias = c2.text_input(
        "New Name (Optional)", value=params.alias, key=f"tl_a_{step_id}")
    return params


def render_string_pad(step_id: str, params: StringPadParams, schema: Optional[pl.Schema]) -> StringPadParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"sp_c_{step_id}")
    side = c2.selectbox("Side", ["left", "right", "center"],
                        index=["left", "right", "center"].index(params.side), key=f"sp_s_{step_id}")

    c3, c4 = st.columns(2)
    length = c3.number_input("Target Length", min_value=1,
                             value=params.length, key=f"sp_l_{step_id}")
    char = c4.text_input("Fill Character", value=params.fill_char,
                         max_chars=1, key=f"sp_fc_{step_id}")

    params.col = col
    params.side = cast(Any, side)
    params.length = int(length)

    params.fill_char = char
    return params


def render_text_extract_delim(step_id: str, params: TextExtractDelimParams, schema: Optional[pl.Schema]) -> TextExtractDelimParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"ted_c_{step_id}")

    c3, c4 = st.columns(2)
    start = c3.text_input(
        "Start Delimiter", value=params.start_delim, key=f"ted_s_{step_id}")
    end = c4.text_input(
        "End Delimiter", value=params.end_delim, key=f"ted_e_{step_id}")

    if not start and not end:
        st.warning("⚠️ Please provide at least one delimiter.")

    params.col = col if col else ""
    params.start_delim = start
    params.end_delim = end

    params.alias = st.text_input(
        "New Alias (Optional)", value=params.alias, key=f"ted_a_{step_id}")
    return params


def render_regex_tool(step_id: str, params: RegexToolParams, schema: Optional[pl.Schema]) -> RegexToolParams:
    current_cols = schema.names() if schema else []

    c1, c2 = st.columns(2)
    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"rt_c_{step_id}")
    action = c2.selectbox("Action", ["replace_all", "replace_one", "extract", "count", "contains"],
                          index=["replace_all", "replace_one", "extract",
                                 "count", "contains"].index(params.action),
                          key=f"rt_a_{step_id}")

    pat = st.text_input(
        "Regex Pattern", value=params.pattern, key=f"rt_p_{step_id}")

    # Conditional input for replacement
    replacement = params.replacement
    if action in ["replace_all", "replace_one"]:
        replacement = st.text_input(
            "Replacement Value", value=params.replacement, key=f"rt_r_{step_id}")

    params.col = col if col else ""
    # safe cast
    params.action = cast(Any, action)
    params.pattern = pat
    params.replacement = replacement

    params.alias = st.text_input(
        "New Alias (Optional)", value=params.alias, key=f"rt_al_{step_id}")
    return params


def render_normalize_spaces(step_id: str, params: NormalizeSpacesParams, schema: Optional[pl.Schema]) -> NormalizeSpacesParams:
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = st.selectbox("Column", current_cols,
                       index=col_idx, key=f"ns_c_{step_id}")
    params.col = col if col else ""

    params.alias = st.text_input(
        "New Alias (Optional)", value=params.alias, key=f"ns_a_{step_id}")
    return params


def render_smart_extract(step_id: str, params: SmartExtractParams, schema: Optional[pl.Schema]) -> SmartExtractParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"se_c_{step_id}")

    ptype = c2.selectbox("Extraction Type",
                         ["email_user", "email_domain",
                             "url_domain", "url_path", "ipv4"],
                         index=["email_user", "email_domain", "url_domain",
                                "url_path", "ipv4"].index(params.type),
                         key=f"se_t_{step_id}")

    params.col = col if col else ""
    params.type = cast(Any, ptype)

    params.alias = st.text_input(
        "New Alias (Optional)", value=params.alias, key=f"se_a_{step_id}")
    return params


def render_clean_text(step_id: str, params: CleanTextParams, schema: Optional[pl.Schema]) -> CleanTextParams:
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = st.selectbox("Column", current_cols,
                       index=col_idx, key=f"ct_c_{step_id}")
    params.col = col if col else ""

    c1, c2 = st.columns(2)
    params.lowercase = c1.checkbox(
        "Lowercase", value=params.lowercase, key=f"ct_lc_{step_id}")
    params.remove_punctuation = c2.checkbox(
        "Remove Punctuation", value=params.remove_punctuation, key=f"ct_rp_{step_id}")

    c3, c4 = st.columns(2)
    params.remove_digits = c3.checkbox(
        "Remove Digits", value=params.remove_digits, key=f"ct_rd_{step_id}")
    params.ascii_only = c4.checkbox(
        "ASCII Only", value=params.ascii_only, key=f"ct_ao_{step_id}")

    params.alias = st.text_input(
        "New Alias", value=params.alias, key=f"ct_a_{step_id}")
    return params


def render_mask_pii(step_id: str, params: MaskPIIParams, schema: Optional[pl.Schema]) -> MaskPIIParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"mp_c_{step_id}")
    params.col = col if col else ""

    type_options = ["email", "credit_card", "phone", "ssn", "ip", "custom"]
    idx = type_options.index(params.type) if params.type in type_options else 0

    ptype = c2.selectbox("PII Type", type_options,
                         index=idx, key=f"mp_t_{step_id}")
    params.type = cast(Any, ptype)

    params.mask_char = st.text_input(
        "Mask Character", value=params.mask_char, max_chars=1, key=f"mp_m_{step_id}")
    params.alias = st.text_input(
        "New Alias", value=params.alias, key=f"mp_a_{step_id}")
    return params


def render_auto_impute(step_id: str, params: AutoImputeParams, schema: Optional[pl.Schema]) -> AutoImputeParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"ai_c_{step_id}")
    params.col = col if col else ""

    strategies = ["mean", "median", "mode", "ffill", "bfill", "zero"]
    idx = strategies.index(
        params.strategy) if params.strategy in strategies else 0

    strat = c2.selectbox("Strategy", strategies,
                         index=idx, key=f"ai_s_{step_id}")
    params.strategy = cast(Any, strat)

    params.alias = st.text_input(
        "New Alias", value=params.alias, key=f"ai_a_{step_id}")
    return params


def render_check_bool(step_id: str, params: CheckBoolParams, schema: Optional[pl.Schema]) -> CheckBoolParams:
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    col = st.selectbox("Column", current_cols,
                       index=col_idx, key=f"cb_c_{step_id}")
    params.col = col if col else ""

    c1, c2 = st.columns(2)

    t_vals = c1.text_input("True Values (comma sep)", value=",".join(
        params.true_values), key=f"cb_t_{step_id}")
    f_vals = c2.text_input("False Values (comma sep)", value=",".join(
        params.false_values), key=f"cb_f_{step_id}")

    if t_vals:
        params.true_values = [x.strip()
                              for x in t_vals.split(",") if x.strip()]
    if f_vals:
        params.false_values = [x.strip()
                               for x in f_vals.split(",") if x.strip()]

    params.alias = st.text_input(
        "New Alias", value=params.alias, key=f"cb_a_{step_id}")
    return params
