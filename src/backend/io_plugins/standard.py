from typing import Any, Dict, List, Optional, Union
import polars as pl
from src.backend.utils.io import get_files_from_path, load_lazy_frame, load_from_sql, load_from_api, export_worker
from src.core.models import PluginDef, IOSchemaField
from src.core.io_params import (
    FileLoaderParams, SqlLoaderParams, ApiLoaderParams,
    ParquetExportParams, CsvExportParams, ExcelExportParams, JsonExportParams,
    IpcExportParams, NdjsonExportParams, SqliteExportParams
)

# --- LOADERS ---


def loader_file_func(params: FileLoaderParams) -> Optional[pl.LazyFrame]:
    if not params.path:
        return None

    files = get_files_from_path(params.path)
    if not files:
        return None
    return load_lazy_frame(files, params.sheet)


LOADER_FILE = PluginDef(
    name="File",
    func=loader_file_func,
    params_model=FileLoaderParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="Path / Glob", placeholder="data/*.csv"),
        IOSchemaField(name="sheet", type="text",
                      label="Sheet (Excel)", default="Sheet1"),
        IOSchemaField(name="alias", type="text",
                      label="Dataset Alias", placeholder="Transactions")
    ]
)


def loader_sql_func(params: SqlLoaderParams) -> Optional[pl.LazyFrame]:
    if not params.conn or not params.query:
        return None

    return load_from_sql(params.conn, params.query)


LOADER_SQL = PluginDef(
    name="SQL",
    func=loader_sql_func,
    params_model=SqlLoaderParams,
    ui_schema=[
        IOSchemaField(name="conn", type="text",
                      label="Connection URI", placeholder="postgresql://..."),
        IOSchemaField(name="query", type="textarea",
                      label="Query / Table", placeholder="SELECT * FROM ..."),
        IOSchemaField(name="alias", type="text",
                      label="Dataset Alias", placeholder="SQL_Data")
    ]
)


def loader_api_func(params: ApiLoaderParams) -> Optional[pl.LazyFrame]:
    if not params.url:
        return None

    return load_from_api(params.url)


LOADER_API = PluginDef(
    name="API",
    func=loader_api_func,
    params_model=ApiLoaderParams,
    ui_schema=[
        IOSchemaField(name="url", type="text", label="API URL",
                      placeholder="https://api..."),
        IOSchemaField(name="alias", type="text",
                      label="Dataset Alias", placeholder="API_Data")
    ]
)


# --- EXPORTERS ---


def exporter_generic_func(lf: pl.LazyFrame, params: Any, fmt: str) -> Dict[str, Any]:
    # params is a Pydantic Model (ParquetExportParams, etc.)
    # All have .path
    path = getattr(params, 'path', '')

    res = {}
    if not path:
        res['status'] = "Error: Path is empty"
        return res

    # CORRECTED CALL: Pass params object, not individual fields
    export_worker(lf, params, fmt, res)
    return res


EXPORTER_PARQUET = PluginDef(
    name="Parquet",
    func=lambda lf, p: exporter_generic_func(lf, p, "Parquet"),
    params_model=ParquetExportParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.parquet"),
        IOSchemaField(name="compression", type="select", label="Compression", options=[
                      'snappy', 'zstd', 'gzip', 'lz4', 'uncompressed', 'brotli'], default="snappy")
    ]
)

EXPORTER_CSV = PluginDef(
    name="CSV",
    func=lambda lf, p: exporter_generic_func(lf, p, "CSV"),
    params_model=CsvExportParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.csv")
    ]
)

EXPORTER_EXCEL = PluginDef(
    name="Excel",
    func=lambda lf, p: exporter_generic_func(lf, p, "Excel"),
    params_model=ExcelExportParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.xlsx")
    ]
)

EXPORTER_JSON = PluginDef(
    name="JSON",
    func=lambda lf, p: exporter_generic_func(lf, p, "JSON"),
    params_model=JsonExportParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.json")
    ]
)

EXPORTER_IPC = PluginDef(
    name="Arrow IPC",
    func=lambda lf, p: exporter_generic_func(lf, p, "IPC"),
    params_model=IpcExportParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.arrow"),
        IOSchemaField(name="compression", type="select", label="Compression", options=[
                      'uncompressed', 'lz4', 'zstd'], default="uncompressed")
    ]
)

EXPORTER_NDJSON = PluginDef(
    name="NDJSON",
    func=lambda lf, p: exporter_generic_func(lf, p, "NDJSON"),
    params_model=NdjsonExportParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.jsonl")
    ]
)

EXPORTER_SQLITE = PluginDef(
    name="SQLite",
    func=lambda lf, p: exporter_generic_func(lf, p, "SQLite"),
    params_model=SqliteExportParams,
    ui_schema=[
        IOSchemaField(name="path", type="text",
                      label="DB Path", default="output.db"),
        IOSchemaField(name="table", type="text",
                      label="Table Name", default="data"),
        IOSchemaField(name="if_exists", type="select", label="If Exists", options=[
                      'fail', 'replace', 'append'], default="replace")
    ]
)

ALL_LOADERS = [LOADER_FILE, LOADER_SQL, LOADER_API]
ALL_EXPORTERS = [EXPORTER_PARQUET, EXPORTER_CSV, EXPORTER_EXCEL, EXPORTER_JSON,
                 EXPORTER_IPC, EXPORTER_NDJSON, EXPORTER_SQLITE]
