"""
IOManager

Provides a unified interface for:
- File loading (CSV, Excel, Parquet, etc.)
- Path resolution (glob patterns, filters)
- Encoding detection and conversion
- Export operations
"""
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from pydantic import BaseModel

import polars as pl

from pyquery_polars.backend.io.helpers.staging import StagingManager
from pyquery_polars.core.io import FileFilter
from pyquery_polars.core.models import PluginDef
from pyquery_polars.backend.io.loaders import DEFAULT_LOADERS, BaseLoader, LoaderOutput
from pyquery_polars.backend.io.plugins import ALL_LOADERS, ALL_EXPORTERS
from pyquery_polars.backend.io.files import (
    resolve_file_paths,
    get_excel_sheet_names,
    get_excel_table_names,
    batch_detect_encodings,
    convert_file_to_utf8,
    get_staging_dir,
    create_unique_staging_folder,
    cleanup_staging_files,
    export_worker
)


class IOManager:
    """
    Manages all I/O operations.

    This class provides a unified interface for:
    - Loading data from files (CSV, Excel, Parquet, JSON, etc.)
    - Resolving file paths with glob patterns and filters
    - Detecting and converting file encodings
    - Managing staging directories
    - Export operations
    """

    def __init__(self):
        self._loaders: Dict[str, Type[BaseLoader]] = {}
        self._exporters: Dict[str, PluginDef] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default loaders and exporters."""
        for l in DEFAULT_LOADERS:
            self._loaders[l.name] = l
        for e in ALL_EXPORTERS:
            self._exporters[e.name] = e

    # ========== Staging Directory Access ==========

    def get_base_staging_dir(self) -> str:
        return get_staging_dir()

    def create_unique_staging_folder(self, base_name: str) -> str:
        return create_unique_staging_folder(base_name)

    # ========== Loader/Exporter Registry ==========

    def get_loaders(self) -> List[Type[BaseLoader]]:
        """Get list of available loaders."""
        return list(self._loaders.values())

    def get_exporters(self) -> List[PluginDef]:
        """Get list of available exporters."""
        return list(self._exporters.values())

    def get_exporter(self, name: str) -> Optional[PluginDef]:
        """Get an exporter by name."""
        return self._exporters.get(name)

    def get_loader(self, name: str) -> Optional[Type[BaseLoader]]:
        """Get a loader by name."""
        return self._loaders.get(name)

    # ========== File Loading ==========

    def run_loader(
        self,
        loader_name: str,
        params: Union[Dict[str, Any], BaseModel]
    ) -> Optional[LoaderOutput]:
        """
        Run a loader plugin to load data.

        Args:
            loader_name: Name of the loader (e.g., "File", "SQL", "API")
            params: Loader parameters

        Returns:
            Tuple of (LazyFrame(s), metadata_dict) or None on failure
        """
        loader_cls = self._loaders.get(loader_name)
        if not loader_cls:
            return None
        try:
            loader: BaseLoader = loader_cls(
                staging_manager=StagingManager(),
                params=params
            )

            return loader.run()

        except Exception as e:
            print(f"Loader Error: {e}")
            return None

    def load_file(
        self,
        path: str,
        **params
    ) -> Optional[LoaderOutput]:
        """
        Load a file using the default File loader.

        This is a convenience method that wraps run_loader with "File" loader.
        """
        params["path"] = path
        return self.run_loader("File", params)

    # ========== Path Resolution ==========

    def resolve_files(
        self,
        path: str,
        filters: Optional[List[FileFilter]] = None,
        limit: Optional[int] = None
    ) -> List[str]:
        """Resolve a file path with optional filters."""
        return resolve_file_paths(path, filters, limit)

    # ========== Excel Metadata ==========

    def get_sheet_names(self, file_path: str) -> List[str]:
        """Get sheet names from an Excel file."""
        return get_excel_sheet_names(file_path)

    def get_table_names(self, file_path: str) -> List[str]:
        """Get table names from an Excel file."""
        return get_excel_table_names(file_path)

    # ========== Encoding Operations ==========

    def scan_encodings(self, files: List[str]) -> Dict[str, str]:
        """Detect non-utf8 encodings in list of files."""
        return batch_detect_encodings(files)

    def convert_encoding(self, file_path: str, source_encoding: str) -> str:
        """Convert a file to UTF-8. Returns path to converted file."""
        return convert_file_to_utf8(file_path, source_encoding)

    # ========== Staging Directory ==========

    def cleanup_staging(self, max_age_hours: int = 24) -> None:
        """Clean up stale staging files."""
        cleanup_staging_files(max_age_hours)
