import os
import glob
import json
import threading
import time
import requests
import polars as pl
import connectorx as cx
from io import BytesIO

def get_files_from_path(path_str):
    if not path_str:
        return []
    if "*" in path_str:
        return glob.glob(path_str)
    return [path_str] if os.path.exists(path_str) else []

def load_lazy_frame(files, sheet_name="Sheet1"):
    if not files:
        return None
    
    lfs = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        try:
            if ext == ".csv":
                lfs.append(pl.scan_csv(f, infer_schema_length=0))
            elif ext == ".parquet":
                lfs.append(pl.scan_parquet(f, infer_schema_length=0))
            elif ext in [".xlsx", ".xls"]:
                # Excel in Polars is eager reading usually
                df = pl.read_excel(f, sheet_name=sheet_name, infer_schema_length=0)
                lfs.append(df.lazy())
            elif ext == ".json":
                lfs.append(pl.scan_ndjson(f, infer_schema_length=0))
        except Exception as e:
            print(f"Error loading {f}: {e}")
            
    if not lfs:
        return None
        
    combined = lfs[0]
    for other in lfs[1:]:
        combined = pl.concat([combined, other], how="vertical_relaxed")
        
    return combined

def load_from_sql(connection_string, query):
    try:
        # connectorx returns eager Arrow/DataFrame, we make it lazy
        # This is strictly backend logic (IO)
        df_arrow = cx.read_sql(connection_string, query, return_type="arrow")
        df = pl.from_arrow(df_arrow)
        return df.lazy()
    except Exception as e:
        print(f"SQL Error: {e}")
        return None

def load_from_api(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        # Assume list of dicts or records
        df = pl.DataFrame(data)
        return df.lazy()
    except Exception as e:
        print(f"API Error: {e}")
        return None

def export_worker(lazy_frame, path, fmt, compression, result_container):
    try:
        df = lazy_frame.collect()
        if fmt == "CSV":
            df.write_csv(path)
        elif fmt == "Parquet":
            df.write_parquet(path, compression=compression)
        elif fmt == "Excel":
             df.write_excel(path)
        elif fmt == "JSON":
             df.write_json(path)
        result_container['status'] = "Done"
    except Exception as e:
        result_container['status'] = f"Error: {e}"
