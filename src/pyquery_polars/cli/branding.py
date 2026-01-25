from typing import Optional, Tuple, List, Dict, Any

import time
import random
import platform
import os
import textwrap
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
)
from importlib.metadata import version

console = Console(force_terminal=True)


def log_table(items: List[Dict[str, Any]], title: str = "Details"):
    """
    Log a generic table of items. 
    items: List of dicts, keys become columns.
    """
    if not items:
        return

    theme = get_current_theme()
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

    # Infer columns from first item
    columns = list(items[0].keys())
    for col in columns:
        table.add_column(col.replace("_", " ").title(),
                         style="cyan", no_wrap=True)

    for item in items:
        row = [str(item.get(col, "")) for col in columns]
        table.add_row(*row)

    console.print(table)
    console.print("\n")


TAGLINES = [
    "PyQuery by Shan.TK — born from Rust, powered by lazy execution, and built to replace Excel, Power Query, Pandas, and the era of waiting.",
    "PyQuery by Shan.TK — the data engine that processes 100GB files while you decide what to watch on Netflix.",
    "PyQuery by Shan.TK — making your laptop feel like a supercomputer since 2025.",
    "PyQuery by Shan.TK — Warning: usage may cause addiction to sub-second query times.",
    "PyQuery by Shan.TK — Your CPU called, it wants to do real work.",
    "PyQuery by Shan.TK — forged in Rust to end Excel, Power Query, Pandas, and the lie that slow analytics is acceptable.",
    "PyQuery by Shan.TK — built for people who stopped apologizing for wanting fast data.",
    "PyQuery by Shan.TK — the data engine that treats waiting as a bug, not a feature.",
    "PyQuery by Shan.TK — because your analysis deserves better than a spinning wheel.",
    "PyQuery by Shan.TK — when Excel crashes, Pandas panics, and Power Query taps out.",
    "PyQuery by Shan.TK — replacing Excel workflows one shattered spreadsheet at a time.",
    "PyQuery by Shan.TK — Pandas but without the suffering.",
    "PyQuery by Shan.TK — Power Query, if it actually had power.",
    "PyQuery by Shan.TK — lazy execution for people who think before they compute.",
    "PyQuery by Shan.TK — where query planning matters more than blind execution.",
    "PyQuery by Shan.TK — built on the assumption that your data is bigger than RAM.",
    "PyQuery by Shan.TK — your CPU finally gets to do something meaningful.",
    "PyQuery by Shan.TK — warning: may permanently ruin your tolerance for slow tools.",
    "PyQuery by Shan.TK — once you go lazy, you don't go back.",
    "PyQuery by Shan.TK — making laptops feel illegal since 2025.",
    "PyQuery by Shan.TK — Excel died so this could run.",
    "PyQuery by Shan.TK — this is what happens when patience hits zero.",
    "PyQuery by Shan.TK — not responsible for broken legacy workflows.",
]

