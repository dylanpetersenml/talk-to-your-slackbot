"""
Engine: load stats, plan, and reason with PandasAI.

Load stats.json into DataFrames; planner decides which fields to investigate;
reasoner analyzes key factors using PandasAI and the semantic layer (pickleball_stats.yaml).
"""

from .loader import load_stats
from .models import LoadError, LoadedStats, Plan, ReasonerResult
from .planner import plan
from .reasoner import reason

__all__ = [
    "load_stats",
    "LoadedStats",
    "LoadError",
    "Plan",
    "plan",
    "ReasonerResult",
    "reason",
]
