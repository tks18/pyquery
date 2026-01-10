import sys
import os
import glob
import uuid
import time
import json
from typing import Dict, Any, Type, List, get_args, get_origin, Optional
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

import questionary
from rich.panel import Panel
from rich.table import Table

from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io_params import (
    FileLoaderParams, ParquetExportParams, CsvExportParams,
    ExcelExportParams, JsonExportParams, IpcExportParams
)
from pyquery_polars.cli.branding import init_logging, log_step, log_error, log_success, log_table, console

# Initialize
engine = PyQueryEngine()

# State
active_dataset: Optional[str] = None
active_dataset_path: Optional[str] = None
recipe: List[RecipeStep] = []


def print_header():
    console.print(Panel.fit(
        "[bold cyan]⚡ PyQuery Interactive CLI[/bold cyan]", border_style="cyan"))


def get_pydantic_input(model_cls: Type[BaseModel], available_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    inputs = {}
    schema = model_cls.model_fields

    COLUMN_FIELDS = {
        'col', 'cols', 'subset', 'include_cols', 'exclude_cols',
        'keys', 'left_on', 'right_on', 'target', 'over', 'sort',
        'idx', 'val', 'id_vars', 'val_vars', 'by'
    }

    # CHOICE OVERRIDES FOR STR FIELDS
    CHOICE_OVERRIDES = {
        'CastChange': {
            'action': [
                "To String", "To Int", "To Float", "To Boolean",
                "To Date", "To Datetime", "To Time", "To Duration",
                "Trim Whitespace", "Standardize NULLs",
                "Fix Excel Serial Date", "Fix Excel Serial Datetime", "Fix Excel Serial Time"
            ]
        },
        'FilterCondition': {
            'op': ["==", "!=", ">", "<", ">=", "<=", "contains", "starts_with", "ends_with", "is_null", "is_not_null"]
        },
        'AggDef': {
            'op': ["sum", "mean", "min", "max", "count", "n_unique", "first", "last", "median", "std", "var"]
        },
        'WindowFuncParams': {
            'op': ["sum", "mean", "min", "max", "count", "first", "last", "rank", "dense_rank", "row_number"]
        }
    }

    for field_name, field_info in schema.items():
        label = field_name.replace("_", " ").title()
        default_val = field_info.default if field_info.default is not None and field_info.default != PydanticUndefined else ""
        outer_type = field_info.annotation

        args = get_args(outer_type)
        origin = get_origin(outer_type)

        # INTELLIGENT COLUMN SELECTION
        is_col_field = field_name in COLUMN_FIELDS
        if not is_col_field and (field_name.endswith("_col") or field_name.endswith("_cols")):
            is_col_field = True

        # CHECK OVERRIDES
        model_name = model_cls.__name__
        if model_name in CHOICE_OVERRIDES and field_name in CHOICE_OVERRIDES[model_name]:
            opts = CHOICE_OVERRIDES[model_name][field_name]
            safe_default = str(default_val)
            if safe_default not in opts:
                safe_default = opts[0]

            try:
                val = questionary.select(
                    message=f"{label}:", choices=opts, default=safe_default).ask()
                inputs[field_name] = val
            except:
                inputs[field_name] = questionary.text(
                    message=f"{label}:", default=str(default_val)).ask()
            continue

        # 1. Handle List[BaseModel] (Recursive)
        is_list = (origin is list or outer_type == list or str(
            origin) == "<class 'list'>" or str(outer_type).startswith("typing.List"))

        if is_list and args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
            nested_cls = args[0]
            items = []
            console.print(
                f"[bold cyan]Configure list of {label} ({nested_cls.__name__}):[/bold cyan]")
            while True:
                if items and not questionary.confirm(f"Add another {nested_cls.__name__}?", default=False).ask():
                    break
                if not items and default_val == "" and not questionary.confirm(f"Add a {nested_cls.__name__}?", default=True).ask():
                    break
                console.print(f"  [cyan]Item {len(items)+1}:[/cyan]")
                item_data = get_pydantic_input(
                    nested_cls, available_columns=available_columns)
                items.append(item_data)
            inputs[field_name] = items

        # 2. Handle List[str]
        elif is_list:
            if is_col_field and available_columns:
                # Checkbox
                d_val = default_val if isinstance(default_val, list) else []
                try:
                    val = questionary.checkbox(
                        f"Select {label}:", choices=available_columns, default=d_val).ask()
                    inputs[field_name] = val
                except:
                    val = questionary.text(
                        f"{label} (comma separated):", default=str(default_val)).ask()
                    inputs[field_name] = [x.strip()
                                          for x in val.split(",")] if val else []
            else:
                val = questionary.text(
                    f"{label} (comma separated):", default=str(default_val)).ask()
                inputs[field_name] = [x.strip()
                                      for x in val.split(",")] if val else []

        # 3. Literal Options (Including Optional[Literal])
        else:
            is_literal = False
            lit_options = []

            if origin is not None and "Literal" in str(origin):
                is_literal = True
                lit_options = list(args)
            elif args:
                for arg in args:
                    if "Literal" in str(get_origin(arg)) or "Literal" in str(arg):
                        is_literal = True
                        try:
                            lit_options = list(get_args(arg))
                        except:
                            pass
                        break

            if is_literal:
                final_choices = [str(o) for o in lit_options]
                safe_default = str(default_val)
                if safe_default not in final_choices:
                    safe_default = final_choices[0] if final_choices else None

                try:
                    val = questionary.select(
                        message=f"{label}:", choices=final_choices, default=safe_default).ask()
                    inputs[field_name] = val
                except:
                    inputs[field_name] = questionary.text(
                        message=f"{label}:", default=str(default_val)).ask()

            # 4. Primitives
            elif outer_type == int:
                val = questionary.text(
                    f"{label} (int):", default=str(default_val)).ask()
                inputs[field_name] = int(val) if val else default_val

            elif outer_type == float:
                val = questionary.text(
                    f"{label} (float):", default=str(default_val)).ask()
                inputs[field_name] = float(val) if val else default_val

            elif outer_type == bool:
                val = questionary.confirm(f"{label}?", default=bool(
                    default_val) if default_val != "" else False).ask()
                inputs[field_name] = val

            # 5. Fallback Text / Single Column Select
            else:
                if is_col_field and available_columns:
                    choices = available_columns + ["(Manual Input)"]
                    try:
                        sel = questionary.select(
                            f"Select {label}:", choices=choices).ask()
                        if sel == "(Manual Input)":
                            val = questionary.text(
                                f"{label}:", default=str(default_val)).ask()
                        else:
                            val = sel
                    except:
                        val = questionary.text(
                            f"{label}:", default=str(default_val)).ask()
                else:
                    val = questionary.text(
                        f"{label}:", default=str(default_val)).ask()
                inputs[field_name] = val

    return inputs


def load_data_flow():
    global active_dataset, active_dataset_path, recipe
    files = glob.glob("*.csv") + glob.glob("*.parquet") + glob.glob("*.xlsx")

    # Enhanced Selection Logic
    choices = ["📂 Select Current Folder"] + files + ["Manual Path"]
    sel = questionary.select(message="Select Source:", choices=choices).ask()

    final_path = ""
    is_glob = False
    pattern = "*"  # Default pattern to avoid UnboundLocalError

    if sel == "📂 Select Current Folder":
        pat_choice = questionary.select(
            "Glob Pattern:",
            choices=["*.csv", "*.parquet", "*.xlsx",
                     "*.json", "* (All Files)", "Custom Pattern"]
        ).ask()

        if pat_choice == "Custom Pattern":
            pattern = questionary.text("Enter Pattern:", default="*.csv").ask()
        elif pat_choice == "* (All Files)":
            pattern = "*"
        else:
            pattern = pat_choice

        final_path = os.path.join(os.getcwd(), pattern)
        is_glob = True
    elif sel == "Manual Path":
        p = questionary.text("File/Folder Path:").ask()
        if os.path.isdir(p):
            pat_choice = questionary.select(
                "Glob Pattern:",
                choices=["*.csv", "*.parquet", "*.xlsx",
                         "*.json", "* (All Files)", "Custom Pattern"]
            ).ask()

            if pat_choice == "Custom Pattern":
                pattern = questionary.text(
                    "Enter Pattern:", default="*.csv").ask()
            elif pat_choice == "* (All Files)":
                pattern = "*"
            else:
                pattern = pat_choice

            final_path = os.path.join(p, pattern)
            is_glob = True
        else:
            final_path = p
            # Infer pattern from manual input
            base = os.path.basename(p)
            if "*" in base:
                pattern = base
            else:
                pattern = base  # Specific file
    else:
        # Selected a specific file
        final_path = sel
        pattern = os.path.basename(sel)

    if not final_path:
        return

    # Mixed Type Handling
    sheet_name = "Sheet1"
    if pattern == "*":
        console.print(
            "[yellow]⚠️ Caution: Loading mixed supported file types. Ensure schemas are compatible or handle manually![/yellow]")
        if questionary.confirm("Does this folder include Excel files?", default=False).ask():
            sheet_name = questionary.text(
                "Excel Sheet Name to extraction:", default="Sheet1").ask()

    # Alias
    default_alias = os.path.basename(final_path).split('.')[0]
    if "*" in default_alias:  # Fix for globs
        default_alias = "dataset"
    if not default_alias:
        default_alias = "dataset"

    alias = questionary.text("Dataset Alias:", default=default_alias).ask()

    # Process Individual
    process_individual = False
    if "*" in final_path or is_glob or os.path.isdir(final_path):
        process_individual = questionary.confirm(
            "Process files individually before concatenating?",
            default=False
        ).ask()
        if process_individual:
            log_step("Individual processing enabled",
                     module="CONFIG", icon="📁")

    # Source Metadata
    include_source_info = questionary.confirm(
        "Include source file metadata (filename, path)?",
        default=False
    ).ask()

    # Excel Sheet Detection (Single File specific fallback if not set above)
    lower_path = final_path.lower()
    if pattern != "*" and (lower_path.endswith(".xlsx") or lower_path.endswith(".xls")):
        try:
            sheets = engine.get_file_sheet_names(final_path)
            if sheets:
                sheet_name = questionary.select(
                    "Select Sheet:", choices=sheets).ask()
        except:
            pass
    is_excel = ".xls" in lower_path

    if is_excel:
        try:
            sample_file = final_path
            # If glob, resolve valid sample
            if "*" in final_path:
                matches = glob.glob(final_path)
                if matches:
                    sample_file = matches[0]
                else:
                    sample_file = None

            if sample_file and os.path.isfile(sample_file):
                console.print(
                    f"[dim]Scanning sheets in {os.path.basename(sample_file)}...[/dim]")
                sheets = engine.get_file_sheet_names(sample_file)
                if sheets and len(sheets) > 1:
                    sheet_name = questionary.select(
                        "Select Sheet:", choices=sheets).ask()
                elif sheets:
                    sheet_name = sheets[0]
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not auto-detect sheets: {e}[/yellow]")

    params = FileLoaderParams(
        path=final_path,
        alias=alias,
        process_individual=process_individual,
        include_source_info=include_source_info,
        sheet=sheet_name
    )

    with console.status(f"Loading {final_path}..."):
        try:
            result = engine.run_loader("File", params)
            if result is not None:
                lf, metadata = result if isinstance(
                    result, tuple) else (result, {})
                engine.add_dataset(alias, lf, metadata=metadata)
                active_dataset = alias
                active_dataset_path = final_path
                recipe = []

                # Show file count if process_individual
                if metadata.get("process_individual", False):
                    file_count = metadata.get("file_count", 1)
                    log_success(
                        f"Loaded {alias}! ({file_count} files, individual processing)")
                else:
                    log_success(f"Loaded {alias}!")
            else:
                log_error("Failed to load file.")
        except Exception as e:
            log_error("Error loading file", str(e))


def add_transform_flow():
    if not active_dataset:
        console.print("[yellow]Load a dataset first![/yellow]")
        return
    registry = StepRegistry.get_all()
    categories = sorted(list(set(d.metadata.group for d in registry.values())))
    cat = questionary.select(
        message="Category:", choices=categories + ["Cancel"]).ask()
    if cat == "Cancel":
        return

    step_map = {}
    choices = []
    for sid, d in registry.items():
        if d.metadata.group == cat:
            step_map[d.metadata.label] = (sid, d)
            choices.append(d.metadata.label)

    step_label = questionary.select(
        message="Transform:", choices=sorted(choices)).ask()
    if not step_label:
        return

    sid, d = step_map[step_label]
    console.print(f"[bold]Configure {step_label}[/bold]")

    # FETCH COLUMNS FOR INTELLIGENT INPUT
    from typing import cast, Union
    recipe_for_engine = cast(List[Union[Dict[str, Any], RecipeStep]], recipe)

    available_columns = None
    try:
        # Schema propagation (usually fast)
        schema = engine.get_transformed_schema(
            active_dataset, recipe_for_engine)
        if schema:
            available_columns = schema.names()
            console.print(
                f"[dim]Detected {len(available_columns)} columns for auto-complete[/dim]")
    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not fetch schema ({e}), falling back to manual input[/yellow]")

    try:
        inputs = get_pydantic_input(
            d.params_model, available_columns=available_columns)
        if inputs is None:
            return

        recipe.append(RecipeStep(id=str(uuid.uuid4()), type=sid,
                      label=step_label, params=inputs))
        log_success("Step Added!")
    except Exception as e:
        log_error("Error configuring step", str(e))


def preview_flow():
    if not active_dataset:
        console.print("[yellow]Load a dataset first![/yellow]")
        return
    from typing import cast, Union
    recipe_for_engine = cast(List[Union[Dict[str, Any], RecipeStep]], recipe)

    with console.status("Running Preview..."):
        try:
            df = engine.get_preview(
                active_dataset, recipe_for_engine, limit=20)
            if df is not None:
                table = Table(show_header=True, header_style="bold magenta")
                for col in df.columns:
                    table.add_column(col, overflow="fold")
                # Show first 20 rows
                for row in df.head(20).iter_rows():
                    table.add_row(*[str(x) for x in row])
                console.print(table)
            else:
                log_error("Preview Failed (None returned)")
        except Exception as e:
            log_error("Preview Error", str(e))


def export_flow():
    if not active_dataset:
        console.print("[yellow]Load a dataset first![/yellow]")
        return

    fmt = questionary.select(
        "Format:", choices=["Parquet", "CSV", "Excel", "JSON", "Arrow"]).ask()
    # Individual Export Check
    meta = engine.get_dataset_metadata(active_dataset)
    export_individual = False

    if meta and meta.get("process_individual") and meta.get("input_type") == "folder":
        export_individual = questionary.confirm(
            "Export as separate files (one per source file)?",
            default=False
        ).ask()

    # Path/Prefix Logic
    default_out = f"output.{fmt.lower().replace('arrow', 'ipc').replace('excel', 'xlsx')}"
    if export_individual:
        prefix = questionary.text(
            "Filename Prefix:", default=f"export_{active_dataset}").ask()
        # Backend expects the base path without wildcard for splitting logic
        # But we construct a path that looks like a file
        folder = questionary.text("Output Folder:", default=os.getcwd()).ask()
        ext = f".{fmt.lower().replace('arrow', 'ipc').replace('excel', 'xlsx')}"
        path = os.path.join(folder, f"{prefix}{ext}")
    else:
        path = questionary.text("Output Path:", default=default_out).ask()

    params = {}
    exporter_name = fmt

    if fmt == "Parquet":
        params = ParquetExportParams(
            path=path, export_individual=export_individual)
    elif fmt == "CSV":
        params = CsvExportParams(
            path=path, export_individual=export_individual)
    elif fmt == "Excel":
        params = ExcelExportParams(
            path=path, export_individual=export_individual)
    elif fmt == "JSON":
        params = JsonExportParams(
            path=path, export_individual=export_individual)
    elif fmt == "Arrow":
        exporter_name = "IPC"
        params = IpcExportParams(
            path=path, export_individual=export_individual)

    from typing import cast, Union
    recipe_for_engine = cast(List[Union[Dict[str, Any], RecipeStep]], recipe)

    log_step(f"Starting Export to {path}...", module="EXPORT", icon="🚀")
    try:
        job_id = engine.start_export_job(
            active_dataset, recipe_for_engine, exporter_name, params)

        with console.status(f"Exporting..."):
            while True:
                info = engine.get_job_status(job_id)
                if not info:
                    time.sleep(0.5)
                    continue

                if info.status == "COMPLETED":
                    log_success(f"Export Complete! Size: {info.size_str}")
                    if info.file_details:
                        log_table(info.file_details,
                                  title="Exported Artifacts")
                    break
                elif info.status == "FAILED":
                    log_error("Export Failed", info.error or "Unknown Error")
                    break
                else:
                    time.sleep(0.1)

    except Exception as e:
        log_error("Export Error", str(e))


def manage_recipe_flow():
    global recipe
    if not recipe:
        console.print(
            "[yellow]Recipe is empty within active session.[/yellow]")
        return

    while True:
        # Display Recipe
        console.rule("[bold]Current Recipe[/bold]")
        step_choices = [
            f"{i+1}. {s.label} ({s.type})" for i, s in enumerate(recipe)]
        choices = step_choices + ["Clear All", "Back"]

        target_str = questionary.select(
            "Select Step to Modify:",
            choices=choices
        ).ask()

        if target_str == "Back":
            break

        if target_str == "Clear All":
            if questionary.confirm("Are you sure you want to clear the entire recipe?", default=False).ask():
                recipe = []
                console.print("[green]Recipe cleared.[/green]")
                break
            continue

        # Extract Index
        target_idx = int(target_str.split(".")[0]) - 1
        step_label = recipe[target_idx].label

        # Action Loop
        while True:
            action = questionary.select(
                f"Action for '{step_label}':",
                choices=["Move Up", "Move Down", "Remove Step", "Back"]
            ).ask()

            if action == "Back":
                break

            if action == "Remove Step":
                removed = recipe.pop(target_idx)
                console.print(f"[green]Removed '{removed.label}'[/green]")
                # Break inner loop to refresh outer list
                break

            elif action == "Move Up":
                if target_idx > 0:
                    recipe[target_idx], recipe[target_idx -
                                               1] = recipe[target_idx-1], recipe[target_idx]
                    console.print("[green]Moved Up[/green]")
                    target_idx -= 1  # Follow the item
                else:
                    console.print("[yellow]Already at top[/yellow]")

            elif action == "Move Down":
                if target_idx < len(recipe) - 1:
                    recipe[target_idx], recipe[target_idx +
                                               1] = recipe[target_idx+1], recipe[target_idx]
                    console.print("[green]Moved Down[/green]")
                    target_idx += 1  # Follow the item
                else:
                    console.print("[yellow]Already at bottom[/yellow]")


def save_recipe_flow():
    if not active_dataset or not active_dataset_path:
        console.print("[yellow]Load a dataset first![/yellow]")
        return

    try:
        from typing import cast, Union
        recipe_for_engine = cast(
            List[Union[Dict[str, Any], RecipeStep]], recipe)

        # Serialize params (convert Pydantic models to dicts)
        recipe_data = []
        for step in recipe_for_engine:
            if isinstance(step, RecipeStep):
                recipe_data.append(step.model_dump())
            else:
                recipe_data.append(step)

        source_dir = os.path.dirname(os.path.abspath(active_dataset_path))
        base_name = os.path.splitext(os.path.basename(active_dataset_path))[0]
        unique_id = uuid.uuid4().hex[:8]
        recipe_filename = f"{base_name}-shan-pyquery-{unique_id}.json"
        recipe_path = os.path.join(source_dir, recipe_filename)

        log_step(f"Saving recipe to {recipe_path}...",
                 module="ARTIFACT", icon="💾")
        with open(recipe_path, 'w') as f:
            json.dump(recipe_data, f, indent=2)

        log_success("Recipe Saved!")

    except Exception as e:
        log_error("Failed to save recipe", str(e))


def run_interactive():
    init_logging()
    print_header()
    while True:
        status = f"Active: {active_dataset} ({len(recipe)} steps)" if active_dataset else "No Data Loaded"
        console.rule(status)
        choice = questionary.select(message="What would you like to do?", choices=[
                                    "📂 Load Data", "🛠️ Add Transformation", "📜 Manage Recipe", "👀 Preview Data", "📤 Export Data", "💾 Save Recipe", "❌ Exit"]).ask()

        if choice == "❌ Exit":
            sys.exit(0)
        elif choice == "📂 Load Data":
            load_data_flow()
        elif choice == "🛠️ Add Transformation":
            add_transform_flow()
        elif choice == "📜 Manage Recipe":
            manage_recipe_flow()
        elif choice == "👀 Preview Data":
            preview_flow()
        elif choice == "📤 Export Data":
            export_flow()
        elif choice == "💾 Save Recipe":
            save_recipe_flow()
