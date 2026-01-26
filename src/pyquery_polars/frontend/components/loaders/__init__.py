"""
Loaders module - Data import UI components.

This module provides loader dialogs for importing data from various sources:
- FileLoader: Local files (CSV, Excel, Parquet, JSON, IPC)
- SQLLoader: Database connections via SQLAlchemy
- APILoader: REST API endpoints

All loaders inherit from BaseLoader and implement the render() method.

Classes:
    BaseLoader: Abstract base class for all loaders
    FileLoader: File import dialog
    SQLLoader: Database connection dialog
    APILoader: REST API import dialog
"""

# Loader classes
from pyquery_polars.frontend.components.loaders.file_loader import FileLoader
from pyquery_polars.frontend.components.loaders.sql_loader import SQLLoader
from pyquery_polars.frontend.components.loaders.api_loader import APILoader

__all__ = [
    "FileLoader",
    "SQLLoader",
    "APILoader",
]
