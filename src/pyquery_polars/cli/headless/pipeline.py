import os
import sys
import json
import time
import polars as pl
from rich.tree import Tree
from rich.panel import Panel

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.core.io import FileLoaderParams, SqlLoaderParams, ApiLoaderParams, FilterType

from pyquery_polars.cli.headless.filters import FilterParser
from pyquery_polars.cli.headless.paths import PathResolver
from pyquery_polars.cli.headless.exporters import ExporterFactory


class HeadlessPipeline:
    """
    Orchestrates the headless CLI execution flow.
    Encapsulates logic for loading projects/sources, applying recipes, and running exports.
    """

    def __init__(self, ui, theme_manager):
        self.engine = PyQueryEngine()
        self.ui = ui
        self.theme_manager = theme_manager
        self.datasets_to_process = []

    def run(self, args):
        """Main entry point."""
        # Note: init_logging() is called by caller (main.py) or we assume initialized

        # Validation
        if args.project and args.source:
            self.ui.log_error(
                "Argument Error", "Cannot specify both --project and --source. Choose one.")
            sys.exit(1)

        if not args.project and not args.source:
            self.ui.log_error(
                "Argument Error", "Must specify either --project <file> or --source <file/url>.")
            sys.exit(1)

        if not args.quiet:
            self.ui.log_step("Initializing Query Engine...",
                             module="KERNEL", icon="⚡")

        # Load Data
        if args.project:
            self._mode_project(args)
        else:
            self._mode_source(args)

        # Show Plan
        if not args.quiet:
            self._show_plan()

        # Execute Export/Merge
        self._execute(args)

    def _mode_project(self, args):
        """Handle Project Loading."""
        project_path = os.path.abspath(args.project)
        if not os.path.exists(project_path):
            self.ui.log_error("Project Not Found", f"{project_path}")
            sys.exit(1)

        if not args.quiet:
            self.ui.log_step(
                f"Loading Project: {os.path.basename(project_path)}", module="PROJECT", icon="📂")

        try:
            with self.ui.create_progress("Hydrating Project State...", module="LOADER") as p:
                result = self.engine.projects.load_from_file(
                    project_path, mode="replace")
                p.update(completed=100)

            if not result.success:
                self.ui.log_error("Project Load Failed",
                                  "\n".join(result.errors))
                sys.exit(1)

            if result.warnings and not args.quiet:
                for w in result.warnings:
                    self.ui.console.print(
                        f"[dim yellow]Warning: {w}[/dim yellow]")

        except Exception as e:
            self.ui.log_error("Critical Project Load Error", str(e))
            sys.exit(1)

        available_datasets = self.engine.datasets.list_names()
        target_datasets = available_datasets

        if args.dataset:
            target_datasets = [
                d for d in available_datasets if d in args.dataset]
            if not target_datasets:
                self.ui.log_error(
                    "Dataset Error", f"None of the requested datasets found: {args.dataset}")
                self.ui.log_error("Available", ", ".join(available_datasets))
                sys.exit(1)

        for ds_name in target_datasets:
            self.datasets_to_process.append((ds_name, []))

        if not args.quiet:
            self.ui.log_step(
                f"Selected {len(target_datasets)} datasets for processing.", module="PLANNER", icon="🎯")

    def _try_infer_format(self, path: str):
        """Try to infer format string from file extension."""
        base, ext = os.path.splitext(path)
        ext = ext.lower()
        # Simplistic reverse lookup
        for fmt_key, ext_val in PathResolver.FMT_EXT_MAP.items():
            if ext_val == ext:
                return fmt_key
        return None

    def _mode_source(self, args):
        """Handle Direct Source Loading."""
        base_ds_name = getattr(args, 'alias', None) or "cli_data"
        self._resolve_sql_files(args)

        if not args.quiet:
            if args.type == "sql":
                self.ui.log_step(f"Connecting to SQL Source...",
                                 module="SQL", icon="🔌")
            else:
                self.ui.log_step(
                    f"Loading Source: {args.source} as '{base_ds_name}'", module="I/O", icon="📥")

        try:
            if getattr(args, 'split_sheets', False) and args.type == "file":
                self._handle_split_sheets(args)
            elif getattr(args, 'split_files', False) and args.type == "file":
                self._handle_split_files(args, base_ds_name)
            else:
                self._handle_standard_load(args, base_ds_name)
        except Exception as e:
            self.ui.log_error("Core Exception", str(e))
            sys.exit(1)

        # Post-Load SQL Transform
        if args.transform_sql:
            self._handle_transform_sql(args)

    def _resolve_sql_files(self, args):
        if args.sql_query and os.path.exists(args.sql_query):
            try:
                with open(args.sql_query, 'r', encoding='utf-8') as f:
                    args.sql_query = f.read()
            except Exception as e:
                self.ui.log_error("SQL File Error",
                                  f"Failed to read SQL file: {e}")
                sys.exit(1)

        if args.transform_sql and os.path.exists(args.transform_sql):
            try:
                with open(args.transform_sql, 'r', encoding='utf-8') as f:
                    args.transform_sql = f.read()
            except Exception as e:
                self.ui.log_error("SQL File Error",
                                  f"Failed to read Transform SQL file: {e}")
                sys.exit(1)

    def _handle_split_sheets(self, args):
        resolved_files = self.engine.io.resolve_files(
            args.source, FilterParser.parse_file_filters(args))
        if not resolved_files:
            self.ui.log_error("No Files Found", f"Pattern: {args.source}")
            sys.exit(1)

        loaded_count = 0
        with self.ui.create_progress("Splitting Sheets & Tables...", module="SPLITTER") as p:
            p.update(total=len(resolved_files))
            for f_path in resolved_files:
                if self._process_split_sheet_file(args, f_path):
                    loaded_count += 1
                p.advance(1)

        if loaded_count == 0:
            self.ui.log_error(
                "Split Logic", "No datasets loaded via split-sheets.")
            sys.exit(1)

    def _process_split_sheet_file(self, args, f_path):
        ext = os.path.splitext(f_path)[1].lower()
        if ext not in [".xlsx", ".xls", ".xlsm", ".xlsb"]:
            return False

        tables = self.engine.io.get_table_names(f_path)
        sheets = self.engine.io.get_sheet_names(f_path)

        sheet_filters = FilterParser.parse_item_filters(
            args.sheet_filter, "sheet_name")
        table_filters = FilterParser.parse_item_filters(
            args.table_filter, "table_name")

        # Determine targets logic (same as original)
        targets = []
        if sheet_filters or table_filters:
            if table_filters:
                targets.extend([("table", t) for t in tables])
            if sheet_filters:
                targets.extend([("sheet", s) for s in sheets])

            # Apply filters
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
                        match = fnmatch.fnmatch(name.lower(), val.lower())
                    if not match:
                        break
                if match:
                    final_targets.append((kind, name))
            targets = final_targets
        else:
            excel_mode = getattr(args, 'excel_mode', "auto")
            if excel_mode == "tables":
                targets.extend([("table", t) for t in tables])
            elif excel_mode == "sheets":
                targets.extend([("sheet", s) for s in sheets])
            else:
                if tables:
                    targets.extend([("table", t) for t in tables])
                else:
                    targets.extend([("sheet", s) for s in sheets])

        f_base = os.path.splitext(os.path.basename(f_path))[0]
        loaded_any = False
        for kind, target_name in targets:
            s_name = "".join([c if c.isalnum() or c in (
                '-', '_') else '_' for c in target_name])
            alias = f"{f_base}_{s_name}"

            l_params = FileLoaderParams(
                path=f_path, sheet=target_name if kind == "sheet" else None,
                table=target_name if kind == "table" else None,
                alias=alias,
                clean_headers=getattr(args, 'clean_headers', False),
                include_source_info=getattr(args, 'include_source_info', False)
            )
            try:
                res = self.engine.io.run_loader("File", l_params)
                if res:
                    self._add_dataset(alias, res, args)
                    loaded_any = True
            except:
                pass
        return loaded_any

    def _handle_split_files(self, args, base_ds_name):
        resolved_files = self.engine.io.resolve_files(
            args.source, FilterParser.parse_file_filters(args))
        if not resolved_files:
            self.ui.log_error("No Files Found", f"Pattern: {args.source}")
            sys.exit(1)

        loaded_count = 0
        with self.ui.create_progress("Processing Files...", module="SPLITTER") as p:
            p.update(total=len(resolved_files))
            for f_path in resolved_files:
                fname = os.path.basename(f_path)
                safe_base = os.path.splitext(fname)[0]
                s_name = "".join([c if c.isalnum() or c in (
                    '-', '_') else '_' for c in safe_base])
                alias = f"{base_ds_name}_{s_name}"

                l_params = FileLoaderParams(
                    path=f_path, alias=alias, process_individual=False,
                    clean_headers=getattr(args, 'clean_headers', False),
                    include_source_info=getattr(
                        args, 'include_source_info', False),
                    filters=[],
                    sheet_filters=FilterParser.parse_item_filters(
                        args.sheet_filter, "sheet_name"),
                    table_filters=FilterParser.parse_item_filters(
                        args.table_filter, "table_name")
                )
                try:
                    res = self.engine.io.run_loader("File", l_params)
                    if res:
                        self._add_dataset(alias, res, args)
                        loaded_count += 1
                except Exception as e:
                    if not args.quiet:
                        self.ui.console.print(
                            f"[dim red]Failed to load {fname}: {e}[/dim red]")
                p.advance(1)

        if loaded_count == 0:
            self.ui.log_error(
                "Split Logic", "No datasets loaded via split-files.")
            sys.exit(1)

    def _handle_standard_load(self, args, base_ds_name):
        result = None
        if args.type == "file":
            l_params = FileLoaderParams(
                path=args.source,
                sheet=args.sheet_name if hasattr(
                    args, 'sheet_name') else "Sheet1",
                alias=base_ds_name,
                process_individual=getattr(args, 'process_individual', False),
                include_source_info=getattr(
                    args, 'include_source_info', False),
                clean_headers=getattr(args, 'clean_headers', False),
                filters=FilterParser.parse_file_filters(args),
                sheet_filters=FilterParser.parse_item_filters(
                    args.sheet_filter, "sheet_name"),
                table_filters=FilterParser.parse_item_filters(
                    args.table_filter, "table_name"),
                files=getattr(args, 'files', None)
            )
            with self.ui.create_progress("Reading File Stream...", module="READER") as p:
                result = self.engine.io.run_loader("File", l_params)
                p.update(completed=100)

        elif args.type == "sql":
            if not args.sql_query:
                self.ui.log_error("Missing SQL Query",
                                  "--sql-query is required for SQL source.")
                sys.exit(1)
            l_params = SqlLoaderParams(
                conn=args.source, query=args.sql_query, alias=base_ds_name)
            with self.ui.create_progress("Connecting to Database...", module="CONNECT") as p:
                result = self.engine.io.run_loader("Sql", l_params)
                p.update(completed=100)

        elif args.type == "api":
            url = args.api_url if args.api_url else args.source
            l_params = ApiLoaderParams(url=url, alias=base_ds_name)
            with self.ui.create_progress("Fetching API Data...", module="NETWORK") as p:
                result = self.engine.io.run_loader("Api", l_params)
                p.update(completed=100)

        if result is None:
            self.ui.log_error("Load Failed", "Engine returned None")
            sys.exit(1)

        self._add_dataset(base_ds_name, result, args,
                          recipe_file=args.recipe, steps=getattr(args, 'step', None))

    def _add_dataset(self, alias, result, args, recipe_file=None, steps=None):
        lf_or_lfs = result.lf
        self.engine.datasets.add(
            alias, lf_or_lfs, metadata=result.meta.model_dump())
        self.engine.recipes.ensure_exists(alias)

        recipe = []
        if recipe_file:
            try:
                with open(recipe_file, 'r') as f:
                    recipe = json.load(f)
            except Exception as e:
                self.ui.log_error("Recipe Load Failed", str(e))
                sys.exit(1)

        if steps:
            for s_str in steps:
                try:
                    recipe.append(json.loads(s_str))
                except:
                    self.ui.log_error("Invalid inline step", s_str)
                    sys.exit(1)

        self.engine.recipes.add(alias, recipe)

        # Auto Infer
        if getattr(args, 'auto_infer', False):
            lf_infer = lf_or_lfs[0] if isinstance(lf_or_lfs, list) and lf_or_lfs else (
                lf_or_lfs if not isinstance(lf_or_lfs, list) and lf_or_lfs is not None else None)
            if lf_infer is not None:
                inferred = self.engine.analytics.infer_types(
                    lf_infer, [], sample_size=1000)
                if inferred:
                    self.engine.recipes.apply_inferred_types(
                        alias, inferred, prepend=True)

        final_recipe = [s.model_dump() for s in self.engine.recipes.get(alias)]
        self.datasets_to_process.append((alias, final_recipe))

    def _handle_transform_sql(self, args):
        if not args.quiet:
            self.ui.log_step("Executing SQL Transformation...",
                             module="SQL-ENGINE", icon="⚙️")

        # If we are in split mode (multi dataset), we need to run the SQL for EACH dataset
        # The SQL likely references the base alias (e.g. 'monthly_data')
        # We need to temporarily map the specific alias to the base alias in the SQL context

        base_alias = getattr(args, 'alias', None) or "cli_data"
        new_datasets_list = []

        for ds_name, recipe in self.datasets_to_process:
            try:
                # 1. Register the current specific dataset as the base alias
                # This allows "SELECT * FROM monthly_data" to work even if the ds is "monthly_data_file1"

                # Get the LazyFrame for the current dataset
                # We need to prepare it first to get the LF
                meta = self.engine.datasets.get_metadata(ds_name)

                if meta is None:
                    self.ui.log_error(
                        f"Metadata missing for {ds_name}", "Skipping SQL transform")
                    continue

                current_lf = self.engine.processing.prepare_view(
                    meta, recipe, mode="full")

                if current_lf is not None:
                    # Register this specific LF as the base alias in the SQL Context
                    self.engine.datasets.add(base_alias, current_lf)

                    # 2. Execute SQL
                    sql_lf = self.engine.processing.execute_sql(
                        args.transform_sql, preview=False)

                    # 3. Save Result back to a NEW dataset or OVERWRITE
                    # Logic: We replace the original dataset in the list with the SQL result
                    # We keep the original name to maintain the flow
                    self.engine.datasets.add(ds_name, sql_lf)

                    # Clear recipe since the transform is now baked in
                    new_datasets_list.append((ds_name, []))
                else:
                    # If prepare failed, keep original
                    new_datasets_list.append((ds_name, recipe))

            except Exception as e:
                self.ui.log_error(
                    f"SQL Transform Failed for {ds_name}", str(e))
                # On failure, maybe skip or keep original?
                # For strict CLI, we probably want to error out or log
                continue

        # Update the main list
        self.datasets_to_process = new_datasets_list

    def _show_plan(self):
        tree = Tree(
            f"[bold gold1]Execution Plan ({len(self.datasets_to_process)} Datasets)[/]")
        for ds, steps in self.datasets_to_process:
            node = tree.add(f"[cyan]{ds}[/]")
            if steps:
                node.add(f"[dim]{len(steps)} Steps Queued[/]")
            else:
                node.add("[dim]Direct Export[/]")
        panel = Panel(tree, title="Job Manifest", border_style="blue")
        self.ui.console.print(panel)

    def _execute(self, args):
        final_reports = []
        project_recipes = self.engine.recipes.get_all()

        if args.merge and len(self.datasets_to_process) > 1:
            self._handle_merge(args, final_reports, project_recipes)
        else:
            self._handle_individual(args, final_reports, project_recipes)

        if not args.quiet:
            print("\n")
            self.ui.log_table(final_reports, title="Execution Summary")

        if any(r['Status'] == 'FAILED' for r in final_reports):
            sys.exit(1)
        sys.exit(0)

    def _handle_merge(self, args, final_reports, project_recipes):
        if not args.quiet:
            self.ui.log_step("Merging Datasets into Single Output...",
                             module="MERGE", icon="🧬")

        # Infer Format from output arg
        output_fmt = args.format
        if "." in os.path.basename(args.output):
            ext = os.path.splitext(args.output)[1].lower()
            # Simple map check
            # Simplistic
            rev_map = {v: k for k, v in PathResolver.FMT_EXT_MAP.items()}
            # Original logic was explicit if/else

        # Logic from original
        output_path = PathResolver.resolve_output_path(
            args.output, args.format, is_dir=False)
        # Re-implement infer logic properly if needed, but for now assuming args.format is usually correct or user specified

        try:
            lfs = []
            with self.ui.create_progress("Processing & Merging...", total=len(self.datasets_to_process), module="COMPUTE") as p:
                for name, recipe in self.datasets_to_process:
                    eff_recipe = recipe if recipe else project_recipes.get(
                        name, [])
                    meta = self.engine.datasets.get_metadata(name)
                    lf = None
                    if meta:
                        lf = self.engine.processing.prepare_view(
                            meta, eff_recipe, mode="full")
                    if lf is not None:
                        lfs.append(lf)
                    p.advance(1)

            if not lfs:
                self.ui.log_error(
                    "Merge Failed", "No valid datasets to merge.")
                sys.exit(1)

            merged_lf = pl.concat(lfs, how="diagonal")

            # Strategy: Prefer Inferred Format from Path -> override args.format
            inferred_fmt = self._try_infer_format(output_path)
            final_fmt = inferred_fmt if inferred_fmt else args.format

            params = ExporterFactory.create_params(
                final_fmt, output_path, args)
            exporter_key = ExporterFactory.resolve_name(final_fmt)

            job_id = self.engine.jobs.start_export_job(
                dataset_name="MERGED_RESULT", recipe=[], exporter_name=exporter_key,
                params=params, project_recipes=None, precomputed_lf=merged_lf
            )
            final_reports.append(self._wait_for_job(
                job_id, "Merged Project", args.quiet))
        except Exception as e:
            self.ui.log_error("Merge Execution Failed", str(e))
            sys.exit(1)

    def _handle_individual(self, args, final_reports, project_recipes):
        out_pattern = args.output
        is_multi = len(self.datasets_to_process) > 1
        has_ext = "." in os.path.basename(out_pattern)

        if "*" not in out_pattern and is_multi and not has_ext:
            if not os.path.exists(out_pattern):
                os.makedirs(out_pattern, exist_ok=True)

        for name, recipe in self.datasets_to_process:
            safe_name = "".join(
                [c if c.isalnum() or c in ('-', '_') else '_' for c in name])

            # Path Logic
            if "*" in out_pattern:
                current_output = out_pattern.replace("*", safe_name)
            elif is_multi:
                if has_ext:
                    root, ext = os.path.splitext(out_pattern)
                    current_output = f"{root}_{safe_name}{ext}"
                else:
                    fname = f"{safe_name}.{args.format.lower()}"  # Simplistic
                    current_output = os.path.join(out_pattern, fname)
            else:
                current_output = PathResolver.resolve_output_path(
                    out_pattern, args.format)

            eff_recipe = recipe if recipe else project_recipes.get(name, [])

            if not args.quiet:
                self.ui.log_step(
                    f"Exporting {name} -> {os.path.basename(current_output)}", module="EXPORT", icon="📤")

            # Strategy: Prefer Inferred Format from Path -> override args.format
            inferred_fmt = self._try_infer_format(current_output)
            final_fmt = inferred_fmt if inferred_fmt else args.format

            try:
                params = ExporterFactory.create_params(
                    final_fmt, current_output, args)
                exporter_key = ExporterFactory.resolve_name(final_fmt)

                job_id = self.engine.jobs.start_export_job(
                    dataset_name=name, recipe=eff_recipe, exporter_name=exporter_key,
                    params=params, project_recipes=project_recipes
                )
                final_reports.append(
                    self._wait_for_job(job_id, name, args.quiet))
            except Exception as e:
                self.ui.log_error(f"Failed to export {name}", str(e))

    def _wait_for_job(self, job_id, label, quiet):
        while True:
            info = self.engine.jobs.get_job_status(job_id)
            if info is None:
                time.sleep(0.5)
                continue
            if info.status == "COMPLETED":
                return {
                    "Dataset": label,
                    "Status": "SUCCESS",
                    "Size": info.size_str or "N/A",
                    "Path": info.file,
                    "Error": ""
                }
            elif info.status == "FAILED":
                return {
                    "Dataset": label,
                    "Status": "FAILED",
                    "Size": "-",
                    "Path": "-",
                    "Error": info.error
                }
            time.sleep(0.1)
