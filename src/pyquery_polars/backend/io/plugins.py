import os
from typing import Any, Dict, List, Optional, Union
import polars as pl

from pyquery_polars.backend.io.files import get_files_from_path, load_lazy_frame, load_from_sql, load_from_api, export_worker
from pyquery_polars.core.models import PluginDef
from pyquery_polars.core.io_params import (
    FileLoaderParams, SqlLoaderParams, ApiLoaderParams,
    ParquetExportParams, CsvExportParams, ExcelExportParams, JsonExportParams,
    IpcExportParams, NdjsonExportParams, SqliteExportParams
)


def loader_file_func(params: FileLoaderParams) -> Optional[tuple]:
    if not params.path:
        return None

    files = get_files_from_path(params.path)
    if not files:
        return None

    result = load_lazy_frame(files, params.sheet, params.process_individual)
    if result is None:
        return None

    lf_or_lfs, metadata = result

    # Enhance metadata with source_path
    source_path = os.path.dirname(os.path.abspath(files[0])) if files else None
    metadata["source_path"] = source_path

    return lf_or_lfs, metadata


LOADER_FILE = PluginDef(
    name="File",
    func=loader_file_func,
    params_model=FileLoaderParams
)


def loader_sql_func(params: SqlLoaderParams) -> Optional[tuple]:
    if not params.conn or not params.query:
        return None

    lf = load_from_sql(params.conn, params.query)
    return (lf, {}) if lf is not None else None


LOADER_SQL = PluginDef(
    name="SQL",
    func=loader_sql_func,
    params_model=SqlLoaderParams
)


def loader_api_func(params: ApiLoaderParams) -> Optional[tuple]:
    if not params.url:
        return None

    lf = load_from_api(params.url)
    return (lf, {}) if lf is not None else None


LOADER_API = PluginDef(
    name="API",
    func=loader_api_func,
    params_model=ApiLoaderParams
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
    params_model=ParquetExportParams
)

EXPORTER_CSV = PluginDef(
    name="CSV",
    func=lambda lf, p: exporter_generic_func(lf, p, "CSV"),
    params_model=CsvExportParams
)

EXPORTER_EXCEL = PluginDef(
    name="Excel",
    func=lambda lf, p: exporter_generic_func(lf, p, "Excel"),
    params_model=ExcelExportParams
)

EXPORTER_JSON = PluginDef(
    name="JSON",
    func=lambda lf, p: exporter_generic_func(lf, p, "JSON"),
    params_model=JsonExportParams
)

EXPORTER_IPC = PluginDef(
    name="Arrow IPC",
    func=lambda lf, p: exporter_generic_func(lf, p, "IPC"),
    params_model=IpcExportParams
)

EXPORTER_NDJSON = PluginDef(
    name="NDJSON",
    func=lambda lf, p: exporter_generic_func(lf, p, "NDJSON"),
    params_model=NdjsonExportParams
)

EXPORTER_SQLITE = PluginDef(
    name="SQLite",
    func=lambda lf, p: exporter_generic_func(lf, p, "SQLite"),
    params_model=SqliteExportParams
)

ALL_LOADERS = [LOADER_FILE, LOADER_SQL, LOADER_API]
ALL_EXPORTERS = [EXPORTER_PARQUET, EXPORTER_CSV, EXPORTER_EXCEL, EXPORTER_JSON,
                 EXPORTER_IPC, EXPORTER_NDJSON, EXPORTER_SQLITE]
