"""
DatasetManager

Manages the storage and retrieval of datasets (LazyFrames + metadata).
"""
from typing import Any, Dict, List, Literal, Optional, Union

import polars as pl

from pyquery_polars.core.models import DatasetMetadata


class DatasetManager:
    """
    Manage dataset lifecycle (CRUD).

    This class handles:
    - Adding datasets with metadata
    - Removing datasets
    - Renaming datasets
    - Retrieving datasets and their metadata
    - Getting datasets for execution context
    """

    def __init__(self):
        self._datasets: Dict[str, DatasetMetadata] = {}
        self._sql_context = pl.SQLContext()

    def add(
        self,
        name: str,
        lf_or_lfs: Union[pl.LazyFrame, List[pl.LazyFrame]],
        metadata: Optional[Dict[str, Any]] = None,
        loader_type: Optional[Literal["File", "SQL", "API"]] = None,
        loader_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a dataset with comprehensive metadata."""
        if metadata is None:
            metadata = {}

        # Create DatasetMetadata object
        ds_meta = DatasetMetadata(
            source_path=metadata.get("source_path"),
            input_type=metadata.get("input_type", "file"),
            input_format=metadata.get("input_format"),
            process_individual=metadata.get("process_individual", False),
            file_list=metadata.get("file_list"),
            file_count=metadata.get("file_count", 1),
            loader_type=loader_type,
            loader_params=loader_params
        )

        # Handle LazyFrame vs List[LazyFrame]
        if isinstance(lf_or_lfs, list):
            ds_meta.base_lfs = lf_or_lfs
            # For SQL context, register concatenated view
            concat_lf = pl.concat(lf_or_lfs, how="diagonal")
            ds_meta.base_lf = None  # Don't store twice
        else:
            ds_meta.base_lf = lf_or_lfs
            ds_meta.base_lfs = None
            concat_lf = lf_or_lfs

        self._datasets[name] = ds_meta

        # Register with SQL context
        try:
            self._sql_context.register(name, concat_lf)
        except Exception as e:
            print(f"SQL Registration Warning: {e}")

    def remove(self, name: str) -> bool:
        """Remove a dataset by name."""
        if name in self._datasets:
            del self._datasets[name]
            try:
                self._sql_context.unregister(name)
            except:
                pass
            return True
        return False

    def rename(self, old_name: str, new_name: str) -> bool:
        """Rename a dataset, updating all references."""
        if old_name not in self._datasets or new_name in self._datasets:
            return False

        # Move metadata to new key
        self._datasets[new_name] = self._datasets.pop(old_name)

        # Update SQL context
        try:
            # Get the LazyFrame for re-registration
            meta = self._datasets[new_name]
            if meta.base_lf is not None:
                lf = meta.base_lf
            elif meta.base_lfs:
                lf = pl.concat(meta.base_lfs, how="diagonal")
            else:
                lf = None

            self._sql_context.unregister(old_name)
            if lf is not None:
                self._sql_context.register(new_name, lf)
        except Exception as e:
            print(f"SQL Context Rename Warning: {e}")

        return True

    def get(self, name: str) -> Optional[pl.LazyFrame]:
        """Get LazyFrame for preview (returns first file if process_individual)."""
        meta = self._datasets.get(name)
        if meta is None:
            return None

        # Return appropriate LazyFrame
        if meta.base_lf is not None:
            return meta.base_lf
        elif meta.base_lfs is not None and len(meta.base_lfs) > 0:
            # For preview with process_individual, return first file only
            return meta.base_lfs[0]

        return None

    def get_metadata(self, name: str) -> Optional[DatasetMetadata]:
        """Get the full DatasetMetadata object."""
        return self._datasets.get(name)

    def get_metadata_dict(self, name: str) -> Dict[str, Any]:
        """Get dataset metadata as dict (for frontend/API)."""
        meta = self._datasets.get(name)
        if meta is None:
            return {}

        # Calculate LF count
        lf_count = 0
        if meta.base_lfs:
            lf_count = len(meta.base_lfs)
        elif meta.base_lf is not None:
            lf_count = 1

        return {
            "source_path": meta.source_path,
            "input_type": meta.input_type,
            "input_format": meta.input_format,
            "process_individual": meta.process_individual,
            "file_list": meta.file_list,
            "file_count": meta.file_count,
            "lazyframe_count": lf_count,
            "loader_type": meta.loader_type,
            "loader_params": meta.loader_params
        }

    def list_names(self) -> List[str]:
        """Get list of all dataset names."""
        return list(self._datasets.keys())

    def clear_all(self) -> None:
        """Clear all datasets."""
        names = list(self._datasets.keys())
        for name in names:
            self.remove(name)

    def get_all_for_context(self) -> Dict[str, pl.LazyFrame]:
        """Get dict of dataset names to LazyFrames for execution context."""
        result = {}
        for name, meta in self._datasets.items():
            if meta.base_lf is not None:
                result[name] = meta.base_lf
            elif meta.base_lfs is not None and len(meta.base_lfs) > 0:
                # Use concatenated view
                result[name] = pl.concat(meta.base_lfs, how="diagonal")
        return result

    def get_context(self) -> Dict[str, pl.LazyFrame]:
        """Alias for get_all_for_context (for consistency)."""
        return self.get_all_for_context()

    def exists(self, name: str) -> bool:
        """Check if a dataset exists."""
        return name in self._datasets

    def __contains__(self, name: str) -> bool:
        """Support 'in' operator for dataset existence check."""
        return self.exists(name)

    def __iter__(self):
        """Iterate over dataset names."""
        return iter(self._datasets.keys())

    def items(self):
        """Iterate over (name, metadata) pairs."""
        return self._datasets.items()
