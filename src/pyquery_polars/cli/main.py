import argparse
import sys
import subprocess
import os

from pyquery_polars.cli.headless import run_headless
from pyquery_polars.cli.interactive import run_interactive


def main():
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

    # 2. INTERACTIVE (TUI)
    subparsers.add_parser(
        "interactive", help="Start the Interactive Terminal UI")

    # 3. API (Server)
    api_parser = subparsers.add_parser("api", help="Start the FastAPI Server")
    api_parser.add_argument(
        "--port", type=int, default=8000, help="Port to run on")
    api_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload")

    # 4. UI (Streamlit)
    ui_parser = subparsers.add_parser("ui", help="Start the Streamlit Web App")
    ui_parser.add_argument(
        "--port", type=int, default=8501, help="Port to run on")

    # Default to UI if no args
    if len(sys.argv) == 1:
        sys.argv.append("ui")

    args = parser.parse_args()

    if args.command == "run":
        run_headless(args)

    elif args.command == "interactive":
        run_interactive()

    elif args.command == "api":
        print(f"🚀 Launching API on port {args.port}...")

        target = "pyquery_polars.api.main:app"
        cmd = ["uvicorn", target, "--port", str(args.port)]
        if args.reload:
            cmd.append("--reload")
        subprocess.run(cmd)

    elif args.command == "ui":
        print(f"🌊 Launching Streamlit on port {args.port}...")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(os.path.dirname(
            current_dir), "frontend", "app.py")

        if not os.path.exists(app_path):
            print(f"❌ Error: Could not find frontend app at {app_path}")
            sys.exit(1)

        cmd = ["streamlit", "run", app_path, "--server.port", str(args.port)]
        subprocess.run(cmd)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
