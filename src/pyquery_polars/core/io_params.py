from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# --- LOADERS ---


class FileLoaderParams(BaseModel):
    path: str
    sheet: str = "Sheet1"
    alias: str
    process_individual: bool = False  # Process files individually then concat


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


class CsvExportParams(BaseModel):
    path: str = "output.csv"


class ExcelExportParams(BaseModel):
    path: str = "output.xlsx"


class JsonExportParams(BaseModel):
    path: str = "output.json"


class IpcExportParams(BaseModel):
    path: str = "output.arrow"
    compression: Literal['uncompressed', 'lz4', 'zstd'] = "uncompressed"


class NdjsonExportParams(BaseModel):
    path: str = "output.jsonl"


class SqliteExportParams(BaseModel):
    path: str = "output.db"
    table: str = "data"
    if_exists: Literal['fail', 'replace', 'append'] = "replace"
