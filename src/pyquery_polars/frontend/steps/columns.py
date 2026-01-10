import streamlit as st
import polars as pl
from typing import Optional, cast
from pyquery_polars.core.params import (
    CastChange, SelectColsParams, DropColsParams, RenameColParams,
    KeepColsParams, AddColParams, CleanCastParams, PromoteHeaderParams,
    SplitColParams, CombineColsParams, AddRowNumberParams,
    ExplodeParams, CoalesceParams, OneHotEncodeParams
)


def render_select_cols(step_id: str, params: SelectColsParams, schema: Optional[pl.Schema]) -> SelectColsParams:
    current_cols = schema.names() if schema else []
    default = [c for c in params.cols if c in current_cols]
    selected = st.multiselect(
        "Select columns:", current_cols, default=default, key=f"sel_{step_id}")
    params.cols = selected
    return params


def render_drop_cols(step_id: str, params: DropColsParams, schema: Optional[pl.Schema]) -> DropColsParams:
    current_cols = schema.names() if schema else []
    default = [c for c in params.cols if c in current_cols]
    dropped = st.multiselect(
        "Select columns to remove:", current_cols, default=default, key=f"drp_{step_id}")
    params.cols = dropped
    return params


def render_keep_cols(step_id: str, params: KeepColsParams, schema: Optional[pl.Schema]) -> KeepColsParams:
    current_cols = schema.names() if schema else []
    default = [c for c in params.cols if c in current_cols]
    kept = st.multiselect(
        "Keep ONLY these columns:", current_cols, default=default, key=f"kp_{step_id}")
    params.cols = kept
    return params


def render_rename_col(step_id: str, params: RenameColParams, schema: Optional[pl.Schema]) -> RenameColParams:
    current_cols = schema.names() if schema else []
    c1, c2 = st.columns(2)

    # params.old is a string
    old_col_val = params.old if params.old in current_cols else (
        current_cols[0] if current_cols else None)

    try:
        idx = current_cols.index(old_col_val) if old_col_val else 0
    except ValueError:
        idx = 0

    target = c1.selectbox("Old Name", current_cols,
                          index=idx, key=f"rn_o_{step_id}")
    new_name = c2.text_input(
        "New Name", value=params.new, key=f"rn_n_{step_id}")

    params.old = target
    params.new = new_name
    return params


def render_add_col(step_id: str, params: AddColParams, schema: Optional[pl.Schema]) -> AddColParams:
    c1, c2 = st.columns([1, 2])

    def _update_cb():
        # Fetch current values from widget state
        new_name = st.session_state.get(f"fe_n_{step_id}", "")
        new_expr = st.session_state.get(f"fe_e_{step_id}", "1")

        # Update param model
        from pyquery_polars.frontend.state_manager import update_step_params
        # Create fresh dict
        p_dict = {"name": new_name, "expr": new_expr}
        update_step_params(step_id, p_dict)

    new_col = c1.text_input(
        "New Col Name", value=params.name, key=f"fe_n_{step_id}", on_change=_update_cb)
    expr_str = c2.text_input(
        "Polars Expression", value=params.expr, key=f"fe_e_{step_id}", on_change=_update_cb)

    params.name = new_col if new_col else ""
    params.expr = expr_str if expr_str else "1"
    return params


