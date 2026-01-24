import os
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

from pyquery_polars.core.project import (
    ProjectFile, ProjectMeta, PathConfig, DatasetProject
)


def save_project(project: ProjectFile, file_path: str) -> None:
    """
    Save a ProjectFile to disk as a .pyquery file.

    Args:
        project: The ProjectFile to save
        file_path: Target path (should end with .pyquery)
    """
    # Ensure .pyquery extension
    if not file_path.endswith('.pyquery'):
        file_path = f"{file_path}.pyquery"

    # Ensure parent directory exists
    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(project.to_json())


def load_project(file_path: str) -> ProjectFile:
    """
    Load a ProjectFile from disk.

    Args:
        file_path: Path to .pyquery file

    Returns:
        Parsed ProjectFile

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not valid JSON or schema mismatch
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Project file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        return ProjectFile.from_json(content)
    except Exception as e:
        raise ValueError(f"Invalid project file: {e}")


def resolve_paths(project: ProjectFile, target_base_dir: Optional[str] = None) -> ProjectFile:
    """
    Resolve paths in project based on path_config.

    If project uses relative paths, converts them to absolute using:
    - target_base_dir if provided
    - project's base_dir otherwise

    Args:
        project: The project to resolve paths for
        target_base_dir: Optional base directory override

    Returns:
        New ProjectFile with resolved absolute paths
    """
    if project.path_config.mode == "absolute":
        return project  # Already absolute

    base_dir = target_base_dir or project.path_config.base_dir
    if not base_dir:
        raise ValueError("Relative path mode requires a base directory")

    base_path = Path(base_dir).resolve()

    resolved_datasets = []
    for ds in project.datasets:
        new_params = ds.loader_params.copy()

        # Resolve 'path' field if present
        if 'path' in new_params and new_params['path']:
            rel_path = new_params['path']
            if not os.path.isabs(rel_path):
                new_params['path'] = str(base_path / rel_path)

        # Resolve 'files' list if present
        if 'files' in new_params and new_params['files']:
            new_files = []
            for f in new_params['files']:
                if not os.path.isabs(f):
                    new_files.append(str(base_path / f))
                else:
                    new_files.append(f)
            new_params['files'] = new_files

        resolved_datasets.append(DatasetProject(
            alias=ds.alias,
            loader_type=ds.loader_type,
            loader_params=new_params,
            recipe=ds.recipe
        ))

    # Return with absolute mode since we resolved everything
    return ProjectFile(
        meta=project.meta,
        path_config=PathConfig(mode="absolute"),
        datasets=resolved_datasets
    )


def convert_paths_to_relative(project: ProjectFile, base_dir: str) -> ProjectFile:
    """
    Convert absolute paths in project to relative paths.

    Args:
        project: The project with absolute paths
        base_dir: Base directory for relative path calculation

    Returns:
        New ProjectFile with relative paths
    """
    base_path = Path(base_dir).resolve()

    converted_datasets = []
    for ds in project.datasets:
        new_params = ds.loader_params.copy()

        # Convert 'path' field if present and absolute
        if 'path' in new_params and new_params['path']:
            abs_path = new_params['path']
            if os.path.isabs(abs_path):
                try:
                    rel_path = os.path.relpath(abs_path, base_dir)
                    new_params['path'] = rel_path
                except ValueError:
                    # Different drive on Windows, keep absolute
                    pass

        # Convert 'files' list if present
        if 'files' in new_params and new_params['files']:
            new_files = []
            for f in new_params['files']:
                if os.path.isabs(f):
                    try:
                        rel_f = os.path.relpath(f, base_dir)
                        new_files.append(rel_f)
                    except ValueError:
                        new_files.append(f)
                else:
                    new_files.append(f)
            new_params['files'] = new_files

        converted_datasets.append(DatasetProject(
            alias=ds.alias,
            loader_type=ds.loader_type,
            loader_params=new_params,
            recipe=ds.recipe
        ))

    return ProjectFile(
        meta=project.meta,
        path_config=PathConfig(mode="relative", base_dir=base_dir),
        datasets=converted_datasets
    )


def convert_paths_to_absolute(project: ProjectFile) -> ProjectFile:
    """
    Convenience wrapper around resolve_paths.

    Converts a project with relative paths to use absolute paths.
    Uses the project's stored base_dir.
    """
    return resolve_paths(project)


def validate_dataset_files(project: ProjectFile) -> Dict[str, List[str]]:
    """
    Check if dataset source files exist.

    Args:
        project: Project to validate

    Returns:
        Dict mapping dataset alias to list of missing files
    """
    missing = {}

    # First resolve if relative
    resolved = resolve_paths(project)

    for ds in resolved.datasets:
        if ds.loader_type != "File":
            continue

        missing_files = []

        # Check main path
        if 'path' in ds.loader_params:
            path = ds.loader_params['path']
            # For patterns, we can't easily validate, skip
            if path and not any(c in path for c in ['*', '?']):
                if not os.path.exists(path):
                    missing_files.append(path)

        # Check explicit files list
        if 'files' in ds.loader_params:
            for f in ds.loader_params['files']:
                if not os.path.exists(f):
                    missing_files.append(f)

        if missing_files:
            missing[ds.alias] = missing_files

    return missing
