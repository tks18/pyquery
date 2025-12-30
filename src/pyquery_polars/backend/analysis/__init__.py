from .stats import StatsEngine
from .ml import MLEngine

class AnalysisEngine:
    """Facade for all analysis modules."""
    def __init__(self):
        self.stats = StatsEngine()
        self.ml = MLEngine()
