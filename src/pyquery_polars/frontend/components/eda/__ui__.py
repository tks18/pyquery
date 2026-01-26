"""
EDA Component - Exploratory Data Analysis Dashboard.

This module provides the main entry point for the EDA dashboard,
integrating various analysis tabs (overview, profiling, distributions, etc.).
"""
import streamlit as st
import pandas as pd
import polars as pl
import hashlib
import json

from pyquery_polars.frontend.base import BaseComponent
from pyquery_polars.frontend.elements import sql_editor

# Sub components
from pyquery_polars.frontend.components.eda.core import EDAContext
from pyquery_polars.frontend.components.eda.overview import OverviewTab
from pyquery_polars.frontend.components.eda.ml import MLTab
from pyquery_polars.frontend.components.eda.simulation import SimulationTab
from pyquery_polars.frontend.components.eda.plots import PlotsTab
from pyquery_polars.frontend.components.eda.contrast import ContrastTab
from pyquery_polars.frontend.components.eda.profiling import ProfilingTab


class EDAComponent(BaseComponent):
    """
    Exploratory Data Analysis (EDA) Component.

    Orchestrates the EDA dashboard, handling:
    - Data selection (Strategy / Custom SQL)
    - Context initialization (LazyFrame preparation)
    - Rendering of sub-tabs (Overview, Profiling, etc.)
    """

    def render(self, dataset_name: str) -> None:
        """
        Render the EDA Dashboard.

        Args:
            dataset_name: Name of the dataset to analyze
        """
        st.header("🔍 Exploratory Intelligence")

        if not dataset_name:
            st.info("👈 Please load a dataset from the sidebar to begin.")
            return

        if not self.engine:
            st.error("Engine not initialized.")
            return

        # 1. SETTINGS & CONFIGURATION
        with st.expander("⚙️ Analysis Configuration", expanded=True):
            c1, c2, c3 = st.columns(3)

            # Interactive Row Limit
            limit = c1.number_input(
                "Row Limit / Sample Size",
                min_value=1000,
                max_value=100000,
                value=self.state.eda_sample_limit,
                step=1000,
                help="Max rows for EDA. Higher = slower.",
                key="eda_limit_input"
            )
            self.state.eda_sample_limit = limit

            # Strategy Selector
            strat_map = {
                "⚡ Fast Preview (First File)": "preview",
                "📚 Full Dataset (First N)": "full_head",
                "🎲 Full Dataset (Random Sample)": "full_sample"
            }
            selected_strat_label = c2.selectbox(
                "Data Strategy",
                list(strat_map.keys()),
                index=0,
                key="eda_strategy_select",
                help="Choose how to fetch data. 'Full' modes process all files (slower)."
            )
            selected_strategy = strat_map[selected_strat_label]

            theme_options = ["plotly", "plotly_dark",
                             "seaborn", "ggplot2", "simple_white"]
            selected_theme = c3.selectbox(
                "Theme", theme_options, index=0, key="eda_theme")

            show_labels = st.checkbox(
                "Show Data Labels", value=self.state.eda_show_labels, key="eda_show_labels_chk")
            self.state.eda_show_labels = show_labels

            if selected_strategy != "preview":
                st.warning(
                    "⚠️ Full Processing Enabled: Reading entire dataset before limiting. This may be slow for large files.")

            # Context Info based on Strategy & Metadata
            self._render_strategy_info(dataset_name, selected_strategy, limit)

            # Custom SQL Section
            st.divider()
            use_sql = st.checkbox("Use Custom SQL Query",
                                  value=False, key="eda_use_sql")

            custom_sql = ""
            if use_sql:
                custom_sql = self._render_sql_section(dataset_name)

            # Column Exclusion
            all_cols_display = []
            if not use_sql:
                try:
                    lf_temp = self.engine.datasets.get(dataset_name)
                    recipe_temp = self.engine.recipes.get(dataset_name)
                    if lf_temp is not None:
                        schema = self.engine.processing.get_transformed_schema(
                            lf_temp, recipe_temp)
                        if schema:
                            all_cols_display = schema.names()
                except:
                    pass

            excluded_cols = st.multiselect(
                "🚫 Exclude Columns",
                options=all_cols_display,
                key="eda_exclude_cols",
                disabled=use_sql,
                help="Col exclusion disabled in SQL mode. Use SELECT to exclude columns." if use_sql else None
            )
            if not use_sql:
                st.caption(
                    "Settings affect all tabs. Press 'Generate' inside each tab to run analysis.")

        # 2. PREPARE CONTEXT (Lazy Execution)
        ctx = self._prepare_context(
            dataset_name=dataset_name,
            selected_strategy=selected_strategy,
            limit=limit,
            use_sql=use_sql,
            custom_sql=custom_sql,
            selected_theme=selected_theme,
            show_labels=show_labels,
            excluded_cols=excluded_cols
        )

        if not ctx:
            return  # Initialization failed or blocked

        # 3. RENDER TABS
        self._render_tabs(ctx)

    def _render_strategy_info(self, dataset_name, selected_strategy, limit):
        metadata = self.engine.datasets.get_metadata(dataset_name)
        process_individual = metadata.process_individual if metadata else False
        file_count = (len(metadata.base_lfs)
                      if metadata and metadata.base_lfs else 1)

        info_msgs = []
        if process_individual:
            if selected_strategy == "preview":
                info_msgs.append(
                    f"**Dataset Mode:** Folder ({file_count} files).")
                info_msgs.append(
                    f"**Generic Strategy:** Only the **First File** is analyzed (Limit: {limit}).")
            elif selected_strategy == "full_head":
                info_msgs.append(
                    f"**Dataset Mode:** Folder ({file_count} files).")
                info_msgs.append(
                    f"**Generic Strategy:** **ALL Files** are concatenated, then top {limit} rows are used.")
            elif selected_strategy == "full_sample":
                info_msgs.append(
                    f"**Dataset Mode:** Folder ({file_count} files).")
                info_msgs.append(
                    f"**Generic Strategy:** **ALL Files** are concatenated (up to 100k rows), then {limit} samples drawn.")
        else:
            # Single File Mode
            if selected_strategy == "preview":
                info_msgs.append(f"**Strategy:** Analyzing top {limit} rows.")
            elif selected_strategy == "full_head":
                info_msgs.append(f"**Strategy:** Analyzing top {limit} rows.")
            elif selected_strategy == "full_sample":
                info_msgs.append(
                    f"**Strategy:** Random sample of {limit} rows (from max 100k source).")

        st.info("\n\n".join(info_msgs))

    def _render_sql_section(self, dataset_name) -> str:
        # Schema Explorer
        with st.expander("📚 Schema Explorer (Tables & Columns)", expanded=False):
            tables = self.engine.datasets.list_names()
            if not tables:
                st.warning("No datasets loaded.")
            else:
                selected_table_schema = st.selectbox(
                    "Select Table to Inspect:", tables, key="eda_schema_table_selector")
                if selected_table_schema:
                    try:
                        lf_temp = self.engine.datasets.get(
                            selected_table_schema)
                        if lf_temp is not None:
                            recipe_temp = self.engine.recipes.get(
                                selected_table_schema)
                            schema = self.engine.processing.get_transformed_schema(
                                lf_temp, recipe_temp)

                            if schema:
                                schema_df = pd.DataFrame([
                                    {"Column": col, "Type": str(dtype)}
                                    for col, dtype in schema.items()
                                ])
                                st.dataframe(
                                    schema_df,
                                    height=200,
                                    hide_index=True,
                                    column_config={
                                        "Column": st.column_config.TextColumn("Column Name", width="medium"),
                                        "Type": st.column_config.TextColumn("Data Type", width="small"),
                                    }
                                )
                    except Exception as e:
                        st.warning(f"Could not load schema: {e}")

        st.caption(
            f"Write a SQL query to select data. The active dataset is available as **`{dataset_name}`**.")
        default_query = f"SELECT * FROM {dataset_name}"

        sql_res = sql_editor(
            code=self.state.eda_sql_query if self.state.eda_sql_query else default_query,
            key="eda_sql_editor",
            height=[7, 15],
            state=self.state
        )

        if sql_res is not None:
            self.state.eda_sql_query = sql_res
            st.rerun()

        return self.state.eda_sql_query if self.state.eda_sql_query else default_query

    def _prepare_context(self, dataset_name, selected_strategy, limit, use_sql, custom_sql, selected_theme, show_labels, excluded_cols):
        # Initialize meta to None to avoid UnboundLocalError
        meta = None
        try:
            lf_eda = None
            current_recipe = self.state.all_recipes.get(dataset_name, [])

            if use_sql and custom_sql.strip():
                # SQL PATH - Integrate Strategy
                try:
                    # Determine Collection Limit for optimization
                    is_preview = (selected_strategy == "preview")
                    coll_limit = None
                    if selected_strategy == "full_head":
                        coll_limit = limit
                    elif selected_strategy == "full_sample":
                        coll_limit = 100000

                    lf_sql = self.engine.processing.execute_sql(
                        custom_sql,
                        preview=is_preview,
                        preview_limit=limit,
                        collection_limit=coll_limit
                    )

                    if lf_sql is None:
                        lf_eda = None
                    elif selected_strategy == "full_sample":
                        # Full data, random sample
                        df = lf_sql.collect()
                        if len(df) <= limit:
                            lf_eda = df.lazy()
                        else:
                            lf_eda = df.sample(n=limit, seed=42).lazy()
                    else:
                        # full_head or preview (limit already applied at source)
                        lf_eda = lf_sql

                except Exception as e:
                    st.error(f"SQL Error: {e}")
                    return None
            else:
                # DEFAULT RECIPE PATH
                # Use new specialized EDA View getter
                meta = self.engine.datasets.get_metadata(dataset_name)
                if meta:
                    lf_eda = self.engine.processing.get_eda_view(
                        meta=meta,
                        recipe=current_recipe,
                        strategy=selected_strategy,
                        limit=limit
                    )

                if lf_eda is not None and excluded_cols:
                    lf_eda = lf_eda.drop(excluded_cols)

            if lf_eda is None:
                return None  # Blocked

            # Get Schema (Cheap) from the plan
            schema_final = lf_eda.collect_schema()
            final_cols = schema_final.names()

            # Heuristic type inference
            num_cols = [c for c, t in schema_final.items() if t.is_numeric()]
            cat_cols = [c for c, t in schema_final.items(
            ) if t == pl.String or t == pl.Categorical or t == pl.Boolean]
            date_cols = [c for c, t in schema_final.items()
                         if t in (pl.Date, pl.Datetime)]

            # Generate Cache Fingerprint
            def serialize(obj):
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                if hasattr(obj, 'dict'):
                    return obj.dict()
                return str(obj)

            recipe_str = json.dumps(
                current_recipe if not use_sql else "SQL_MODE", default=serialize)
            sql_str = custom_sql if use_sql else "NO_SQL"
            excl_str = ",".join(excluded_cols) if excluded_cols else "None"

            # Include LazyFrame plan AND Loader Params in fingerprint to detect subtle changes
            plan_str = str(lf_eda)

            # Loader Params from metadata (crucial for detecting changes like encoding/excel options)
            loader_params_str = "None"
            if meta and meta.loader_params:
                try:
                    loader_params_str = json.dumps(
                        meta.loader_params, default=str, sort_keys=True)
                except:
                    loader_params_str = str(meta.loader_params)

            raw_key = f"{dataset_name}|{limit}|{recipe_str}|{sql_str}|{excl_str}|{plan_str}|{loader_params_str}"
            fingerprint = hashlib.md5(raw_key.encode()).hexdigest()

            # Build Context
            return EDAContext(
                lf=lf_eda,
                df=None,
                engine=self.engine,
                state_manager=self.state,
                all_cols=final_cols,
                num_cols=num_cols,
                cat_cols=cat_cols,
                date_cols=date_cols,
                fingerprint=fingerprint,
                theme=selected_theme,
                show_labels=show_labels
            )

        except Exception as e:
            st.error(f"Context Initialization Error: {e}")
            return None

    def _render_tabs(self, ctx: EDAContext):
        tabs = st.tabs([
            "Overview",
            "Data Profiling",
            "Distributions",
            "Target Analysis",
            "Relationships",
            "Hierarchy",
            "Comparative",
            "Time Series",
            "Model Simulator",
            "Decision ML"
        ])

        (tab_overview, tab_profile, tab_dist, tab_target, tab_rel, tab_hier,
         tab_contrast, tab_time, tab_sim, tab_ml) = tabs

        with tab_overview:
            OverviewTab(ctx).render()

        with tab_profile:
            ProfilingTab(ctx).render()

        with tab_dist:
            PlotsTab(ctx).render_distributions()

        with tab_target:
            SimulationTab(ctx).render_target_analysis(ctx.get_pandas())

        with tab_rel:
            PlotsTab(ctx).render_relationships()

        with tab_contrast:
            ContrastTab(ctx).render()

        with tab_time:
            PlotsTab(ctx).render_time_series()

        with tab_sim:
            SimulationTab(ctx).render_simulator(ctx.get_pandas())

        with tab_ml:
            MLTab(ctx).render()

        with tab_hier:
            PlotsTab(ctx).render_hierarchy()
