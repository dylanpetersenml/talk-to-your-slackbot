"""
Engine: load stats and (later) plan + reason with PandasAI.

Start with loading stats.json into PandasAI-compatible DataFrames aligned
with pickleball_stats.yaml. Planner and reasoner will be added next.
"""

from .loader import load_stats
from .models import LoadError, LoadedStats

__all__ = ["load_stats", "LoadedStats", "LoadError"]
