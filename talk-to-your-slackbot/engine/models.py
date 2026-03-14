"""Data models for the Engine (stats load result, PandasAI-compatible context)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class LoadMetrics:
    """
    Key metrics computed from loaded stats (for monitoring and data-quality checks).

    Attributes
    ----------
    median_return_speed : float or None
        Median return-shot speed (mph) across players.
    median_baseline_distance : float or None
        Median baseline distance (ft) for returns across players.
    median_height_above_net : float or None
        Median height above net (ft) for returns across players.
    total_shots : int
        Sum of shot_count across all players (game activity level).
    kitchen_rallies : int or None
        Number of kitchen rallies in the game.
    """

    median_return_speed: float | None
    median_baseline_distance: float | None
    median_height_above_net: float | None
    total_shots: int
    kitchen_rallies: int | None


@dataclass
class LoadedStats:
    """
    Successfully loaded stats: raw JSON and PandasAI-compatible DataFrames.

    DataFrames are aligned with pickleball_stats.yaml (game, players,
    shot_stats, kitchen_arrival, ball_directions).

    Attributes
    ----------
    raw : dict
        The full stats.json as a dict (for flexible access).
    game_df : pd.DataFrame
        One row per game: game_id, session_type, scoring, avg_shots, etc.
    players_df : pd.DataFrame
        One row per player: full scalar fields (shot_count, team_*%, etc.).
    shot_stats_df : pd.DataFrame
        One row per (player, shot_type): count, avg_quality, success_pct, etc.
    kitchen_arrival_df : pd.DataFrame
        One row per (player, role): numerator, denominator.
    ball_directions_df : pd.DataFrame
        One row per (player, direction): count.
    metrics : LoadMetrics
        Small set of key metrics computed from the loaded data.
    """

    raw: dict
    game_df: pd.DataFrame
    players_df: pd.DataFrame
    shot_stats_df: pd.DataFrame
    kitchen_arrival_df: pd.DataFrame
    ball_directions_df: pd.DataFrame
    metrics: LoadMetrics


@dataclass
class LoadError:
    """
    Stats could not be loaded (missing file, invalid JSON, or empty/partial data).

    Attributes
    ----------
    message : str
        User-friendly error message (safe to show in Slack).
    """

    message: str


@dataclass
class Plan:
    """
    Output of the planner: which tables and measures to use to answer the question.

    The reasoner (e.g. PandasAI) uses this to focus analysis. Memory can be
    incorporated later for multi-match patterns.

    Attributes
    ----------
    intent : str
        Short tag: e.g. "why_lost", "compare_serving_returning", "where_points_lost".
    focus_tables : list of str
        Table names to prioritize: "game_df", "players_df", "shot_stats_df",
        "kitchen_arrival_df", "ball_directions_df".
    focus_hints : dict
        Optional table -> list of column names or values (e.g. shot_type) to emphasize.
    """

    intent: str
    focus_tables: list[str]
    focus_hints: dict[str, list[str]]


@dataclass
class ReasonerResult:
    """
    Output of the reasoner (PandasAI analysis).

    Attributes
    ----------
    response : str or None
        Natural-language analysis answer when successful.
    error : str or None
        User-friendly error message when analysis failed (e.g. LLM not configured).
    """

    response: str | None = None
    error: str | None = None
