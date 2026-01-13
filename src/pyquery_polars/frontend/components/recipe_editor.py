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
    # Strategy: We maintain a running LazyFrame state to propagate schema correctly
    # even for data-dependent steps like "Promote Headers".
    current_lf = engine.get_dataset(dataset_name)
    current_schema = None
    
    # Callback for View Inspection
    def _set_view_step(sid):
        if st.session_state.get('view_at_step_id') == sid:
            st.session_state.view_at_step_id = None
        else:
            st.session_state.view_at_step_id = sid

    # --- RECIPE UI LOOP ---
    for i, step in enumerate(st.session_state.recipe_steps):
        # 1. Resolve Schema for THIS step
        try:
            if current_lf is not None:
                current_schema = current_lf.collect_schema()
        except:
            # Fallback if pipeline broke previously
            pass

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

        # --- UPDATE STATE FOR NEXT STEP ---
        if current_lf is not None:
            try:
                # Apply this step to the running LF
                # We use internal engine logic which handles params conversion
                current_lf = engine.apply_step(current_lf, step)
            except Exception as e:
                # If step fails (e.g. invalid params while typing), we invalidate LF
                # This prevents cascading errors but stops schema propagation
                current_lf = None

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
    
    # Show indicator if processing individually
    if dataset_name:
        metadata = engine.get_dataset_metadata(dataset_name)
        if metadata.get("process_individual", False):
            file_count = metadata.get("file_count", 1)
            lf_count = metadata.get("lazyframe_count", 0)
            
            st.info(
                f"📁 **Folder Mode** ({file_count} files, {lf_count} lazyframes): Preview shows **first file only**. "
                f"Export will process all files individually."
            )

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

    # Snapshot UI
    with st.expander("📸 Snapshot Pipeline", expanded=False):
         st.caption("Save the current transformed state as a new dataset.")
         snap_name = st.text_input("Snapshot Name", placeholder="e.g. clean_v1")
         
         if st.button("Save Snapshot", width="stretch", disabled=not snap_name or not dataset_name):
               try:
                   with st.spinner("Snapshotting..."):
                        # Get current recipe
                        current_recipe = st.session_state.all_recipes.get(dataset_name, [])
                         
                        # Materialize with recipe (backend handles everything)
                        if engine.materialize_dataset(
                            dataset_name, 
                            snap_name, 
                            recipe=current_recipe,
                            project_recipes=st.session_state.all_recipes
                        ):
                            st.success(f"Snapshot '{snap_name}' saved! It's now in your Datasets list.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Snapshot failed.")
               except Exception as e:
                   st.error(f"Error: {e}")
