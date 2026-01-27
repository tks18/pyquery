import os


class PathResolver:
    """
    Resolves input and output paths strategies.
    """

    FMT_EXT_MAP = {
        "parquet": ".parquet",
        "csv": ".csv",
        "excel": ".xlsx",
        "xlsx": ".xlsx",
        "json": ".json",
        "ndjson": ".jsonl",
        "ipc": ".arrow",
        "arrow": ".arrow",
        "sqlite": ".db"
    }

    @classmethod
    def resolve_output_path(cls, base_path: str, format_str: str, is_dir: bool = False) -> str:
        """Intelligently resolve the output path."""
        expected_ext = cls.FMT_EXT_MAP.get(format_str.lower(), "")

        if is_dir:
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)
            return base_path

        if os.path.isdir(base_path) or base_path.endswith(os.sep) or (os.altsep and base_path.endswith(os.altsep)):
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)
            return os.path.join(base_path, f"export{expected_ext}")

        root, mk_ext = os.path.splitext(base_path)
        if not mk_ext:
            return f"{base_path}{expected_ext}"

        return base_path