def render_clean_cast(step_id: str, params: CleanCastParams, schema: Optional[pl.Schema]) -> CleanCastParams:
    current_cols = schema.names() if schema else []

    # --- AUTO DETECT SECTION ---
    res_key = f"ad_res_{step_id}"

    # Auto-expand if we have results pending
    with st.expander("✨ Auto Detect Types", expanded=(res_key in st.session_state)):

        # TYPE MAP
        TYPE_ACTION_MAP = {
            "Int64": "To Int",
            "Float64": "To Float",
            "Date": "To Date",
            "Datetime": "To Datetime",
            "Boolean": "To Boolean"
        }

        if res_key not in st.session_state:
            # --- PHASE 1: SELECTION ---
            c_ad1, c_ad2 = st.columns([0.7, 0.3])
            ad_cols = c_ad1.multiselect(
                "Inspect Columns", current_cols, default=[], key=f"ad_c_{step_id}")
            sample_sz = c_ad2.number_input(
                "Sample Size", 100, 1000, 500, step=50, key=f"ad_sz_{step_id}")

            if st.button("🔍 Analyze", key=f"btn_ad_{step_id}", help="Infer types from sample data"):
                from pyquery_polars.backend.engine import PyQueryEngine
                engine = cast(PyQueryEngine, st.session_state.get('engine'))
                active_ds = st.session_state.get("active_base_dataset")
                steps = st.session_state.get("recipe_steps", [])

                # Slice recipe up to this step
                partial_recipe = []
                for s in steps:
                    if s.id == step_id:
                        break
                    partial_recipe.append(s)

                if engine and active_ds:
                    with st.spinner("Analyzing..."):
                        inferred = engine.infer_types(
                            active_ds,
                            partial_recipe,
                            project_recipes=st.session_state.get(
                                "all_recipes"),
                            columns=ad_cols,
                            sample_size=sample_sz
                        )

                    if inferred:
                        st.session_state[res_key] = inferred
                        st.rerun()
                    else:
                        st.warning("No new types detected.")

        else:
            # --- PHASE 2: PROPOSAL ---
            inferred = st.session_state[res_key]

            st.info(
                f"⚡ Detected **{len(inferred)}** potential changes. Review and edit before applying:")

            # Full Action Options
            ALL_CAST_ACTIONS = [
                "To String",
                "To Int", "To Int (Robust)",
                "To Float", "To Float (Robust)",
                "To Boolean",
                "To Date", "To Date (Robust)", "To Date (Format)",
                "To Datetime", "To Datetime (Robust)", "To Datetime (Format)",
                "To Time", "To Time (Robust)", "To Time (Format)",
                "To Duration",
                "Trim Whitespace", "Standardize NULLs",
                "Fix Excel Serial Date", "Fix Excel Serial Datetime", "Fix Excel Serial Time"
            ]

            # Prepare Preview Data
            preview_data = []
            for col, dtype in inferred.items():
                action = TYPE_ACTION_MAP.get(dtype, "Unknown")
                preview_data.append(
                    {"Column": col, "Detected": dtype, "Proposed Action": action})

            # Editable Dataframe
            edited_data = st.data_editor(
                preview_data,
                column_config={
                    "Column": st.column_config.TextColumn("Column", disabled=True),
                    "Detected": st.column_config.TextColumn("Detected Type", disabled=True),
                    "Proposed Action": st.column_config.SelectboxColumn(
                        "Action",
                        options=ALL_CAST_ACTIONS,
                        required=True,
                        width="large"
                    )
                },
                width="stretch",
                hide_index=True,
                key=f"ad_editor_{step_id}"
            )

            c_yes, c_no = st.columns([1, 1])

            if c_yes.button("✅ Confirm & Apply", type="primary", key=f"ad_y_{step_id}"):
                new_changes = []

                # Parse Edited Data
                # Fallback to handle List[Dict] or DataFrame
                rows = edited_data if isinstance(
                    edited_data, list) else edited_data.to_dict('records')

                for row in rows:
                    col = row.get("Column")
                    action = row.get("Proposed Action")

                    if col and action and action != "Unknown":
                        new_changes.append(CastChange(col=col, action=action))

                # Merge logic
                changing_cols = {c.col for c in new_changes}
                kept_changes = [
                    c for c in params.changes if c.col not in changing_cols]
                params.changes = kept_changes + new_changes

                # Cleanup
                del st.session_state[res_key]
                st.success("Applied!")
                # Rerun implicitly via return params

            if c_no.button("❌ Discard", key=f"ad_n_{step_id}"):
                del st.session_state[res_key]
                st.rerun()

    # Params initialized with default_factory list, so params.changes exists

    # Render active changes
    if params.changes:
        for idx, change in enumerate(params.changes):
            c_txt, c_btn = st.columns([0.9, 0.1])
            with c_txt:
                st.text(f"• {change.col} ➝ {change.action}")
            with c_btn:
                def _del_cc_cb(idx_to_remove=idx):
                    from pyquery_polars.frontend.state_manager import get_active_recipe, update_step_params
                    steps = get_active_recipe()
                    target = next((s for s in steps if s.id == step_id), None)
                    if target:
                        try:
                            p = CleanCastParams(**target.params)
                            if 0 <= idx_to_remove < len(p.changes):
                                p.changes.pop(idx_to_remove)
                                update_step_params(step_id, p.model_dump())
                        except:
                            pass

                st.button("x", key=f"del_{step_id}_{idx}", on_click=_del_cc_cb)

    c1, c2, c3 = st.columns([2, 2, 1])
    target_cols = c1.multiselect(
        "Columns", current_cols, key=f"cc_c_{step_id}")
    action = c2.selectbox("Action", [
        "To String",
        "To Int", "To Int (Robust)",
        "To Float", "To Float (Robust)",
        "To Boolean",
        "To Date", "To Date (Robust)", "To Date (Format)",
        "To Datetime", "To Datetime (Robust)", "To Datetime (Format)",
        "To Time", "To Time (Robust)", "To Time (Format)",
        "To Duration",
        "Trim Whitespace", "Standardize NULLs",
        "Fix Excel Serial Date", "Fix Excel Serial Datetime", "Fix Excel Serial Time"
    ], key=f"cc_a_{step_id}")

    custom_fmt = None
    if action and "(Format)" in action:
        custom_fmt = st.text_input(
            "Format String (e.g. %d/%m/%Y)", key=f"cc_f_{step_id}")

    def _add_cc_cb():
        t_cols = st.session_state.get(f"cc_c_{step_id}")
        act = st.session_state.get(f"cc_a_{step_id}")
        fmt = st.session_state.get(f"cc_f_{step_id}")

        if t_cols and act:
            from pyquery_polars.frontend.state_manager import get_active_recipe, update_step_params
            steps = get_active_recipe()
            target = next((s for s in steps if s.id == step_id), None)
            if target:
                try:
                    p = CleanCastParams(**target.params)
                except:
                    p = CleanCastParams()

                for col in t_cols:
                    p.changes.append(CastChange(
                        col=col, action=act, fmt=fmt if fmt else None))

                update_step_params(step_id, p.model_dump())

    c3.button("Add", key=f"add_{step_id}", on_click=_add_cc_cb)

    return params


