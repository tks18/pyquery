import json
import sys
import os
import time
import uuid
import polars as pl
from typing import List, Dict, Any, Optional

from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io import (
    FileLoaderParams, SqlLoaderParams, ApiLoaderParams,
    ParquetExportParams, CsvExportParams, ExcelExportParams,
    JsonExportParams, NdjsonExportParams, IpcExportParams, SqliteExportParams,
    FileFilter, ItemFilter, FilterType
)
from pyquery_polars.cli.branding import (
    init_logging, log_step, log_error, log_success,
    log_table, log_progress, console
)
from rich.tree import Tree
from rich.panel import Panel

# Constants
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


def parse_filter_string(f_str: str, default_target: str) -> Dict[str, str]:
    """Parse filter string 'type:value[:target]'."""
    parts = f_str.split(":", 2)
    type_val = parts[0]
    val = parts[1] if len(parts) > 1 else ""
    target = parts[2] if len(parts) > 2 else default_target
    return {"type": type_val, "value": val, "target": target}


def build_file_filters(args) -> Optional[List[FileFilter]]:
    if not args.file_filter:
        return None
    filters = []
    for f in args.file_filter:
        p = parse_filter_string(f, "filename")
        try:
            ft = FilterType(p["type"])
            filters.append(FileFilter(
                type=ft, value=p["value"], target=p["target"]))  # type: ignore
        except Exception:
            log_error(f"Invalid Filter Type: {p['type']}",
                      "Supported: glob, regex, contains, exact, is_not")
            sys.exit(1)
    return filters


def build_item_filters(arg_list, default_target="sheet_name") -> Optional[List[ItemFilter]]:
    if not arg_list:
        return None
    filters = []
    for f in arg_list:
        p = parse_filter_string(f, default_target)
        try:
            ft = FilterType(p["type"])
            filters.append(ItemFilter(
                # type: ignore
                type=ft, value=p["value"], target=default_target))
        except Exception:
            log_error(f"Invalid Filter Type: {p['type']}",
                      "Supported: glob, regex, contains, exact, is_not")
            sys.exit(1)
    return filters


def resolve_output_path(base_path: str, format_str: str, is_dir: bool = False) -> str:
    """Intelligently resolve the output path."""
    expected_ext = FMT_EXT_MAP.get(format_str.lower(), "")

    if is_dir:
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
        return base_path

    if os.path.isdir(base_path) or base_path.endswith(os.sep) or (os.altsep and base_path.endswith(os.altsep)):
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
        return os.path.join(base_path, f"export{expected_ext}")

    root, mk_ext = os.path.splitext(base_path)
    if not mk_ext:
        return f"{base_path}{expected_ext}"

    return base_path


def resolve_exporter_name(fmt_str: str) -> str:
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


def get_export_params(format_str: str, output_path: str, args) -> Any:
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


