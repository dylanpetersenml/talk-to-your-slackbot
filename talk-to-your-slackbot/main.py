"""
Entrypoint: wire Slack-style input into the intake subsystem.

Run from repo root with the package on PYTHONPATH, e.g.:
  PYTHONPATH=talk-to-your-slackbot python -m talk-to-your-slackbot.main
or from the package directory:
  python main.py

Example assumed input: "why did I lose" is parsed and validated by the
input/intake component before being passed to the engine (not yet implemented).
"""

import sys
from pathlib import Path

# Ensure the package directory is on path when run as a script.
if __name__ == "__main__":
    pkg_dir = Path(__file__).resolve().parent
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))

from intake import IntakeRejection, RawSlackInput, process


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
    """Example: parse and validate an assumed input string."""
    assumed_input = "why did I lose"
    result = run_intake(assumed_input)

    if isinstance(result, IntakeRejection):
        print("Rejected:", result.reason, f"(code={result.code})")
        return 1

    print("Validated:", result.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
