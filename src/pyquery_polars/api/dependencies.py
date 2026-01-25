from pyquery_polars.backend import PyQueryEngine

# Global singleton instance
# In a real production app, this might be per-request or use a lifespan context
_engine_instance = None


def get_engine() -> PyQueryEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PyQueryEngine()
    return _engine_instance
