from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar, Union

import polars as pl

from pydantic import BaseModel

from pyquery_polars.backend.io.helpers.staging import StagingManager

# Define TypeVars for Input and Output
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class LoaderOutput(BaseModel, Generic[OutputT]):
    lf: Union[pl.LazyFrame, List[pl.LazyFrame]]
    meta: OutputT


class BaseLoader(ABC, Generic[InputT, OutputT]):
    """
    Base class for all Loader Plugins.

    This class uses Generics to ensure strict typing for both input parameters
    and output results

    Subclasses must implement the `run` method.
    """

    def __init__(self, staging_manager: StagingManager, params: InputT) -> None:
        self.params = params
        self.staging = staging_manager

    @abstractmethod
    def run(self) -> Optional[LoaderOutput[OutputT]]:
        """
        Execute the loader logic.

        Returns:
            The loaded data or result.
            Type is defined by the OutputT generic.
        """
        pass
