from pyquery_polars.backend.io.loaders.file_loader import Fileloader
from pyquery_polars.backend.io.loaders.api_loader import APILoader
from pyquery_polars.backend.io.loaders.sql_loader import SQLLoader

__all__ = ["Fileloader", "APILoader", "SQLLoader"]

DEFAULT_LOADERS = [Fileloader, APILoader, SQLLoader]
