"""
Engine: load stats, plan, and (later) reason with PandasAI.

Load stats.json into DataFrames; planner decides which fields to investigate
for the user's question. Reasoner (PandasAI) and insight generator next.
"""

from .loader import load_stats
from .models import LoadError, LoadedStats, Plan
from .planner import plan

__all__ = ["load_stats", "LoadedStats", "LoadError", "Plan", "plan"]
