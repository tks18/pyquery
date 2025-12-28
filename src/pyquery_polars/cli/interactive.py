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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io_params import (
    FileLoaderParams, ParquetExportParams, CsvExportParams,
    ExcelExportParams, JsonExportParams, IpcExportParams
)

# Initialize
console = Console()
engine = PyQueryEngine()

# State
active_dataset: Optional[str] = None
active_dataset_path: Optional[str] = None
recipe: List[RecipeStep] = []


def print_header():
    console.print(Panel.fit(
        "[bold cyan]⚡ PyQuery Interactive CLI[/bold cyan]", border_style="cyan"))


def get_pydantic_input(model_cls: Type[BaseModel]) -> Dict[str, Any]:
    inputs = {}
    schema = model_cls.model_fields

    for field_name, field_info in schema.items():
        label = field_name.replace("_", " ").title()
        default_val = field_info.default if field_info.default is not None and field_info.default != PydanticUndefined else ""
        outer_type = field_info.annotation

        args = get_args(outer_type)
        origin = get_origin(outer_type)

        # 1. Handle List[BaseModel] (e.g. CleanCastParams.changes)
        if (origin is list or outer_type == list) and args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
            nested_cls = args[0]
            items = []
            console.print(
                f"[bold cyan]Configure list of {label} ({nested_cls.__name__}):[/bold cyan]")

            while True:
                if items and not questionary.confirm(f"Add another {nested_cls.__name__}?", default=False).ask():
                    break
                # Force at least one item if default is empty? No, respect user choice if optional.
                # But usually for params, if it exists, we want at least one or it's optional.
                if not items and default_val == "" and not questionary.confirm(f"Add a {nested_cls.__name__}?", default=True).ask():
                    break

                console.print(f"  [cyan]Item {len(items)+1}:[/cyan]")
                item_data = get_pydantic_input(nested_cls)
                items.append(item_data)

            inputs[field_name] = items

        # 2. Handle List[str] -> Comma separated input
        elif origin is list or outer_type == list:
            val = questionary.text(
                f"{label} (comma separated):", default=str(default_val)).ask()
            if val:
                inputs[field_name] = [x.strip() for x in val.split(",")]
            else:
                inputs[field_name] = []

        # 3. Literal Options
        elif origin is not None and "Literal" in str(origin):
            options = list(args)
            val = questionary.select(message=f"{label}:", choices=[str(
                o) for o in options], default=str(default_val)).ask()
            inputs[field_name] = val

        # 4. Primitives
        elif outer_type == int:
            val = questionary.text(f"{label} (int):", default=str(
                default_val), validate=lambda t: t.isdigit() or (t == "" and default_val == "")).ask()
            if val == "":
                inputs[field_name] = default_val
            else:
                inputs[field_name] = int(val)

        elif outer_type == float:
            val = questionary.text(
                f"{label} (float):", default=str(default_val)).ask()
            if val == "":
                inputs[field_name] = default_val
            else:
                inputs[field_name] = float(val)

        elif outer_type == bool:
            val = questionary.confirm(f"{label}?", default=bool(
                default_val) if default_val != "" else False).ask()
            inputs[field_name] = val

        # 5. Fallback Text
        else:
            val = questionary.text(f"{label}:", default=str(default_val)).ask()
            inputs[field_name] = val

    return inputs


def load_data_flow():
    global active_dataset, active_dataset_path, recipe
    files = glob.glob("*.csv") + glob.glob("*.parquet") + glob.glob("*.xlsx")
    if not files:
        path = questionary.text("File Path:").ask()
    else:
        path = questionary.select(
            message="Select File:", choices=files + ["Manual Path"]).ask()
        if path == "Manual Path":
            path = questionary.text("File Path:").ask()

    if not path:
        return

    default_alias = os.path.basename(path).split('.')[0]
    if not default_alias:
        default_alias = "dataset"

    alias = questionary.text("Dataset Alias:", default=default_alias).ask()
    params = FileLoaderParams(path=path, alias=alias)

    with console.status(f"Loading {path}..."):
        try:
            result = engine.run_loader("File", params)
            if result is not None:
                lf, _ = result
                engine.add_dataset(alias, lf)
                active_dataset = alias
                active_dataset_path = path
                recipe = []
                console.print(f"[green]Loaded {alias}![/green]")
            else:
                console.print("[red]Failed to load file.[/red]")
        except Exception as e:
            console.print(f"[red]Error loading file: {e}[/red]")


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
    try:
        inputs = get_pydantic_input(d.params_model)
        if inputs is None:
            return

        recipe.append(RecipeStep(id=str(uuid.uuid4()), type=sid,
                      label=step_label, params=inputs))
        console.print("[green]Step Added![/green]")
    except Exception as e:
        console.print(f"[red]Error configuring step: {e}[/red]")


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
                console.print("[red]Preview Failed (None returned)[/red]")
        except Exception as e:
            console.print(f"[red]Preview Error: {e}[/red]")


def export_flow():
    if not active_dataset:
        console.print("[yellow]Load a dataset first![/yellow]")
        return

    fmt = questionary.select(
        "Format:", choices=["Parquet", "CSV", "Excel", "JSON", "Arrow"]).ask()
    default_out = f"output.{fmt.lower().replace('arrow', 'ipc')}"
    path = questionary.text("Output Path:", default=default_out).ask()

    params = {}
    exporter_name = fmt

    if fmt == "Parquet":
        params = ParquetExportParams(path=path)
    elif fmt == "CSV":
        params = CsvExportParams(path=path)
    elif fmt == "Excel":
        params = ExcelExportParams(path=path)
    elif fmt == "JSON":
        params = JsonExportParams(path=path)
    elif fmt == "Arrow":
        exporter_name = "IPC"
        params = IpcExportParams(path=path)

    from typing import cast, Union
    recipe_for_engine = cast(List[Union[Dict[str, Any], RecipeStep]], recipe)

    console.print(f"🚀 Starting Export to {path}...")
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
                    console.print(
                        f"[green]✅ Export Complete! Size: {info.size_str}[/green]")
                    break
                elif info.status == "FAILED":
                    console.print(f"[red]❌ Export Failed: {info.error}[/red]")
                    break
                else:
                    time.sleep(0.1)

    except Exception as e:
        console.print(f"[red]Export Error: {e}[/red]")


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

        console.print(f"💾 Saving recipe to {recipe_path}...")
        with open(recipe_path, 'w') as f:
            json.dump(recipe_data, f, indent=2)

        console.print(f"[green]✅ Recipe Saved![/green]")

    except Exception as e:
        console.print(f"[red]Failed to save recipe: {e}[/red]")


def run_interactive():
    print_header()
    while True:
        status = f"Active: {active_dataset} ({len(recipe)} steps)" if active_dataset else "No Data Loaded"
        console.rule(status)
        choice = questionary.select(message="What would you like to do?", choices=[
                                    "📂 Load Data", "🛠️ Add Transformation", "👀 Preview Data", "📤 Export Data", "💾 Save Recipe", "❌ Exit"]).ask()

        if choice == "❌ Exit":
            sys.exit(0)
        elif choice == "📂 Load Data":
            load_data_flow()
        elif choice == "🛠️ Add Transformation":
            add_transform_flow()
        elif choice == "👀 Preview Data":
            preview_flow()
        elif choice == "📤 Export Data":
            export_flow()
        elif choice == "💾 Save Recipe":
            save_recipe_flow()
