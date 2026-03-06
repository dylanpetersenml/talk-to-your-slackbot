"""Tests for the Engine reasoner (PandasAI) component."""

from pathlib import Path

import pandas as pd
import pytest

from engine import LoadedStats, Plan, ReasonerResult, load_stats, plan, reason


def _minimal_loaded_stats() -> LoadedStats:
    """Minimal LoadedStats for reasoner tests."""
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


def test_reason_returns_result():
    """reason() returns ReasonerResult; without API key or pandasai, error is set."""
    loaded = _minimal_loaded_stats()
    investigation_plan = plan("Why did I lose?", loaded)
    result = reason("Why did I lose?", loaded, investigation_plan)
    assert isinstance(result, ReasonerResult)
    # Either error (no API key, pandasai not installed, or analysis failed) or response
    assert result.error is not None or result.response is not None
    if result.error:
        assert len(result.error) > 0


def test_reason_semantic_context_loads():
    """Semantic context can be loaded from YAML or fallback."""
    from engine.reasoner import _load_semantic_context
    ctx = _load_semantic_context()
    assert "pickleball" in ctx.lower() or "game" in ctx.lower()
    assert len(ctx) > 50


def test_reason_semantic_context_nonexistent_path():
    """Semantic context returns fallback for nonexistent path."""
    from engine.reasoner import _load_semantic_context
    ctx = _load_semantic_context(Path("/nonexistent/pickleball_stats.yaml"))
    assert "pickleball" in ctx.lower() or "game" in ctx.lower()
