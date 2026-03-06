"""Tests for the Engine planner component."""

import pandas as pd
import pytest

from engine import LoadedStats, Plan, load_stats, plan


def _minimal_loaded_stats() -> LoadedStats:
    """Minimal LoadedStats with one game, one player, for planner tests."""
    game_df = pd.DataFrame([{"game_id": "v1", "team0_outcome": 7, "team1_outcome": 15}])
    players_df = pd.DataFrame([{"player_id": 0, "game_id": "v1", "team": 0, "shot_count": 10}])
    shot_df = pd.DataFrame([{"game_id": "v1", "player_id": 0, "shot_type": "serves", "count": 2}])
    kitchen_df = pd.DataFrame([{"game_id": "v1", "player_id": 0, "role": "serving_oneself", "numerator": 2, "denominator": 2}])
    ball_df = pd.DataFrame([{"game_id": "v1", "player_id": 0, "direction": "down_the_middle", "count": 3}])
    return LoadedStats(
        raw={},
        game_df=game_df,
        players_df=players_df,
        shot_stats_df=shot_df,
        kitchen_arrival_df=kitchen_df,
        ball_directions_df=ball_df,
    )


def test_plan_returns_plan():
    loaded = _minimal_loaded_stats()
    result = plan("Why did I lose this game?", loaded)
    assert isinstance(result, Plan)
    assert result.intent
    assert isinstance(result.focus_tables, list)
    assert isinstance(result.focus_hints, dict)


def test_plan_why_lost_intent():
    loaded = _minimal_loaded_stats()
    result = plan("How did I lose this game?", loaded)
    assert result.intent == "why_lost"
    assert "game_df" in result.focus_tables
    assert "players_df" in result.focus_tables
    assert "shot_stats_df" in result.focus_tables
    assert "game_df" in result.focus_hints
    assert "team0_outcome" in result.focus_hints["game_df"]


def test_plan_why_won_intent():
    loaded = _minimal_loaded_stats()
    result = plan("Why did we win this game?", loaded)
    assert result.intent == "why_won"
    assert "game_df" in result.focus_tables
    assert "players_df" in result.focus_tables
    assert "shot_stats_df" in result.focus_tables
    assert "team0_outcome" in result.focus_hints["game_df"]


def test_plan_where_points_lost_intent():
    loaded = _minimal_loaded_stats()
    result = plan("Where did we give up the most points?", loaded)
    assert result.intent == "where_points_lost"
    assert "shot_stats_df" in result.focus_tables or "players_df" in result.focus_tables


def test_plan_compare_serving_returning_intent():
    loaded = _minimal_loaded_stats()
    result = plan("Compare my serving vs returning", loaded)
    assert result.intent == "compare_serving_returning"
    assert "shot_stats_df" in result.focus_tables
    assert "kitchen_arrival_df" in result.focus_tables


def test_plan_kitchen_intent():
    loaded = _minimal_loaded_stats()
    result = plan("How was our kitchen arrival?", loaded)
    assert result.intent == "kitchen_analysis"
    assert "kitchen_arrival_df" in result.focus_tables


def test_plan_shot_patterns_intent():
    loaded = _minimal_loaded_stats()
    result = plan("What were our shot patterns?", loaded)
    assert result.intent == "shot_patterns"
    assert "ball_directions_df" in result.focus_tables or "shot_stats_df" in result.focus_tables


def test_plan_errors_intent():
    loaded = _minimal_loaded_stats()
    result = plan("Where did we make the most errors?", loaded)
    assert result.intent == "errors_faults"
    assert "players_df" in result.focus_tables


def test_plan_general_intent():
    loaded = _minimal_loaded_stats()
    result = plan("Tell me about the match", loaded)
    assert result.intent == "general"
    assert len(result.focus_tables) >= 1
