from abc import ABC, abstractmethod
from typing import Generic, List, Literal, Optional, TypeAlias, TypeVar, cast, ClassVar

import polars as pl

from pydantic import BaseModel, ConfigDict, ValidationError

from pyquery_polars.backend.io.helpers.staging import StagingManager

PydanticModel: TypeAlias = type[BaseModel]

InputT = TypeVar("InputT", bound=BaseModel)


class FileDetails(BaseModel):
    name: str
    path: str
    size: int

    model_config = ConfigDict(frozen=True)


class ExporterOutput(BaseModel):
    status: Literal["COMPLETED", "FAILED"]
    error: Optional[str] = None
    size_str: str
    file_details: List[FileDetails]

    model_config = ConfigDict(frozen=True)


class BaseExporter(ABC, Generic[InputT]):
    """
    Base class for all Exporter Plugins.

    This class uses Generics to ensure strict typing for both input parameters
    and output results

    Subclasses must implement the `_run_impl` method.
    """

    # Explicit contracts (must be set by subclasses)
    name: str
    input_model: ClassVar[PydanticModel]
    output_model = ExporterOutput

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
        self, result: Optional[ExporterOutput]
    ) -> Optional[ExporterOutput]:

        if result is None:
            return None

        if not isinstance(result, ExporterOutput):
            raise TypeError(
                f"[{self.__class__.__name__}] Must return ExporterOutput"
            )

        try:
            # Validate meta explicitly
            self.output_model.model_validate(result)
        except ValidationError as e:
            raise ValueError(
                f"[{self.__class__.__name__}] Invalid output meta"
            ) from e

        return result

    def run(self) -> Optional[ExporterOutput]:
        raw = self._run_impl()
        return self._validate_output(raw)

    @abstractmethod
    def _run_impl(self) -> Optional[ExporterOutput]:
        """
        Execute the Exporter logic.

        Returns:
            The loaded data or result.
            Type is defined by the OutputT generic.
        """
        pass
