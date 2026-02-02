from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeAlias, TypeVar, Union, cast, ClassVar

import polars as pl

from pydantic import BaseModel, ConfigDict, ValidationError

from pyquery_polars.backend.io.helpers.staging import StagingManager

PydanticModel: TypeAlias = type[BaseModel]

# Define TypeVars for Input and Output
InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class LoaderOutput(BaseModel, Generic[OutputT]):
    lf: Union[pl.LazyFrame, List[pl.LazyFrame]]
    meta: OutputT

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True
    )


class BaseLoader(ABC, Generic[InputT, OutputT]):
    """
    Base class for all Loader Plugins.

    This class uses Generics to ensure strict typing for both input parameters
    and output results

    Subclasses must implement the `run` method.
    """

    # Explicit contracts (must be set by subclasses)
    name: str
    input_model: ClassVar[PydanticModel]
    output_model: ClassVar[PydanticModel]

    def __init__(self, staging_manager: StagingManager, params: InputT | dict) -> None:
        self.params = self._validate_input(params)
        self.staging = staging_manager

    def _validate_input(self, params: InputT | dict) -> InputT:
        try:
            if isinstance(params, BaseModel):
                return cast(InputT, params)

            validated = self.input_model.model_validate(params)
            return cast(InputT, validated)

        except ValidationError as e:
            raise ValueError(
                f"[{self.__class__.__name__}] Invalid input params"
            ) from e

    def _validate_output(
        self, result: Optional[LoaderOutput[OutputT]]
    ) -> Optional[LoaderOutput[OutputT]]:

        if result is None:
            return None

        if not isinstance(result, LoaderOutput):
            raise TypeError(
                f"[{self.__class__.__name__}] Must return LoaderOutput"
            )

        try:
            # Validate meta explicitly
            self.output_model.model_validate(result.meta)
        except ValidationError as e:
            raise ValueError(
                f"[{self.__class__.__name__}] Invalid output meta"
            ) from e

        return result

    def run(self) -> Optional[LoaderOutput[OutputT]]:
        raw = self._run_impl()
        return self._validate_output(raw)

    @abstractmethod
    def _run_impl(self) -> Optional[LoaderOutput[OutputT]]:
        """
        Execute the loader logic.

        Returns:
            The loaded data or result.
            Type is defined by the OutputT generic.
        """
        pass
