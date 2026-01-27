from typing import Optional, List, Dict, Any, Tuple

import time
from rich.console import Console
from rich.text import Text
from rich import box
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
)

from pyquery_polars.cli.branding.theme_manager import ThemeManager


class ConsoleUI:
    """
    Handles all console output operations using the Rich library.
    Depends on ThemeManager for visual consistency.
    """

    def __init__(self, theme_manager: ThemeManager):
        self._console = Console(force_terminal=True)
        self._theme_manager = theme_manager
        self._start_time = time.time()

    @property
    def console(self) -> Console:
        return self._console

    def reset_timer(self):
        self._start_time = time.time()

    def gradient_text(self, text: str, start_color: Tuple[int, int, int], end_color: Tuple[int, int, int]) -> Text:
        """Generate a text object with a linear gradient."""
        result = Text()
        lines = text.split("\n")
        steps = len(lines)

        for i, line in enumerate(lines):
            t = i / max(steps - 1, 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
            color = f"rgb({r},{g},{b})"
            result.append(line + "\n", style=color)
        return result

    def log_step(self, message: str, module: str = "SYSTEM", icon: str = "•", style: Optional[str] = None):
        """
        Log a step with a timestamp and module tag.
        """
        theme = self._theme_manager.get_theme()
        final_style = style if style is not None else theme["border_style"]

        elapsed = time.time() - self._start_time
        self._console.print(
            f"[dim] [ {elapsed:.3f}s ][/dim] "
            f"[bold {final_style}] [ {module.center(9)} ][/bold {final_style}] "
            f"{icon}  {message}"
        )

    def log_error(self, message: str, details: str = ""):
        """Log an error message."""
        self._console.print(f"[bold red]❌ {message}[/bold red]")
        if details:
            self._console.print(f"[dim red]   {details}[/dim red]")

    def log_success(self, message: str):
        """Log a success message."""
        elapsed = time.time() - self._start_time
        self._console.print(
            f"\n[bold green] ➤ {message} ({elapsed:.3f}s)[/bold green]\n")

    def log_table(self, items: List[Dict[str, Any]], title: str = "Details"):
        """
        Log a generic table of items. 
        """
        if not items:
            return

        theme = self._theme_manager.get_theme()
        header_style = f"bold {theme['border_style']}"

        table = Table(
            show_header=True,
            header_style=header_style,
            title=f"[bold]{title}[/bold]",
            box=box.ROUNDED,
            padding=(0, 2),
            collapse_padding=True,
            show_lines=False,
            row_styles=["none", "dim"]
        )

        # Robust Column Inference: Union of all keys from all items
        all_keys = dict.fromkeys(key for item in items for key in item.keys())
        columns = list(all_keys.keys())

        # Prioritize Specific Columns Logic (Optional but good for UX)
        priority_cols = ["Dataset", "Status", "Size", "Path", "Error"]
        sorted_cols = [c for c in priority_cols if c in columns] + \
            [c for c in columns if c not in priority_cols]

        for col in sorted_cols:
            table.add_column(col.replace("_", " ").title(),
                             style="cyan", no_wrap=False)

        for item in items:
            row = [str(item.get(col, "")) for col in sorted_cols]
            table.add_row(*row)

        self._console.print(table)
        self._console.print("\n")

    def create_progress(self, description: str, total: Optional[int] = None, module: str = "SYSTEM", icon: str = "⏳"):
        """Factory method for progress tracking context manager."""
        return _ProgressContext(self, description, total, module, icon)


class _ProgressContext:
    """
    Context manager for a Rich Progress Bar.
    """

    def __init__(self, ui: ConsoleUI, description: str, total: Optional[int] = None, module: str = "SYSTEM", icon: str = "⏳"):
        self.ui = ui
        self.description = description
        self.total = total
        self.module = module
        self.icon = icon
        self.task_id = None
        self.progress = None

    def __enter__(self):
        theme = self.ui._theme_manager.get_theme()
        style = theme['border_style']

        self.progress = Progress(
            SpinnerColumn(style=style),
            TextColumn(
                f"[bold {style}][ {self.module.center(9)} ][/bold {style}]"),
            TextColumn(f"{self.icon} [bold]{self.description}[/bold]"),
            BarColumn(bar_width=None, style=style),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.ui.console,
            transient=True
        )
        self.progress.start()
        self.task_id = self.progress.add_task(
            self.description, total=self.total)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()

    def update(self, **kwargs):
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, **kwargs)

    def advance(self, advance: int = 1):
        if self.progress and self.task_id is not None:
            self.progress.advance(self.task_id, advance=advance)
