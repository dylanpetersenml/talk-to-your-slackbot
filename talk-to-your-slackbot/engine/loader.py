"""
Load stats.json and build PandasAI-compatible DataFrames.

Aligns with pickleball_stats.yaml semantic model (game, players entities).
Handles missing/malformed files and empty or partial data with clear error messages.
"""

import json
import os
from pathlib import Path

import pandas as pd

from .models import LoadError, LoadedStats


def _safe_get(obj: dict, *keys: str, default=None):
    """Navigate nested dict; return default if any key is missing."""
    for key in keys:
        if obj is None or not isinstance(obj, dict):
            return default
        obj = obj.get(key)
    return obj


def _build_game_row(data: dict) -> dict | None:
    """Build one game-level row aligned with semantic model (game entity)."""
    session = data.get("session")
    game = data.get("game")
    if not session or not game:
        return None
    longest = game.get("longest_rally") or {}
    outcome = game.get("game_outcome") or [None, None]
    kitchen_pct = game.get("team_percentage_to_kitchen") or [None, None]
    return {
        "game_id": _safe_get(session, "vid") or "",
        "session_type": _safe_get(session, "session_type") or "",
        "num_players": _safe_get(session, "num_players"),
        "scoring": game.get("scoring"),
        "min_points": game.get("min_points"),
        "avg_shots": game.get("avg_shots"),
        "kitchen_rallies": game.get("kitchen_rallies"),
        "longest_rally_shots": longest.get("num_shots"),
        "longest_rally_index": longest.get("rally_idx"),
        "team0_outcome": outcome[0] if len(outcome) > 0 else None,
        "team1_outcome": outcome[1] if len(outcome) > 1 else None,
        "team0_kitchen_pct": kitchen_pct[0] if len(kitchen_pct) > 0 else None,
        "team1_kitchen_pct": kitchen_pct[1] if len(kitchen_pct) > 1 else None,
    }


def _build_players_table(data: dict, game_id: str) -> pd.DataFrame:
    """Build players DataFrame aligned with semantic model (players entity)."""
    players = data.get("players")
    if not isinstance(players, list):
        return pd.DataFrame()

    rows = []
    for i, p in enumerate(players):
        if not isinstance(p, dict):
            continue
        rows.append({
            "player_id": i,
            "game_id": game_id,
            "team": p.get("team"),
            "shot_count": p.get("shot_count"),
            "final_shot_count": p.get("final_shot_count"),
            "volley_count": p.get("volley_count"),
            "ground_stroke_count": p.get("ground_stroke_count"),
            "avg_shot_quality": p.get("average_shot_quality"),
            "net_impact_score": p.get("net_impact_score"),
            "net_fault_pct": p.get("net_fault_percentage"),
            "out_fault_pct": p.get("out_fault_percentage"),
        })
    return pd.DataFrame(rows)


def load_stats(path: str | Path | None = None) -> LoadedStats | LoadError:
    """
    Load stats.json and return raw dict plus PandasAI-compatible DataFrames.

    Path is resolved in order: argument -> STATS_PATH env -> default 'stats.json'
    in the current working directory. Handles missing file, invalid JSON, and
    empty/partial data with user-friendly error messages (no stack traces).

    Parameters
    ----------
    path : str or Path, optional
        Path to the stats JSON file. If None, uses STATS_PATH env or 'stats.json'.

    Returns
    -------
    LoadedStats | LoadError
        LoadedStats with raw dict, game_df, and players_df; or LoadError with
        a message safe to show in Slack.
    """
    if path is None:
        path = os.environ.get("STATS_PATH", "stats.json")
    path = Path(path)

    if not path.exists():
        return LoadError(message="Match statistics file is missing. Please try again later.")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return LoadError(message="Match statistics could not be read. The file may be invalid.")

    if not isinstance(data, dict):
        return LoadError(message="Match statistics format is invalid.")

    session = data.get("session")
    game = data.get("game")
    players = data.get("players")

    if not session or not game:
        return LoadError(message="Match statistics are incomplete (missing session or game data).")

    if not isinstance(players, list) or len(players) == 0:
        return LoadError(message="Match statistics contain no player data.")

    game_row = _build_game_row(data)
    if game_row is None:
        return LoadError(message="Match statistics are incomplete (could not build game summary).")

    game_id = game_row.get("game_id") or ""
    game_df = pd.DataFrame([game_row])
    players_df = _build_players_table(data, game_id)

    if players_df.empty:
        return LoadError(message="Match statistics contain no valid player records.")

    return LoadedStats(raw=data, game_df=game_df, players_df=players_df)
