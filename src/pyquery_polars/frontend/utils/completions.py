from types import ModuleType
from typing import Dict, List

import inspect
import polars as pl
import numpy as np
import datetime
import math
import streamlit as st


def get_standard_pyquery_completions() -> List[Dict[str, str]]:
    """Returns the full set of standard completions for PyQuery Python editor."""
    completions = get_common_completions()

    # Generate dynamically but perhaps we should cache this result to avoid re-inspecting every render
    # Since this is a util, we rely on st.cache_data if used in a streamlit app context
    completions.extend(generate_module_completions(pl, "pl"))
    completions.extend(generate_module_completions(np, "np"))
    completions.extend(generate_module_completions(math, "math"))
    completions.extend(generate_module_completions(datetime, "datetime"))
    return completions


def get_sql_completions() -> List[Dict[str, str]]:
    """Returns standard SQL keywords and functions."""
    keywords = [
        "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
        "JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "INNER JOIN",
        "ON", "AS", "DISTINCT", "UNION", "ALL", "CASE", "WHEN", "THEN", "ELSE", "END",
        "CAST", "COALESCE", "NULL", "TRUE", "FALSE", "AND", "OR", "NOT", "IN", "IS", "LIKE"
    ]
    funcs = [
        "COUNT", "SUM", "AVG", "MIN", "MAX", "STDDEV", "VARIANCE",
        "ROUND", "CEIL", "FLOOR", "ABS", "SQRT", "POWER", "EXP", "LN", "LOG",
        "concat", "substring", "lower", "upper", "trim", "ltrim", "rtrim",
        "now", "date", "year", "month", "day", "hour", "minute", "second"
    ]

    comps = []
    for k in keywords:
        comps.append({"caption": k, "value": k,
                     "meta": "keyword", "name": "sql"})

    for f in funcs:
        comps.append({"caption": f, "value": f"{f}()",
                     "meta": "function", "name": "sql_func"})

    return comps


def generate_module_completions(module: ModuleType, alias_name: str) -> List[Dict[str, str]]:
    """
    Generates a list of completions for a given module.

    Args:
        module: The module object to inspect (e.g., polars, numpy).
        alias_name: The name the module is aliased as in the script (e.g., 'pl', 'np').

    Returns:
        List of dictionaries with 'caption', 'value', 'meta', 'name'.
    """
    completions = []

    for name, member in inspect.getmembers(module):
        if name.startswith("_"):
            continue

        # Determine type for meta tag
        meta = "attr"
        if inspect.isfunction(member) or inspect.isbuiltin(member) or inspect.ismethod(member):
            meta = "func"
        elif inspect.isclass(member):
            meta = "class"
        elif inspect.ismodule(member):
            meta = "module"

        # Value is what gets inserted
        value = name

        # Caption is just the name as requested (no signature)
        caption = name

        completions.append({
            "caption": caption,
            "value": value,
            "meta": meta,
            "name": f"{alias_name}.{name}"
        })

    return completions


def get_common_completions() -> List[Dict[str, str]]:
    """Returns a curated list of common completions/snippets."""
    return [
        {"caption": "lf", "value": "lf", "meta": "variable", "name": "lf"},
        {"caption": "pyquery_transform",
            "value": "pyquery_transform(lf)", "meta": "function", "name": "transform"},
        {"caption": "with_columns", "value": "with_columns()", "meta": "method",
         "name": "pl.Expr"},
        {"caption": "filter", "value": "filter()", "meta": "method",
         "name": "pl.Expr"},
        {"caption": "select", "value": "select()", "meta": "method",
         "name": "pl.Expr"},
        {"caption": "alias", "value": "alias()", "meta": "method",
         "name": "pl.Expr"},
        {"caption": "col", "value": "col()", "meta": "function", "name": "pl.col"},
        {"caption": "lit", "value": "lit()", "meta": "function", "name": "pl.lit"},
        {"caption": "when", "value": "when()", "meta": "function",
         "name": "pl.when"},
        {"caption": "then", "value": "then()", "meta": "function",
         "name": "pl.then"},
        {"caption": "otherwise", "value": "otherwise()", "meta": "function",
         "name": "pl.otherwise"},
    ]
