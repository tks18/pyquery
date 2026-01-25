from typing import List, Dict, Any, Optional

import streamlit as st

from pyquery_polars.backend import PyQueryEngine


@st.cache_data(show_spinner=False, ttl=60)
def get_cached_sheet_names(_engine: PyQueryEngine, path: str, last_modified: Optional[float] = None) -> List[str]:
    """
    Cached wrapper for get_file_sheet_names. 
    'last_modified' is an optional argument to force cache invalidation if file changes,
    though ttl=60 covers most intuitive cases.
    """
    return _engine.io.get_sheet_names(path)


@st.cache_data(show_spinner=False, ttl=60)
def get_cached_table_names(_engine: PyQueryEngine, path: str, last_modified: Optional[float] = None) -> List[str]:
    """
    Cached wrapper for get_file_table_names.
    """
    return _engine.io.get_table_names(path)


@st.cache_data(show_spinner=False, ttl=30)
def get_cached_resolved_files(_engine: PyQueryEngine, path: str, filters: List[Any], limit: int = 1000) -> List[str]:
    """
    Cached wrapper for resolve_files.
    We assume filters (List[FileFilter]) are Pydantic models which might hash okay,
    or we can rely on their string repr.
    """
    # Verify filters is list of FileFilter, make sure it hashes
    return _engine.io.resolve_files(path, filters, limit=limit)


@st.cache_data(show_spinner=False)
def get_cached_encoding_scan(_engine: PyQueryEngine, files: List[str]) -> Dict[str, str]:
    """
    Cached encoding scan. Very expensive operation, so good to cache.
    Depends on the list of file paths.
    """
    return _engine.io.scan_encodings(files)
