from typing import Any, Dict, Optional, Callable, Type
from pydantic import BaseModel
import polars as pl
from src.core.models import StepMetadata, TransformContext

# Type definitions
BackendFunc = Callable[[pl.LazyFrame, Any,
                        Optional[TransformContext]], pl.LazyFrame]
FrontendFunc = Callable[[str, Any, Optional[pl.Schema]], Any]


class StepDefinition(BaseModel):
    """
    Complete definition of a transformation step.
    Includes Backend Logic, Frontend UI, Metadata, and Parameter Schema.
    """
    step_type: str
    metadata: StepMetadata
    params_model: Type[BaseModel]
    backend_func: BackendFunc
    frontend_func: Optional[FrontendFunc] = None

    class Config:
        arbitrary_types_allowed = True


class StepRegistry:
    _instance = None
    _steps: Dict[str, StepDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StepRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls,
                 step_type: str,
                 metadata: StepMetadata,
                 params_model: Type[BaseModel],
                 backend_func: BackendFunc,
                 frontend_func: Optional[FrontendFunc] = None):
        """
        Register a new transformation step.
        """
        def_obj = StepDefinition(
            step_type=step_type,
            metadata=metadata,
            params_model=params_model,
            backend_func=backend_func,
            frontend_func=frontend_func
        )
        cls._steps[step_type] = def_obj

    @classmethod
    def get(cls, step_type: str) -> Optional[StepDefinition]:
        return cls._steps.get(step_type)

    @classmethod
    def get_all(cls) -> Dict[str, StepDefinition]:
        return cls._steps

    @classmethod
    def get_supported_steps(cls):
        return list(cls._steps.keys())
