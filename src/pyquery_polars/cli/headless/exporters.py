from typing import Any

from pyquery_polars.core.io import (
    ParquetExportParams, CsvExportParams, ExcelExportParams,
    JsonExportParams, NdjsonExportParams, IpcExportParams, SqliteExportParams
)


class ExporterFactory:
    """
    Factory for resolving exporter names and creating configuration parameters.
    """

    @staticmethod
    def resolve_name(fmt_str: str) -> str:
        """Resolve CLI format string to Backend Registry Key."""
        fmt = fmt_str.lower()
        if fmt == "csv":
            return "CSV"
        if fmt == "json":
            return "JSON"
        if fmt == "ndjson":
            return "NDJSON"
        if fmt == "parquet":
            return "Parquet"
        if fmt in ["excel", "xlsx"]:
            return "Excel"
        if fmt in ["ipc", "arrow"]:
            return "Arrow IPC"
        if fmt in ["sqlite", "db"]:
            return "SQLite"
        return fmt.title()  # Fallback

    @staticmethod
    def create_params(format_str: str, output_path: str, args: Any) -> Any:
        """Generate export parameters based on format."""
        format_lower = format_str.lower()
        export_individual = getattr(args, 'export_individual', False)

        if format_lower == "parquet":
            return ParquetExportParams(
                path=output_path,
                compression=args.compression or "snappy",
                export_individual=export_individual
            )
        elif format_lower == "csv":
            return CsvExportParams(path=output_path, export_individual=export_individual)
        elif format_lower in ["excel", "xlsx"]:
            return ExcelExportParams(path=output_path, export_individual=export_individual)
        elif format_lower == "json":
            return JsonExportParams(path=output_path, export_individual=export_individual)
        elif format_lower == "ndjson":
            return NdjsonExportParams(path=output_path, export_individual=export_individual)
        elif format_lower in ["ipc", "arrow"]:
            return IpcExportParams(
                path=output_path,
                compression=args.compression or "uncompressed",
                export_individual=export_individual
            )
        elif format_lower == "sqlite":
            return SqliteExportParams(
                path=output_path,
                table=args.table or "data",
                if_exists=args.if_exists or "replace"
            )
        return None
