"""
Application context containing shared resources for all components.
"""

from dataclasses import dataclass

from pyquery_polars.backend import PyQueryEngine
from pyquery_polars.frontend.base.state import StateManager


@dataclass
class AppContext:
    """
    Application context containing shared resources.

    This is the central dependency container passed to all components.
    It provides access to:
    - engine: PyQueryEngine instance for all backend operations
    - state_manager: StateManager for session state operations

    Usage:
        ctx = AppContext.create(engine)
        sidebar = SidebarComponent(ctx)
        sidebar.render()

    Benefits:
    - Explicit dependencies (no hidden st.session_state access)
    - Easy to test (can mock the context)
    - Single source of truth for shared resources
    """
    engine: PyQueryEngine
    state_manager: StateManager

    @classmethod
    def create(cls, engine: PyQueryEngine) -> "AppContext":
        """
        Factory method to create AppContext with initialized StateManager.

        This is the preferred way to create an AppContext. It ensures
        that the StateManager is properly initialized with the engine.

        Args:
            engine: PyQueryEngine instance

        Returns:
            Fully initialized AppContext
        """
        state_manager = StateManager(engine)
        return cls(engine=engine, state_manager=state_manager)
