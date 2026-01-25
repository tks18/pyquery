from typing import Optional, Any, cast

import streamlit as st
import polars as pl

from pyquery_polars.core.params import (
    MathSciParams, ClipParams, DateOffsetParams, DateDiffParams
)


def render_math_sci(step_id: str, params: MathSciParams, schema: Optional[pl.Schema]) -> MathSciParams:
    c1, c2, c3 = st.columns(3)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"ms_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"ms_c_{step_id}")

    ops = ["log", "log10", "exp", "pow", "sqrt", "cbrt", "mod",
           "sin", "cos", "tan", "arcsin", "arccos", "arctan",
           "degrees", "radians", "sign"]

    try:
        idx = ops.index(params.op)
    except:
        idx = 0

    # safe cast for literal
    params.op = cast(Any, c2.selectbox(
        "Operation", ops, index=idx, key=f"ms_o_{step_id}"))

    if params.op in ["pow", "mod"]:
        params.arg = c3.number_input(
            "Arg (Power/Mod)", value=params.arg, key=f"ms_a_{step_id}")

    return params


def render_clip(step_id: str, params: ClipParams, schema: Optional[pl.Schema]) -> ClipParams:
    c1, c2, c3 = st.columns(3)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"cl_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"cl_c_{step_id}")

    c2_chk = c2.checkbox("Min", value=(
        params.min_val is not None), key=f"cl_mn_c_{step_id}")
    if c2_chk:
        val = params.min_val if params.min_val is not None else 0.0
        params.min_val = c2.number_input(
            "Min Value", value=val, key=f"cl_mn_v_{step_id}")
    else:
        params.min_val = None

    c3_chk = c3.checkbox("Max", value=(
        params.max_val is not None), key=f"cl_mx_c_{step_id}")
    if c3_chk:
        val = params.max_val if params.max_val is not None else 100.0
        params.max_val = c3.number_input(
            "Max Value", value=val, key=f"cl_mx_v_{step_id}")
    else:
        params.max_val = None

    return params


def render_date_offset(step_id: str, params: DateOffsetParams, schema: Optional[pl.Schema]) -> DateOffsetParams:
    c1, c2, c3 = st.columns(3)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Date Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"do_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Date Column", value=params.col, key=f"do_c_{step_id}")

    params.action = c2.selectbox("Action", ["add", "sub"], index=[
                                 "add", "sub"].index(params.action), key=f"do_a_{step_id}")
    params.offset = c3.text_input(
        "Offset (e.g. 1d, 2h)", value=params.offset, key=f"do_o_{step_id}")
    return params


def render_date_diff(step_id: str, params: DateDiffParams, schema: Optional[pl.Schema]) -> DateDiffParams:
    c1, c2, c3 = st.columns(3)
    current_cols = schema.names() if schema else []

    start_val = params.start_col if params.start_col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.start_col = c1.selectbox("Start Date", current_cols, index=current_cols.index(
            start_val) if start_val in current_cols else 0, key=f"dd_s_{step_id}")
    else:
        params.start_col = c1.text_input(
            "Start Date", value=params.start_col, key=f"dd_s_{step_id}")

    end_val = params.end_col if params.end_col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.end_col = c2.selectbox("End Date", current_cols, index=current_cols.index(
            end_val) if end_val in current_cols else 0, key=f"dd_e_{step_id}")
    else:
        params.end_col = c2.text_input(
            "End Date", value=params.end_col, key=f"dd_e_{step_id}")

    params.unit = c3.selectbox("Unit", ["days", "hours", "minutes", "seconds"], index=["days", "hours", "minutes", "seconds"].index(
        params.unit) if params.unit in ["days", "hours", "minutes", "seconds"] else 0, key=f"dd_u_{step_id}")

    params.alias = st.text_input(
        "Alias", value=params.alias, key=f"dd_a_{step_id}")
    return params
