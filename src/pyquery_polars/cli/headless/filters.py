from typing import Dict, List, Optional, Literal

from pyquery_polars.core.io import FileFilter, ItemFilter, FilterType


class FilterParser:
    """
    Parses filter strings from CLI arguments into structured Filter objects.
    """

    @staticmethod
    def parse_string(f_str: str, default_target: str) -> Dict[str, str]:
        """Parse filter string 'type:value[:target]'."""
        parts = f_str.split(":", 2)
        type_val = parts[0]
        val = parts[1] if len(parts) > 1 else ""
        target = parts[2] if len(parts) > 2 else default_target
        return {"type": type_val, "value": val, "target": target}

    @classmethod
    def parse_file_filters(cls, args) -> Optional[List[FileFilter]]:
        if not getattr(args, 'file_filter', None):
            return None
        filters = []
        for f in args.file_filter:
            p = cls.parse_string(f, "filename")
            try:
                ft = FilterType(p["type"])
                target_raw = p["target"]
                target_val: Literal["filename", "path"] = "filename"
                if target_raw == "path":
                    target_val = "path"

                filters.append(FileFilter(
                    type=ft, value=p["value"], target=target_val))
            except Exception:
                raise ValueError(
                    f"Invalid Filter Type: {p['type']}. Supported: glob, regex, contains, exact, is_not")
        return filters

    @classmethod
    def parse_item_filters(cls, arg_list, default_target: Literal["sheet_name", "table_name"] = "sheet_name") -> Optional[List[ItemFilter]]:
        if not arg_list:
            return None
        filters = []
        for f in arg_list:
            p = cls.parse_string(f, default_target)
            try:
                ft = FilterType(p["type"])
                filters.append(ItemFilter(
                    type=ft, value=p["value"], target=default_target))
            except Exception:
                raise ValueError(
                    f"Invalid Filter Type: {p['type']}. Supported: glob, regex, contains, exact, is_not")
        return filters
