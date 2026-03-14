"""
Entrypoint: intake -> engine (load stats -> plan -> reason) -> output.

Run from repo root with the package on PYTHONPATH, e.g.:
  PYTHONPATH=talk-to-your-slackbot python talk-to-your-slackbot/main.py
Stats path: STATS_PATH env or default stats.json. Set OPENAI_API_KEY for reasoner (Custom GPT / OpenAI API).
"""

import sys
from pathlib import Path

# Ensure the package directory is on path when run as a script.
if __name__ == "__main__":
    pkg_dir = Path(__file__).resolve().parent
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))
    # Load .env from repo root so OPENAI_API_KEY, SLACK_BOT_TOKEN, etc. are set.
    from dotenv import load_dotenv
    env_file = pkg_dir.parent / ".env"
    load_dotenv(env_file)

from intake import IntakeRejection, RawSlackInput, process
from engine import LoadError, load_stats, log_qa, plan, reason
from output import (
    FormatterInput,
    OutputRejection,
    process_output,
    send_output_to_slack,
    send_to_slack,
)


def run_intake(
    text: str,
    user_id: str = "U1",
    channel_id: str = "D0AJGBPE8SK",
    thread_ts: str | None = None,
):
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
    thread_ts : str, optional
        Thread timestamp when the message is in a thread.

    Returns
    -------
    ValidatedInput | IntakeRejection
        Validated input to pass to the engine, or a rejection with a reason.
    """
    raw = RawSlackInput(
        text=text, user_id=user_id, channel_id=channel_id, thread_ts=thread_ts
    )
    return process(raw)


def run_pipeline_from_slack(
    text: str,
    user_id: str,
    channel_id: str,
    thread_ts: str | None = None,
) -> None:
    """
    Run the full pipeline (intake -> engine -> output) using Slack message as the
    question, and post the result (or a user-friendly error) back to Slack.

    Parameters
    ----------
    text : str
        User message from Slack (the question).
    user_id : str
        Slack user ID.
    channel_id : str
        Slack channel ID to post the response to.
    thread_ts : str, optional
        Thread timestamp to reply in thread.
    """
    result = run_intake(text, user_id=user_id, channel_id=channel_id, thread_ts=thread_ts)

    if isinstance(result, IntakeRejection):
        send_to_slack(channel_id=channel_id, message=result.reason, thread_ts=thread_ts)
        return

    stats_path = Path(__file__).resolve().parent.parent / "stats.json"
    loaded = load_stats(stats_path)

    if isinstance(loaded, LoadError):
        send_to_slack(
            channel_id=channel_id, message=loaded.message, thread_ts=thread_ts
        )
        return

    investigation_plan = plan(result.text, loaded)
    log_qa(result.text, investigation_plan.intent, investigation_plan.focus_tables)
    reasoning = reason(result.text, loaded, investigation_plan)

    formatter_input = FormatterInput(
        engine_response=reasoning.response,
        error=reasoning.error,
        memory_context=None,
    )
    out = process_output(formatter_input)
    send_output_to_slack(
        channel_id=channel_id, output=out, thread_ts=result.thread_ts
    )


def main():
    """Example: intake then load stats (PandasAI-compatible DataFrames)."""
    assumed_input = "why did player 3 and player 4 win"
    result = run_intake(assumed_input, thread_ts=None)

    if isinstance(result, IntakeRejection):
        print("Rejected:", result.reason, f"(code={result.code})")
        return 1

    # Engine: load stats (compatible with PandasAI + pickleball_stats.yaml).
    stats_path = Path(__file__).resolve().parent.parent / "stats.json"
    loaded = load_stats(stats_path)

    if isinstance(loaded, LoadError):
        print("Stats load failed:", loaded.message)
        return 1

    # Planner: which fields to investigate for this question.
    investigation_plan = plan(result.text, loaded)
    log_qa(result.text, investigation_plan.intent, investigation_plan.focus_tables)
    print("Validated:", result.text)
    print("Stats loaded: game_id =", loaded.game_df["game_id"].iloc[0])
    print("Plan: intent =", investigation_plan.intent, "| focus_tables =", investigation_plan.focus_tables)

    # Reasoner: send data + context to OpenAI API (Custom GPT style).
    reasoning = reason(result.text, loaded, investigation_plan)

    # Output: format for Slack and apply guardrails.
    formatter_input = FormatterInput(
        engine_response=reasoning.response,
        error=reasoning.error,
        memory_context=None,
    )
    out = process_output(formatter_input)
    if isinstance(out, OutputRejection):
        print("Output rejected:", out.reason, f"(code={out.code})")
    else:
        print(out.slack_message)

    # Send to Slack when channel_id is present (e.g. from Slack request).
    if result.channel_id:
        send_result = send_output_to_slack(
            channel_id=result.channel_id,
            output=out,
            thread_ts=result.thread_ts,
        )
        if not send_result.ok:
            print("Slack send failed:", send_result.error)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
