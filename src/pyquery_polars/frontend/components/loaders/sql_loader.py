import streamlit as st
from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.frontend.components.loaders.utils import handle_auto_inference


@st.dialog("SQL Connection", width="large")
def show_sql_loader(engine: PyQueryEngine):
    st.caption("Connect to SQL Databases via SQLAlchemy")

    loader_name = "SQL"

    # State for visibility
    if "show_loader_sql" not in st.session_state:
        st.session_state.show_loader_sql = False

    conn = st.text_input("Connection String",
                         placeholder="postgresql://user:pass@host:port/dbname", key="dlg_sql_conn")
    query = st.text_area("SQL Query", height=150,
                         placeholder="SELECT * FROM table_name LIMIT 1000", key="dlg_sql_query")

    alias_val = st.text_input(
        "Dataset Alias", value=f"sql_data_{len(st.session_state.all_recipes) + 1}", key="dlg_sql_alias")
    auto_infer = st.checkbox("✨ Auto Detect & Clean Types", value=False, key="dlg_sql_infer")

    c_cancel, c_submit = st.columns([0.3, 0.7])
    
    if c_cancel.button("Cancel", key=f"dlg_btn_{loader_name}_cancel"):
        st.session_state.show_loader_sql = False
        st.rerun()

    if c_submit.button("Execute Query", type="primary", width="stretch"):
        if not conn or not query:
            st.error("Connection string and query are required.")
            return

        params = {"conn": conn, "query": query, "alias": alias_val}

        with st.spinner("Executing query & loading..."):
            res = engine.run_loader("SQL", params)
            if res:
                lf_or_lfs, meta = res
                engine.add_dataset(alias_val, lf_or_lfs, meta)
                st.session_state.all_recipes[alias_val] = []
                st.session_state.active_base_dataset = alias_val
                st.session_state.recipe_steps = []

                if auto_infer:
                    handle_auto_inference(engine, alias_val)

                st.session_state.show_loader_sql = False
                st.rerun()
            else:
                st.error("SQL Load Failed.")
