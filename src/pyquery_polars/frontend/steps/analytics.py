import streamlit as st
import polars as pl
from typing import Optional
from pyquery_polars.core.params import (
    TimeBinParams, RollingAggParams, NumericBinParams, MathOpParams, DateExtractParams,
    CumulativeParams, RankParams, DiffParams, ZScoreParams, SkewKurtParams
)


def render_time_bin(step_id: str, params: TimeBinParams, schema: Optional[pl.Schema]) -> TimeBinParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Timestamp Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"tb_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Timestamp Column", value=params.col, key=f"tb_c_{step_id}")

    params.interval = c2.text_input(
        "Interval (e.g. 1h, 1d, 15m)", value=params.interval, key=f"tb_i_{step_id}")
    return params


def render_rolling_agg(step_id: str, params: RollingAggParams, schema: Optional[pl.Schema]) -> RollingAggParams:
    current_cols = schema.names() if schema else []
    col_val = params.target if params.target in current_cols else (
        current_cols[0] if current_cols else "")

    if current_cols:
        params.target = st.selectbox("Target Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"ra_t_{step_id}")
    else:
        params.target = st.text_input(
            "Target Column", value=params.target, key=f"ra_t_{step_id}")

    c1, c2, c3 = st.columns(3)
    params.window_size = c1.number_input(
        "Window Size", value=params.window_size, min_value=1, key=f"ra_w_{step_id}")
    params.op = c2.selectbox("Agg Op", ["mean", "sum", "min", "max", "std"],
                             index=["mean", "sum", "min", "max", "std"].index(params.op), key=f"ra_o_{step_id}")
    params.center = c3.checkbox(
        "Center Window", value=params.center, key=f"ra_c_{step_id}")
    return params


def render_numeric_bin(step_id: str, params: NumericBinParams, schema: Optional[pl.Schema]) -> NumericBinParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"nb_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"nb_c_{step_id}")

    params.bins = c2.number_input(
        "Bin Count", value=params.bins, min_value=2, key=f"nb_b_{step_id}")
    return params


def render_math_op(step_id: str, params: MathOpParams, schema: Optional[pl.Schema]) -> MathOpParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"mo_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"mo_c_{step_id}")

    params.op = c2.selectbox("Operation", ["round", "abs", "ceil", "floor", "sqrt"],
                             index=["round", "abs", "ceil", "floor", "sqrt"].index(params.op), key=f"mo_o_{step_id}")
    if params.op == "round":
        params.precision = st.slider(
            "Precision", 0, 10, value=params.precision, key=f"mo_p_{step_id}")

    params.alias = st.text_input("Output Name (Optional)", value=params.alias,
                                 key=f"mo_a_{step_id}", help="Leave empty to overwrite")
    return params


def render_date_extract(step_id: str, params: DateExtractParams, schema: Optional[pl.Schema]) -> DateExtractParams:
    c1, c2 = st.columns(2)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Date Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"de_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Date Column", value=params.col, key=f"de_c_{step_id}")

    params.part = c2.selectbox("Extract Part", ["year", "month", "day", "hour", "minute", "second", "weekday"],
                               index=["year", "month", "day", "hour", "minute", "second", "weekday"].index(params.part), key=f"de_p_{step_id}")

    params.alias = st.text_input("Output Name (Optional)", value=params.alias,
                                 key=f"de_a_{step_id}", help="Leave empty to overwrite")
    return params


def render_cumulative(step_id: str, params: CumulativeParams, schema: Optional[pl.Schema]) -> CumulativeParams:
    c1, c2, c3 = st.columns(3)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"cu_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"cu_c_{step_id}")

    params.op = c2.selectbox("Operation", ["cumsum", "cummin", "cummax", "cumprod"],
                             index=["cumsum", "cummin", "cummax", "cumprod"].index(params.op), key=f"cu_o_{step_id}")

    params.reverse = c3.checkbox(
        "Reverse Order", value=params.reverse, key=f"cu_r_{step_id}")

    params.alias = st.text_input(
        "New Alias", value=params.alias, key=f"cu_a_{step_id}")
    return params


def render_rank(step_id: str, params: RankParams, schema: Optional[pl.Schema]) -> RankParams:
    c1, c2, c3 = st.columns(3)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"rk_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"rk_c_{step_id}")

    params.method = c2.selectbox("Method", ["average", "min", "max", "dense", "ordinal", "random"],
                                 index=["average", "min", "max", "dense", "ordinal", "random"].index(params.method), key=f"rk_m_{step_id}")

    params.descending = c3.checkbox(
        "Descending", value=params.descending, key=f"rk_d_{step_id}")

    params.alias = st.text_input(
        "New Alias", value=params.alias, key=f"rk_a_{step_id}")
    return params


def render_diff(step_id: str, params: DiffParams, schema: Optional[pl.Schema]) -> DiffParams:
    c1, c2, c3 = st.columns(3)
    current_cols = schema.names() if schema else []
    col_val = params.col if params.col in current_cols else (
        current_cols[0] if current_cols else "")
    if current_cols:
        params.col = c1.selectbox("Column", current_cols, index=current_cols.index(
            col_val) if col_val in current_cols else 0, key=f"df_c_{step_id}")
    else:
        params.col = c1.text_input(
            "Column", value=params.col, key=f"df_c_{step_id}")

    params.method = c2.selectbox("Operation", ["diff", "pct_change"],
                                 index=["diff", "pct_change"].index(params.method), key=f"df_m_{step_id}")

    params.n = c3.number_input(
        "Periods", value=params.n, min_value=1, key=f"df_n_{step_id}")

    params.alias = st.text_input(
        "New Alias", value=params.alias, key=f"df_a_{step_id}")
    return params


def render_z_score(step_id: str, params: ZScoreParams, schema: Optional[pl.Schema]) -> ZScoreParams:
    current_cols = schema.names() if schema else []

    c1, c2 = st.columns(2)
    # Col
    idx = current_cols.index(params.col) if params.col in current_cols else 0
    params.col = c1.selectbox(
        "Target Column", current_cols, index=idx, key=f"zs_c_{step_id}")

    # By
    params.by = c2.multiselect(
        "Group By (Optional)", current_cols, default=params.by, key=f"zs_b_{step_id}")

    params.alias = st.text_input(
        "New Alias (Optional)", value=params.alias, key=f"zs_a_{step_id}")
    return params


def render_skew_kurt(step_id: str, params: SkewKurtParams, schema: Optional[pl.Schema]) -> SkewKurtParams:
    current_cols = schema.names() if schema else []

    c1, c2 = st.columns(2)
    idx = current_cols.index(params.col) if params.col in current_cols else 0
    params.col = c1.selectbox(
        "Target Column", current_cols, index=idx, key=f"sk_c_{step_id}")

    params.measure = c2.selectbox("Measure", ["skew", "kurtosis"],
                                  index=0 if params.measure == "skew" else 1, key=f"sk_m_{step_id}")

    params.alias = st.text_input(
        "New Alias (Optional)", value=params.alias, key=f"sk_a_{step_id}")
    return params
