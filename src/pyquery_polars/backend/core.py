"""
PyQueryEngine - The Central Orchestrator.

This is the main entry point for the PyQuery backend. It orchestrates all operations
by wiring together specialized manager classes using Dependency Injection.

Dependencies are exposed directly (e.g. engine.datasets.add()).
"""
from pyquery_polars.backend.datasets import DatasetManager
from pyquery_polars.backend.recipes import RecipeManager
from pyquery_polars.backend.io import IOManager
from pyquery_polars.backend.jobs import JobManager
from pyquery_polars.backend.projects import ProjectManager
from pyquery_polars.backend.analytics import AnalyticsManager
from pyquery_polars.backend.processing import ProcessingManager
from pyquery_polars.backend.transforms import TransformRegistry


class PyQueryEngine:
    """
    Central Orchestrator for PyQuery backend.

    Wiring:
    1. Base Managers (IO, Datasets, Recipes)
    2. ProcessingManager (depends on Datasets, Recipes)
    3. JobManager (depends on Processing, IO)
    4. ProjectManager (depends on Datasets, Recipes, IO)
    5. AnalyticsManager (depends on Processing)

    Usage:
    - engine.datasets.add(...)
    - engine.processing.execute_sql(...)
    """

    def __init__(self):
        self.io = IOManager()
        self.datasets = DatasetManager()
        self.recipes = RecipeManager()

        # Initialize Registry
        TransformRegistry.register_all()

        # 2. Dependent Managers

        # Processing depends on data, recipes & io for staging
        self.processing = ProcessingManager(
            io_manager=self.io,
            dataset_manager=self.datasets,
            recipe_manager=self.recipes
        )

        # Jobs depends on processing (for views) and io (for export)
        self.jobs = JobManager(
            processing_manager=self.processing,
            io_manager=self.io
        )

        # Projects depends on data/recipes (state) and io (loading)
        self.projects = ProjectManager(
            dataset_manager=self.datasets,
            recipe_manager=self.recipes,
            io_manager=self.io
        )

        # Analytics depends on processing (for data views)
        self.analytics = AnalyticsManager(
            processing_manager=self.processing
        )
