import streamlit as st
import polars as pl
from typing import cast
from pyquery_polars.frontend.state_manager import move_step, delete_step
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.utils.renderers import render_step_ui


def render_recipe_editor(dataset_name):
    if not dataset_name:
        st.info("Please select or import a dataset.")
        return

    if st.session_state.recipe_steps:
        with st.expander("🗺️ Recipe Overview", expanded=False):
            st.markdown(" ➝ ".join(
                [f"**{i+1}.** {s.label}" for i, s in enumerate(st.session_state.recipe_steps)]))

    engine = cast(PyQueryEngine, st.session_state.get('engine'))

    if not engine:
        st.error("System not initialized.")
        return

    # Use Engine to check active columns (Schema)
    base_schema = engine.get_dataset_schema(dataset_name)
    current_schema = base_schema

    # --- RECIPE UI LOOP ---
    for i, step in enumerate(st.session_state.recipe_steps):
        step_type = step.type
        params = step.params  # Generic Dict
        step_id = step.id

        is_expanded = (step.id == st.session_state.last_added_id)
        label_display = f"#{i+1}: {step.label}"

        with st.expander(label_display, expanded=is_expanded):
            c_lbl, c_actions = st.columns([0.65, 0.35])
            with c_lbl:
                st.text_input(
                    "Label", value=step.label, key=f"lbl_{step.id}", label_visibility="collapsed", placeholder="Step Name...")
                step.label = st.session_state[f"lbl_{step.id}"]

            with c_actions:
                b1, b2, b3 = st.columns(3)
                b1.button("⬆️", key=f"u{i}", help="Move Up",
                          on_click=move_step, args=(i, -1))
                b2.button("⬇️", key=f"d{i}", help="Move Down",
                          on_click=move_step, args=(i, 1))
                b3.button("🗑️", key=f"x{i}", help="Delete Step",
                          type="primary", on_click=delete_step, args=(i,))

            st.markdown("---")

            # Render UI via Registry Dispatch with CURRENT Step Schema
            updated_params = render_step_ui(
                step_type, step_id, params, current_schema)

            # Detect Change & Force Sync
            if updated_params != step.params:
                step.params = updated_params
                st.session_state.recipe_steps = st.session_state.recipe_steps
                active_ds = st.session_state.active_base_dataset
                if active_ds:
                    st.session_state.all_recipes[active_ds] = st.session_state.recipe_steps
                st.rerun()

        # --- PROAGATE SCHEMA FOR NEXT STEP ---
        # We simulate the step on a dummy Frame to get output schema
        if current_schema:
            try:
                # 1. Create Dummy LF with current schema
                schema_dict = dict(current_schema)
                dummy_lf = pl.LazyFrame([], schema=schema_dict)

                # 2. Apply Step (Engine handles Dict -> Pydantic conversion)
                next_lf = engine.apply_step(dummy_lf, step)

                # 3. Get New Schema
                current_schema = next_lf.collect_schema()
            except Exception as e:
                pass

    st.divider()
    st.subheader("📊 Live Preview (Top 1k)")

    try:
        preview_df = engine.get_preview(
            dataset_name, st.session_state.recipe_steps, limit=1000, project_recipes=st.session_state.all_recipes)
        if preview_df is not None:
            st.dataframe(preview_df, width="stretch")
            st.caption(f"Shape: {preview_df.shape} (Rows shown are limited)")
        else:
            st.warning("No preview returned.")
    except Exception as e:
        st.error(f"Pipeline Error: {e}")
