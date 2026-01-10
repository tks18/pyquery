from typing import Union
import os
import glob
import requests
import shutil
import uuid
import polars as pl
import connectorx as cx
import chardet
import fastexcel
import tempfile
import time
from openpyxl import load_workbook
from typing import List, Literal, Optional, Any, Dict, cast

STAGING_DIR_NAME = "pyquery_staging"


def get_staging_dir() -> str:
    """Get or create the centralized staging directory."""
    temp_dir = tempfile.gettempdir()
    staging_path = os.path.join(temp_dir, STAGING_DIR_NAME)
    os.makedirs(staging_path, exist_ok=True)
    return staging_path


def cleanup_staging_files(max_age_hours: int = 24):
    """Clean up old files from the staging directory."""
    try:
        staging_dir = get_staging_dir()
        now = time.time()
        cutoff = now - (max_age_hours * 3600)

        if os.path.exists(staging_dir):
            for filename in os.listdir(staging_dir):
                file_path = os.path.join(staging_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        if os.path.getmtime(file_path) < cutoff:
                            os.remove(file_path)
                            # print(f"Cleaned up stale staging file: {filename}") # Reduce noise
                except Exception as e:
                    print(f"Failed to delete {filename}: {e}")
    except Exception as e:
        print(f"Cleanup Error: {e}")


def get_files_from_path(path_str: str) -> List[str]:
    if not path_str:
        return []
    if "*" in path_str:
        return glob.glob(path_str)
    return [path_str] if os.path.exists(path_str) else []


def get_excel_sheet_names(file_path: str) -> List[str]:
    """
    Efficiently retrieve sheet names from an Excel file using fastexcel.
    Fallback to 'Sheet1' if any error occurs.
    Handles globs and directories by inspecting the first matching file.
    """
    try:
        # Resolve path (handle globs, dirs)
        files = get_files_from_path(file_path)
        if not files:
            return ["Sheet1"]

        target_file = files[0]

        ext = os.path.splitext(target_file)[1].lower()
        if ext not in [".xlsx", ".xls", ".xlsm"]:
            return ["Sheet1"]

        try:
            excel = fastexcel.read_excel(target_file)
            return excel.sheet_names
        except Exception:
            # Fallback
            try:
                wb = load_workbook(
                    target_file, read_only=True, keep_links=False)
                return wb.sheetnames
            except:
                return ["Sheet1"]
    except Exception:
        return ["Sheet1"]



def detect_encoding(file_path: str, n_bytes: int = 10000) -> str:
    """
    Detect the encoding of a file using chardet.
    Defaults to 'utf8' if detection fails or chardet is not installed.
    """
    try:
        with open(file_path, 'rb') as f:
            rawdata = f.read(n_bytes)
        result = chardet.detect(rawdata)
        encoding = result['encoding']
        confidence = result['confidence']
        
        # If confidence is low or None, stick to default
        if not encoding or (confidence and confidence < 0.5):
            return 'utf8'
            
        # Polars expects 'utf8' not 'utf-8' sometimes, but 'utf8' is safe alias
        # Common fix: 'ascii' -> 'utf8'
        if encoding.lower() == 'ascii':
            return 'utf8'
            
        return encoding
    except (ImportError, Exception) as e:
        # Fallback to UTF-8 if chardet is missing or fails
        return 'utf8'


def load_lazy_frame(files: List[str], sheet_name: str = "Sheet1", process_individual: bool = False, include_source_info: bool = False) -> Optional[tuple]:
    """
    Load files into LazyFrame(s).

    Returns:
        Tuple of (Union[LazyFrame, List[LazyFrame]], metadata_dict) or None

    When process_individual=True and multiple files:
        Returns (List[LazyFrame], metadata) for individual processing
    Otherwise:
        Returns (LazyFrame, metadata) as concatenated result
    """
    if not files:
        return None

    # Determine file format
    exts = {os.path.splitext(f)[1].lower() for f in files}
    ext = list(exts)[0] if len(exts) == 1 else ".mixed"

    # OPTIMIZATION: Try Bulk Scan for homogeneous files
    # Polars supports list of files for scan_csv, scan_parquet, scan_ipc, scan_ndjson
    # BUT: If include_source_info is True, we force Iterative to reliably add columns per file
    if len(exts) == 1 and not process_individual and not include_source_info:
        try:
            if ext == ".csv":
                # Detect encoding for ALL files to ensure homogeneity
                # If encodings differ, we must fallback to iterative loading
                detected_encodings = set()
                for f in files:
                    detected_encodings.add(detect_encoding(f))
                
                if len(detected_encodings) > 1:
                    # Mixed encodings detected (e.g. {'utf8', 'windows-1252'})
                    # Cannot use bulk scan_csv with single encoding.
                    raise ValueError(f"Mixed encodings detected: {detected_encodings}")
                
                # Single encoding confirmed
                common_encoding = detected_encodings.pop()
                
                lf = pl.scan_csv(files, infer_schema_length=0, encoding=common_encoding)
                metadata = {
                    "input_type": "folder" if len(files) > 1 else "file",
                    "input_format": ext,
                    "file_list": files,
                    "file_count": len(files)
                }
                return lf, metadata
            elif ext == ".parquet":
                lf = pl.scan_parquet(files)
                metadata = {
                    "input_type": "folder" if len(files) > 1 else "file",
                    "input_format": ext,
                    "file_list": files,
                    "file_count": len(files)
                }
                return lf, metadata
            elif ext in [".arrow", ".ipc", ".feather"]:
                lf = pl.scan_ipc(files)
                metadata = {
                    "input_type": "folder" if len(files) > 1 else "file",
                    "input_format": ext,
                    "file_list": files,
                    "file_count": len(files)
                }
                return lf, metadata
            elif ext == ".json":
                lf = pl.scan_ndjson(files, infer_schema_length=0)
                metadata = {
                    "input_type": "folder" if len(files) > 1 else "file",
                    "input_format": ext,
                    "file_list": files,
                    "file_count": len(files)
                }
                return lf, metadata
        except Exception as e:
            print(f"Bulk scan error, falling back to iterative: {e}")

    # Fallback: Iterative (Mixed types or Excel or process_individual OR include_source_info)
    lfs = []
    for f in files:
        file_ext = os.path.splitext(f)[1].lower()
        try:
            current_lf = None
            if file_ext == ".csv":
                encoding = detect_encoding(f)
                current_lf = pl.scan_csv(f, infer_schema_length=0, encoding=encoding)
            elif file_ext == ".parquet":
                current_lf = pl.scan_parquet(f)
            elif file_ext in [".arrow", ".ipc", ".feather"]:
                current_lf = pl.scan_ipc(f)
            elif file_ext in [".xlsx", ".xls"]:
                # Dump to Parquet
                # Excel is eager-only.
                try:
                    df = pl.read_excel(f, sheet_name=sheet_name,
                                       infer_schema_length=0)

                    # STAGING: Centralized
                    # Prevents cluttering the app directory
                    staging_dir = get_staging_dir()

                    stage_filename = f"{os.path.splitext(os.path.basename(f))[0]}_{uuid.uuid4().hex[:8]}.parquet"
                    stage_path = os.path.join(staging_dir, stage_filename)

                    df.write_parquet(stage_path)
                    del df

                    current_lf = pl.scan_parquet(stage_path)

                except Exception as ex:
                    print(f"Excel Load Error {f}: {ex}")

            elif file_ext == ".json":
                current_lf = pl.scan_ndjson(f, infer_schema_length=0)
            
            # --- SOURCE INFO INJECTION ---
            if current_lf is not None and include_source_info:
                abs_path = os.path.abspath(f)
                name = os.path.basename(f)
                ext_val = os.path.splitext(f)[1]
                
                current_lf = current_lf.with_columns([
                    pl.lit(abs_path).alias("__pyquery_source_path__"),
                    pl.lit(name).alias("__pyquery_source_name__"),
                    pl.lit(ext_val).alias("__pyquery_source_ext__")
                ])
            
            if current_lf is not None:
                lfs.append(current_lf)
                
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if not lfs:
        return None

    # Build metadata
    metadata = {
        "input_type": "folder" if len(files) > 1 else "file",
        "input_format": ext,
        "file_list": files,
        "file_count": len(files),
        "process_individual": process_individual
    }

    # Decision: Return list or concatenated
    if process_individual and len(lfs) > 1:
        # Return list of LazyFrames for individual processing
        return lfs, metadata
    else:
        # Return concatenated LazyFrame (existing behavior)
        combined = lfs[0]

        # DIAGONAL STRATEGY:
        # Handles schema evolution (new columns in later files filled with nulls).
        # Graceful handling of missing columns.
        if len(lfs) > 1:
            combined = pl.concat(lfs, how="diagonal")

        return combined, metadata


def load_from_sql(connection_string: str, query: str) -> Optional[pl.LazyFrame]:
    try:
        # connectorx returns eager Arrow/DataFrame, we make it lazy
        # This is strictly backend logic (IO)
        df_arrow = cx.read_sql(connection_string, query, return_type="arrow")
        df = pl.from_arrow(df_arrow)

        # Ensure it's a DataFrame before calling lazy
        if isinstance(df, pl.Series):
            df = df.to_frame()

        return df.lazy()
    except Exception as e:
        print(f"SQL Error: {e}")
        return None


def load_from_api(url: str) -> Optional[pl.LazyFrame]:
    try:
        # Enterprise Staged Loading: Stream to disk first
        staging_dir = get_staging_dir()

        file_name = f"api_dump_{uuid.uuid4()}.json"
        file_path = os.path.join(staging_dir, file_name)

        # Stream download (low memory usage)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        # Return LazyFrame from disk
        return pl.read_json(file_path).lazy()
    except Exception as e:
        print(f"API Error: {e}")
        return None


def export_worker(lazy_frame: pl.LazyFrame, params: Any, fmt: str, result_container: Dict[str, Any]):
    try:
        # Extract path safely from params (Dict or Pydantic)
        path = params.get('path') if isinstance(
            params, dict) else getattr(params, 'path', None)
        if not path:
            raise ValueError("Output path not specified")

        # OPTIMIZATION: Use Streaming Sinks where possible
        if fmt == "CSV":
            # sink_csv is streaming
            lazy_frame.sink_csv(path)

        elif fmt == "Parquet":
            compression = params.get('compression', 'snappy') if isinstance(
                params, dict) else getattr(params, 'compression', 'snappy')
            valid_compression = cast(
                Literal['snappy', 'zstd', 'gzip', 'lz4', 'uncompressed', 'brotli'], compression)
            # sink_parquet is streaming
            lazy_frame.sink_parquet(path, compression=valid_compression)

        elif fmt == "IPC":
            compression = params.get('compression', 'uncompressed') if isinstance(
                params, dict) else getattr(params, 'compression', 'uncompressed')
            valid_compression = cast(
                Literal['uncompressed', 'lz4', 'zstd'], compression)
            # sink_ipc is streaming
            lazy_frame.sink_ipc(path, compression=valid_compression)

        elif fmt == "NDJSON":
            # sink_ndjson is streaming
            lazy_frame.sink_ndjson(path)

        elif fmt == "Excel":
            # Native Polars (Fast Eager Write)
            df = lazy_frame.collect()
            df.write_excel(path)

        elif fmt == "JSON":
            # Native Polars (Fast Eager Write)
            df = lazy_frame.collect()
            df.write_json(path)

        elif fmt == "SQLite":
            # SQLite Export (Eager)
            table = params.get('table', 'data') if isinstance(
                params, dict) else getattr(params, 'table', 'data')
            if_exists = params.get('if_exists', 'replace') if isinstance(
                params, dict) else getattr(params, 'if_exists', 'replace')
            valid_if_exists = cast(
                Literal['fail', 'replace', 'append'], if_exists)

            df = lazy_frame.collect()
            # Construct connection string
            # write_database supports "sqlite:///path.db"
            uri = f"sqlite:///{path}"
            df.write_database(table_name=table, connection=uri,
                              if_table_exists=valid_if_exists, engine="sqlalchemy")

        result_container['status'] = "Done"
    except Exception as e:
        result_container['status'] = f"Error: {e}"
