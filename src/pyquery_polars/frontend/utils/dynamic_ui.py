import streamlit as st
from typing import List, Dict, Any
from pyquery_polars.core.models import IOSchemaField


def render_schema_fields(schema: List[IOSchemaField], key_prefix: str, columns: int = 1) -> Dict[str, Any]:
    """
    Renders Streamlit widgets based on a UI Schema list.
    Returns a dictionary of parameter values.
    """
    params = {}

    cols = st.columns(columns) if columns > 1 else None

    for i, field in enumerate(schema):
        if cols:
            col = cols[i % columns]
        else:
            col = st

        ftype = field.type
        flabel = field.label
        fname = field.name
        fdef = field.default
        fplace = field.placeholder

        # Unique Key Generation
        w_key = f"{key_prefix}_{fname}"

        val = None
        if ftype == "text":
            val = col.text_input(flabel, value=str(
                fdef), placeholder=fplace, key=w_key)
        elif ftype == "textarea":
            val = col.text_area(flabel, value=str(
                fdef), placeholder=fplace, key=w_key)
        elif ftype == "select":
            opts = field.options or []
            # Handle default index
            idx = 0
            if fdef in opts:
                idx = opts.index(fdef)
            val = col.selectbox(flabel, opts, index=idx, key=w_key)
        elif ftype == "number":
            val = col.number_input(flabel, value=float(
                fdef) if fdef else 0.0, key=w_key)
        elif ftype == "bool":
            val = col.checkbox(flabel, value=bool(fdef), key=w_key)

        params[fname] = val

    return params
