import sys
import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from importlib.metadata import version

console = Console()

TAGLINE = "PyQuery by Shan.TK — born from Rust, powered by lazy execution, and built to replace Excel, Power Query, Pandas, and the era of waiting they normalized."

def show_banner():
    # 1. Clear screen
    console.clear()
    
    # Get Version
    try:
        v = version("pyquery-polars")
    except:
        v = "dev"
    
    # 2. Cool ASCII Art (Text)
    ascii_art = """
    ██████╗ ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗
    ██╔══██╗╚██╗ ██╔╝██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝
    ██████╔╝ ╚████╔╝ ██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝ 
    ██╔═══╝   ╚██╔╝  ██║   ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝  
    ██║        ██║   ╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║   
    ╚═╝        ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   
    """
    
    # 3. Animation: "Booting Data OS..."
    steps = [
        "Initializing Quantum Cores...",
        "Mounting Data Fabric...",
        "Optimizing Polars Engines...",
        "Syncing with Doomscroll API...",
        "PyQuery OS Ready."
    ]
    
    with Live(transient=True) as live:
        for step in steps:
            time.sleep(0.04) # Fast boot
            spinner = Spinner("dots", text=f"[bold cyan]{step}[/bold cyan]")
            live.update(Align.center(spinner))
            time.sleep(0.3)
            
    # 4. Final Banner Display
    title = Text(ascii_art, style="bold cyan")
    subtitle = Text(TAGLINE, style="italic magenta")
    
    panel = Panel(
        Align.center(
            Text.assemble(
                title,
                "\n\n",
                subtitle
            )
        ),
        border_style="cyan",
        title="[bold yellow]★ SHAN'S PYQUERY ★[/bold yellow]",
        subtitle=f"[dim]v{v}[/dim]",
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print("\n")

if __name__ == "__main__":
    show_banner()
