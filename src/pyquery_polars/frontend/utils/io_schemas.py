from typing import List, Dict

from pyquery_polars.core.models import IOSchemaField

# --- LOADERS ---

LOADER_SCHEMAS: Dict[str, List[IOSchemaField]] = {
    "File": [
        IOSchemaField(name="path", type="text",
                      label="Path / Glob", placeholder="data/*.csv"),
        IOSchemaField(name="sheet", type="text",
                      label="Sheet (Excel)", default="Sheet1"),
        IOSchemaField(name="alias", type="text",
                      label="Dataset Alias", placeholder="Transactions")
    ],
    "SQL": [
        IOSchemaField(name="conn", type="text",
                      label="Connection URI", placeholder="postgresql://..."),
        IOSchemaField(name="query", type="textarea",
                      label="Query / Table", placeholder="SELECT * FROM ..."),
        IOSchemaField(name="alias", type="text",
                      label="Dataset Alias", placeholder="SQL_Data")
    ],
    "API": [
        IOSchemaField(name="url", type="text", label="API URL",
                      placeholder="https://api..."),
        IOSchemaField(name="alias", type="text",
                      label="Dataset Alias", placeholder="API_Data")
    ]
}

# --- EXPORTERS ---

EXPORTER_SCHEMAS: Dict[str, List[IOSchemaField]] = {
    "Parquet": [
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.parquet"),
        IOSchemaField(name="compression", type="select", label="Compression", options=[
                      'snappy', 'zstd', 'gzip', 'lz4', 'uncompressed', 'brotli'], default="snappy")
    ],
    "CSV": [
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.csv")
    ],
    "Excel": [
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.xlsx")
    ],
    "JSON": [
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.json")
    ],
    "Arrow IPC": [
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.arrow"),
        IOSchemaField(name="compression", type="select", label="Compression", options=[
                      'uncompressed', 'lz4', 'zstd'], default="uncompressed")
    ],
    "NDJSON": [
        IOSchemaField(name="path", type="text",
                      label="Output Path", default="output.jsonl")
    ],
    "SQLite": [
        IOSchemaField(name="path", type="text",
                      label="DB Path", default="output.db"),
        IOSchemaField(name="table", type="text",
                      label="Table Name", default="data"),
        IOSchemaField(name="if_exists", type="select", label="If Exists", options=[
                      'fail', 'replace', 'append'], default="replace")
    ]
}


def get_loader_schema(name: str) -> List[IOSchemaField]:
    return LOADER_SCHEMAS.get(name, [])


def get_exporter_schema(name: str) -> List[IOSchemaField]:
    return EXPORTER_SCHEMAS.get(name, [])
