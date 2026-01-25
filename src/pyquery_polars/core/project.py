from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field

from datetime import datetime

from pyquery_polars.core.models import RecipeStep


class ProjectMeta(BaseModel):
    """Metadata about the project file itself."""
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    pyquery_version: str = "1.0.0"  # TODO: Pull from package version
    description: Optional[str] = None


class PathConfig(BaseModel):
    """Configuration for how paths are stored in the project file."""
    mode: Literal["absolute", "relative"] = "absolute"
    base_dir: Optional[str] = None  # Required for relative mode


class DatasetProject(BaseModel):
    """
    Complete serialization of a single dataset including:
    - Loader configuration (how to reload the data)
    - Recipe steps (transformations to apply)
    """
    alias: str
    loader_type: Literal["File", "SQL", "API"]
    loader_params: Dict[str, Any] = Field(default_factory=dict)
    recipe: List[RecipeStep] = Field(default_factory=list)


class ProjectFile(BaseModel):
    """
    Complete project file structure for .pyquery files.

    Contains all information needed to fully reconstruct a PyQuery session:
    - Project metadata (version, timestamps)
    - Path configuration (absolute vs relative)
    - All datasets with their loader params and recipes
    """
    meta: ProjectMeta = Field(default_factory=ProjectMeta)
    path_config: PathConfig = Field(default_factory=PathConfig)
    datasets: List[DatasetProject] = Field(default_factory=list)

    def to_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2, **kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectFile":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)


class ProjectImportResult(BaseModel):
    """Result of importing a project file."""
    success: bool = True
    datasets_loaded: List[str] = Field(default_factory=list)
    datasets_skipped: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
