import json
import sys
import os
import time
import uuid
from typing import List, Dict, Any

from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io_params import FileLoaderParams, ParquetExportParams, CsvExportParams


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
    loader_params = FileLoaderParams(path=args.source, alias="cli_data")

    try:
        result = engine.run_loader("File", loader_params)
        if result is None:
            print("❌ Failed to load file.")
            sys.exit(1)
        lf, _ = result
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
