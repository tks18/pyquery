import polars as pl
import ast
import math
import datetime
import numpy as np
import scipy
import sklearn
import statsmodels.api as sm
import re
import json
import random
import statistics
import collections
import itertools
from typing import Optional, Any
from pyquery_polars.core.models import TransformContext
from pyquery_polars.core.params import CustomScriptParams


class SecurityViolation(Exception):
    pass


def validate_script(script: str):
    """
    Parses the script using AST and ensures no unsafe imports or operations are used.
    Allowed: basic operations, assignments, function calls.
    Disallowed: import statements (except internal safe ones if we handled them, but here we block all imports for now),
    access to double underscores (except init maybe, but generally block __), etc.
    """
    try:
        tree = ast.parse(script)
    except SyntaxError as e:
        raise SecurityViolation(f"Syntax Error in script: {e}")

    for node in ast.walk(tree):
        # Block all imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SecurityViolation(
                "Imports are not allowed in custom scripts. Use the pre-imported modules available in the environment.")

        # Block accessing internal attributes like __dict__, __class__, etc.
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise SecurityViolation(
                    f"Accessing private attribute '{node.attr}' is not allowed.")


def custom_script_func(lf: pl.LazyFrame, params: CustomScriptParams, context: Optional[TransformContext] = None) -> pl.LazyFrame:
    script = params.script
    if not script.strip():
        return lf

    # 1. Validate
    validate_script(script)

    # 2. Prepare Execution Environment
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
        "enumerate": enumerate, "filter": filter, "float": float, "int": int,
        "len": len, "list": list, "map": map, "max": max, "min": min,
        "range": range, "round": round, "set": set, "sorted": sorted,
        "str": str, "sum": sum, "tuple": tuple, "zip": zip,
        "print": print
    }

    # Modules must be in global_env so functions defined in the script can access them
    global_env = {
        "__builtins__": safe_builtins,
        "pl": pl,
        "np": np,
        "datetime": datetime,
        "math": math,
        "scipy": scipy,
        "sklearn": sklearn,
        "sm": sm,
        "re": re,
        "json": json,
        "random": random,
        "statistics": statistics,
        "collections": collections,
        "itertools": itertools
    }

    local_env = {}

    try:
        exec(script, global_env, local_env)
    except Exception as e:
        raise RuntimeError(f"Error executing custom script: {e}")

    # 3. Retrieve and Execute 'pyquery_transform' function
    # We look for a function named 'pyquery_transform'
    if "pyquery_transform" in local_env and callable(local_env["pyquery_transform"]):
        transform_func = local_env["pyquery_transform"]
        try:
            # We pass the lf to the function
            new_lf = transform_func(lf)
        except Exception as e:
            raise RuntimeError(
                f"Error while executing 'pyquery_transform' function: {e}")
    else:
        # Fallback: Check if 'lf' was modified in place (backward compatibility or alternative style)
        new_lf = local_env.get("lf")
        if new_lf is None:
            raise ValueError(
                "Your script must define a function 'def pyquery_transform(lf): ... return lf'.")

    if not isinstance(new_lf, pl.LazyFrame):
        raise ValueError(
            "The 'pyquery_transform' function must return a Polars LazyFrame.")

    return new_lf
