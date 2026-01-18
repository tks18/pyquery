import argparse
import sys
import subprocess
import os

from pyquery_polars.cli.headless import run_headless
from pyquery_polars.cli.interactive import run_interactive
from pyquery_polars.cli.branding import show_banner, log_step, log_error, log_success, init_logging


def main():
    # Default to UI if no args
    if len(sys.argv) == 1:
        sys.argv.append("ui")
    elif len(sys.argv) == 2 and sys.argv[1] == "--dev":
        sys.argv.insert(1, "ui")

    # Check for --dev flag early to skip banner
    dev_mode = "--dev" in sys.argv
    
    # Show Banner for all commands (Console Appeal) IF NOT IN DEV MODE
    if not dev_mode:
        try:
            show_banner()
        except Exception:
            pass # Fallback if rich fails or unicode issues

    parser = argparse.ArgumentParser(description="Shan's PyQuery Platform CLI")
    subparsers = parser.add_subparsers(
        dest="command", help="Available subcommands")

    # 1. RUN (Headless)
    run_parser = subparsers.add_parser(
        "run", help="Execute a recipe logic headless")
    run_parser.add_argument(
        "--source", "-s", required=True, help="Input data file, connection string, or URL")
    run_parser.add_argument(
        "--type", default="file", choices=["file", "sql", "api"], help="Input type")
    run_parser.add_argument(
        "--sql-query", help="Query for SQL input")
    run_parser.add_argument(
        "--api-url", help="URL for API input (overrides source if provided)")
    run_parser.add_argument(
        "--sheet-name", "-S", default="Sheet1", help="Sheet name for Excel files")
    run_parser.add_argument(
        "--recipe", "-r", required=False, help="JSON recipe file")
    run_parser.add_argument(
        "--output", "-o", required=True, help="Output file path")
    run_parser.add_argument(
        "--format", "-f", default="Parquet", help="Output format (Parquet, CSV, Excel, JSON, NDJSON, IPC, SQLite)")
    run_parser.add_argument(
        "--compression", help="Compression (snappy, zstd, gzip, lz4, uncompressed, brotli)")
    run_parser.add_argument(
        "--table", help="Table name for SQLite export")
    run_parser.add_argument(
        "--if-exists", default="replace", choices=["fail", "replace", "append"], help="Behavior if table exists (SQLite)")
    run_parser.add_argument(
        "--step", "-t", action="append", help="Inline transformation step (JSON string)")
    run_parser.add_argument(
        "--save-recipe", action="store_true", help="Save the executed recipe to JSON")
    run_parser.add_argument(
        "--process-individual", action="store_true", 
        help="Process each file individually before concatenating (useful for folder inputs)")
    run_parser.add_argument(
        "--include-source-info", action="store_true",
        help="Add source metadata columns (__pyquery_source_name__, etc.)")
    run_parser.add_argument(
        "--export-individual", action="store_true",
        help="Export results as separate files (requires --process-individual)")
    run_parser.add_argument(
        "--dev", action="store_true", help="Enable Dev Mode (No Banner, Verbose Logs)")

    # 2. INTERACTIVE (TUI)
    interactive_parser = subparsers.add_parser(
        "interactive", help="Start the Interactive Terminal UI")
    interactive_parser.add_argument(
        "--dev", action="store_true", help="Enable Dev Mode (No Banner, Verbose Logs)")

    # 3. API (Server)
    api_parser = subparsers.add_parser("api", help="Start the FastAPI Server")
    api_parser.add_argument(
        "--port", type=int, default=8000, help="Port to run on")
    api_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload")
    api_parser.add_argument(
        "--dev", action="store_true", help="Enable Dev Mode (No Banner, Verbose Logs)")

    # 4. UI (Streamlit)
    ui_parser = subparsers.add_parser("ui", help="Start the Streamlit Web App")
    ui_parser.add_argument(
        "--port", type=int, default=8501, help="Port to run on")
    ui_parser.add_argument(
        "--dev", action="store_true", help="Enable Dev Mode (No Banner, Verbose Logs)")

    args = parser.parse_args()

    if args.command == "run":
        if args.dev:
             log_step("Dev Mode Enabled (Headless)", module="DEV-MODE", icon="🛠️")
        run_headless(args)

    elif args.command == "interactive":
        if args.dev:
            log_step("Dev Mode Enabled (Interactive)", module="DEV-MODE", icon="🛠️")
        run_interactive()

    elif args.command == "api":
        init_logging()
        log_step(f"Launching API on port {args.port}...", module="UVICORN", icon="🚀")

        target = "pyquery_polars.api.main:app"
        cmd = ["uvicorn", target, "--port", str(args.port)]
        if args.reload:
            cmd.append("--reload")
        
        if args.dev:
            cmd.append("--log-level=debug")
            log_step("Dev Mode Enabled: Verbose Logging Active", module="DEV-MODE", icon="🛠️")
            
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            log_step("API Server stopped.", module="Shutdown", icon="🛑")
            sys.exit(0)

    elif args.command == "ui":
        init_logging()
        log_step(f"Launching Streamlit on port {args.port}...", module="WEB-UI", icon="🌊")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(os.path.dirname(
            current_dir), "frontend", "app.py")

        if not os.path.exists(app_path):
            log_error("Frontend App Not Found", f"Path: {app_path}")
            sys.exit(1)

        cmd = ["streamlit", "run", app_path, "--server.port", str(args.port)]
        
        if args.dev:
            # Watch the entire package root using Streamlit's folderWatchList option
            package_root = os.path.dirname(current_dir)
            cmd.extend(["--server.folderWatchList", package_root])
            log_step(f"Watching Folders: {package_root}", module="DEV-MODE", icon="👀")
            log_step("Dev Mode Enabled: Verbose Logging Active", module="DEV-MODE", icon="🛠️")
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            log_step("Streamlit Server stopped.", module="Shutdown", icon="🛑")
            sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
