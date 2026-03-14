"""Tests for the Engine stats loader (PandasAI-compatible)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from engine import LoadError, LoadMetrics, LoadedStats, load_stats


def test_load_stats_missing_file():
    result = load_stats("/nonexistent/stats.json")
    assert isinstance(result, LoadError)
    assert "missing" in result.message.lower() or "try again" in result.message.lower()


def test_load_stats_invalid_json(tmp_path):
    bad = tmp_path / "stats.json"
    bad.write_text("not json {")
    result = load_stats(bad)
    assert isinstance(result, LoadError)
    assert "invalid" in result.message.lower() or "could not be read" in result.message.lower()


def test_load_stats_empty_object(tmp_path):
    (tmp_path / "stats.json").write_text("{}")
    result = load_stats(tmp_path / "stats.json")
    assert isinstance(result, LoadError)
    assert "incomplete" in result.message.lower() or "missing" in result.message.lower()


def test_load_stats_no_players(tmp_path):
    data = {
        "session": {"vid": "abc", "session_type": "game", "num_players": 4},
        "game": {"avg_shots": 4.0, "scoring": "side_out", "min_points": 15},
        "players": [],
    }
    (tmp_path / "stats.json").write_text(json.dumps(data))
    result = load_stats(tmp_path / "stats.json")
    assert isinstance(result, LoadError)
    assert "player" in result.message.lower()


def test_load_stats_success_returns_dataframes():
    # Use repo-level stats.json if present
    repo_root = Path(__file__).resolve().parent.parent
    path = repo_root / "stats.json"
    if not path.exists():
        pytest.skip("stats.json not found at repo root")
    result = load_stats(path)
    assert isinstance(result, LoadedStats)
    assert isinstance(result.raw, dict)
    assert "session" in result.raw and "game" in result.raw and "players" in result.raw
    assert isinstance(result.game_df, pd.DataFrame)
    assert isinstance(result.players_df, pd.DataFrame)
    assert isinstance(result.shot_stats_df, pd.DataFrame)
    assert isinstance(result.kitchen_arrival_df, pd.DataFrame)
    assert isinstance(result.ball_directions_df, pd.DataFrame)
    assert len(result.game_df) == 1
    assert len(result.players_df) >= 1
    # Many columns in game and players, not just a single summary
    assert len(result.game_df.columns) >= 14
    assert len(result.players_df.columns) >= 18
    assert "game_id" in result.game_df.columns
    assert "avg_shots" in result.game_df.columns
    assert "player_id" in result.players_df.columns
    assert "shot_count" in result.players_df.columns
    assert "team_thirds_percentage" in result.players_df.columns
    # Shot stats and related tables have many rows
    assert len(result.shot_stats_df) >= 1
    assert "shot_type" in result.shot_stats_df.columns
    assert len(result.ball_directions_df) >= 1
    assert "direction" in result.ball_directions_df.columns
    assert len(result.kitchen_arrival_df) >= 1
    assert "role" in result.kitchen_arrival_df.columns
    assert isinstance(result.metrics, LoadMetrics)
    assert result.metrics.total_shots >= 0
    assert result.metrics.kitchen_rallies is None or result.metrics.kitchen_rallies >= 0
    # Return-focused metrics (from returns shot type)
    assert result.metrics.median_return_speed is None or result.metrics.median_return_speed >= 0
    assert result.metrics.median_baseline_distance is None or result.metrics.median_baseline_distance >= 0
    assert result.metrics.median_height_above_net is None or result.metrics.median_height_above_net >= 0


def test_load_stats_minimal_valid(tmp_path):
    data = {
        "session": {"vid": "test1", "session_type": "game", "num_players": 4},
        "game": {
            "avg_shots": 4.0,
            "scoring": "side_out",
            "min_points": 15,
            "game_outcome": [7, 15],
            "kitchen_rallies": 5,
            "team_percentage_to_kitchen": [0.5, 0.5],
            "longest_rally": {"rally_idx": 0, "num_shots": 8},
        },
        "players": [
            {
                "team": 0,
                "shot_count": 10,
                "final_shot_count": 2,
                "volley_count": 4,
                "ground_stroke_count": 6,
                "average_shot_quality": 0.7,
                "net_impact_score": 0.5,
                "net_fault_percentage": 0,
                "out_fault_percentage": 0,
                "ball_directions": {"down_the_middle_count": 3},
                "kitchen_arrival_percentage": {
                    "serving": {"oneself": {"numerator": 2, "denominator": 2}},
                    "returning": {"oneself": {"numerator": 1, "denominator": 1}},
                },
                "serves": {"count": 2, "average_quality": 0.8, "outcome_stats": {"success_percentage": 100}, "speed_stats": {"average": 40}},
            },
        ],
    }
    (tmp_path / "stats.json").write_text(json.dumps(data))
    result = load_stats(tmp_path / "stats.json")
    assert isinstance(result, LoadedStats)
    assert result.game_df["game_id"].iloc[0] == "test1"
    assert result.players_df["player_id"].iloc[0] == 0
    assert result.players_df["shot_count"].iloc[0] == 10
    assert len(result.shot_stats_df) >= 1
    assert len(result.kitchen_arrival_df) >= 1
    assert len(result.ball_directions_df) >= 1
    m = result.metrics
    assert m.total_shots == 10
    assert m.kitchen_rallies == 5
    # Minimal fixture has no "returns" block, so return medians are None
    assert m.median_return_speed is None
    assert m.median_baseline_distance is None
    assert m.median_height_above_net is None
