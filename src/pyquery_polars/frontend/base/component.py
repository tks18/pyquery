from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from pyquery_polars.frontend.base.context import AppContext
from pyquery_polars.frontend.base.state import StateManager


class BaseComponent(ABC):
    """
    Abstract base class for all frontend components.

    All components receive AppContext via constructor and must implement render().
    This enforces a consistent pattern across the frontend:
    - Dependency injection of engine/state via AppContext
    - Single Responsibility: each component has one render() method
    - Explicit dependencies: no reliance on st.session_state for engine

    Example:
        class MySidebar(BaseComponent):
            def render(self):
                st.sidebar.title("My App")
                # Use self.engine or self.state as needed
    """

    def __init__(self, ctx: AppContext) -> None:
        """
        Initialize component with application context.

        Args:
            ctx: AppContext containing engine, state_manager, and other shared resources
        """
        self.ctx = ctx

    @property
    def engine(self):
        """Shortcut to access PyQueryEngine."""
        return self.ctx.engine

    @property
    def state(self) -> 'StateManager':
        """Shortcut to access StateManager."""
        return self.ctx.state_manager

    @abstractmethod
    def render(self, *args, **kwargs) -> Any:
        """
        Render the component using Streamlit.

        Subclasses must implement this method to define their UI.
        The method signature can be extended by subclasses to accept
        additional parameters (e.g., dataset_name).

        Returns:
            Implementation-specific return value (often None for pure UI components)
        """
        pass
