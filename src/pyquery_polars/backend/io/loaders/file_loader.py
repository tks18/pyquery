from typing import Literal, Optional
from pydantic import BaseModel

import os
import polars as pl
import uuid
import gc

from pyquery_polars.backend.io.loaders.base import BaseLoader, LoaderOutput
from pyquery_polars.backend.io.helpers import FilterEngine, ExcelEngine
from pyquery_polars.core.io import FileLoaderParams


class FileloaderOutput(BaseModel):
    input_type: Literal["file", "folder"]
    input_format: str
    file_list: list[str]
    file_count: int
    process_individual: bool
    source_info: bool
    clean_headers: bool


class Fileloader(BaseLoader[FileLoaderParams, FileloaderOutput]):
    """
    Loads data from a local file or folder.
    Supports CSV, Excel, Parquet, JSON, NDJSON, IPC 
    """

    def clean_header_name(self, col: str) -> str:
        """Normalize column name by replacing whitespace with single spaces and stripping."""
        return " ".join(col.strip().split())

    def run(self) -> Optional[LoaderOutput[FileloaderOutput]]:
        """
        Load files into LazyFrame(s).

        Returns:
            FileloaderOutput: if successful returns the lf with metadata otherwise none
        """

        path = self.params.path
        file_filters = self.params.filters
        sheets = self.params.sheet
        tables = self.params.table
        sheet_filters = self.params.sheet_filters
        table_filters = self.params.table_filters
        process_individual = self.params.process_individual
        include_source_info = self.params.include_source_info
        clean_headers = self.params.clean_headers
        dataset_alias = self.params.alias

        if not path:
            return None

        files = FilterEngine.resolve_file_paths(path, file_filters)

        if not files:
            return None

        # Determine file format
        exts = {os.path.splitext(f)[1].lower() for f in files}
        ext = list(exts)[0] if len(exts) == 1 else ".mixed"

        # OPTIMIZATION: Try Bulk Scan for homogeneous files
        # Only if NOT processing individual, NOT including source info, AND NOT cleaning headers
        if len(exts) == 1 and not process_individual and not include_source_info and not clean_headers:
            try:
                lf = None
                if ext == ".csv":
                    lf = pl.scan_csv(
                        files, infer_schema_length=0, encoding="utf8")
                elif ext == ".parquet":
                    lf = pl.scan_parquet(files)
                elif ext in [".arrow", ".ipc", ".feather"]:
                    lf = pl.scan_ipc(files)
                elif ext == ".ndjson":
                    lf = pl.scan_ndjson(files, infer_schema_length=0)

                if isinstance(lf, pl.LazyFrame):
                    meta = FileloaderOutput(
                        input_type="folder" if len(files) > 1 else "file",
                        input_format=ext,
                        file_list=files,
                        file_count=len(files),
                        process_individual=process_individual,
                        source_info=include_source_info,
                        clean_headers=clean_headers
                    )
                    loader_output = LoaderOutput(
                        lf=lf,
                        meta=meta
                    )
                    return loader_output
                else:
                    print(
                        f"Unknown Error during Bulk scan using Polars, falling back to iterative")

            except Exception as e:
                print(f"Bulk scan error, falling back to iterative: {e}")

        # Staging folder cache to ensure all files in this batch go to same unique folder
        batch_staging_dir = None

        # Fallback: Iterative
        lfs = []
        for f in files:
            file_ext = os.path.splitext(f)[1].lower()
            try:
                current_lf = None
                if file_ext == ".csv":
                    # Strict UTF-8
                    current_lf = pl.scan_csv(
                        f, infer_schema_length=0, encoding="utf8")
                elif file_ext == ".parquet":
                    current_lf = pl.scan_parquet(f)
                elif file_ext in [".arrow", ".ipc", ".feather"]:
                    current_lf = pl.scan_ipc(f)
                elif file_ext in [".xlsx", ".xls", ".xlsm", ".xlsb"]:
                    try:
                        # Initialize staging dir for this batch if needed
                        if batch_staging_dir is None:
                            # Use alias if provided, else first filename
                            base_for_folder = dataset_alias if dataset_alias else os.path.basename(
                                files[0])
                            batch_staging_dir = self.staging.create_unique_staging_folder(
                                base_for_folder)

                        staging_path = batch_staging_dir

                        # OPTIMIZATION: Single metadata extraction per file
                        excel_meta = ExcelEngine.get_excel_metadata(f)

                        # Determine what to load
                        # Priority: Table Name(s) > Sheet Name(s) > Default Sheet1

                        # Normalize inputs to lists
                        target_tables = []

                        if tables == "__ALL_TABLES__" or tables == ["__ALL_TABLES__"]:
                            target_tables = excel_meta['tables']
                        elif tables:
                            if isinstance(tables, list):
                                target_tables = tables
                            else:
                                target_tables = [tables]

                        target_sheets = []

                        if not target_tables:
                            if table_filters:
                                # DYNAMIC TABLE SELECTION
                                all_tables = excel_meta['tables']
                                # Reuse _check_item_match (generic enough)
                                target_tables = [t for t in all_tables if all(
                                    FilterEngine.check_item_match(t, tf) for tf in table_filters)]

                            elif sheet_filters is not None:
                                # DYNAMIC SHEET SELECTION
                                all_sheets = excel_meta['sheets']
                                # Apply filters
                                target_sheets = [s for s in all_sheets if all(
                                    FilterEngine.check_item_match(s, sf) for sf in sheet_filters)]

                            elif sheets == "__ALL_SHEETS__" or sheets == ["__ALL_SHEETS__"]:
                                target_sheets = excel_meta['sheets']

                            elif isinstance(sheets, list):
                                target_sheets = sheets

                            else:
                                # Single sheet string or None -> Default
                                if sheets:
                                    target_sheets = [sheets]
                                else:
                                    # Use first sheet from metadata
                                    if excel_meta['sheets']:
                                        target_sheets = [
                                            excel_meta['sheets'][0]]
                                    else:
                                        target_sheets = ["Sheet1"]

                        # 1. LOAD TABLES (via Polars read_excel -> Parquet)
                        if target_tables:
                            for t_name in target_tables:
                                try:
                                    # Polars read_excel with table_name
                                    df = pl.read_excel(
                                        f, table_name=t_name, engine="calamine", infer_schema_length=0)

                                    if clean_headers:
                                        new_cols = {c: self.clean_header_name(
                                            c) for c in df.columns}
                                        df = df.rename(new_cols)

                                    if include_source_info:
                                        df = df.with_columns([
                                            pl.lit(os.path.abspath(f)).alias(
                                                "__pyquery_source_path__"),
                                            pl.lit(f"{os.path.basename(f)}[table][{t_name}]").alias(
                                                "__pyquery_source_name__"),
                                            pl.lit(file_ext).alias(
                                                "__pyquery_source_ext__")
                                        ])

                                    # Write to Staging
                                    out_name = f"staged_{uuid.uuid4().hex[:8]}_{t_name}.parquet"
                                    out_path = os.path.join(
                                        staging_path, out_name)
                                    df.write_parquet(out_path)

                                    # MEMORY CLEANUP: Explicit deletion
                                    del df

                                    # Append LazyFrame reference
                                    lfs.append(pl.scan_parquet(out_path))

                                except Exception as e:
                                    print(
                                        f"Failed to load table {t_name}: {e}")

                        # 2. LOAD SHEETS (via Polars read_excel -> Parquet)
                        if target_sheets:
                            for s_name in target_sheets:
                                try:
                                    # pl.read_excel is eager
                                    df = pl.read_excel(
                                        f, sheet_name=s_name, engine="calamine", infer_schema_length=0)

                                    if clean_headers:
                                        new_cols = {c: self.clean_header_name(
                                            c) for c in df.columns}
                                        df = df.rename(new_cols)

                                    if include_source_info:
                                        df = df.with_columns([
                                            pl.lit(os.path.abspath(f)).alias(
                                                "__pyquery_source_path__"),
                                            pl.lit(f"{os.path.basename(f)}[sheet][{s_name}]").alias(
                                                "__pyquery_source_name__"),
                                            pl.lit(file_ext).alias(
                                                "__pyquery_source_ext__")
                                        ])

                                    # Write to Staging
                                    out_name = f"staged_{uuid.uuid4().hex[:8]}_{s_name}.parquet"
                                    out_path = os.path.join(
                                        staging_path, out_name)
                                    df.write_parquet(out_path)

                                    # MEMORY CLEANUP: Explicit deletion
                                    del df

                                    # Append LazyFrame reference
                                    lfs.append(pl.scan_parquet(out_path))

                                except Exception as e:
                                    print(
                                        f"Failed to load sheet {s_name}: {e}")

                        # Ensure common block is skipped
                        current_lf = None

                    except Exception as ex:
                        print(f"Excel Load Error {f}: {ex}")
                        # Ensure common block is skipped on error too
                        current_lf = None

                elif file_ext == ".json":
                    current_lf = pl.scan_ndjson(f, infer_schema_length=0)

                # --- POST-SCAN PROCESSING (Common) ---
                if current_lf is not None:
                    # 1. Clean Headers (Lazy Rename)
                    if clean_headers and file_ext != ".xlsx" and file_ext != ".xls":
                        # We need the schema to rename. collect_schema() is fast.
                        try:
                            base_cols = current_lf.collect_schema().names()
                            rename_map = {c: self.clean_header_name(
                                c) for c in base_cols}
                            current_lf = current_lf.rename(rename_map)
                        except Exception as e:
                            print(f"Header cleaning failed for {f}: {e}")

                    # 2. Source Info
                    if include_source_info:
                        abs_path = os.path.abspath(f)
                        name = os.path.basename(f)
                        ext_val = os.path.splitext(f)[1]

                        current_lf = current_lf.with_columns([
                            pl.lit(abs_path).alias("__pyquery_source_path__"),
                            pl.lit(name).alias("__pyquery_source_name__"),
                            pl.lit(ext_val).alias("__pyquery_source_ext__")
                        ])

                    lfs.append(current_lf)

            except Exception as e:
                print(f"Error loading {f}: {e}")

        if len(files) > 5:  # Only for batch operations
            gc.collect()

        if not lfs:
            return None

        # Build metadata
        meta = FileloaderOutput(
            input_type="folder" if len(files) > 1 else "file",
            input_format=ext,
            file_list=files,
            file_count=len(files),
            process_individual=process_individual,
            source_info=include_source_info,
            clean_headers=clean_headers
        )

        # Decision: Return list or concatenated
        if process_individual:
            return LoaderOutput(lf=lfs, meta=meta)
        else:
            combined = lfs[0]
            if len(lfs) > 1:
                combined = pl.concat(lfs, how="diagonal")
            return LoaderOutput(lf=combined, meta=meta)
