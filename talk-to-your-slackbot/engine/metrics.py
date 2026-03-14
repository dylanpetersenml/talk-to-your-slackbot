"""
Metrics layer on top of the loader: compute 3–5 key metrics from loaded stats.

Used for monitoring, data-quality checks, and quick sanity checks on loaded data.
Includes median return speed, median baseline distance, and height above net.
"""

from __future__ import annotations

import pandas as pd

from .models import LoadMetrics


def _median_or_avg(series: pd.Series | None, fallback: pd.Series | None = None) -> float | None:
    """Median of series; if all NaN or missing, use fallback series; return None if still empty."""
    use = series.dropna() if series is not None and isinstance(series, pd.Series) else pd.Series(dtype=float)
    if use.empty and fallback is not None:
        use = fallback.dropna()
    if use.empty:
        return None
    return float(use.median())


def compute_metrics(
    game_df: pd.DataFrame,
    players_df: pd.DataFrame,
    shot_stats_df: pd.DataFrame,
) -> LoadMetrics:
    """
    Compute a small set of key metrics from loader DataFrames.

    Parameters
    ----------
    game_df : pd.DataFrame
        One-row game summary (avg_shots, kitchen_rallies, etc.).
    players_df : pd.DataFrame
        One row per player (shot_count, etc.).
    shot_stats_df : pd.DataFrame
        One row per (player_id, shot_type), with median/avg speed, baseline, height.

    Returns
    -------
    LoadMetrics
        median_return_speed, median_baseline_distance, median_height_above_net,
        total_shots, kitchen_rallies.
    """
    total_shots = int(players_df["shot_count"].sum()) if "shot_count" in players_df else 0
    kitchen_rallies = None
    if len(game_df) > 0 and "kitchen_rallies" in game_df.columns:
        val = game_df["kitchen_rallies"].iloc[0]
        kitchen_rallies = None if pd.isna(val) else int(val)

    returns_df = pd.DataFrame()
    if "shot_type" in shot_stats_df.columns:
        returns_df = shot_stats_df[shot_stats_df["shot_type"] == "returns"]

    median_return_speed = None
    median_baseline_distance = None
    median_height_above_net = None
    if not returns_df.empty:
        median_return_speed = _median_or_avg(
            returns_df["median_speed"] if "median_speed" in returns_df.columns else None,
            returns_df["avg_speed"] if "avg_speed" in returns_df.columns else None,
        )
        median_baseline_distance = _median_or_avg(
            returns_df["median_baseline_distance"] if "median_baseline_distance" in returns_df.columns else None,
            returns_df["avg_baseline_distance"] if "avg_baseline_distance" in returns_df.columns else None,
        )
        median_height_above_net = _median_or_avg(
            returns_df["median_height_above_net"] if "median_height_above_net" in returns_df.columns else None,
            returns_df["avg_height_above_net"] if "avg_height_above_net" in returns_df.columns else None,
        )

    return LoadMetrics(
        median_return_speed=median_return_speed,
        median_baseline_distance=median_baseline_distance,
        median_height_above_net=median_height_above_net,
        total_shots=total_shots,
        kitchen_rallies=kitchen_rallies,
    )
