import sys
import os
import glob
import uuid
from typing import Dict, Any, Type, List, get_args, get_origin, Optional
from pydantic import BaseModel

import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from pyquery_polars.backend.engine import PyQueryEngine
from pyquery_polars.core.registry import StepRegistry
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.io_params import FileLoaderParams

# Initialize
console = Console()
engine = PyQueryEngine()

# State
active_dataset: Optional[str] = None
recipe: List[RecipeStep] = []


def print_header():
    console.print(Panel.fit(
        "[bold cyan]⚡ PyQuery Interactive CLI[/bold cyan]", border_style="cyan"))


def get_pydantic_input(model_cls: Type[BaseModel]) -> Dict[str, Any]:
    inputs = {}
    schema = model_cls.model_fields

    for field_name, field_info in schema.items():
        label = field_name.replace("_", " ").title()
        default_val = field_info.default if field_info.default is not None else ""
        outer_type = field_info.annotation

        if get_origin(outer_type) is not None and "Literal" in str(get_origin(outer_type)):
            options = list(get_args(outer_type))
            val = questionary.select(message=f"{label}:", choices=[str(
                o) for o in options], default=str(default_val)).ask()
            inputs[field_name] = val
        elif outer_type == int:
            val = questionary.text(f"{label} (int):", default=str(
                default_val), validate=lambda t: t.isdigit()).ask()
            inputs[field_name] = int(val)
        elif outer_type == float:
            val = questionary.text(f"{label} (float):", default=str(
                default_val), validate=lambda t: t.replace('.', '', 1).isdigit()).ask()
            inputs[field_name] = float(val)
        elif outer_type == bool:
            val = questionary.confirm(
                f"{label}?", default=bool(default_val)).ask()
            inputs[field_name] = val
        else:
            val = questionary.text(f"{label}:", default=str(default_val)).ask()
            inputs[field_name] = val

    return inputs


def load_data_flow():
    global active_dataset, recipe
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

    alias = questionary.text(
        "Dataset Alias:", default=os.path.basename(path).split('.')[0]).ask()
    params = FileLoaderParams(path=path, alias=alias)

    with console.status(f"Loading {path}..."):
        lf = engine.run_loader("File", params)
        if lf is not None:
            engine.add_dataset(alias, lf)
            active_dataset = alias
            recipe = []
            console.print(f"[green]Loaded {alias}![/green]")
        else:
            console.print("[red]Failed to load file.[/red]")


def add_transform_flow():
    if not active_dataset:
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
    inputs = get_pydantic_input(d.params_model)
    if inputs is None:
        return

    recipe.append(RecipeStep(id=str(uuid.uuid4()), type=sid,
                  label=step_label, params=inputs))
    console.print("[green]Step Added![/green]")


def preview_flow():
    if not active_dataset:
        return
    from typing import cast, Union
    recipe_for_engine = cast(List[Union[Dict[str, Any], RecipeStep]], recipe)

    with console.status("Running Preview..."):
        df = engine.get_preview(active_dataset, recipe_for_engine, limit=20)
    if df is not None:
        table = Table(show_header=True, header_style="bold magenta")
        for col in df.columns:
            table.add_column(col, overflow="fold")
        for row in df.iter_rows():
            table.add_row(*[str(x) for x in row])
        console.print(table)
    else:
        console.print("[red]Preview Failed[/red]")


def run_interactive():
    print_header()
    while True:
        status = f"Active: {active_dataset} ({len(recipe)} steps)" if active_dataset else "No Data Loaded"
        console.rule(status)
        choice = questionary.select(message="What would you like to do?", choices=[
                                    "📂 Load Data", "🛠️ Add Transformation", "👀 Preview Data", "❌ Exit"]).ask()

        if choice == "❌ Exit":
            sys.exit(0)
        elif choice == "📂 Load Data":
            load_data_flow()
        elif choice == "🛠️ Add Transformation":
            add_transform_flow()
        elif choice == "👀 Preview Data":
            preview_flow()
