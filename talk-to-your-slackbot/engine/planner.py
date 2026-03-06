"""
Planner: determine which fields to investigate to answer the user's question.

Maps the validated question to a Plan (intent, focus_tables, focus_hints) so the
reasoner knows which stats to use. Memory can be wired in later for multi-match patterns.
"""

from .models import LoadedStats, Plan

# Table names the loader produces; planner only references these.
TABLE_NAMES = frozenset({
    "game_df",
    "players_df",
    "shot_stats_df",
    "kitchen_arrival_df",
    "ball_directions_df",
})


def _normalize(text: str) -> str:
    return text.lower().strip()


def _detect_intent(question: str) -> str:
    """Classify question intent from keywords. Order matters: more specific first."""
    q = _normalize(question)
    if any(w in q for w in ("lose", "lost", "why did we lose", "why did i lose")):
        return "why_lost"
    if any(w in q for w in ("error", "fault", "unforced", "errors")):
        return "errors_faults"
    if any(w in q for w in ("give up", "most points", "where")) and "point" in q:
        return "where_points_lost"
    if any(w in q for w in ("serving", "return", "returns", "compare")) and ("serv" in q or "return" in q):
        return "compare_serving_returning"
    if any(w in q for w in ("kitchen", "nvz", "arrival")):
        return "kitchen_analysis"
    if any(w in q for w in ("shot", "direction", "pattern", "ball direction")):
        return "shot_patterns"
    if any(w in q for w in ("quality", "decision", "improve")):
        return "quality_decision"
    return "general"


def _plan_for_intent(intent: str, available_tables: frozenset[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Return (focus_tables, focus_hints) for the given intent."""
    focus_tables: list[str] = []
    focus_hints: dict[str, list[str]] = {}

    if intent == "why_lost":
        focus_tables = [t for t in ["game_df", "players_df", "shot_stats_df"] if t in available_tables]
        focus_hints = {
            "game_df": ["team0_outcome", "team1_outcome", "team0_kitchen_pct", "team1_kitchen_pct"],
            "players_df": ["team", "shot_count", "avg_shot_quality", "net_fault_pct", "out_fault_pct", "team_shot_percentage"],
            "shot_stats_df": ["success_pct", "rally_win_pct", "out_fault_pct", "net_fault_pct", "shot_type"],
        }
    elif intent == "where_points_lost":
        focus_tables = [t for t in ["players_df", "shot_stats_df", "kitchen_arrival_df"] if t in available_tables]
        focus_hints = {
            "shot_stats_df": ["shot_type", "rally_win_pct", "success_pct", "out_fault_pct", "net_fault_pct"],
            "players_df": ["team", "team_shot_percentage", "net_fault_pct", "out_fault_pct"],
        }
    elif intent == "compare_serving_returning":
        focus_tables = [t for t in ["shot_stats_df", "kitchen_arrival_df", "players_df"] if t in available_tables]
        focus_hints = {
            "shot_stats_df": ["serves", "returns"],  # shot_type values to filter
            "kitchen_arrival_df": ["role"],
            "players_df": ["shot_count", "avg_shot_quality"],
        }
    elif intent == "kitchen_analysis":
        focus_tables = [t for t in ["kitchen_arrival_df", "players_df", "game_df"] if t in available_tables]
        focus_hints = {
            "kitchen_arrival_df": ["role", "numerator", "denominator"],
            "game_df": ["team0_kitchen_pct", "team1_kitchen_pct"],
        }
    elif intent == "shot_patterns":
        focus_tables = [t for t in ["ball_directions_df", "shot_stats_df", "players_df"] if t in available_tables]
        focus_hints = {
            "ball_directions_df": ["direction", "count"],
            "shot_stats_df": ["shot_type", "count", "avg_quality"],
        }
    elif intent == "errors_faults":
        focus_tables = [t for t in ["players_df", "shot_stats_df"] if t in available_tables]
        focus_hints = {
            "players_df": ["net_fault_pct", "out_fault_pct"],
            "shot_stats_df": ["out_fault_pct", "net_fault_pct", "shot_type"],
        }
    elif intent == "quality_decision":
        focus_tables = [t for t in ["players_df", "shot_stats_df"] if t in available_tables]
        focus_hints = {
            "players_df": ["avg_shot_quality", "net_impact_score", "team_shot_percentage"],
            "shot_stats_df": ["avg_quality", "success_pct", "rally_win_pct", "shot_type"],
        }
    else:
        focus_tables = [t for t in TABLE_NAMES if t in available_tables]
        focus_hints = {}

    return focus_tables, focus_hints


def plan(question: str, loaded: LoadedStats, memory: None = None) -> Plan:
    """
    Determine which fields to investigate to answer the question.

    Uses keyword-based intent detection and returns a Plan (focus_tables,
    focus_hints) for the reasoner. Memory is reserved for future use
    (past investigation patterns across matches).

    Parameters
    ----------
    question : str
        Validated user question (e.g. "How did I lose this game?").
    loaded : LoadedStats
        Loaded stats; used to know which tables exist (all five are always
        present on success, but we still validate).
    memory : None
        Reserved for future Memory integration (multi-match patterns).

    Returns
    -------
    Plan
        intent, focus_tables, and focus_hints for the reasoner.
    """
    _ = memory  # reserved for future use
    available = TABLE_NAMES  # all tables are present when LoadedStats is returned from load_stats
    intent = _detect_intent(question)
    focus_tables, focus_hints = _plan_for_intent(intent, available)
    if not focus_tables:
        focus_tables = list(TABLE_NAMES)
    return Plan(intent=intent, focus_tables=focus_tables, focus_hints=focus_hints)
