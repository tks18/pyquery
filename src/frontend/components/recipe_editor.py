import streamlit as st
from src.frontend.state_manager import move_step, delete_step

from src.frontend.renderers import RENDERER_MAP


def render_recipe_editor(dataset_name):  # Takes name, not LF
    if not dataset_name:
        st.info("Please select or import a dataset.")
        return

    if st.session_state.recipe_steps:
        with st.expander("🗺️ Recipe Overview", expanded=False):
            st.markdown(" ➝ ".join(
                [f"**{i+1}.** {s['label']}" for i, s in enumerate(st.session_state.recipe_steps)]))

    engine = st.session_state.get('engine')

    if not engine:
        st.error("System not initialized.")
        return

    base_schema = engine.get_dataset_schema(dataset_name)

    # --- RECIPE UI LOOP ---
    # We iterate steps to show UI controls. Params are updated in place in session_state.
    for i, step in enumerate(st.session_state.recipe_steps):
        step_type = step['type']
        params = step['params']
        step_id = step['id']

        renderer = RENDERER_MAP.get(step_type)
        if not renderer:
            st.error(f"Unknown step type: {step_type}")
            continue

        is_expanded = (step['id'] == st.session_state.last_added_id)
        label_display = f"#{i+1}: {step['label']}"

        with st.expander(label_display, expanded=is_expanded):
            # Clean Header Actions
            c_lbl, c_actions = st.columns([0.65, 0.35])
            with c_lbl:
                st.text_input(
                    "Label", value=step['label'], key=f"lbl_{step['id']}", label_visibility="collapsed", placeholder="Step Name...")
                # Sync immediately
                step['label'] = st.session_state[f"lbl_{step['id']}"]

            with c_actions:
                # Icon-only buttons with better spacing
                b1, b2, b3 = st.columns(3)
                b1.button("⬆️", key=f"u{i}", help="Move Up",
                          on_click=move_step, args=(i, -1))
                b2.button("⬇️", key=f"d{i}", help="Move Down",
                          on_click=move_step, args=(i, 1))
                b3.button("🗑️", key=f"x{i}", help="Delete Step",
                          type="primary", on_click=delete_step, args=(i,))

            st.markdown("---")

            # Render UI
            # We pass base_schema. Ideally we pass "current_schema" but that requires backend call.
            # Optimization: pass base_schema for now.
            step['params'] = renderer(step_id, params, base_schema)

    st.divider()
    st.subheader("📊 Live Preview (Top 50)")

    # --- ENGINE PREVIEW CALL ---
    try:
        # Engine handles all logic
        preview_df = engine.get_preview(
            dataset_name, st.session_state.recipe_steps, limit=50)
        if preview_df is not None:
            st.dataframe(preview_df, width="stretch")
            st.caption(f"Shape: {preview_df.shape} (Rows shown are limited)")
        else:
            st.warning("No preview returned.")
    except Exception as e:
        st.error(f"Pipeline Error: {e}")
