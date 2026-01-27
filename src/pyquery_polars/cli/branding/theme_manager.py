from typing import List, Dict, Any, Optional

import random


class ThemeManager:
    """
    Manages the CLI visual themes and taglines.
    Follows SRP by isolating theme data and selection logic.
    """

    TAGLINES: List[str] = [
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

    THEMES: List[Dict[str, Any]] = [
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
        },
    ]

    def __init__(self):
        self._active_theme: Optional[Dict[str, Any]] = None

    def get_theme(self) -> Dict[str, Any]:
        """Lazy load a random theme if none selected."""
        if self._active_theme is None:
            self._active_theme = random.choice(self.THEMES)
        return self._active_theme

    def get_tagline(self) -> str:
        """Get a random tagline."""
        return random.choice(self.TAGLINES)
