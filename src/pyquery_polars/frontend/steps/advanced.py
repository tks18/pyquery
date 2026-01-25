from typing import Any, Optional

import streamlit as st
import polars as pl
import numpy as np
import datetime
import math

from pyquery_polars.core.params import CustomScriptParams
from pyquery_polars.frontend.components.editor import python_editor
from pyquery_polars.frontend.utils.completions import generate_module_completions, get_common_completions


def render_custom_script(step_id: str, params: CustomScriptParams, schema: Optional[pl.Schema] = None) -> CustomScriptParams:
    st.markdown("### Custom Python Script")

    st.warning("⚠️ **Security Warning**: Standard security protocols are active. External imports (os, sys) are blocked. Use the provided modules.")

    with st.expander("Available Variables & Modules", expanded=True):
        st.markdown("""
        **Instructions**:
        Define a function named `pyquery_transform(lf)` that takes the LazyFrame as input and returns a modified LazyFrame.
        
        - **Input**: `lf` (LazyFrame)
        - **Modules**: `pl` (polars), `np` (numpy), `scipy`, `sklearn`, `sm` (statsmodels), `math`, `datetime`, `re`, `json`, `collections`, `itertools`, `random`, `statistics`
        """)

    with st.expander("Import Script", expanded=False):
        uploaded_file = st.file_uploader("Upload .py file", type=[
                                         "py"], key=f"{step_id}_upload")
        if uploaded_file is not None:
            if st.button("Load File Content", key=f"{step_id}_load_file"):
                string_data = uploaded_file.getvalue().decode("utf-8")
                params.script = string_data
                st.rerun()

    # Generate rich completions dynamically
    # Use st.cache_data/resource probably better but for now direct generation (it's fast enough for these libs)
    @st.cache_data
    def get_all_completions():
        all_comps = get_common_completions()
        all_comps.extend(generate_module_completions(pl, "pl"))
        all_comps.extend(generate_module_completions(np, "np"))
        all_comps.extend(generate_module_completions(math, "math"))
        all_comps.extend(generate_module_completions(datetime, "datetime"))
        return all_comps

    completions = get_all_completions()

    # Use reusable component
    new_code = python_editor(
        code=params.script,
        key=f"{step_id}_editor",
        height=[10, 20],
        completions=completions
    )

    if new_code is not None:
        params.script = new_code
        st.success("Script updated successfully!")
        return params

    return params
