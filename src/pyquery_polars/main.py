import sys

from pyquery_polars.cli import (
    ThemeManager, ConsoleUI, BannerRenderer, setup_parser, launch_headless, launch_ui, launch_api
)


def main():
    """
    Main entry point for the PyQuery CLI.
    Orchestrates the command delegation to the CLI module.
    """
    # Instantiate Core Services
    theme_manager = ThemeManager()
    ui = ConsoleUI(theme_manager)
    banner_renderer = BannerRenderer(ui, theme_manager)

    # Initialize Parser
    parser = setup_parser()

    # Default to UI if no args
    if len(sys.argv) == 1:
        sys.argv.append("ui")
    elif len(sys.argv) == 2 and sys.argv[1] == "--dev":
        sys.argv.insert(1, "ui")

    # Check for --dev flag early to skip banner
    dev_mode = "--dev" in sys.argv

    # Show Banner
    if not dev_mode:
        try:
            banner_renderer.render()
        except Exception:
            pass

    # Parse Arguments
    args = parser.parse_args()

    # Dispatch Commands
    if args.command == "run":
        launch_headless(args, ui, theme_manager)
    elif args.command == "ui":
        launch_ui(args, ui)
    elif args.command == "api":
        launch_api(args, ui)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