def render_promote_header(step_id: str, params: PromoteHeaderParams, schema: Optional[pl.Schema]) -> PromoteHeaderParams:
    st.info("ℹ️ This step will take the **first row** of the dataset, use its values as column headers, and then remove that row.")
    return params


def render_split_col(step_id: str, params: SplitColParams, schema: Optional[pl.Schema]) -> SplitColParams:
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    c1, c2, c3 = st.columns(3)
    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"sp_c_{step_id}")
    pat = c2.text_input("Delimiter", value=params.pat, key=f"sp_p_{step_id}")
    n = c3.number_input("Max Splits", min_value=1,
                        value=params.n, key=f"sp_n_{step_id}")

    params.col = col
    params.pat = pat
    params.n = int(n)
    return params


def render_combine_cols(step_id: str, params: CombineColsParams, schema: Optional[pl.Schema]) -> CombineColsParams:
    current_cols = schema.names() if schema else []
    default_cols = [c for c in params.cols if c in current_cols]

    cols = st.multiselect("Columns", current_cols,
                          default=default_cols, key=f"cb_c_{step_id}")

    c1, c2 = st.columns(2)
    sep = c1.text_input("Separator", value=params.separator,
                        key=f"cb_s_{step_id}")
    name = c2.text_input("New Name", value=params.new_name,
                         key=f"cb_n_{step_id}")

    params.cols = cols
    params.separator = sep
    params.new_name = name
    return params


def render_add_row_number(step_id: str, params: AddRowNumberParams, schema: Optional[pl.Schema]) -> AddRowNumberParams:
    name = st.text_input("Index Column Name",
                         value=params.name, key=f"rn_n_{step_id}")
    params.name = name
    return params


def render_explode(step_id: str, params: ExplodeParams, schema: Optional[pl.Schema]) -> ExplodeParams:
    current_cols = schema.names() if schema else []

    default_cols = [c for c in params.cols if c in current_cols]
    cols = st.multiselect("Columns to Explode (List)", current_cols,
                          default=default_cols, key=f"ex_c_{step_id}")

    params.cols = cols
    return params


def render_coalesce(step_id: str, params: CoalesceParams, schema: Optional[pl.Schema]) -> CoalesceParams:
    current_cols = schema.names() if schema else []
    default_cols = [c for c in params.cols if c in current_cols]

    st.caption("Select columns in priority order (first non-null value is taken).")
    cols = st.multiselect("Columns", current_cols,
                          default=default_cols, key=f"cl_c_{step_id}")
    new_name = st.text_input(
        "New Name", value=params.new_name, key=f"cl_n_{step_id}")

    params.cols = cols
    params.new_name = new_name
    return params


def render_one_hot_encode(step_id: str, params: OneHotEncodeParams, schema: Optional[pl.Schema]) -> OneHotEncodeParams:
    st.info("ℹ️ Converts categorical column into multiple binary columns (0/1). Uses unique values found in data.")
    current_cols = schema.names() if schema else []

    col_idx = 0
    if params.col in current_cols:
        col_idx = current_cols.index(params.col)

    c1, c2, c3 = st.columns(3)
    col = c1.selectbox("Column", current_cols,
                       index=col_idx, key=f"ohe_c_{step_id}")

    prefix = c2.text_input("Prefix (Optional)", value=params.prefix,
                           placeholder=col, key=f"ohe_p_{step_id}")

    sep = c3.text_input("Separator", value=params.separator,
                        key=f"ohe_s_{step_id}")

    params.col = col if col else ""
    params.prefix = prefix
    params.separator = sep
    return params
