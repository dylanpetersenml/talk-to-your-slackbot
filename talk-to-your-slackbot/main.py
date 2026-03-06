"""
Entrypoint: intake -> engine (load stats) -> (later: planner, reasoner, output).

Run from repo root with the package on PYTHONPATH, e.g.:
  PYTHONPATH=talk-to-your-slackbot python talk-to-your-slackbot/main.py
Stats path: STATS_PATH env or default stats.json (relative to cwd).
"""

import sys
from pathlib import Path

# Ensure the package directory is on path when run as a script.
if __name__ == "__main__":
    pkg_dir = Path(__file__).resolve().parent
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))

from intake import IntakeRejection, RawSlackInput, process
from engine import LoadError, load_stats


def run_intake(text: str, user_id: str = "U1", channel_id: str = "C1"):
    """
    Take raw Slack-style input text and run it through the intake subsystem.

    Parameters
    ----------
    text : str
        User message, e.g. "why did I lose".
    user_id : str, optional
        Slack user ID for permission checks.
    channel_id : str, optional
        Slack channel ID.

    Returns
    -------
    ValidatedInput | IntakeRejection
        Validated input to pass to the engine, or a rejection with a reason.
    """
    raw = RawSlackInput(text=text, user_id=user_id, channel_id=channel_id)
    return process(raw)


def main():
    """Example: intake then load stats (PandasAI-compatible DataFrames)."""
    assumed_input = "why did I lose"
    result = run_intake(assumed_input)

    if isinstance(result, IntakeRejection):
        print("Rejected:", result.reason, f"(code={result.code})")
        return 1

    # Engine: load stats (compatible with PandasAI + pickleball_stats.yaml).
    stats_path = Path(__file__).resolve().parent.parent / "stats.json"
    loaded = load_stats(stats_path)

    if isinstance(loaded, LoadError):
        print("Stats load failed:", loaded.message)
        return 1

    print("Validated:", result.text)
    print("Stats loaded: game_id =", loaded.game_df["game_id"].iloc[0])
    print("DataFrames ready for PandasAI:")
    print("  game_df:", loaded.game_df.shape)
    print("  players_df:", loaded.players_df.shape)
    print("  shot_stats_df:", loaded.shot_stats_df.shape)
    print("  kitchen_arrival_df:", loaded.kitchen_arrival_df.shape)
    print("  ball_directions_df:", loaded.ball_directions_df.shape)
    return 0


if __name__ == "__main__":
    sys.exit(main())
