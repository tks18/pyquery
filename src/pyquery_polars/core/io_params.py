from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# --- LOADERS ---


class FileLoaderParams(BaseModel):
    path: str
    sheet: Union[str, List[str]] = "Sheet1"
    alias: str
    process_individual: bool = False  # Process files individually then concat
    include_source_info: bool = False  # Add source metadata columns


class SqlLoaderParams(BaseModel):
    conn: str
    query: str
    alias: str


class ApiLoaderParams(BaseModel):
    url: str
    alias: str

# --- EXPORTERS ---


class ParquetExportParams(BaseModel):
    path: str = "output.parquet"
    compression: Literal['snappy', 'zstd', 'gzip',
                         'lz4', 'uncompressed', 'brotli'] = "snappy"
    export_individual: bool = False


class CsvExportParams(BaseModel):
    path: str = "output.csv"
    export_individual: bool = False


class ExcelExportParams(BaseModel):
    path: str = "output.xlsx"
    export_individual: bool = False


class JsonExportParams(BaseModel):
    path: str = "output.json"
    export_individual: bool = False


class IpcExportParams(BaseModel):
    path: str = "output.arrow"
    compression: Literal['uncompressed', 'lz4', 'zstd'] = "uncompressed"
    export_individual: bool = False


class NdjsonExportParams(BaseModel):
    path: str = "output.jsonl"
    export_individual: bool = False


class SqliteExportParams(BaseModel):
    path: str = "output.db"
    table: str = "data"
    if_exists: Literal['fail', 'replace', 'append'] = "replace"