# Define Themes associated with sequences
THEMED_SEQUENCES = [

    {
        "name": "CYBERPUNK // MAIN CHARACTER MODE",
        "start_color": (0, 255, 255),   # Cyan
        "end_color": (255, 0, 255),     # Magenta
        "border_style": "cyan",
        "steps": [
            "Initializing Quantum Cores...",
            "Mounting Lazy Execution Graph...",
            "Optimizing Polars Engines...",
            "Reclaiming Memory from Legacy Tools...",
            "PyQuery Online."
        ]
    },

    {
        "name": "RUSTACEAN AWAKENING 🦀",
        "start_color": (255, 165, 0),   # Orange
        "end_color": (255, 69, 0),      # Red-Orange
        "border_style": "red",
        "steps": [
            "Waking up the Rust Crab...",
            "Compiling LazyFrames...",
            "Vectorizing Everything...",
            "Ignoring Memory Limits Politely...",
            "Execution Ready."
        ]
    },

    {
        "name": "THE MATRIX // NO GOING BACK",
        "start_color": (0, 255, 0),     # Bright Green
        "end_color": (0, 100, 0),       # Dark Green
        "border_style": "green",
        "steps": [
            "Establishing Secure Data Tunnel...",
            "Downloading Additional RAM...",
            "Bypassing Single-Threaded Constraints...",
            "Rewriting the Laws of Time...",
            "Access Granted."
        ]
    },

    {
        "name": "EXCEL SLAYER // LEGACY ERA ENDS",
        "start_color": (32, 114, 68),   # Excel Green
        "end_color": (255, 255, 255),   # White
        "border_style": "green",
        "steps": [
            "Scanning for Excel Artifacts...",
            "Detecting Fragile Workflows...",
            "Shredding Legacy Spreadsheets...",
            "Replacing VLOOKUP with Sanity...",
            "Migration Complete."
        ]
    },

    {
        "name": "VILLAIN ARC // TOTAL DOMINATION",
        "start_color": (128, 0, 128),   # Purple
        "end_color": (255, 215, 0),     # Gold
        "border_style": "magenta",
        "steps": [
            "Summoning Data Entities...",
            "Banishing Null Values...",
            "Aligning Memory Segments...",
            "Optimizing for Total Domination...",
            "Begin."
        ]
    },

    {
        "name": "CHILL MODE // EFFORTLESS FLEX",
        "start_color": (135, 206, 235),  # Sky Blue
        "end_color": (255, 192, 203),   # Pink
        "border_style": "blue",
        "steps": [
            "Vibing with the CPU...",
            "Letting the SSD Cook...",
            "Parallel Thoughts Activated...",
            "Outperforming Expectations...",
            "Let's Go."
        ]
    },

    # ============================
    # NEW HIGH-IMPACT THEMES
    # ============================

    {
        "name": "LAZY EXECUTION GOSPEL",
        "start_color": (180, 180, 255),
        "end_color": (120, 120, 200),
        "border_style": "blue",
        "steps": [
            "Building Logical Plan...",
            "Optimizing Query Graph...",
            "Pushing Down Predicates...",
            "Streaming Execution Initiated...",
            "Query Complete."
        ]
    },

    {
        "name": "PANDAS DETOX // RECOVERY MODE",
        "start_color": (200, 200, 200),
        "end_color": (100, 100, 100),
        "border_style": "white",
        "steps": [
            "Detecting Pandas Trauma...",
            "Releasing Unnecessary Copies...",
            "Unlearning Eager Execution...",
            "Rediscovering Performance...",
            "You’re Free Now."
        ]
    },

    {
        "name": "BENCHMARK GOD MODE 🔥",
        "start_color": (255, 0, 0),
        "end_color": (0, 0, 0),
        "border_style": "red",
        "steps": [
            "Locking CPU Cores...",
            "Maximizing Thread Utilization...",
            "Disabling Excuses...",
            "Executing at Full Throttle...",
            "Benchmark Complete."
        ]
    },

    {
        "name": "EXCEL EXISTENTIAL CRISIS",
        "start_color": (34, 139, 34),
        "end_color": (0, 0, 0),
        "border_style": "green",
        "steps": [
            "Opening Workbook...",
            "Counting Rows...",
            "Freezing...",
            "Closing Workbook...",
            "Launching PyQuery Instead."
        ]
    },

    {
        "name": "SILENT ASSASSIN",
        "start_color": (50, 50, 50),
        "end_color": (0, 0, 0),
        "border_style": "white",
        "steps": [
            "Loading Dataset...",
            "Optimizing Plan...",
            "Executing...",
            "Done.",
            ""
        ]
    }
]

# --- UNIFIED LOGGING HELPERS ---
START_TIME = time.time()
ACTIVE_THEME = None


def get_current_theme():
    global ACTIVE_THEME
    if ACTIVE_THEME is None:
        ACTIVE_THEME = random.choice(THEMED_SEQUENCES)
    return ACTIVE_THEME


def init_logging():
    """Initialize the logging timer and theme."""
    global START_TIME, ACTIVE_THEME
    START_TIME = time.time()
    if ACTIVE_THEME is None:
        ACTIVE_THEME = random.choice(THEMED_SEQUENCES)


def log_step(message: str, module: str = "SYSTEM", icon: str = "•", style: Optional[str] = None):
    """
    Log a step with a timestamp and module tag.
    Style defaults to the active theme's primary color if not specified.
    """
    theme = get_current_theme()
    final_style = style if style is not None else theme["border_style"]

    elapsed = time.time() - START_TIME
    console.print(
        f"[dim] [ {elapsed:.3f}s ][/dim] "
        f"[bold {final_style}] [ {module.center(9)} ][/bold {final_style}] "
        f"{icon}  {message}"
    )


def log_error(message: str, details: str = ""):
    """Log an error message."""
    console.print(f"[bold red]❌ {message}[/bold red]")
    if details:
        console.print(f"[dim red]   {details}[/dim red]")


def log_success(message: str):
    """Log a success message."""
    elapsed = time.time() - START_TIME
    console.print(
        f"\n[bold green] ➤ {message} ({elapsed:.3f}s)[/bold green]\n")


class log_progress:
    """
    Context manager for a Rich Progress Bar.
    Usage:
    with log_progress("Processing...", total=100) as progress:
        for i in range(100):
            progress.advance(1)
    """

    def __init__(self, description: str, total: Optional[int] = None, module: str = "SYSTEM", icon: str = "⏳"):
        self.description = description
        self.total = total
        self.module = module
        self.icon = icon

        # Use simple variable first to avoid "self.progress" possibly None inference confusion during init
        progress_obj = None
        self.task_id = None

        theme = get_current_theme()
        style = theme['border_style']

        progress_obj = Progress(
            SpinnerColumn(style=style),
            TextColumn(f"[bold {style}][ {module.center(9)} ][/bold {style}]"),
            TextColumn(f"{icon} [bold]{description}[/bold]"),
            BarColumn(bar_width=None, style=style),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=True  # Disappear when done for cleaner logs
        )
        self.progress = progress_obj

    def __enter__(self):
        if self.progress:
            self.progress.start()
            self.task_id = self.progress.add_task(
                self.description, total=self.total)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()
        if exc_type is None:
            # Optional: Log completion
            pass

    def update(self, completed: Optional[int] = None, advance: Optional[int] = None, description: Optional[str] = None, total: Optional[int] = None):
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, completed=completed,
                                 advance=advance, description=description, total=total)

    def advance(self, advance: int = 1):
        if self.progress and self.task_id is not None:
            self.progress.advance(self.task_id, advance=advance)


