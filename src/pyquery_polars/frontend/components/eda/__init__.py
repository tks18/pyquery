from typing import Dict, cast, Optional

import streamlit as st
import pandas as pd
import polars as pl

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.frontend.components.editor import sql_editor

# Import Sub-Modules
from pyquery_polars.frontend.components.eda.core import EDAContext
from pyquery_polars.frontend.components.eda.overview import render_overview
from pyquery_polars.frontend.components.eda.ml import render_ml
from pyquery_polars.frontend.components.eda.simulation import render_simulation, render_target_analysis
from pyquery_polars.frontend.components.eda.plots import (
    render_time_series,
    render_distributions,
    render_hierarchy,
    render_relationships
)
from pyquery_polars.frontend.components.eda.contrast import render_contrast
from pyquery_polars.frontend.components.eda.profiling import render_profiling


def render_eda_tab(dataset_name: str):
    """
    Refactored EDA Dashboard with LazyContext and Per-Tab Buttons.
    Now supports Custom SQL Queries for data selection.
    """
    st.header("🔍 Exploratory Intelligence")

    if not dataset_name:
        st.info("👈 Please load a dataset from the sidebar to begin.")
        return

    # 1. GET ENGINE
    engine = cast(PyQueryEngine, st.session_state.get('engine'))
    if not engine:
        st.error("Engine not initialized.")
        return

    # 2. SETTINGS
    with st.expander("⚙️ Analysis Configuration", expanded=True):
        c1, c2, c3 = st.columns(3)
        # Interactive Row Limit
        limit = c1.number_input(
            "Row Limit / Sample Size",
            min_value=1000,
            max_value=100000,
            value=st.session_state.get('eda_sample_limit', 5000),
            step=1000,
            help="Max rows for EDA. Higher = slower.",
            key="eda_limit_input"
        )
        st.session_state.eda_sample_limit = limit

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

        show_labels = st.checkbox("Show Data Labels", value=st.session_state.get(
            'eda_show_labels', False), key="eda_show_labels_chk")
        st.session_state['eda_show_labels'] = show_labels

        if selected_strategy != "preview":
            st.warning(
                "⚠️ Full Processing Enabled: Reading entire dataset before limiting. This may be slow for large files.")

        # Context Info based on Strategy & Metadata
        metadata = engine.datasets.get_metadata(dataset_name)
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

        # New: Custom SQL
        st.divider()
        use_sql = st.checkbox("Use Custom SQL Query",
                              value=False, key="eda_use_sql")

        custom_sql = ""
        if use_sql:
            # 1. Schema Explorer (Requested Feature)
            with st.expander("📚 Schema Explorer (Tables & Columns)", expanded=False):
                tables = engine.datasets.list_names()
                if not tables:
                    st.warning("No datasets loaded.")
                else:
                    # Interactive Selector for cleaner UX
                    selected_table_schema = st.selectbox(
                        "Select Table to Inspect:", tables, key="eda_schema_table_selector")
                    if selected_table_schema:
                        try:
                            lf_temp = engine.datasets.get(
                                selected_table_schema)
                            if lf_temp is not None:
                                recipe_temp = engine.recipes.get(
                                    selected_table_schema)
                                schema = engine.processing.get_transformed_schema(
                                    lf_temp, recipe_temp)
                            else:
                                schema = None

                            if schema:
                                # Render as Dataframe for easy scanning/sorting
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

            # Use SQL Editor
            # Need to initialize state if not present to avoid reset on rerun
            if "eda_sql_query" not in st.session_state:
                st.session_state["eda_sql_query"] = default_query

            sql_res = sql_editor(
                code=st.session_state.get("eda_sql_query", default_query),
                key="eda_sql_editor",
                height=[7, 15]
            )

            if sql_res is not None:
                st.session_state["eda_sql_query"] = sql_res
                st.rerun()

            custom_sql = st.session_state.get("eda_sql_query", default_query)

        # Exclude Cols (Only show if NOT using SQL, or show generic?)
        # If using SQL, schema depends on query. We can't easily show columns before running it.
        # But we can try if user wants. For now, let's keep it simple: exclude applies AFTER SQL too.

        all_cols_display = []
        if not use_sql:
            try:
                # Metadata fetch for default path
                lf_temp = engine.datasets.get(dataset_name)
                recipe_temp = engine.recipes.get(dataset_name)
                if lf_temp is not None:
                    schema = engine.processing.get_transformed_schema(
                        lf_temp, recipe_temp)
                else:
                    schema = None
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

    # 3. PREPARE LAZY CONTEXT (No execution yet)
    try:
        lf_eda = None
        current_recipe = []

        if use_sql and custom_sql.strip():
            # SQL PATH - Integrate Strategy
            all_recipes = st.session_state.get('all_recipes', {})
            try:
                # Determine Collection Limit for optimization
                is_preview = (selected_strategy == "preview")
                coll_limit = None
                if selected_strategy == "full_head":
                    coll_limit = limit
                elif selected_strategy == "full_sample":
                    coll_limit = 100000

                lf_sql = engine.processing.execute_sql(
                    custom_sql,
                    preview=is_preview,
                    preview_limit=limit,
                    collection_limit=coll_limit
                )

                if lf_sql is None:
                    lf_eda = None
                elif selected_strategy == "full_sample":
                    # Full data, random sample
                    # Memory Optimization: Limit collection (Already happened at source via coll_limit)
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
                return
        else:
            # DEFAULT RECIPE PATH
            current_recipe = st.session_state.get(
                'all_recipes', {}).get(dataset_name, [])

            # Use new specialized EDA View getter
            # Must pass metadata
            meta = engine.datasets.get_metadata(dataset_name)
            if meta:
                lf_eda = engine.processing.get_eda_view(
                    meta=meta,
                    recipe=current_recipe,
                    strategy=selected_strategy,
                    limit=limit
                )

            if lf_eda is not None and excluded_cols:
                lf_eda = lf_eda.drop(excluded_cols)

        if lf_eda is None:
            return  # Blocked

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
        # Key components: Dataset, Applied Recipe, Limit, SQL (if used), Excluded Cols
        import hashlib
        import json

        # Helper to make recipe hashable
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

        # Include LazyFrame plan in fingerprint to detect reloaded data (different staging files)
        # str(lf_eda) usually contains the query plan or at least the scan paths
        plan_str = str(lf_eda)

        raw_key = f"{dataset_name}|{limit}|{recipe_str}|{sql_str}|{excl_str}|{plan_str}"
        fingerprint = hashlib.md5(raw_key.encode()).hexdigest()

        # Build Context
        ctx = EDAContext(
            lf=lf_eda,
            df=None,
            engine=engine,
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
        return

    # 4. RENDER TABS
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

    # Each module now responsible for its own execution via button
    with tab_overview:
        render_overview(ctx)

    with tab_profile:
        render_profiling(ctx)

    with tab_dist:
        render_distributions(ctx)

    with tab_target:
        render_target_analysis(ctx)

    with tab_rel:
        render_relationships(ctx)

    with tab_contrast:
        render_contrast(ctx)

    with tab_time:
        render_time_series(ctx)

    with tab_sim:
        render_simulation(ctx)

    with tab_ml:
        render_ml(ctx)

    with tab_hier:
        render_hierarchy(ctx)
