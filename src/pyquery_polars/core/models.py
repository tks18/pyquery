from typing import Type
import polars as pl
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Union, Literal, Callable


class StepMetadata(BaseModel):
    """Metadata for a transformation step."""
    label: str
    group: str = "Misc"


class RecipeStep(BaseModel):
    id: str
    type: str  # Discriminator, matches Registry key
    label: str
    params: Dict[str, Any] = Field(
        default_factory=dict)  # Generic params container

    model_config = ConfigDict(extra='ignore')  # Allow extra fields if needed


class IOSchemaField(BaseModel):
    """Definition for a single UI field in I/O plugins."""
    name: str
    type: Literal["text", "textarea", "select", "number", "bool"]
    label: str
    placeholder: Optional[str] = ""
    default: Optional[Union[str, int, float, bool]] = ""
    options: Optional[List[str]] = Field(default_factory=list)


class PluginDef(BaseModel):
    """Definition for a Loader or Exporter plugin."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    func: Callable
    params_model: Optional[Type[BaseModel]] = None


class JobInfo(BaseModel):
    """Status and metadata for an asynchronous job."""
    job_id: str
    status: Literal["RUNNING", "COMPLETED", "FAILED"]
    duration: float = 0.0
    size_str: str = "Unknown"
    error: Optional[str] = None
    file: str


class TransformContext(BaseModel):
    """Context passed to transformation functions."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # typed as Dict[str, pl.LazyFrame] in practice
    datasets: Dict[str, pl.LazyFrame]
    project_recipes: Optional[Dict[str, List[RecipeStep]]] = None
    apply_recipe_callback: Optional[Callable[..., Any]] = None