def gradient_text(text: str, start_color: Tuple[int, int, int], end_color: Tuple[int, int, int]) -> Text:
    """Generate a text object with a linear gradient."""
    # Simple linear interpolation for MVP
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


def get_hardware_nfo():
    """Get catchy hardware info."""
    try:
        system = platform.system()
        cpu_count = os.cpu_count() or "Unknown"
        return f"{system} / {cpu_count} CPU Cores Active / SIMD Enabled"
    except:
        return "Quantum System / Infinite Cores"


def show_banner():
    # 1. Clear screen
    console.clear()

    # Get Version
    try:
        v = version("pyquery-polars")
    except:
        v = "dev"

    # 2. Cool ASCII Art (Block Style with Manual Tail Fix on Q)
    # I added a little tail on the last line of Q
    ascii_art = """
    ██████╗ ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗
    ██╔══██╗╚██╗ ██╔╝██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝
    ██████╔╝ ╚████╔╝ ██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝ 
    ██╔═══╝   ╚██╔╝  ██║   ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝  
    ██║        ██║   ╚██████╗║╚██████╔╝███████╗██║  ██║   ██║   
    ╚═╝        ╚═╝    ╚═════╝╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   
    """
    # Remove python indentation padding
    ascii_art = textwrap.dedent(ascii_art).strip()

    # 3. Randomize Experience (Theme Based)
    tagline = random.choice(TAGLINES)
    # Set Global Theme
    global ACTIVE_THEME
    theme = random.choice(THEMED_SEQUENCES)
    ACTIVE_THEME = theme

    steps = theme["steps"]

    # 4. Display Banner FIRST
    # Use Theme Colors for Gradient
    title_text = gradient_text(
        ascii_art, theme["start_color"], theme["end_color"])
    subtitle = Text(tagline, style="italic white")

    content = Text.assemble(
        title_text,
        "\n",
        subtitle
    )

    panel = Panel(
        content,
        border_style=theme["border_style"],
        title="[bold yellow]★ SHAN'S PYQUERY ★[/bold yellow]",
        subtitle=f"[dim]v{v}[/dim] [bold {theme['border_style']}] // {theme['name']} Mode[/]",
        padding=(1, 2)
    )

    console.print(panel)
    console.print("\n")

    # 5. Boot Animation (Enhanced "System Log" Style)
    t0 = time.time()
    for i, step in enumerate(steps):
        time.sleep(random.uniform(0.05, 0.15))

        # Fake "Module" based on content keywords or random
        module = "SYSTEM"
        color = theme["border_style"]  # Use theme color for modules
        icon = "✓"

        lower_step = step.lower()
        if "quantum" in lower_step or "core" in lower_step:
            module = "KERNEL"
            icon = "⚡"
        elif "data" in lower_step or "memory" in lower_step:
            module = "MEMORY"
            icon = "💾"
        elif "optimizi" in lower_step:
            module = "OPTIMIZER"
            icon = "🚀"
        elif "mount" in lower_step:
            module = "I/O"
            icon = "�"
        elif "rust" in lower_step:
            module = "SAFE_MODE"
            icon = "🦀"
        elif "excel" in lower_step or "shred" in lower_step:
            module = "PURGE"
            icon = "�"
        elif "hack" in lower_step or "bypass" in lower_step:
            module = "EXPLOIT"
            icon = "💀"
        elif "summ" in lower_step or "banis" in lower_step:
            module = "ARCANE"
            icon = "🔮"
        elif "vibing" in lower_step:
            module = "MOOD"
            icon = "🎵"

        elapsed = time.time() - t0

        # Format: [ 0.120s ] [ KERNEL ] ⚡ Message...
        console.print(
            f"[dim] [ {elapsed:.3f}s ][/dim] "
            f"[bold {color}] [ {module.center(9)} ][/bold {color}] "
            f"{icon}  {step}"
        )

    # 6. Hardware Stats Highlight
    hw_info = get_hardware_nfo()
    time.sleep(0.1)
    console.print(
        f"[dim] [ {time.time()-t0:.3f}s ][/dim] [bold white] [ DETECTED  ] [/bold white] 💻  {hw_info}")

    time.sleep(0.2)
    console.print(
        f"\n[bold green] ➤ SYSTEM ONLINE ({time.time() - t0:.3f}s)[/bold green]\n")
    time.sleep(0.3)


if __name__ == "__main__":
    show_banner()
