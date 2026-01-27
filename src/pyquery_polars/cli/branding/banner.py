import time
import textwrap
import random
import platform
import os
from importlib.metadata import version
from rich.panel import Panel
from rich.text import Text

from pyquery_polars.cli.branding.console_ui import ConsoleUI
from pyquery_polars.cli.branding.theme_manager import ThemeManager


class BannerRenderer:
    """
    Handles the rendering of the CLI startup banner and boot sequence.
    """

    ASCII_ART = """
    ██████╗ ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗
    ██╔══██╗╚██╗ ██╔╝██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝
    ██████╔╝ ╚████╔╝ ██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝ 
    ██╔═══╝   ╚██╔╝  ██║   ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝  
    ██║        ██║   ╚██████╗║╚██████╔╝███████╗██║  ██║   ██║   
    ╚═╝        ╚═╝    ╚═════╝╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   
    """

    def __init__(self, ui: ConsoleUI, theme_manager: ThemeManager):
        self.ui = ui
        self.theme_manager = theme_manager

    def _get_hardware_info(self) -> str:
        """Get catchy hardware info."""
        try:
            system = platform.system()
            cpu_count = os.cpu_count() or "Unknown"
            return f"{system} / {cpu_count} CPU Cores Active / SIMD Enabled"
        except:
            return "Quantum System / Infinite Cores"

    def render(self):
        """Execute the full banner sequence."""
        # 1. Clear screen
        self.ui.console.clear()

        # Get Version
        try:
            v = version("pyquery-polars")
        except:
            v = "dev"

        # 2. Get Theme and Metadata
        ascii_art_dedented = textwrap.dedent(self.ASCII_ART).strip()
        theme = self.theme_manager.get_theme()
        tagline = self.theme_manager.get_tagline()

        # 3. Create Title Text with Gradient
        title_text = self.ui.gradient_text(
            ascii_art_dedented, theme["start_color"], theme["end_color"]
        )
        subtitle = Text(tagline, style="italic white")

        content = Text.assemble(title_text, "\n", subtitle)

        panel = Panel(
            content,
            border_style=theme["border_style"],
            title="[bold yellow]★ SHAN'S PYQUERY ★[/bold yellow]",
            subtitle=f"[dim]v{v}[/dim] [bold {theme['border_style']}] // {theme['name']} Mode[/]",
            padding=(1, 2)
        )

        self.ui.console.print(panel)
        self.ui.console.print("\n")

        # 4. Boot Animation
        t0 = time.time()
        steps = theme["steps"]

        for step in steps:
            time.sleep(random.uniform(0.05, 0.15))

            # Smart Module Inference
            module = "SYSTEM"
            color = theme["border_style"]
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
                icon = "📂"
            elif "rust" in lower_step:
                module = "SAFE_MODE"
                icon = "🦀"
            elif "excel" in lower_step or "shred" in lower_step:
                module = "PURGE"
                icon = "♻️"
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
            self.ui.console.print(
                f"[dim] [ {elapsed:.3f}s ][/dim] "
                f"[bold {color}] [ {module.center(9)} ][/bold {color}] "
                f"{icon}  {step}"
            )

        # 5. Hardware Stats
        hw_info = self._get_hardware_info()
        time.sleep(0.1)
        self.ui.console.print(
            f"[dim] [ {time.time()-t0:.3f}s ][/dim] [bold white] [ DETECTED  ] [/bold white] 💻  {hw_info}")

        time.sleep(0.2)
        self.ui.console.print(
            f"\n[bold green] ➤ SYSTEM ONLINE ({time.time() - t0:.3f}s)[/bold green]\n")
        time.sleep(0.3)
