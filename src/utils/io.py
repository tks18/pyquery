import os
import io
import glob
import threading
import time
import requests
import polars as pl
from datetime import datetime
import streamlit as st

def get_files_from_path(path_input):
    path_input = path_input.strip('"').strip("'")
    if os.path.isdir(path_input):
        return os.path.join(path_input, "*")
    return path_input

def load_from_sql(connection_string, query):
    try:
        # Requires connectorx
        return pl.read_database_uri(query=query, uri=connection_string).lazy()
    except Exception as e:
        st.error(f"SQL Load Error: {e}")
        return None

def load_from_api(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        content = r.content
        # Try JSON first
        try:
            return pl.read_json(io.BytesIO(content)).lazy()
        except:
            pass
        # Try CSV
        try:
            return pl.read_csv(io.BytesIO(content)).lazy()
        except:
            st.error("Could not parse API response as JSON or CSV.")
            return None
    except Exception as e:
        st.error(f"API Request Error: {e}")
        return None


def load_lazy_frame(source_path, sheet_name="Sheet1"):
    if not source_path:
        return None
    file_ext = source_path.split(
        '.')[-1].lower() if "." in source_path else "csv"
    try:
        if "csv" in file_ext:
            return pl.scan_csv(source_path, infer_schema_length=0, ignore_errors=True)
        elif "parquet" in file_ext:
            return pl.scan_parquet(source_path)
        elif "json" in file_ext:
            return pl.scan_ndjson(source_path, infer_schema_length=0)
        elif "xlsx" in file_ext or "xls" in file_ext:
            is_glob = "*" in source_path
            files = glob.glob(source_path) if is_glob else [source_path]
            if not files:
                return None
            lazy_frames = []
            for f in files:
                try:
                    df = pl.read_excel(
                        f, sheet_name=sheet_name, infer_schema_length=0)
                    df = df.select(pl.all().cast(pl.Utf8))
                    lazy_frames.append(df.lazy())
                except:
                    pass
            return pl.concat(lazy_frames) if lazy_frames else None
        else:
            return pl.scan_csv(source_path, infer_schema_length=0)
    except:
        return None

def export_worker(lazy_frame, path, fmt, compression, result_container):
    try:
        start_time = datetime.now()
        os.makedirs(os.path.dirname(os.path.abspath(path))
                    or ".", exist_ok=True)
        if fmt == "Parquet":
            lazy_frame.sink_parquet(
                path, compression=compression)
        elif fmt == "CSV":
            lazy_frame.sink_csv(path)
        elif fmt == "Excel":
            lazy_frame.collect().write_excel(path)
        elif fmt == "SQL":
            # path here acts as table name, compression acts as connection URI
            table_name = path
            conn_uri = compression
            lazy_frame.collect().write_database(table_name=table_name, connection=conn_uri, if_table_exists="append")
        result_container['status'] = 'success'
        result_container['message'] = f"Success! Time: {datetime.now() - start_time}"
    except Exception as e:
        result_container['status'] = 'error'
        result_container['message'] = str(e)
