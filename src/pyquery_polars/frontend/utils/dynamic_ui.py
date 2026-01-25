from typing import List, Dict, Any, Optional

import streamlit as st

from pyquery_polars.core.models import IOSchemaField


def render_schema_fields(schema: List[IOSchemaField], key_prefix: str, columns: int = 1,
                         override_options: Optional[Dict[str,
                                                         List[Any]]] = None,
                         on_change_handlers: Optional[Dict[str, Any]] = None,
                         exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Renders Streamlit widgets based on a UI Schema list.
    Returns a dictionary of parameter values.
    override_options: Dict mapping field names to list of options (forces selectbox)
    on_change_handlers: Dict mapping field names to callables (or None for simple st.rerun if implied)
    exclude: List of field names to skip rendering
    """
    params = {}

    cols = st.columns(columns) if columns > 1 else None

    for i, field in enumerate(schema):
        fname = field.name

        # EXCLUDE CHECK
        if exclude and fname in exclude:
            continue

        if cols:
            col = cols[i % columns]
        else:
            col = st

        ftype = field.type
        flabel = field.label
        fdef = field.default
        fplace = field.placeholder

        # Unique Key Generation
        w_key = f"{key_prefix}_{fname}"

        # OVERRIDE CHECK
        if override_options and fname in override_options:
            opts = override_options[fname]
            idx = 0
            if fdef in opts:
                idx = opts.index(fdef)
            val = col.selectbox(flabel, opts, index=idx, key=w_key)
            params[fname] = val
            continue

        # Change Handler
        on_change = None
        if on_change_handlers and fname in on_change_handlers:
            on_change = on_change_handlers[fname]

        val = None
        if ftype == "text":
            val = col.text_input(flabel, value=str(
                fdef), placeholder=fplace, key=w_key, on_change=on_change)
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
