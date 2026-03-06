"""
Reasoner: analyze match stats by sending data + context to the OpenAI API (Custom GPT style).

Builds a data payload from loaded stats and the plan, plus semantic context from
pickleball_stats.yaml, and calls the Chat Completions API so the model has full
data and context to produce a coaching summary.
"""

import os
from pathlib import Path

import pandas as pd

from .models import LoadedStats, Plan, ReasonerResult

# Default path to semantic layer (repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SEMANTIC_YAML = _REPO_ROOT / "pickleball_stats.yaml"

# Max rows per table in the payload to avoid token overflow.
_MAX_DATA_ROWS = 50


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
        import yaml
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


def _df_to_text(df: pd.DataFrame, name: str, max_rows: int = _MAX_DATA_ROWS) -> str:
    """Serialize a DataFrame to readable text for the prompt."""
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        return f"{name}: (no data)"
    head = df.head(max_rows)
    try:
        return f"{name}:\n{head.to_markdown(index=False)}"
    except (AttributeError, Exception):
        return f"{name}:\n{head.to_string()}"


def _build_data_payload(loaded: LoadedStats, plan: Plan) -> str:
    """Build a single text payload of all relevant tables for the Custom GPT input."""
    parts = []
    # Order by plan focus so the model sees priority tables first.
    focus_set = set(plan.focus_tables)
    table_order = [
        ("game_df", loaded.game_df),
        ("players_df", loaded.players_df),
        ("shot_stats_df", loaded.shot_stats_df),
        ("kitchen_arrival_df", loaded.kitchen_arrival_df),
        ("ball_directions_df", loaded.ball_directions_df),
    ]
    ordered = sorted(table_order, key=lambda x: (x[0] not in focus_set, x[0]))
    for name, df in ordered:
        if df is not None and not (isinstance(df, pd.DataFrame) and df.empty):
            parts.append(_df_to_text(df, name))
    return "\n\n---\n\n".join(parts) if parts else "(no match data)"


def _call_openai(system_content: str, user_content: str) -> str | None:
    """Call OpenAI Chat Completions; return assistant content or None on failure."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            max_tokens=500,
        )
        if resp.choices and len(resp.choices) > 0:
            msg = resp.choices[0].message
            if msg and msg.content:
                return msg.content.strip()
    except Exception:
        pass
    return None


def reason(
    question: str,
    loaded: LoadedStats,
    plan: Plan,
    semantic_yaml_path: Path | None = None,
) -> ReasonerResult:
    """
    Run analysis by sending match data and context to the OpenAI API (Custom GPT style).

    Builds a data payload from loaded DataFrames and semantic context from
    pickleball_stats.yaml, then calls the Chat Completions API so the model
    has full data and context to answer the question.

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
    data_payload = _build_data_payload(loaded, plan)

    # Optional: use custom GPT instructions as system prompt (paste from ChatGPT custom GPT).
    custom_system = os.environ.get("CUSTOM_GPT_SYSTEM_PROMPT", "").strip()
    if custom_system:
        system_content = custom_system + "\n\nUse the following semantic context about the data:\n" + context
    else:
        system_content = (
            "You are a pickleball coaching analyst. You receive match statistics and a question. "
            "Answer in 2–4 short sentences suitable for a coaching summary. Focus on shot quality, "
            "errors, kitchen arrival, and shot patterns when relevant.\n\n"
            "Semantic context for the data:\n" + context
        )

    user_content = (
        "Match data (tables):\n\n"
        f"{data_payload}\n\n"
        f"Focus for this question: {', '.join(plan.focus_tables)}. "
        f"Intent: {plan.intent}.\n\n"
        f"Question: {question}"
    )

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return ReasonerResult(
            error="OPENAI_API_KEY is not set. Set it to use the reasoner (Custom GPT / OpenAI API)."
        )

    try:
        response = _call_openai(system_content, user_content)
    except Exception as e:
        return ReasonerResult(error=f"API call failed: {str(e).strip() or 'Unknown error'}")

    if not response:
        return ReasonerResult(error="Model produced no response.")
    return ReasonerResult(response=response)
