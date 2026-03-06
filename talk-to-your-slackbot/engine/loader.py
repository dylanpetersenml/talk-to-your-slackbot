"""
Load stats.json and build PandasAI-compatible DataFrames.

Aligns with pickleball_stats.yaml (game, players, shot_stats,
kitchen_arrival, ball_directions). Exposes the full structured data,
not just a single summary row.
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
    """Build one game-level row; includes relative_adjustments when present."""
    session = data.get("session")
    game = data.get("game")
    if not session or not game:
        return None
    longest = game.get("longest_rally") or {}
    outcome = game.get("game_outcome") or [None, None]
    kitchen_pct = game.get("team_percentage_to_kitchen") or [None, None]
    adj = game.get("relative_adjustments") or {}
    row = {
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
        "relative_adj_between_teams": adj.get("between_teams"),
        "relative_adj_within_team0": (adj.get("within_teams") or [None, None])[0] if len(adj.get("within_teams") or []) > 0 else None,
        "relative_adj_within_team1": (adj.get("within_teams") or [None, None])[1] if len(adj.get("within_teams") or []) > 1 else None,
    }
    return row


def _build_players_table(data: dict, game_id: str) -> pd.DataFrame:
    """Build players DataFrame with all scalar fields from each player."""
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
            "total_distance_covered": p.get("total_distance_covered"),
            "average_x_coverage_percentage": p.get("average_x_coverage_percentage"),
            "team_short_length_rallies_won": p.get("team_short_length_rallies_won"),
            "team_medium_length_rallies_won": p.get("team_medium_length_rallies_won"),
            "team_long_length_rallies_won": p.get("team_long_length_rallies_won"),
            "team_shot_percentage": p.get("team_shot_percentage"),
            "team_left_side_percentage": p.get("team_left_side_percentage"),
            "team_thirds_percentage": p.get("team_thirds_percentage"),
            "team_fourths_percentage": p.get("team_fourths_percentage"),
            "team_fifths_percentage": p.get("team_fifths_percentage"),
        })
    return pd.DataFrame(rows)


# Keys under each player that are shot-type objects (have count and/or outcome_stats).
_SHOT_TYPE_KEYS = frozenset({
    "serves", "returns", "thirds", "fourths", "fifths", "drives", "drops", "dinks",
    "lobs", "smashes", "third_drives", "third_drops", "third_lobs", "resets",
    "speedups", "passing", "poaches", "forehands", "backhands",
    "left_side_player", "right_side_player", "kitchen_area", "mid_court_area",
    "near_baseline_area", "near_midline_area", "near_left_sideline_area", "near_right_sideline_area",
})


def _build_shot_stats_table(data: dict, game_id: str) -> pd.DataFrame:
    """One row per (player_id, shot_type) with count, quality, outcome rates, speed."""
    players = data.get("players")
    if not isinstance(players, list):
        return pd.DataFrame()

    rows = []
    for player_id, p in enumerate(players):
        if not isinstance(p, dict):
            continue
        for shot_type in _SHOT_TYPE_KEYS:
            block = p.get(shot_type)
            if not isinstance(block, dict):
                continue
            count = block.get("count", 0)
            outcome = block.get("outcome_stats") or {}
            speed = block.get("speed_stats") or {}
            rows.append({
                "game_id": game_id,
                "player_id": player_id,
                "shot_type": shot_type,
                "count": count,
                "avg_quality": block.get("average_quality"),
                "avg_speed": speed.get("average"),
                "fastest_speed": speed.get("fastest"),
                "success_pct": outcome.get("success_percentage"),
                "rally_win_pct": outcome.get("rally_won_percentage"),
                "out_fault_pct": outcome.get("out_fault_percentage"),
                "net_fault_pct": outcome.get("net_fault_percentage"),
            })
    return pd.DataFrame(rows)


def _build_kitchen_arrival_table(data: dict, game_id: str) -> pd.DataFrame:
    """One row per (player_id, role) from kitchen_arrival_percentage."""
    players = data.get("players")
    if not isinstance(players, list):
        return pd.DataFrame()

    rows = []
    for player_id, p in enumerate(players):
        if not isinstance(p, dict):
            continue
        kap = p.get("kitchen_arrival_percentage") or {}
        for role_top in ("serving", "returning"):
            for role_sub, sub in (("oneself", "oneself"), ("partner", "partner")):
                block = (kap.get(role_top) or {}).get(role_sub)
                if not isinstance(block, dict):
                    continue
                role_name = f"{role_top}_{sub}"
                num = block.get("numerator")
                den = block.get("denominator")
                if num is not None or den is not None:
                    rows.append({
                        "game_id": game_id,
                        "player_id": player_id,
                        "role": role_name,
                        "numerator": num,
                        "denominator": den,
                    })
    return pd.DataFrame(rows)


def _build_ball_directions_table(data: dict, game_id: str) -> pd.DataFrame:
    """One row per (player_id, direction) from ball_directions."""
    players = data.get("players")
    if not isinstance(players, list):
        return pd.DataFrame()

    rows = []
    for player_id, p in enumerate(players):
        if not isinstance(p, dict):
            continue
        bd = p.get("ball_directions") or {}
        for key, val in bd.items():
            if not isinstance(val, (int, float)):
                continue
            direction = key.replace("_count", "") if key.endswith("_count") else key
            rows.append({
                "game_id": game_id,
                "player_id": player_id,
                "direction": direction,
                "count": int(val),
            })
    return pd.DataFrame(rows)


def load_stats(path: str | Path | None = None) -> LoadedStats | LoadError:
    """
    Load stats.json and return raw dict plus PandasAI-compatible DataFrames.

    Path is resolved in order: argument -> STATS_PATH env -> default 'stats.json'.
    Builds game_df (1 row), players_df (N rows, many columns), shot_stats_df,
    kitchen_arrival_df, and ball_directions_df so the full dataset is queryable.

    Parameters
    ----------
    path : str or Path, optional
        Path to the stats JSON file. If None, uses STATS_PATH env or 'stats.json'.

    Returns
    -------
    LoadedStats | LoadError
        LoadedStats with raw and five DataFrames; or LoadError with a safe message.
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

    shot_stats_df = _build_shot_stats_table(data, game_id)
    kitchen_arrival_df = _build_kitchen_arrival_table(data, game_id)
    ball_directions_df = _build_ball_directions_table(data, game_id)

    return LoadedStats(
        raw=data,
        game_df=game_df,
        players_df=players_df,
        shot_stats_df=shot_stats_df,
        kitchen_arrival_df=kitchen_arrival_df,
        ball_directions_df=ball_directions_df,
    )