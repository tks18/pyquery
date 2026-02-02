from typing import ClassVar, Optional, Type

import connectorx as cx
import polars as pl
from pydantic import BaseModel

from pyquery_polars.backend.io.loaders.base import BaseLoader, LoaderOutput
from pyquery_polars.core.io import SqlLoaderParams


class SqlLoaderOutput(BaseModel):
    connection_string: str
    query: str


class SQLLoader(BaseLoader[SqlLoaderParams, SqlLoaderOutput]):
    """
    Loads data from a SQL source.(SQLite, Postgres, etc.)
    """

    name = "SQL"
    input_model:  ClassVar[type[BaseModel]] = SqlLoaderParams
    output_model:  ClassVar[type[BaseModel]] = LoaderOutput[SqlLoaderOutput]

    def _run_impl(self) -> Optional[LoaderOutput[SqlLoaderOutput]]:
        connection_string = self.params.conn
        query = self.params.query
        meta = SqlLoaderOutput(
            connection_string=connection_string, query=query)
        try:
            # connectorx returns eager Arrow/DataFrame, we make it lazy
            # This is strictly backend logic (IO)
            df_arrow = cx.read_sql(
                connection_string, query, return_type="arrow")
            df = pl.from_arrow(df_arrow)

            # Ensure it's a DataFrame before calling lazy
            if isinstance(df, pl.Series):
                df = df.to_frame().lazy()
            else:
                df = df.lazy()

            return LoaderOutput(lf=df, meta=meta)
        except Exception as e:
            print(f"SQL Error: {e}")
            return None
