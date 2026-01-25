from typing import Type, List, Dict, Any, Optional, Union, Literal, Callable
from pydantic import BaseModel, Field, ConfigDict

import polars as pl


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

    # Allow extra fields/obj loading
    model_config = ConfigDict(extra='ignore', from_attributes=True)


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


class DatasetMetadata(BaseModel):
    """Comprehensive metadata for a loaded dataset."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core LazyFrame storage
    base_lf: Optional[pl.LazyFrame] = None  # For single file or concatenated
    base_lfs: Optional[List[pl.LazyFrame]] = None  # For individual processing

    # Source information
    source_path: Optional[str] = None
    input_type: str = "file"  # 'file', 'folder', 'sql', 'api'
    input_format: Optional[str] = None  # File extension or source type

    # Processing mode
    process_individual: bool = False
    file_list: Optional[List[str]] = None
    file_count: int = 1

    # Loader Configuration Persistence (for Edit/Settings feature)
    loader_type: Optional[Literal["File", "SQL", "API"]] = None
    # Full params dict from frontend
    loader_params: Optional[Dict[str, Any]] = None


class JobInfo(BaseModel):
    """Status and metadata for an asynchronous job."""
    job_id: str
    status: Literal["RUNNING", "COMPLETED", "FAILED"]
    duration: float = 0.0
    size_str: str = "Unknown"
    error: Optional[str] = None
    file: str
    file_details: Optional[List[Dict[str, Any]]] = None


class TransformContext(BaseModel):
    """Context passed to transformation functions."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # typed as Dict[str, pl.LazyFrame] in practice
    datasets: Dict[str, pl.LazyFrame]
    project_recipes: Optional[Dict[str, List[RecipeStep]]] = None
    apply_recipe_callback: Optional[Callable[..., Any]] = None
