from typing import Callable, List, Optional, Type
from pydantic import BaseModel, ConfigDict
from pyquery_polars.backend.io.loaders.base import BaseLoader, LoaderOutput
from pyquery_polars.backend.io.loaders.file_loader import Fileloader
from pyquery_polars.backend.io.loaders.api_loader import APILoader
from pyquery_polars.backend.io.loaders.sql_loader import SQLLoader


__all__ = ["Fileloader", "APILoader",
           "SQLLoader", "BaseLoader", "LoaderOutput"]

DEFAULT_LOADERS: List[Type[BaseLoader]] = [Fileloader, APILoader, SQLLoader]
