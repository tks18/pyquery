from pyquery_polars.cli.headless.pipeline import HeadlessPipeline


def run_headless(args, ui, theme_manager):
    """
    Entry point for headless execution.
    Instantiates the pipeline and runs logic.
    Requires UI and ThemeManager instances.
    """
    pipeline = HeadlessPipeline(ui, theme_manager)
    pipeline.run(args)
