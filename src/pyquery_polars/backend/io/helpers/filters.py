from typing import List, Optional, Iterator

import os
import glob
import re
import fnmatch
from itertools import islice

from git import Union

from pyquery_polars.core.io import FileFilter, ItemFilter, FilterType


class FilterEngine:
    """
    Utility class for resolving file paths and applying advanced filters.
    """

    @classmethod
    def resolve_file_paths(cls, base_path: str, filters: Optional[List[FileFilter]] = None, limit: Optional[int] = None) -> List[str]:
        """
        Resolve a base path and optional filters into a list of file paths.

        Uses a streaming approach to efficiently handle large directories.
        Optimizes simple filters into glob patterns where possible (Partial Globbing).
        Falls back to Python-side filtering for complex requirements.

        Args:
            base_path: Target path (file, directory, or glob pattern).
            filters: Optional list of filters to apply.
            limit: Optional maximum number of files to return (for previews).
        """
        if not base_path:
            return []

        # Scenario 1: No Filters
        # If a specific path or valid glob is provided without extra filters,
        # we return it directly to let the optimized Polars reader handle scanning.
        if not filters:
            if os.path.isfile(base_path):
                return [base_path]
            if "*" in base_path:
                # standard behavior for 'resolve' implies returning the list.
                if limit:
                    return list(islice(glob.iglob(base_path, recursive="**" in base_path), limit))
                return glob.glob(base_path, recursive="**" in base_path)

            if os.path.isdir(base_path):
                # Return directory as-is for Polars to scan/hive-partition auto-detect
                return [base_path]

            return []

        # Scenario 2: Filters Present
        # We must scan and filter files manually (or partially optimized).

        # Attempt to narrow the search space using the most restrictive filter (Partial Globbing)
        optimized_glob = cls._optimize_filters_to_glob(base_path, filters)

        candidates_iter: Iterator[str]

        if optimized_glob:
            # Use the optimized glob as the primary candidate source
            candidates_iter = glob.iglob(
                optimized_glob, recursive="**" in optimized_glob)
        else:
            # Fallback: Determine candidate source based on base_path type
            if "*" in base_path:
                candidates_iter = glob.iglob(
                    base_path, recursive="**" in base_path)
            elif os.path.isdir(base_path):
                # Generator for recursive directory scan
                candidates_iter = cls._recursive_dir_walker(base_path)
            elif os.path.isfile(base_path):
                candidates_iter = iter([base_path])
            else:
                return []

        # Apply remaining filters in a streaming fashion
        return cls._apply_param_filters(candidates_iter, filters, limit)

    @classmethod
    def _recursive_dir_walker(cls, path: str) -> Iterator[str]:
        """Yields all file paths recursively from a directory."""
        for dp, dn, filenames in os.walk(path):
            for f in filenames:
                yield os.path.join(dp, f)

    @classmethod
    def _optimize_filters_to_glob(cls, base_path: str, filters: List[FileFilter]) -> Optional[str]:
        """
        Selects the best available filter to create a narrowing glob pattern.
        Priority: EXACT > GLOB > CONTAINS (filename target only).
        """
        # Globbing is only applicable if we are starting from a directory
        if not os.path.isdir(base_path):
            return None

        # Priority 1: Exact Filename Match
        for f in filters:
            if f.target == "filename" and f.type == FilterType.EXACT:
                return os.path.join(base_path, f.value)

        # Priority 2: User-provided Glob
        for f in filters:
            if f.target == "filename" and f.type == FilterType.GLOB:
                return os.path.join(base_path, f.value)

        # Priority 3: Contains (Substring)
        for f in filters:
            if f.target == "filename" and f.type == FilterType.CONTAINS:
                return os.path.join(base_path, "**", f"*{f.value}*")

        return None

    @classmethod
    def check_filter_match(cls, path: str, f: FileFilter) -> bool:
        """Evaluates if a file path satisfies a single filter."""

        # Resolve target
        if f.target == "path":
            check_val = path
        else:
            check_val = os.path.basename(path)

        return cls.check_item_match(check_val, f)

    @classmethod
    def check_item_match(cls, name: str, f: Union[ItemFilter, FileFilter]) -> bool:
        """Evaluates if a sheet name satisfies a filter."""
        val = f.value
        check_val = name

        # Standardize case for case-insensitive comparisons
        # EXACT is the only strictly case-sensitive mode
        check_lower = check_val.lower()
        val_lower = val.lower()

        if f.type == FilterType.EXACT:
            return val == check_val

        if f.type == FilterType.IS_NOT:
            return val != check_val

        if f.type == FilterType.CONTAINS:
            return val_lower in check_lower

        if f.type == FilterType.NOT_CONTAINS:
            return val_lower not in check_lower

        if f.type == FilterType.GLOB:
            return fnmatch.fnmatch(check_lower, val_lower)

        if f.type == FilterType.REGEX:
            try:
                return bool(re.search(val, check_val, re.IGNORECASE))
            except re.error:
                return False

        return False

    @classmethod
    def _apply_param_filters(cls, files: Iterator[str], filters: List[FileFilter], limit: Optional[int] = None) -> List[str]:
        """
        Consumes the file iterator, applies filters, and returns a list up to the limit.
        """
        kept = []

        for path in files:
            # Check limit before processing
            if limit is not None and len(kept) >= limit:
                break

            # Verify all filters match
            if all(cls.check_filter_match(path, f) for f in filters):
                kept.append(path)

        return kept
