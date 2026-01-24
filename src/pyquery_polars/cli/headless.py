import json
import sys
import os
import time
import uuid
import random
from typing import List, Dict, Any

from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io import (
    FileLoaderParams, SqlLoaderParams, ApiLoaderParams,
    ParquetExportParams, CsvExportParams, ExcelExportParams,
    JsonExportParams, NdjsonExportParams, IpcExportParams, SqliteExportParams,
    FileFilter, ItemFilter, FilterType
)
from pyquery_polars.cli.branding import init_logging, log_step, log_error, log_success, log_table

def run_headless(args):
    """
    Executes a recipe in headless mode.
    args: Namespace from argparse (source, recipe, output, format)
    """
    init_logging()
    
    # 1. Initialize Engine
    log_step("Initializing Engine...", module="KERNEL", icon="⚡")
    engine = PyQueryEngine()

    # 1.5 Validation
    if getattr(args, 'export_individual', False) and not getattr(args, 'process_individual', False):
        log_error("Configuration Error", "--export-individual requires --process-individual")
        sys.exit(1)

    # 2. Load Recipe
    if args.recipe:
        log_step(f"Loading recipe from {os.path.basename(args.recipe)}...", module="CONFIG", icon="📖")
        try:
            with open(args.recipe, 'r') as f:
                recipe_data = json.load(f)
                if not isinstance(recipe_data, list):
                    log_error("Invalid Recipe", "Must be a JSON list.")
                    sys.exit(1)
        except Exception as e:
            log_error("Recipe Load Failed", str(e))
            sys.exit(1)
    else:
        log_step("No recipe provided (Direct Conversion Mode)", module="CONFIG", icon="ℹ️")
        recipe_data = []

    # 2.5 Parse Inline Steps
    if getattr(args, 'step', None):
        log_step(f"Parsing {len(args.step)} inline steps...", module="CONFIG", icon="🧩")
        for s_str in args.step:
            try:
                step_obj = json.loads(s_str)
                if not isinstance(step_obj, dict) or 'type' not in step_obj:
                    log_error("Invalid inline step", s_str)
                    sys.exit(1)
                recipe_data.append(step_obj)
            except Exception as e:
                log_error("Step Parse Failed", f"{s_str}: {e}")
                sys.exit(1)

    # 2.6 Save Recipe (If requested)
    if getattr(args, 'save_recipe', False):
        try:
            source_dir = os.path.dirname(os.path.abspath(args.source))
            base_name = os.path.splitext(os.path.basename(args.source))[0]
            unique_id = uuid.uuid4().hex[:8]
            recipe_filename = f"{base_name}-shan-pyquery-{unique_id}.json"
            recipe_path = os.path.join(source_dir, recipe_filename)

            log_step(f"Saving recipe snapshot...", module="ARTIFACT", icon="💾")
            with open(recipe_path, 'w') as f:
                json.dump(recipe_data, f, indent=2)

        except Exception as e:
            log_error("Warning: Failed to save recipe", str(e))

    # 3. Load Data
    log_step(f"Loading source: {args.source}", module="I/O", icon="📥")
    try:
        if args.type == "file":
            loader_params = FileLoaderParams(
                path=args.source,
                sheet=args.sheet_name if hasattr(args, 'sheet_name') else "Sheet1",
                alias="cli_data",
                process_individual=getattr(args, 'process_individual', False),
                include_source_info=getattr(args, 'include_source_info', False)
            )
            result = engine.run_loader("File", loader_params)

        elif args.type == "sql":
            if not args.sql_query:
                log_error("Missing SQL Query", "--sql-query is required.")
                sys.exit(1)
            loader_params = SqlLoaderParams(
                conn=args.source,
                query=args.sql_query,
                alias="cli_data"
            )
            result = engine.run_loader("Sql", loader_params)

        elif args.type == "api":
            url = args.api_url if args.api_url else args.source
            loader_params = ApiLoaderParams(
                url=url,
                alias="cli_data"
            )
            result = engine.run_loader("Api", loader_params)

        else:
            log_error("Unknown Type", args.type)
            sys.exit(1)

        if result is None:
            log_error("Load Failed", "Engine returned None")
            sys.exit(1)
        
        # Extract LazyFrame(s) and metadata
        lf_or_lfs, metadata = result if isinstance(result, tuple) else (result, {})
    except Exception as e:
        log_error("Loader Exception", str(e))
        sys.exit(1)

    # Add dataset to engine (handles both single LF and list)
    engine.add_dataset("cli_data", lf_or_lfs, metadata=metadata)
    
    # Show processing mode info
    if metadata.get("process_individual", False):
        file_count = metadata.get("file_count", 1)
        log_step(f"Batch Processing Enabled: {file_count} files", module="OPTIMIZER", icon="🔥")
    
    # 4. Apply Recipe (Validation Check)
    recipe_len = len(recipe_data)
    if recipe_len > 0:
        log_step(f"Validating {recipe_len} steps...", module="PLANNER", icon="⚙️")
        try:
            # Get the dataset from engine (returns preview LF, which is OK for validation)
            validation_lf = engine.get_dataset("cli_data")
            if validation_lf is None:
                raise ValueError("Failed to load dataset for validation")
            engine.apply_recipe(validation_lf, recipe_data)
        except Exception as e:
            log_error("Validation Failed", str(e))
            sys.exit(1)
    else:
        log_step("Skipping validation (Empty Recipe)", module="PLANNER", icon="⏭️")

    # 5. Export
    log_step(f"Exporting to {args.format}...", module="EXPORT", icon="📤")

    # Resolve Output Path (Ensure Pattern Logic)
    # Mapping
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

    target_path = args.output
    expected_ext = FMT_EXT_MAP.get(args.format.lower(), "")

    # 1. Handle Directory Input
    if os.path.isdir(target_path) or target_path.endswith(os.sep) or (os.altsep and target_path.endswith(os.altsep)):
        if os.path.exists(target_path) and not os.path.isdir(target_path):
             pass # Logic below handles file
        else:
             # It is a dir or looks like one
             target_path = os.path.join(target_path, f"export{expected_ext}")

    # 2. Handle Missing Extension
    if expected_ext:
        root, mk_ext = os.path.splitext(target_path)
        if not mk_ext:
            target_path = f"{target_path}{expected_ext}"
        elif mk_ext.lower() != expected_ext:
             pass 
    
    # Update Args safely
    args.output = target_path
    if args.output != sys.argv[sys.argv.index("--output") + 1] if "--output" in sys.argv else args.output:
         log_step(f"Resolved Path: {args.output}", module="PATH", icon="🎯")

    exporter_name = args.format
    export_params = {}

    export_individual = getattr(args, 'export_individual', False)

    if args.format.lower() == "parquet":
        exporter_name = "Parquet"
        # Use compression arg if provided, default to snappy
        compression = args.compression if args.compression else "snappy"
        export_params = ParquetExportParams(
            path=args.output, compression=compression, export_individual=export_individual)

    elif args.format.lower() == "csv":
        exporter_name = "CSV"
        export_params = CsvExportParams(path=args.output, export_individual=export_individual)

    elif args.format.lower() in ["excel", "xlsx"]:
        exporter_name = "Excel"
        export_params = ExcelExportParams(path=args.output, export_individual=export_individual)

    elif args.format.lower() == "json":
        exporter_name = "JSON"
        export_params = JsonExportParams(path=args.output, export_individual=export_individual)

    elif args.format.lower() == "ndjson":
        exporter_name = "NDJSON"
        export_params = NdjsonExportParams(path=args.output, export_individual=export_individual)

    elif args.format.lower() in ["ipc", "arrow"]:
        exporter_name = "IPC"
        compression = args.compression if args.compression else "uncompressed"
        export_params = IpcExportParams(
            path=args.output, compression=compression, export_individual=export_individual)

    elif args.format.lower() == "sqlite":
        exporter_name = "SQLite"
        table = args.table if args.table else "data"
        if_exists = args.if_exists if args.if_exists else "replace"
        export_params = SqliteExportParams(
            path=args.output, table=table, if_exists=if_exists)

    try:
        job_id = engine.start_export_job(
            "cli_data", recipe_data, exporter_name, export_params)

        # Poll
        while True:
            info = engine.get_job_status(job_id)

            if info is None:
                time.sleep(0.5)
                continue

            if info.status == "COMPLETED":
               
                # File Table
                if info.file_details:
                    print("\n")
                    log_table(info.file_details, title="Artifact Manifest")
                else:
                    print("\n")
                    log_step(f"Success! Size: {info.size_str}", module="DONE", icon="✅")
                    
                break
            elif info.status == "FAILED":
                log_error("Export Failed", info.error or "Unknown Error")
                sys.exit(1)
            else:
                # Running... 
                time.sleep(0.5)

    except Exception as e:
        log_error("Job Exception", str(e))
        sys.exit(1)
