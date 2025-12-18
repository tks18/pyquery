import streamlit as st
import json
from src.utils.io import get_files_from_path, load_lazy_frame, load_from_sql, load_from_api
from src.state_manager import add_step, load_recipe_from_json

def render_sidebar():
    with st.sidebar:
        st.title("⚡ Shan's PyQuery")

        st.header("1. Project Datasets")
        with st.expander("Import Dataset", expanded=True):
            tab_file, tab_sql, tab_api = st.tabs(["File", "SQL", "API"])
            
            with tab_file:
                f_path = st.text_input(
                    "Path / Glob", placeholder="data/sales.csv", key="fp_input")
                f_name_file = st.text_input(
                    "Dataset Alias", placeholder="e.g. Sales", key="fn_input_file")
                f_sheet = st.text_input("Sheet (Excel Only)", "Sheet1", key="fs_input")
                if st.button("Add File", type="primary"):
                    if f_path and f_name_file:
                        resolved = get_files_from_path(f_path)
                        lf = load_lazy_frame(resolved, f_sheet)
                        if lf is not None:
                            st.session_state.datasets[f_name_file] = lf
                            if len(st.session_state.datasets) == 1:
                                st.session_state.active_base_dataset = f_name_file
                            st.success(f"Added '{f_name_file}'")
                            st.rerun()
                        else:
                            st.error("Could not load file.")
                    else:
                        st.error("Path and Alias required.")

            with tab_sql:
                s_conn = st.text_input("Connection URI", placeholder="postgresql://user:pass@localhost:5432/db", key="sql_conn")
                s_query = st.text_area("SQL Query / Table", placeholder="SELECT * FROM sales", key="sql_query")
                f_name_sql = st.text_input("Dataset Alias", placeholder="e.g. Sales_SQL", key="fn_input_sql")
                if st.button("Add SQL", type="primary"):
                    if s_conn and s_query and f_name_sql:
                        lf = load_from_sql(s_conn, s_query)
                        if lf is not None:
                            st.session_state.datasets[f_name_sql] = lf
                            if len(st.session_state.datasets) == 1:
                                st.session_state.active_base_dataset = f_name_sql
                            st.success(f"Added '{f_name_sql}'")
                            st.rerun()
                        else:
                            st.error("Could not load SQL.")

            with tab_api:
                a_url = st.text_input("API URL", placeholder="https://api.example.com/data.json", key="api_url")
                f_name_api = st.text_input("Dataset Alias", placeholder="e.g. API_Data", key="fn_input_api")
                if st.button("Add API", type="primary"):
                    if a_url and f_name_api:
                        lf = load_from_api(a_url)
                        if lf is not None:
                            st.session_state.datasets[f_name_api] = lf
                            if len(st.session_state.datasets) == 1:
                                st.session_state.active_base_dataset = f_name_api
                            st.success(f"Added '{f_name_api}'")
                            st.rerun()
                        else:
                             st.error("Could not load API data.")

        if st.session_state.datasets:
            st.markdown("**Loaded Datasets:**")
            for name in list(st.session_state.datasets.keys()):
                c1, c2 = st.columns([0.8, 0.2])
                c1.caption(f"📄 {name}")
                if c2.button("🗑️", key=f"del_ds_{name}"):
                    del st.session_state.datasets[name]
                    if st.session_state.active_base_dataset == name:
                        st.session_state.active_base_dataset = None
                    st.rerun()

        st.divider()

        st.header("2. Transform")
        
        # Transformation Map: Display Name -> (Step Type, Default Label)
        transform_options = {
            "Select Columns": ("select_cols", "Select Columns"),
            "Drop Columns": ("drop_cols", "Remove Columns"),
            "Rename Column": ("rename_col", "Rename Column"),
            "Keep Specific (Finalize)": ("keep_cols", "Keep Specific Columns"),
            "Filter Rows": ("filter_rows", "Filter Group"),
            "Sort Rows": ("sort_rows", "Sort Order"),
            "Deduplicate": ("deduplicate", "Remove Duplicates"),
            "Sample Data": ("sample", "Random Sample"),
            "Clean / Cast Types": ("clean_cast", "Multi-Col Types"),
            "Add New Column": ("add_col", "Feature Eng."),
            "Join Dataset": ("join_dataset", "Merge Dataset"),
            "Group By (Aggregate)": ("aggregate", "Summarize Data"),
            "Window Function": ("window_func", "Rolling/Rank"),
            "Reshape (Pivot/Melt)": ("reshape", "Pivot/Unpivot")
        }
        
        selected_transform = st.selectbox("Choose Transformation", list(transform_options.keys()), key="transform_selector")
        
        if st.button("➕ Add Step", type="primary", use_container_width=True):
            step_type, default_label = transform_options[selected_transform]
            add_step(step_type, default_label)

        st.divider()
        st.header("3. Recipe")
        recipe_json = json.dumps(st.session_state.recipe_steps, indent=2)
        st.download_button("💾 Save", recipe_json,
                           "recipe.json", "application/json")
        uploaded_recipe = st.file_uploader("📂 Load", type=["json"])
        if uploaded_recipe and st.button("Apply"):
            load_recipe_from_json(uploaded_recipe)
            st.rerun()
        if st.button("🗑️ Reset"):
            st.session_state.recipe_steps = []
            st.rerun()
