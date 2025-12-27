import streamlit as st
import polars as pl
import time
from typing import cast
from pyquery_polars.frontend.state_manager import move_step, delete_step, update_step_params
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
    
    # Callback for View Inspection
    def _set_view_step(sid):
        if st.session_state.get('view_at_step_id') == sid:
            st.session_state.view_at_step_id = None
        else:
            st.session_state.view_at_step_id = sid

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
                b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                
                is_viewing = (st.session_state.get("view_at_step_id") == step.id)
                btn_type = "primary" if is_viewing else "secondary"

                b1.button("👁️", key=f"vw{i}", help="Inspect Data at this step", 
                          type=btn_type, on_click=_set_view_step, args=(step.id,))
                
                b2.button("⬆️", key=f"u{i}", help="Move Up",
                          on_click=move_step, args=(i, -1))
                b3.button("⬇️", key=f"d{i}", help="Move Down",
                          on_click=move_step, args=(i, 1))
                b4.button("🗑️", key=f"x{i}", help="Delete Step",
                          type="primary", on_click=delete_step, args=(i,))

            st.markdown("---")

            # Render UI via Registry Dispatch with CURRENT Step Schema
            updated_params = render_step_ui(
                step_type, step_id, params, current_schema)

            # Detect Change & Force Sync
            if updated_params != step.params:
                create_cp = True
                if st.session_state.get("just_added_step") and step.id == st.session_state.last_added_id:
                    create_cp = False
                    st.session_state.just_added_step = False
                
                update_step_params(step.id, updated_params, create_checkpoint=create_cp)
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

    # Logic for Preview Slicing
    target_steps = st.session_state.recipe_steps
    title_suffix = ""
    
    view_id = st.session_state.get('view_at_step_id')
    if view_id:
        idx = next((i for i, s in enumerate(target_steps) if s.id == view_id), -1)
        if idx != -1:
            target_steps = target_steps[:idx+1]
            title_suffix = f" (Step #{idx+1})"
        else:
            st.session_state.view_at_step_id = None

    st.subheader(f"📊 Live Preview (Top 1k){title_suffix}")

    try:
        preview_df = engine.get_preview(
            dataset_name, target_steps, limit=1000, project_recipes=st.session_state.all_recipes)
        if preview_df is not None:
            st.dataframe(preview_df, width="stretch")
            st.caption(f"Shape: {preview_df.shape} (Rows shown are limited)")
        else:
            st.warning("No preview returned.")
    except Exception as e:
        st.error(f"Pipeline Error: {e}")

    st.divider()
    # Snapshot UI
    with st.expander("📸 Snapshot Pipeline", expanded=False):
         st.caption("Save the current transformed state as a new dataset.")
         snap_name = st.text_input("Snapshot Name", placeholder="e.g. clean_v1")
         
         if st.button("Save Snapshot", width="stretch", disabled=not snap_name or not dataset_name):
               try:
                   with st.spinner("Snapshoting..."):
                        # Get current recipe logic
                        current_recipe = st.session_state.all_recipes.get(dataset_name, [])
                        
                        # Get base LF
                        lf = engine.get_dataset(dataset_name)
                        if lf is not None:
                             # Apply transformations
                             transformed = engine.apply_recipe(
                                 lf, 
                                 current_recipe, 
                                 project_recipes=st.session_state.all_recipes
                             )
                             
                             # Materialize (ref = dataset_name)
                             if engine.materialize_dataset(snap_name, transformed, reference_name=dataset_name):
                                  st.success(f"Snapshot '{snap_name}' saved! It's now in your Datasets list.")
                                  time.sleep(1)
                                  st.rerun()
                             else:
                                  st.error("Snapshot failed.")
                        else:
                             st.error("Base dataset not found.")
               except Exception as e:
                   st.error(f"Error: {e}")
