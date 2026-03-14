"""
Engine: load stats, plan, and reason with PandasAI.

Load stats.json into DataFrames; planner decides which fields to investigate;
reasoner analyzes key factors using PandasAI and the semantic layer (pickleball_stats.yaml).
"""

from .loader import load_stats
from .models import LoadError, LoadedStats, Plan, ReasonerResult
from .planner import plan
from .qa_log import log_qa
from .reasoner import reason

__all__ = [
    "load_stats",
    "LoadedStats",
    "LoadError",
    "log_qa",
    "Plan",
    "plan",
    "ReasonerResult",
    "reason",
]
