import json
import sys
import os
import time
import uuid
from typing import List, Dict, Any

from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io_params import (
    FileLoaderParams, SqlLoaderParams, ApiLoaderParams,
    ParquetExportParams, CsvExportParams, ExcelExportParams,
    JsonExportParams, NdjsonExportParams, IpcExportParams, SqliteExportParams
)


def run_headless(args):
    """
    Executes a recipe in headless mode.
    args: Namespace from argparse (source, recipe, output, format)
    """

    # 1. Initialize Engine
    print(f"⚡ Starting PyQuery Engine...")
    engine = PyQueryEngine()

    # 2. Load Recipe
    if args.recipe:
        print(f"📖 Loading recipe from {args.recipe}...")
        try:
            with open(args.recipe, 'r') as f:
                recipe_data = json.load(f)
                if not isinstance(recipe_data, list):
                    print("Error: Recipe must be a JSON list of steps.")
                    sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to read recipe: {e}")
            sys.exit(1)
    else:
        print("ℹ️ No recipe provided, performing direct conversion.")
        recipe_data = []

    # 2.5 Parse Inline Steps
    if getattr(args, 'step', None):
        print(f"🧩 Parsing {len(args.step)} inline steps...")
        for s_str in args.step:
            try:
                step_obj = json.loads(s_str)
                if not isinstance(step_obj, dict) or 'type' not in step_obj:
                    print(
                        f"⚠️ Warning: Invalid step (must be object with 'type'): {s_str}")
                    sys.exit(1)
                recipe_data.append(step_obj)
            except Exception as e:
                print(f"❌ Failed to parse step JSON: {s_str}")
                print(f"   Error: {e}")
                sys.exit(1)

    # 2.6 Save Recipe (If requested)
    if getattr(args, 'save_recipe', False):
        try:
            source_dir = os.path.dirname(os.path.abspath(args.source))
            base_name = os.path.splitext(os.path.basename(args.source))[0]
            unique_id = uuid.uuid4().hex[:8]
            recipe_filename = f"{base_name}-shan-pyquery-{unique_id}.json"
            recipe_path = os.path.join(source_dir, recipe_filename)

            print(f"💾 Saving recipe to {recipe_path}...")
            with open(recipe_path, 'w') as f:
                json.dump(recipe_data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Warning: Failed to save recipe: {e}")

    # 3. Load Data
    print(f"📥 Loading source: {args.source}")
    try:
        if args.type == "file":
            loader_params = FileLoaderParams(
                path=args.source,
                sheet=args.sheet_name if hasattr(args, 'sheet_name') else "Sheet1",
                alias="cli_data",
                process_individual=getattr(args, 'process_individual', False)
            )
            result = engine.run_loader("File", loader_params)

        elif args.type == "sql":
            if not args.sql_query:
                print("❌ Error: --sql-query is required for SQL input.")
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
            print(f"❌ Error: Unknown input type: {args.type}")
            sys.exit(1)

        if result is None:
            print("❌ Failed to load data.")
            sys.exit(1)
        
        # Extract LazyFrame(s) and metadata
        lf_or_lfs, metadata = result if isinstance(result, tuple) else (result, {})
    except Exception as e:
        print(f"❌ Loader Error: {e}")
        sys.exit(1)

    # Add dataset to engine (handles both single LF and list)
    engine.add_dataset("cli_data", lf_or_lfs, metadata=metadata)
    
    # Show processing mode info
    if metadata.get("process_individual", False):
        file_count = metadata.get("file_count", 1)
        print(f"📁 Individual processing enabled: {file_count} files will be processed separately")
    
    # 4. Apply Recipe (Validation Check)
    print("⚙️ Validating recipe...")
    try:
        # Get the dataset from engine (returns preview LF, which is OK for validation)
        validation_lf = engine.get_dataset("cli_data")
        if validation_lf is None:
            raise ValueError("Failed to load dataset for validation")
        engine.apply_recipe(validation_lf, recipe_data)
    except Exception as e:
        print(f"❌ Transformation Error: {e}")
        sys.exit(1)

    # 5. Export
    print(f"📤 Exporting to {args.output} ({args.format})...")

    exporter_name = args.format
    export_params = {}

    if args.format.lower() == "parquet":
        exporter_name = "Parquet"
        # Use compression arg if provided, default to snappy
        compression = args.compression if args.compression else "snappy"
        export_params = ParquetExportParams(
            path=args.output, compression=compression)

    elif args.format.lower() == "csv":
        exporter_name = "CSV"
        export_params = CsvExportParams(path=args.output)

    elif args.format.lower() in ["excel", "xlsx"]:
        exporter_name = "Excel"
        export_params = ExcelExportParams(path=args.output)

    elif args.format.lower() == "json":
        exporter_name = "JSON"
        export_params = JsonExportParams(path=args.output)

    elif args.format.lower() == "ndjson":
        exporter_name = "NDJSON"
        export_params = NdjsonExportParams(path=args.output)

    elif args.format.lower() in ["ipc", "arrow"]:
        exporter_name = "IPC"
        compression = args.compression if args.compression else "uncompressed"
        export_params = IpcExportParams(
            path=args.output, compression=compression)

    elif args.format.lower() == "sqlite":
        exporter_name = "SQLite"
        table = args.table if args.table else "data"
        if_exists = args.if_exists if args.if_exists else "replace"
        export_params = SqliteExportParams(
            path=args.output, table=table, if_exists=if_exists)

    try:
        print(f"📋 Recipe has {len(recipe_data)} steps")
        if recipe_data:
            print(f"   Steps: {[s.get('type', 'unknown') if isinstance(s, dict) else s.type for s in recipe_data]}")
        
        job_id = engine.start_export_job(
            "cli_data", recipe_data, exporter_name, export_params)

        # Poll
        while True:
            info = engine.get_job_status(job_id)

            if info is None:
                # Should not happen for a valid job_id usually, but handle it
                time.sleep(0.5)
                continue

            if info.status == "COMPLETED":
                print(f"✅ Success! Written {info.size_str} to {args.output}")
                break
            elif info.status == "FAILED":
                print(f"❌ Export Failed: {info.error}")
                sys.exit(1)
            else:
                time.sleep(0.1)

    except Exception as e:
        print(f"❌ Export Error: {e}")
        sys.exit(1)
