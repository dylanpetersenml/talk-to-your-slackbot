"""Data models for the Engine (stats load result, PandasAI-compatible context)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class LoadedStats:
    """
    Successfully loaded stats: raw JSON and PandasAI-compatible DataFrames.

    DataFrames are aligned with pickleball_stats.yaml entities (game, players)
    so they can be passed to PandasAI with the semantic layer.

    Attributes
    ----------
    raw : dict
        The full stats.json as a dict (for flexible access).
    game_df : pd.DataFrame
        One row per game: game_id, session_type, scoring, avg_shots, etc.
    players_df : pd.DataFrame
        One row per player: player_id, game_id, team, shot_count, etc.
    """

    raw: dict
    game_df: pd.DataFrame
    players_df: pd.DataFrame


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
