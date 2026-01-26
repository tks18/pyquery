"""
Recipe Editor Component - Class-based transformation pipeline editor.

This module provides the recipe editor for building and managing
data transformation pipelines.
"""

from typing import Optional
import streamlit as st
import polars as pl
import time

from pyquery_polars.frontend.base import BaseComponent, AppContext
from pyquery_polars.frontend.utils.renderers import render_step_ui
from pyquery_polars.backend.processing.executor import apply_step as core_apply_step
from pyquery_polars.core.models import RecipeStep


class RecipeEditorComponent(BaseComponent):
    """
    Recipe editor component for transformation pipeline management.

    Displays:
    - Recipe overview
    - Step-by-step editor with expand/collapse
    - Live preview of transformations
    - Snapshot functionality
    """

    def __init__(self, ctx: AppContext) -> None:
        """Initialize with app context."""
        super().__init__(ctx)
        self.dataset_name: Optional[str] = None
        self.current_lf: Optional[pl.LazyFrame] = None
        self.current_schema: Optional[pl.Schema] = None

    def render(self, dataset_name: str) -> None:
        """
        Render the recipe editor for a dataset.

        Args:
            dataset_name: Name of the dataset being edited
        """
        if not dataset_name:
            st.info("Please select or import a dataset.")
            return

        self.dataset_name = dataset_name

        if not self.engine:
            st.error("System not initialized.")
            return

        # Initialize LazyFrame for schema tracking
        self.current_lf = self.engine.datasets.get(dataset_name)

        # Render sections
        self._render_recipe_overview()
        self._render_source_section()
        self._render_steps()

        st.divider()

        self._render_preview()
        self._render_snapshot()

    def _move_step_cb(self, index: int, direction: int) -> None:
        self.ctx.state_manager.move_step(index, direction)

    def _delete_step_cb(self, index: int) -> None:
        self.ctx.state_manager.delete_step(index)

    def _set_view_step(self, sid: str) -> None:
        """Toggle step preview view."""
        if self.state.view_at_step_id == sid:
            self.state.view_at_step_id = None
        else:
            self.state.view_at_step_id = sid

    def _set_view_raw(self) -> None:
        """Toggle raw source preview view."""
        if self.state.view_at_step_id == "__RAW_SOURCE__":
            self.state.view_at_step_id = None
        else:
            self.state.view_at_step_id = "__RAW_SOURCE__"

    def _render_recipe_overview(self) -> None:
        """Render the recipe overview expander."""
        if not self.state.recipe_steps:
            return

        with st.expander("🗺️ Recipe Overview", expanded=False):
            steps = self.state.recipe_steps

            for i, s in enumerate(steps):
                c_num, c_label = st.columns([0.08, 0.92])
                c_num.markdown(f"**{i+1}.**")
                c_label.markdown(f"`{s.type}` → {s.label}")

            st.caption(
                f"📊 Total: {len(steps)} step{'s' if len(steps) != 1 else ''}")

    def _render_source_section(self) -> None:
        """Render the source data section."""
        is_viewing_raw = self.state.view_at_step_id == "__RAW_SOURCE__"

        with st.expander("📄 Source Data", expanded=False):
            c_lbl, c_actions = st.columns([0.65, 0.35])
            with c_lbl:
                st.caption("Preview Original data before any transformations")

            with c_actions:
                btn_type_raw = "primary" if is_viewing_raw else "secondary"
                st.button("👁️ Preview", key="view_raw_source",
                          help="Inspect raw source data",
                          type=btn_type_raw, on_click=self._set_view_raw)

    def _render_steps(self) -> None:
        """Render all recipe steps."""
        for i, step in enumerate(self.state.recipe_steps):
            self._render_single_step(i, step)

    def _render_single_step(self, index: int, step: RecipeStep) -> None:
        """Render a single recipe step."""
        # Resolve schema for this step
        try:
            if self.current_lf is not None:
                self.current_schema = self.current_lf.collect_schema()
        except:
            pass

        step_type = step.type
        params = step.params
        step_id = step.id

        is_expanded = (step.id == self.state.last_added_id)
        label_display = f"#{index+1}: {step.label}"

        with st.expander(label_display, expanded=is_expanded):
            c_lbl, c_actions = st.columns([0.65, 0.35])
            with c_lbl:
                st.text_input(
                    "Label", value=step.label, key=f"lbl_{step.id}",
                    label_visibility="collapsed", placeholder="Step Name...")
                if self.state.has_value(f"lbl_{step.id}"):
                    step.label = self.state.get_value(f"lbl_{step.id}")

            with c_actions:
                b1, b2, b3, b4 = st.columns([1, 1, 1, 1])

                is_viewing = (self.state.view_at_step_id == step.id)
                btn_type = "primary" if is_viewing else "secondary"

                b1.button("👁️", key=f"vw{index}", help="Inspect Data at this step",
                          type=btn_type, on_click=self._set_view_step, args=(step.id,))

                # Use ctx.state_manager for step actions via wrappers to satisfy type checker (return None)
                b2.button("⬆️", key=f"u{index}", help="Move Up",
                          on_click=self._move_step_cb, args=(index, -1))
                b3.button("⬇️", key=f"d{index}", help="Move Down",
                          on_click=self._move_step_cb, args=(index, 1))
                b4.button("🗑️", key=f"x{index}", help="Delete Step",
                          type="primary", on_click=self._delete_step_cb, args=(index,))

            st.markdown("---")

            # Render UI via Registry Dispatch with CURRENT Step Schema
            updated_params = render_step_ui(
                step_type, step_id, params, self.current_schema, ctx=self.ctx)

            # Detect Change & Force Sync
            if updated_params != step.params:
                create_cp = True
                if self.state.just_added_step and step.id == self.state.last_added_id:
                    create_cp = False
                    self.state.just_added_step = False

                self.ctx.state_manager.update_step_params(step.id, updated_params,
                                                          create_checkpoint=create_cp)
                st.rerun()

        # Update state for next step
        if self.current_lf is not None:
            try:
                self.current_lf = core_apply_step(
                    self.current_lf, step, self.engine.datasets.get_context())
            except Exception as e:
                self.current_lf = None

    def _render_preview(self) -> None:
        """Render the live preview section."""
        target_steps = self.state.recipe_steps
        title_suffix = ""

        view_id = self.state.view_at_step_id
        if view_id:
            if view_id == "__RAW_SOURCE__":
                target_steps = []
                title_suffix = " (Raw Source)"
            else:
                idx = next((i for i, s in enumerate(
                    target_steps) if s.id == view_id), -1)
                if idx != -1:
                    target_steps = target_steps[:idx+1]
                    title_suffix = f" (Step #{idx+1})"
                else:
                    self.state.view_at_step_id = None

        st.subheader(f"📊 Live Preview (Top 1k){title_suffix}")

        if self.dataset_name:
            metadata = self.engine.datasets.get_metadata(self.dataset_name)

            if metadata:
                if metadata.process_individual:
                    file_count = len(
                        metadata.base_lfs) if metadata.base_lfs else 1
                    lf_count = len(
                        metadata.base_lfs) if metadata.base_lfs else 0

                    st.info(
                        f"📁 **Folder Mode** ({file_count} files, {lf_count} lazyframes): "
                        f"Preview shows **first file only**. Export will process all files individually.")

                try:
                    preview_df = self.engine.processing.get_preview(
                        metadata, target_steps, limit=1000)
                    if preview_df is not None:
                        st.dataframe(preview_df, width="stretch")
                        st.caption(
                            f"Shape: {preview_df.shape} (Rows shown are limited)")
                    else:
                        st.warning("No preview returned.")
                except Exception as e:
                    st.error(f"Pipeline Error: {e}")
            else:
                st.error(
                    f"Dataset '{self.dataset_name}' not found. It may have been unloaded.")

    def _render_snapshot(self) -> None:
        """Render the snapshot section."""
        with st.expander("📸 Snapshot Pipeline", expanded=False):
            st.caption("Save the current transformed state as a new dataset.")
            snap_name = st.text_input(
                "Snapshot Name", placeholder="e.g. clean_v1")

            if st.button("Save Snapshot", width="stretch",
                         disabled=not snap_name or not self.dataset_name):
                try:
                    if not self.dataset_name:
                        st.error("Dataset not selected")
                        return

                    with st.spinner("Snapshotting..."):
                        current_recipe = self.state.all_recipes.get(
                            self.dataset_name, [])

                        if self.engine.processing.materialize_dataset(
                            self.dataset_name,
                            snap_name,
                            recipe=current_recipe
                        ):
                            st.success(
                                f"Snapshot '{snap_name}' saved! It's now in your Datasets list.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Snapshot failed.")
                except Exception as e:
                    st.error(f"Error: {e}")
