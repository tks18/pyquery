"""
Base module for frontend components.

Contains:
- BaseComponent: Abstract base class for all UI components
- AppContext: Application context with shared resources
- StateManager: Session state management
"""

from pyquery_polars.frontend.base.component import BaseComponent
from pyquery_polars.frontend.base.context import AppContext
from pyquery_polars.frontend.base.state import StateManager

__all__ = ["BaseComponent", "AppContext", "StateManager"]
