from typing import List, Literal, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

# --- LOADERS ---


class FilterType(str, Enum):
    GLOB = "glob"
    REGEX = "regex"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EXACT = "exact"  # is
    IS_NOT = "is_not"


class FileFilter(BaseModel):
    type: FilterType
    value: str
    target: Literal["filename", "path"] = "filename"


class ItemFilter(BaseModel):
    type: FilterType
    value: str
    target: Literal["sheet_name"] = "sheet_name"


class FileLoaderParams(BaseModel):
    path: str
    filters: Optional[List[FileFilter]] = None
    sheet_filters: Optional[List[ItemFilter]] = None  # Dynamic Sheet Filtering
    table_filters: Optional[List[ItemFilter]] = None  # Dynamic Table Filtering
    sheet: Optional[Union[str, List[str]]] = "Sheet1"
    table: Optional[Union[str, List[str]]] = None
    alias: str
    process_individual: bool = False  # Process files individually then concat
    include_source_info: bool = False  # Add source metadata columns
    files: Optional[List[str]] = None  # Explicit file list override
    clean_headers: bool = False  # Sanitize column names


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
