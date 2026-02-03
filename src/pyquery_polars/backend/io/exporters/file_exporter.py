from typing import Any, ClassVar, List, Literal, Optional, Type, Union
from pydantic import BaseModel, ConfigDict

import os
import polars as pl
import uuid
import gc

from pyquery_polars.backend.io.exporters.base import BaseExporter, ExporterOutput
from pyquery_polars.backend.io.loaders.base import BaseLoader, LoaderOutput
from pyquery_polars.backend.io.helpers import FilterEngine, ExcelEngine
from pyquery_polars.core.io import FileLoaderParams


class FileExporterInput(BaseModel):
    lazy_frame: Union[pl.LazyFrame, List[pl.LazyFrame]]
    params: Any
    fmt: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FileloaderOutput(BaseModel):
    input_type: Literal["file", "folder"]
    input_format: str
    file_list: list[str]
    file_count: int
    process_individual: bool
    source_info: bool
    clean_headers: bool


class FileExporter(BaseExporter[FileLoaderParams]):
    """
    Loads data from a local file or folder.
    Supports CSV, Excel, Parquet, JSON, NDJSON, IPC 
    """

    name = "File"
    input_model:  ClassVar[type[BaseModel]] = FileLoaderParams

    def clean_header_name(self, col: str) -> str:
        """Normalize column name by replacing whitespace with single spaces and stripping."""
        return " ".join(col.strip().split())

    def _run_impl(self) -> Optional[ExporterOutput]:
        """
        Load files into LazyFrame(s).

        Returns:
            FileloaderOutput: if successful returns the lf with metadata otherwise none
        """
