"""
Reasoner: analyze key factors using PandasAI over loaded stats and the semantic layer.

Uses pickleball_stats.yaml for context (entities: game, players, shot_stats,
kitchen_arrival, ball_directions). Focuses on tables and hints from the Plan.
"""

import os
from pathlib import Path

import pandas as pd

from .models import LoadedStats, Plan, ReasonerResult

# Default path to semantic layer (repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SEMANTIC_YAML = _REPO_ROOT / "pickleball_stats.yaml"


def _load_semantic_context(yaml_path: Path | None = None) -> str:
    """Load short semantic context from pickleball_stats.yaml for the prompt."""
    path = yaml_path or _SEMANTIC_YAML
    if not path.exists():
        return (
            "Pickleball match stats: game-level (outcomes, kitchen %), "
            "per-player (shot counts, quality, faults), shot-type stats (serves, returns, "
            "drives, dinks, etc.), kitchen arrival by role, and ball direction counts."
        )
    try:
        import yaml  # optional: pyyaml for full semantic context
    except ImportError:
        return (
            "Pickleball match statistics: game (outcomes, kitchen %), players (shot counts, "
            "quality, faults), shot_stats (success/rally-win % by shot type), "
            "kitchen_arrival by role, ball_directions."
        )
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "semantic_model" not in data:
            return "Pickleball match statistics with game, players, shot stats, kitchen arrival, ball directions."
        sm = data["semantic_model"]
        desc = sm.get("description", "")
        if isinstance(desc, str) and desc.strip():
            return desc.strip()
        entities = sm.get("entities", {})
        names = list(entities.keys()) if isinstance(entities, dict) else []
        return (
            "Pickleball stats semantic model. Entities: " + ", ".join(names) + ". "
            "Use game for outcomes and kitchen %; players for shot counts and quality; "
            "shot_stats for success/rally-win % by shot type; kitchen_arrival for role rates; "
            "ball_directions for shot direction counts."
        )
    except Exception:
        return "Pickleball match statistics (game, players, shot types, kitchen arrival, directions)."


def _build_lake(loaded: LoadedStats, plan: Plan):
    """Build PandasAI SmartDatalake from loaded DataFrames, using plan focus order."""
    try:
        from pandasai import SmartDatalake, SmartDataframe
    except ImportError:
        return None, "pandasai is not installed. Install with: pip install pandasai"

    # Order tables: put plan focus_tables first, then the rest.
    table_order = [
        ("game_df", loaded.game_df),
        ("players_df", loaded.players_df),
        ("shot_stats_df", loaded.shot_stats_df),
        ("kitchen_arrival_df", loaded.kitchen_arrival_df),
        ("ball_directions_df", loaded.ball_directions_df),
    ]
    focus_set = set(plan.focus_tables)
    ordered = sorted(table_order, key=lambda x: (x[0] not in focus_set, x[0]))
    config = {}
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("PANDASAI_OPENAI_API_KEY")
    if api_key:
        try:
            from pandasai.llms import OpenAI
            config["llm"] = OpenAI(api_token=api_key)
        except Exception as e:
            config["llm"] = None
            config["_llm_error"] = str(e)
    else:
        config["llm"] = None

    if config.get("llm") is None:
        return None, (
            "LLM not configured. Set OPENAI_API_KEY (or PANDASAI_OPENAI_API_KEY) "
            "for PandasAI to analyze the data."
        )

    smart_dfs = []
    for _name, df in ordered:
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            continue
        smart_dfs.append(SmartDataframe(df, config={"llm": config["llm"]}))
    if not smart_dfs:
        return None, "No data available to analyze."
    lake = SmartDatalake(smart_dfs, config={"llm": config["llm"]})
    return lake, None


def reason(
    question: str,
    loaded: LoadedStats,
    plan: Plan,
    semantic_yaml_path: Path | None = None,
) -> ReasonerResult:
    """
    Run PandasAI analysis on the loaded stats to answer the question.

    Uses the semantic layer (pickleball_stats.yaml) for context and the plan's
    focus_tables to prioritize relevant data. Analyzes key factors such as
    return depth, kitchen arrival, and shot directions when present in the data.

    Parameters
    ----------
    question : str
        Validated user question (e.g. "How did I lose this game?").
    loaded : LoadedStats
        Loaded game_df, players_df, shot_stats_df, kitchen_arrival_df, ball_directions_df.
    plan : Plan
        Planner output (intent, focus_tables, focus_hints).
    semantic_yaml_path : Path, optional
        Path to pickleball_stats.yaml. Defaults to repo-root pickleball_stats.yaml.

    Returns
    -------
    ReasonerResult
        response with analysis text, or error with a user-friendly message.
    """
    context = _load_semantic_context(semantic_yaml_path)
    lake, err = _build_lake(loaded, plan)
    if err:
        return ReasonerResult(error=err)

    prompt = (
        f"Context: {context}\n\n"
        f"Focus on these tables for this question: {', '.join(plan.focus_tables)}. "
        f"Answer in 2-4 short sentences suitable for a coaching summary.\n\n"
        f"Question: {question}"
    )
    try:
        response = lake.chat(prompt)
        if response is None:
            return ReasonerResult(error="Analysis produced no response.")
        text = str(response).strip()
        return ReasonerResult(response=text if text else None)
    except Exception as e:
        msg = str(e).strip()
        if not msg:
            msg = "Analysis failed."
        return ReasonerResult(error=f"Analysis failed: {msg}")
