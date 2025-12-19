from typing import Any, Dict, List
import polars as pl
from src.backend.utils.io import get_files_from_path, load_lazy_frame, load_from_sql, load_from_api, export_worker

# --- LOADERS ---

def loader_file_func(params: Dict[str, Any]) -> pl.LazyFrame:
    path = params.get('path')
    sheet = params.get('sheet', 'Sheet1')
    files = get_files_from_path(path)
    if not files: return None
    return load_lazy_frame(files, sheet)

LOADER_FILE = {
    "name": "File",
    "func": loader_file_func,
    "ui_schema": [
        {"name": "path", "type": "text", "label": "Path / Glob", "placeholder": "data/*.csv"},
        {"name": "sheet", "type": "text", "label": "Sheet (Excel)", "default": "Sheet1"},
        {"name": "alias", "type": "text", "label": "Dataset Alias", "placeholder": "Transactions"}
    ]
}

def loader_sql_func(params: Dict[str, Any]) -> pl.LazyFrame:
    conn = params.get('conn')
    query = params.get('query')
    return load_from_sql(conn, query)

LOADER_SQL = {
    "name": "SQL",
    "func": loader_sql_func,
    "ui_schema": [
        {"name": "conn", "type": "text", "label": "Connection URI", "placeholder": "postgresql://..."},
        {"name": "query", "type": "textarea", "label": "Query / Table", "placeholder": "SELECT * FROM ..."},
        {"name": "alias", "type": "text", "label": "Dataset Alias", "placeholder": "SQL_Data"}
    ]
}

def loader_api_func(params: Dict[str, Any]) -> pl.LazyFrame:
    url = params.get('url')
    return load_from_api(url)

LOADER_API = {
    "name": "API",
    "func": loader_api_func,
    "ui_schema": [
        {"name": "url", "type": "text", "label": "API URL", "placeholder": "https://api..."},
        {"name": "alias", "type": "text", "label": "Dataset Alias", "placeholder": "API_Data"}
    ]
}

# --- EXPORTERS ---

def exporter_generic_func(lf: pl.LazyFrame, params: Dict[str, Any], fmt: str) -> Dict[str, Any]:
    path = params.get('path')
    compression = params.get('compression', 'snappy')
    res = {}
    export_worker(lf, path, fmt, compression, res)
    return res

EXPORTER_PARQUET = {
    "name": "Parquet",
    "func": lambda lf, p: exporter_generic_func(lf, p, "Parquet"),
    "ui_schema": [
        {"name": "path", "type": "text", "label": "Output Path", "default": "output.parquet"},
        {"name": "compression", "type": "select", "label": "Compression", "options": ["snappy", "zstd", "gzip"], "default": "snappy"}
    ]
}

EXPORTER_CSV = {
    "name": "CSV",
    "func": lambda lf, p: exporter_generic_func(lf, p, "CSV"),
    "ui_schema": [
        {"name": "path", "type": "text", "label": "Output Path", "default": "output.csv"}
    ]
}

EXPORTER_EXCEL = {
    "name": "Excel",
    "func": lambda lf, p: exporter_generic_func(lf, p, "Excel"),
    "ui_schema": [
        {"name": "path", "type": "text", "label": "Output Path", "default": "output.xlsx"}
    ]
}

EXPORTER_JSON = {
    "name": "JSON",
    "func": lambda lf, p: exporter_generic_func(lf, p, "JSON"),
    "ui_schema": [
        {"name": "path", "type": "text", "label": "Output Path", "default": "output.json"}
    ]
}

ALL_LOADERS = [LOADER_FILE, LOADER_SQL, LOADER_API]
ALL_EXPORTERS = [EXPORTER_PARQUET, EXPORTER_CSV, EXPORTER_EXCEL, EXPORTER_JSON]
