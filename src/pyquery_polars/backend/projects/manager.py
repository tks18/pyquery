"""
ProjectManager

Manages saving, loading, and importing project files (.pyquery format).
"""
from typing import Literal, Optional, List, Dict

import os

from pyquery_polars.core.project import (
    ProjectFile, ProjectMeta, PathConfig, DatasetProject, ProjectImportResult
)
from pyquery_polars.backend.projects.serializer import (
    save_project, load_project, resolve_paths, convert_paths_to_relative,
    validate_dataset_files
)
from pyquery_polars.backend.datasets import DatasetManager
from pyquery_polars.backend.recipes import RecipeManager
from pyquery_polars.backend.io import IOManager


class ProjectManager:
    """
    Manage project file operations.

    Dependencies:
    - DatasetManager: To save/restore dataset state
    - RecipeManager: To save/restore recipe state
    - IOManager: To execute loaders during import

    This class handles:
    - Exporting current state to ProjectFile
    - Saving projects to .pyquery files
    - Loading projects from .pyquery files
    - Importing projects (replace/merge modes)
    - Validating project files
    """

    def __init__(
        self,
        dataset_manager: "DatasetManager",
        recipe_manager: "RecipeManager",
        io_manager: "IOManager"
    ):
        """
        Initialize ProjectManager.

        Args:
            dataset_manager: Reference to DatasetManager for dataset operations
            recipe_manager: Reference to RecipeManager for recipe operations
            io_manager: Reference to IOManager for loading files
        """
        self._datasets = dataset_manager
        self._recipes = recipe_manager
        self._io = io_manager

    def export_project(
        self,
        path_mode: Literal["absolute", "relative"] = "absolute",
        base_dir: Optional[str] = None,
        description: Optional[str] = None
    ) -> ProjectFile:
        """
        Export complete project state to a ProjectFile object.
        """
        datasets = []

        for name, meta in self._datasets.items():
            # Get loader params (stored in metadata)
            loader_params = meta.loader_params or {}
            loader_type = meta.loader_type or "File"

            # Get recipe for this dataset
            recipe = self._recipes.get(name)

            ds = DatasetProject(
                alias=name,
                loader_type=loader_type,
                loader_params=loader_params,
                recipe=recipe
            )
            datasets.append(ds)

        # Build project file
        project = ProjectFile(
            meta=ProjectMeta(description=description),
            path_config=PathConfig(mode="absolute"),
            datasets=datasets
        )

        # Convert paths if relative mode requested
        if path_mode == "relative" and base_dir:
            project = convert_paths_to_relative(project, base_dir)

        return project

    def save_to_file(
        self,
        file_path: str,
        path_mode: Literal["absolute", "relative"] = "absolute",
        base_dir: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Export and save project to a .pyquery file.
        """
        project = self.export_project(path_mode, base_dir, description)
        save_project(project, file_path)
        return file_path

    def load_from_file(
        self,
        file_path: str,
        mode: Literal["replace", "merge"] = "replace"
    ) -> ProjectImportResult:
        """
        Load a project from a .pyquery file.
        """
        project = load_project(file_path)

        # Use file's directory as base for relative path resolution
        file_dir = os.path.dirname(os.path.abspath(file_path))

        return self.import_project(project, mode, base_dir_override=file_dir)

    def import_project(
        self,
        project: ProjectFile,
        mode: Literal["replace", "merge"] = "replace",
        base_dir_override: Optional[str] = None
    ) -> ProjectImportResult:
        """
        Import a project, loading datasets and recipes.
        """
        result = ProjectImportResult()

        # Resolve paths to absolute if needed
        resolved = resolve_paths(project, base_dir_override)

        # Check for missing files
        missing = validate_dataset_files(resolved)

        # Clear existing if replace mode
        if mode == "replace":
            self._datasets.clear_all()
            self._recipes.clear_all()

        for ds in resolved.datasets:
            # Skip if dataset exists in merge mode
            if mode == "merge" and ds.alias in self._datasets:
                result.datasets_skipped.append(ds.alias)
                result.warnings.append(f"Skipped '{ds.alias}': already exists")
                continue

            # Skip if files are missing
            if ds.alias in missing:
                result.datasets_skipped.append(ds.alias)
                result.warnings.append(
                    f"Skipped '{ds.alias}': missing files: {missing[ds.alias][:3]}"
                )
                continue

            # Attempt to load dataset
            try:
                # Use IOManager directly to run loader
                loader_result = self._io.run_loader(
                    ds.loader_type, ds.loader_params)

                if loader_result:
                    lf, metadata = loader_result
                    self._datasets.add(
                        ds.alias, lf, metadata,
                        loader_type=ds.loader_type,
                        loader_params=ds.loader_params
                    )

                    # Load recipe
                    if ds.recipe:
                        self._recipes.add(ds.alias, ds.recipe)
                    else:
                        self._recipes.ensure_exists(ds.alias)

                    result.datasets_loaded.append(ds.alias)
                else:
                    result.datasets_skipped.append(ds.alias)
                    result.warnings.append(
                        f"Failed to load '{ds.alias}': loader returned None")

            except Exception as e:
                result.datasets_skipped.append(ds.alias)
                result.errors.append(f"Error loading '{ds.alias}': {str(e)}")

        result.success = len(result.errors) == 0
        return result

    def validate_files(self, project: ProjectFile) -> Dict[str, List[str]]:
        """Check if dataset source files exist in a project."""
        return validate_dataset_files(project)