def run_headless(args):
    """
    Executes a recipe in headless mode with Premium CLI features.
    """
    init_logging()

    # --- 0. STRICT VALIDATION ---
    if args.project and args.source:
        log_error("Argument Error",
                  "Cannot specify both --project and --source. Choose one.")
        sys.exit(1)

    if not args.project and not args.source:
        log_error("Argument Error",
                  "Must specify either --project <file> or --source <file/url>.")
        sys.exit(1)

    # --- 1. INITIALIZE ENGINE (with Flair) ---
    if not args.quiet:
        log_step("Initializing Query Engine...", module="KERNEL", icon="⚡")

    engine = PyQueryEngine()

    datasets_to_process = []  # List of (name, recipe_steps)

    # =========================================================================
    # MODE A: PROJECT MODE
    # =========================================================================
    if args.project:
        project_path = os.path.abspath(args.project)
        if not os.path.exists(project_path):
            log_error("Project Not Found", f"{project_path}")
            sys.exit(1)

        if not args.quiet:
            log_step(
                f"Loading Project: {os.path.basename(project_path)}", module="PROJECT", icon="📂")

        try:
            with log_progress("Hydrating Project State...", module="LOADER") as p:
                result = engine.load_project_from_file(
                    project_path, mode="replace")
                p.update(completed=100)

            if not result.success:
                log_error("Project Load Failed", "\n".join(result.errors))
                sys.exit(1)

            if result.warnings and not args.quiet:
                for w in result.warnings:
                    console.print(f"[dim yellow]Warning: {w}[/dim yellow]")

        except Exception as e:
            log_error("Critical Project Load Error", str(e))
            sys.exit(1)

        available_datasets = engine.get_dataset_names()
        target_datasets = available_datasets

        if args.dataset:
            target_datasets = [
                d for d in available_datasets if d in args.dataset]
            if not target_datasets:
                log_error(
                    "Dataset Error", f"None of the requested datasets found: {args.dataset}")
                log_error("Available", ", ".join(available_datasets))
                sys.exit(1)

        for ds_name in target_datasets:
            datasets_to_process.append((ds_name, []))

        if not args.quiet:
            log_step(
                f"Selected {len(target_datasets)} datasets for processing.", module="PLANNER", icon="🎯")

    # =========================================================================
    # MODE B: SOURCE MODE (Single File / SQL)
    # =========================================================================
    else:
        # Resolve Alias
        base_ds_name = getattr(args, 'alias', None) or "cli_data"

        # Resolve SQL File if provided
        if args.sql_query:
            if os.path.exists(args.sql_query):
                try:
                    with open(args.sql_query, 'r', encoding='utf-8') as f:
                        args.sql_query = f.read()
                except Exception as e:
                    log_error("SQL File Error",
                              f"Failed to read SQL file: {e}")
                    sys.exit(1)

        # Resolve Transform SQL File if provided
        if args.transform_sql:
            if os.path.exists(args.transform_sql):
                try:
                    with open(args.transform_sql, 'r', encoding='utf-8') as f:
                        args.transform_sql = f.read()
                except Exception as e:
                    log_error("SQL File Error",
                              f"Failed to read Transform SQL file: {e}")
                    sys.exit(1)

        if not args.quiet:
            if args.type == "sql":
                log_step(f"Connecting to SQL Source...",
                         module="SQL", icon="🔌")
            else:
                log_step(
                    f"Loading Source: {args.source} as '{base_ds_name}'", module="I/O", icon="📥")

        try:
            # --- SPLIT SHEETS LOGIC ---
            if getattr(args, 'split_sheets', False) and args.type == "file":
                # Only valid for Excel initially
                resolved_files = engine.resolve_files(
                    args.source, build_file_filters(args))

                if not resolved_files:
                    log_error("No Files Found", f"Pattern: {args.source}")
                    sys.exit(1)

                loaded_count = 0

                with log_progress("Splitting Sheets & Tables...", module="SPLITTER") as p:
                    total_work = len(resolved_files)
                    p.update(total=total_work)

                    for f_path in resolved_files:
                        ext = os.path.splitext(f_path)[1].lower()
                        if ext not in [".xlsx", ".xls", ".xlsm", ".xlsb"]:
                            # Non-Excel: Just load normally as base name
                            pass

                        # Get Sheets and Tables
                        tables = engine.get_file_table_names(f_path)
                        sheets = engine.get_file_sheet_names(f_path)

                        # Filter Sheets/Tables if filters exist
                        sheet_filters = build_item_filters(
                            args.sheet_filter, "sheet_name")
                        table_filters = build_item_filters(
                            args.table_filter, "table_name")

                        targets = []

                        # Logic:
                        # 1. Explicit Filters
                        # 2. Excel Mode Override
                        # 3. Default Smart (Tables > Sheets)

                        if sheet_filters or table_filters:
                            # Explicit Mode
                            if table_filters:
                                for t in tables:
                                    # Simple filter check for now (Assume matched if filter logic was consistent,
                                    # here we just iterate. To match strictly we'd need match logic.
                                    # Users rely on CLI to say what they want.
                                    targets.append(("table", t))

                            if sheet_filters:
                                for s in sheets:
                                    targets.append(("sheet", s))

                            # Filter the list
                            final_targets = []
                            for kind, name in targets:
                                active_filters = table_filters if kind == "table" else sheet_filters
                                if not active_filters:
                                    continue

                                match = True
                                for f in active_filters:
                                    val = f.value
                                    if f.type == FilterType.EXACT:
                                        match = val == name
                                    elif f.type == FilterType.CONTAINS:
                                        match = val.lower() in name.lower()
                                    elif f.type == FilterType.GLOB:
                                        import fnmatch
                                        match = fnmatch.fnmatch(
                                            name.lower(), val.lower())
                                    if not match:
                                        break

                                if match:
                                    final_targets.append((kind, name))

                            targets = final_targets

                        else:
                            # Mode Logic
                            excel_mode = getattr(args, 'excel_mode', "auto")

                            if excel_mode == "tables":
                                for t in tables:
                                    targets.append(("table", t))
                            elif excel_mode == "sheets":
                                for s in sheets:
                                    targets.append(("sheet", s))
                            else:
                                # Auto
                                if tables:
                                    for t in tables:
                                        targets.append(("table", t))
                                else:
                                    for s in sheets:
                                        targets.append(("sheet", s))

                        # Load Loop
                        f_base = os.path.splitext(os.path.basename(f_path))[0]

                        for kind, target_name in targets:
                            # Clean Name
                            s_name = "".join([c if c.isalnum() or c in (
                                '-', '_') else '_' for c in target_name])
                            alias = f"{f_base}_{s_name}"

                            l_params = FileLoaderParams(
                                path=f_path,  # Specific file
                                sheet=target_name if kind == "sheet" else None,
                                table=target_name if kind == "table" else None,
                                alias=alias,
                                clean_headers=getattr(
                                    args, 'clean_headers', False),
                                include_source_info=getattr(
                                    args, 'include_source_info', False)
                            )

                            try:
                                res = engine.run_loader("File", l_params)
                                if res:
                                    flf, meta = res if isinstance(
                                        res, tuple) else (res, {})
                                    engine.add_dataset(
                                        alias, flf, metadata=meta)

                                    # AUTO-INFER LOGIC
                                    recipe_steps = []
                                    if getattr(args, 'auto_infer', False):
                                        cast_step = engine.auto_infer_dataset(
                                            alias)
                                        if cast_step:
                                            recipe_steps.append(
                                                cast_step.model_dump())

                                    datasets_to_process.append(
                                        (alias, recipe_steps))
                                    loaded_count += 1
                            except Exception:
                                pass

                        p.advance(1)

                if loaded_count == 0:
                    log_error("Split Logic",
                              "No datasets loaded via split-sheets.")
                    sys.exit(1)

            # --- SPLIT FILES LOGIC ---
            elif getattr(args, 'split_files', False) and args.type == "file":
                # Resolve all files based on filters
                resolved_files = engine.resolve_files(
                    args.source, build_file_filters(args))

                if not resolved_files:
                    log_error("No Files Found", f"Pattern: {args.source}")
                    sys.exit(1)

                loaded_count = 0

                with log_progress("Processing Files...", module="SPLITTER") as p:
                    total_work = len(resolved_files)
                    p.update(total=total_work)

                    for f_path in resolved_files:
                        fname = os.path.basename(f_path)
                        # Clean Name
                        safe_base = os.path.splitext(fname)[0]
                        s_name = "".join([c if c.isalnum() or c in (
                            '-', '_') else '_' for c in safe_base])
                        alias = f"{base_ds_name}_{s_name}"

                        # Create Single File Params
                        l_params = FileLoaderParams(
                            path=f_path,
                            alias=alias,
                            process_individual=False,  # Forced False for split mode
                            clean_headers=getattr(
                                args, 'clean_headers', False),
                            include_source_info=getattr(
                                args, 'include_source_info', False),
                            # Clear filters as we are loading specific resolved file
                            filters=[],
                            sheet_filters=build_item_filters(
                                args.sheet_filter, "sheet_name"),
                            table_filters=build_item_filters(
                                args.table_filter, "table_name")
                        )

                        try:
                            # Load
                            res = engine.run_loader("File", l_params)
                            if res:
                                flf, meta = res if isinstance(
                                    res, tuple) else (res, {})
                                engine.add_dataset(alias, flf, metadata=meta)

                                # AUTO-INFER LOGIC
                                recipe_steps = []
                                if getattr(args, 'auto_infer', False):
                                    cast_step = engine.auto_infer_dataset(
                                        alias)
                                    if cast_step:
                                        recipe_steps.append(
                                            cast_step.model_dump())

                                datasets_to_process.append(
                                    (alias, recipe_steps))
                                loaded_count += 1
                        except Exception as e:
                            # Log but continue
                            if not args.quiet:
                                console.print(
                                    f"[dim red]Failed to load {fname}: {e}[/dim red]")

                        p.advance(1)

                if loaded_count == 0:
                    log_error("Split Logic",
                              "No datasets loaded via split-files.")
                    sys.exit(1)

            else:
                # --- STANDARD (NO SPLIT) ---
                result = None

                if args.type == "file":
                    file_filters = build_file_filters(args)
                    sheet_filters = build_item_filters(
                        args.sheet_filter, "sheet_name")
                    table_filters = build_item_filters(
                        args.table_filter, "table_name")

                    loader_params = FileLoaderParams(
                        path=args.source,
                        sheet=args.sheet_name if hasattr(
                            args, 'sheet_name') else "Sheet1",
                        alias=base_ds_name,
                        process_individual=getattr(
                            args, 'process_individual', False),
                        include_source_info=getattr(
                            args, 'include_source_info', False),
                        clean_headers=getattr(args, 'clean_headers', False),
                        filters=file_filters,
                        sheet_filters=sheet_filters,
                        table_filters=table_filters,
                        files=getattr(args, 'files', None)
                    )
                    with log_progress("Reading File Stream...", module="READER") as p:
                        result = engine.run_loader("File", loader_params)
                        p.update(completed=100)

                elif args.type == "sql":
                    if not args.sql_query:
                        log_error("Missing SQL Query",
                                  "--sql-query is required for SQL source.")
                        sys.exit(1)

                    loader_params = SqlLoaderParams(
                        conn=args.source,
                        query=args.sql_query,
                        alias=base_ds_name
                    )
                    with log_progress("Connecting to Database...", module="CONNECT") as p:
                        result = engine.run_loader("Sql", loader_params)
                        p.update(completed=100)

                elif args.type == "api":
                    url = args.api_url if args.api_url else args.source
                    loader_params = ApiLoaderParams(
                        url=url, alias=base_ds_name)
                    with log_progress("Fetching API Data...", module="NETWORK") as p:
                        result = engine.run_loader("Api", loader_params)
                        p.update(completed=100)

                if result is None:
                    log_error("Load Failed", "Engine returned None")
                    sys.exit(1)

                lf_or_lfs, metadata = result if isinstance(
                    result, tuple) else (result, {})
                engine.add_dataset(base_ds_name, lf_or_lfs, metadata=metadata)

                recipe = []
                if args.recipe:
                    try:
                        with open(args.recipe, 'r') as f:
                            recipe = json.load(f)
                    except Exception as e:
                        log_error("Recipe Load Failed", str(e))
                        sys.exit(1)

                if getattr(args, 'step', None):
                    for s_str in args.step:
                        try:
                            recipe.append(json.loads(s_str))
                        except:
                            log_error("Invalid inline step", s_str)
                            sys.exit(1)

                # AUTO-INFER LOGIC
                if getattr(args, 'auto_infer', False):
                    cast_step = engine.auto_infer_dataset(base_ds_name)
                    if cast_step:
                        recipe.insert(0, cast_step.model_dump())

                datasets_to_process.append((base_ds_name, recipe))

        except Exception as e:
            log_error("Core Exception", str(e))
            sys.exit(1)

        # --- POST-LOAD SQL TRANSFORMATION ---
        # If user provided a --transform-sql (distinct from --sql-query for source)
        if args.transform_sql:
            if not args.quiet:
                log_step("Executing SQL Transformation...",
                         module="SQL-ENGINE", icon="⚙️")

            try:
                # Collect active recipes (including auto-infer steps)
                active_recipes = {name: recipe for name,
                                  recipe in datasets_to_process}

                # Execute against registered context WITH recipes applied
                sql_lf = engine.execute_sql(
                    args.transform_sql, project_recipes=active_recipes)

                # Replace Execution Plan with SQL Result
                engine.add_dataset("SQL_RESULT", sql_lf)
                datasets_to_process = [("SQL_RESULT", [])]

            except Exception as e:
                log_error("SQL Transformation Failed", str(e))
                sys.exit(1)

    # =========================================================================
    # PREMIUM SUMMARY: TREE VIEW
    # =========================================================================
    if not args.quiet:
        tree = Tree(
            f"[bold gold1]Execution Plan ({len(datasets_to_process)} Datasets)[/]")
        for ds, steps in datasets_to_process:
            node = tree.add(f"[cyan]{ds}[/]")
            if steps:
                node.add(f"[dim]{len(steps)} Steps Queued[/]")
            else:
                node.add("[dim]Direct Export[/]")

        panel = Panel(tree, title="Job Manifest", border_style="blue")
        console.print(panel)

    # =========================================================================
    # 3. EXPORT / EXECUTION PHASE
    # =========================================================================

    final_reports = []
    project_recipes = engine.get_all_recipes()

    if args.merge and len(datasets_to_process) > 1:
        # --- MERGE MODE ---
        if not args.quiet:
            log_step("Merging Datasets into Single Output...",
                     module="MERGE", icon="🧬")

        # Infer format from extension if present
        if "." in os.path.basename(args.output):
            ext = os.path.splitext(args.output)[1].lower()
            if ext in [".csv", ".txt"]:
                output_fmt = "csv"
            elif ext in [".parquet"]:
                output_fmt = "parquet"
            elif ext in [".xlsx", ".xls"]:
                output_fmt = "excel"
            elif ext in [".json"]:
                output_fmt = "json"
            elif ext in [".jsonl", ".ndjson"]:
                output_fmt = "ndjson"
            elif ext in [".arrow", ".ipc"]:
                output_fmt = "ipc"
            elif ext in [".db", ".sqlite"]:
                output_fmt = "sqlite"
            else:
                output_fmt = args.format
        else:
            output_fmt = args.format

        output_path = resolve_output_path(
            args.output, output_fmt, is_dir=False)
        exporter_key = resolve_exporter_name(output_fmt)

        try:
            lfs = []
            with log_progress("Processing & Merging...", total=len(datasets_to_process), module="COMPUTE") as p:
                for name, recipe in datasets_to_process:
                    eff_recipe = recipe if recipe else project_recipes.get(
                        name, [])
                    lf = engine.get_dataset_for_export(
                        name, eff_recipe, project_recipes)
                    if lf is not None:
                        lfs.append(lf)
                    p.advance(1)

            if not lfs:
                log_error("Merge Failed", "No valid datasets to merge.")
                sys.exit(1)

            merged_lf = pl.concat(lfs, how="diagonal")

            params = get_export_params(output_fmt, output_path, args)

            job_id = engine._job_manager.start_export_job(
                dataset_name="MERGED_RESULT",
                recipe=[],
                exporter_name=exporter_key,
                params=params,
                project_recipes=None,
                precomputed_lf=merged_lf
            )

            final_reports.append(wait_for_job(
                engine, job_id, "Merged Project", args.quiet))

        except Exception as e:
            log_error("Merge Execution Failed", str(e))
            sys.exit(1)

    else:
        # --- INDIVIDUAL MODE ---

        # 1. Analyze Output Path for Pattern
        # Support: "folder/*.csv" or "folder/{}.csv" or just "folder"
        out_pattern = args.output
        override_format = None

        has_extension = "." in os.path.basename(out_pattern)
        is_multi_dataset = len(datasets_to_process) > 1

        if "*" in out_pattern:
            # User provided pattern like "dist/*.csv"
            ext = os.path.splitext(out_pattern)[1].lower()
            # Infer format from pattern extension
            if ext in [".csv", ".txt"]:
                override_format = "csv"
            elif ext in [".parquet"]:
                override_format = "parquet"
            elif ext in [".xlsx", ".xls"]:
                override_format = "excel"
            elif ext in [".json"]:
                override_format = "json"
            elif ext in [".jsonl", ".ndjson"]:
                override_format = "ndjson"
            elif ext in [".arrow", ".ipc"]:
                override_format = "ipc"
            elif ext in [".db", ".sqlite"]:
                override_format = "sqlite"

        elif has_extension:
            # User provided specific file like "dist/output.xlsx"
            # Infer format from file extension
            ext = os.path.splitext(out_pattern)[1].lower()
            if ext in [".csv", ".txt"]:
                override_format = "csv"
            elif ext in [".parquet"]:
                override_format = "parquet"
            elif ext in [".xlsx", ".xls"]:
                override_format = "excel"
            elif ext in [".json"]:
                override_format = "json"
            elif ext in [".jsonl", ".ndjson"]:
                override_format = "ndjson"
            elif ext in [".arrow", ".ipc"]:
                override_format = "ipc"
            elif ext in [".db", ".sqlite"]:
                override_format = "sqlite"

        if "*" in out_pattern or has_extension:
            # Prepare directory (Parent of the file)
            base_dir = os.path.dirname(out_pattern)
            if base_dir and not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)

        # Apply override
        output_fmt = override_format if override_format else args.format
        exporter_key = resolve_exporter_name(output_fmt)

        # If no pattern but multi-dataset AND NO EXTENSION, treat as directory
        if "*" not in out_pattern and is_multi_dataset and not has_extension:
            if not os.path.exists(out_pattern):
                os.makedirs(out_pattern, exist_ok=True)

        for name, recipe in datasets_to_process:
            # Resolve Path
            # Sanitize name
            safe_name = "".join(
                [c if c.isalnum() or c in ('-', '_') else '_' for c in name])

            if "*" in out_pattern:
                # Replace * with dataset name
                current_output = out_pattern.replace("*", safe_name)

            elif is_multi_dataset:
                if has_extension:
                    # File Logic: "dir/file.csv" -> "dir/file_{safe_name}.csv"
                    root, ext = os.path.splitext(out_pattern)
                    current_output = f"{root}_{safe_name}{ext}"
                else:
                    # Directory Mode: join(dir, name.ext)
                    fname = f"{safe_name}{FMT_EXT_MAP.get(output_fmt.lower(), '')}"
                    current_output = os.path.join(out_pattern, fname)

            else:
                # Single File Mode (Single Dataset)
                current_output = resolve_output_path(out_pattern, output_fmt)

            eff_recipe = recipe if recipe else project_recipes.get(name, [])

            if not args.quiet:
                log_step(
                    f"Exporting {name} -> {os.path.basename(current_output)}", module="EXPORT", icon="📤")

            try:
                params = get_export_params(output_fmt, current_output, args)

                job_id = engine.start_export_job(
                    dataset_name=name,
                    recipe=eff_recipe,
                    exporter_name=exporter_key,
                    params=params,
                    project_recipes=project_recipes
                )

                final_reports.append(wait_for_job(
                    engine, job_id, name, args.quiet))

            except Exception as e:
                log_error(f"Failed to export {name}", str(e))
                if not args.quiet:
                    continue

    # --- SUMMARY ---
    if not args.quiet:
        print("\n")
        log_table(final_reports, title="Execution Summary")

    if any(r['Status'] == 'FAILED' for r in final_reports):
        sys.exit(1)

    sys.exit(0)


def wait_for_job(engine, job_id, label, quiet):
    """Wait for job and return summary dict."""
    while True:
        info = engine.get_job_status(job_id)
        if info is None:
            time.sleep(0.5)
            continue

        if info.status == "COMPLETED":
            return {
                "Dataset": label,
                "Status": "SUCCESS",
                "Size": info.size_str or "N/A",
                "Path": info.file
            }
        elif info.status == "FAILED":
            return {
                "Dataset": label,
                "Status": "FAILED",
                "Error": info.error,
                "Path": "-"
            }

        time.sleep(0.1)
