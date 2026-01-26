"""
Configuration constants for file loader.
"""

from pyquery_polars.core.io import FilterType

# Map UI strings to Backend Enum
FILTER_TYPE_MAP = {
    "contains": FilterType.CONTAINS,
    "regex": FilterType.REGEX,
    "exact": FilterType.EXACT,
    "glob": FilterType.GLOB,
    "not_contains": FilterType.NOT_CONTAINS,
    "is_not": FilterType.IS_NOT
}

# Reverse mapping for pattern dropdown
PATTERN_REVERSE_MAP = {
    "*.csv": "CSV (*.csv)",
    "*.xlsx": "Excel (*.xlsx)",
    "*.parquet": "Parquet (*.parquet)",
    "*.json": "JSON (*.json)",
    "*": "All Supported Files (*)",
}

# Default Pattern Map
PATTERNS = {
    "CSV (*.csv)": "*.csv",
    "Excel (*.xlsx)": "*.xlsx",
    "Parquet (*.parquet)": "*.parquet",
    "JSON (*.json)": "*.json",
    "All Supported Files (*)": "*",
    "Custom": "custom"
}
