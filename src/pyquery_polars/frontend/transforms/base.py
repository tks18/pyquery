"""
Base class for all step renderers.

Step renderers are responsible for rendering the UI for configuring
transformation steps in the recipe editor.
"""

from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic

import polars as pl

from pyquery_polars.frontend.base import AppContext

# Generic type variable for params
P = TypeVar('P')


class BaseStepRenderer(ABC, Generic[P]):
    """
    Abstract base class for step renderers.

    Each step type (e.g., fill_nulls, filter_rows) should have its own class
    that inherits from this. The render() method receives step_id, current params,
    and schema, and returns updated params.

    This enforces a consistent pattern:
    - All step renderers receive AppContext via constructor
    - All step renderers implement render() with the same signature
    - Params type is generic for type safety

    Example:
        class FillNullsStep(BaseStepRenderer[FillNullsParams]):
            def render(self, step_id, params, schema):
                # Render UI using st.* calls
                params.strategy = st.selectbox(...)
                return params
    """

    def __init__(self, ctx: AppContext) -> None:
        """
        Initialize step renderer with app context.

        Args:
            ctx: AppContext for engine/state access
        """
        self.ctx = ctx

    @property
    def engine(self):
        """Shortcut to access PyQueryEngine."""
        return self.ctx.engine

    @property
    def state(self):
        """Shortcut to access StateManager."""
        return self.ctx.state_manager

    @abstractmethod
    def render(self, step_id: str, params: P,
               schema: Optional[pl.Schema]) -> P:
        """
        Render the step configuration UI.

        This method should use Streamlit widgets to allow the user to
        configure the step parameters. The params object should be
        modified in place and returned.

        Args:
            step_id: Unique identifier for this step instance (used for widget keys)
            params: Current parameter values (will be modified)
            schema: Current DataFrame schema for column selection dropdowns

        Returns:
            Updated params with user's selections
        """
        pass
