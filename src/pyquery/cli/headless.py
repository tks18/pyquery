import json
import sys
import os
import time
from typing import List, Dict, Any

from pyquery.backend.engine import PyQueryEngine
from pyquery.core.models import RecipeStep
from pyquery.core.io_params import FileLoaderParams, ParquetExportParams, CsvExportParams


def run_headless(args):
    """
    Executes a recipe in headless mode.
    args: Namespace from argparse (source, recipe, output, format)
    """

    # 1. Initialize Engine
    print(f"⚡ Starting PyQuery Engine...")
    engine = PyQueryEngine()

    # 2. Load Recipe
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

    # 3. Load Data
    print(f"📥 Loading source: {args.source}")
    loader_params = FileLoaderParams(path=args.source, alias="cli_data")

    try:
        lf = engine.run_loader("File", loader_params)
        if lf is None:
            print("❌ Failed to load file.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Loader Error: {e}")
        sys.exit(1)

    engine.add_dataset("cli_data", lf)

    # 4. Apply Recipe (Validation Check)
    print("⚙️ Validating recipe...")
    try:
        engine.apply_recipe(lf, recipe_data)
    except Exception as e:
        print(f"❌ Transformation Error: {e}")
        sys.exit(1)

    # 5. Export
    print(f"📤 Exporting to {args.output} ({args.format})...")

    exporter_name = args.format
    export_params = {}

    if args.format.lower() == "parquet":
        exporter_name = "Parquet"
        export_params = ParquetExportParams(
            path=args.output, compression="snappy")
    elif args.format.lower() == "csv":
        exporter_name = "CSV"
        export_params = CsvExportParams(path=args.output)

    try:
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
