"""
Entrypoint: intake -> engine (load stats -> plan -> reason) -> output.

Run from repo root with the package on PYTHONPATH, e.g.:
  PYTHONPATH=talk-to-your-slackbot python talk-to-your-slackbot/main.py "why did player 3 win?"
  PYTHONPATH=talk-to-your-slackbot python talk-to-your-slackbot/main.py  # start Slack server for user questions
Stats path: STATS_PATH env or default stats.json. Set OPENAI_API_KEY for reasoner (Custom GPT / OpenAI API).
"""

import os
import re
import sys
import threading
from pathlib import Path

# Ensure the package directory is on path when run as a script.
if __name__ == "__main__":
    pkg_dir = Path(__file__).resolve().parent
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))

from intake import IntakeRejection, RawSlackInput, process
from engine import LoadError, load_stats, plan, reason
from output import FormatterInput, FormattedOutput, OutputRejection, process_output, send_output_to_slack


def run_intake(text: str, user_id: str = "U1", channel_id: str = "", thread_ts: str | None = None):
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
    raw = RawSlackInput(text=text, user_id=user_id, channel_id=channel_id, thread_ts=thread_ts)
    return process(raw)


def run_pipeline(
    text: str,
    user_id: str = "U1",
    channel_id: str = "",
    thread_ts: str | None = None,
    stats_path: Path | None = None,
) -> int:
    """
    Run the full pipeline: intake -> engine -> output (and optionally send to Slack).

    Parameters
    ----------
    text : str
        User question (e.g. from Slack or CLI).
    user_id : str, optional
        Slack user ID for permission checks.
    channel_id : str, optional
        Slack channel ID; when set, response is sent to Slack.
    thread_ts : str, optional
        Thread timestamp for threaded reply.
    stats_path : Path, optional
        Path to stats.json; defaults to repo stats.json.

    Returns
    -------
    int
        0 on success, 1 on failure.
    """
    result = run_intake(text, user_id=user_id, channel_id=channel_id, thread_ts=thread_ts)

    if isinstance(result, IntakeRejection):
        print("Rejected:", result.reason, f"(code={result.code})")
        if channel_id:
            send_output_to_slack(
                channel_id=channel_id,
                output=FormattedOutput(slack_message=result.reason),
                thread_ts=thread_ts,
            )
        return 1

    if stats_path is None:
        stats_path = Path(__file__).resolve().parent.parent / "stats.json"
    loaded = load_stats(stats_path)

    if isinstance(loaded, LoadError):
        print("Stats load failed:", loaded.message)
        if channel_id:
            send_output_to_slack(
                channel_id=channel_id,
                output=FormattedOutput(slack_message=loaded.message),
                thread_ts=thread_ts,
            )
        return 1

    investigation_plan = plan(result.text, loaded)
    print("Validated:", result.text)
    print("Stats loaded: game_id =", loaded.game_df["game_id"].iloc[0])
    print("Plan: intent =", investigation_plan.intent, "| focus_tables =", investigation_plan.focus_tables)

    reasoning = reason(result.text, loaded, investigation_plan)

    formatter_input = FormatterInput(
        engine_response=reasoning.response,
        error=reasoning.error,
        memory_context=None,
    )
    out = process_output(formatter_input)
    if isinstance(out, OutputRejection):
        print("Output rejected:", out.reason, f"(code={out.code})")
        if channel_id:
            send_output_to_slack(
                channel_id=channel_id,
                output=FormattedOutput(slack_message=out.reason),
                thread_ts=thread_ts,
            )
        return 1
    print(out.slack_message)

    if channel_id:
        send_result = send_output_to_slack(
            channel_id=channel_id,
            output=out,
            thread_ts=thread_ts,
        )
        if not send_result.ok:
            print("Slack send failed:", send_result.error)
            return 1
    return 0


def _create_slack_app(stats_path: Path):
    """Create Flask app for Slack slash command and events."""
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route("/slack/command", methods=["POST"])
    def slack_command():
        # Slash command: form-urlencoded with text, user_id, channel_id, etc.
        text = (request.form.get("text") or "").strip()
        user_id = request.form.get("user_id") or "U1"
        channel_id = request.form.get("channel_id") or ""
        # Optional: respond in thread (Slack may send thread_ts in some setups)
        thread_ts = request.form.get("thread_ts") or request.form.get("ts")

        if not text:
            return jsonify({"text": "Please provide a question, e.g. _why did player 3 and player 4 win?_"}), 200

        # Respond immediately so Slack doesn't timeout (3 sec); process in background.
        def run():
            run_pipeline(
                text=text,
                user_id=user_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                stats_path=stats_path,
            )

        threading.Thread(target=run, daemon=True).start()
        return jsonify({"text": "Analyzing your match… I'll post the insight here shortly."}), 200

    @app.route("/slack/events", methods=["POST"])
    def slack_events():
        # Events API: url_verification challenge and app_mention (when users @mention the bot).
        body = request.get_json(silent=True) or {}
        if body.get("type") == "url_verification":
            return jsonify({"challenge": body.get("challenge", "")}), 200

        if body.get("type") != "event_callback":
            return jsonify({}), 200

        event = body.get("event") or {}
        if event.get("type") != "app_mention":
            return jsonify({}), 200

        # Strip <@U0LAN0Z89> style mentions from the start of text to get the question.
        text = (event.get("text") or "").strip()
        text = re.sub(r"^<@[A-Z0-9]+>\s*", "", text).strip()

        if not text:
            return jsonify({}), 200

        user_id = event.get("user") or "U1"
        channel_id = event.get("channel") or ""
        thread_ts = event.get("ts")

        def run_event():
            run_pipeline(
                text=text,
                user_id=user_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                stats_path=stats_path,
            )

        threading.Thread(target=run_event, daemon=True).start()
        return jsonify({}), 200

    return app


def main() -> int:
    """Run pipeline with CLI question or start Slack server for user input."""
    stats_env = (os.environ.get("STATS_PATH") or "").strip()
    stats_path = Path(stats_env) if stats_env else (
        Path(__file__).resolve().parent.parent / "stats.json"
    )

    # User question from command line: run pipeline once (print to stdout; send to Slack if channel in env).
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
        if not question:
            print("Usage: python main.py \"your question\"  OR  python main.py  # start Slack server")
            return 1
        channel_id = os.environ.get("SLACK_CHANNEL_ID", "")
        return run_pipeline(
            text=question,
            user_id=os.environ.get("SLACK_USER_ID", "U1"),
            channel_id=channel_id,
            stats_path=stats_path,
        )

    # No args: start HTTP server so Slack can send user questions (slash command).
    app = _create_slack_app(stats_path)
    port = int(os.environ.get("PORT", "5000"))
    print(
        f"Slack handler listening on port {port}. "
        f"Slash command URL: http://localhost:{port}/slack/command  "
        f"Events API URL: http://localhost:{port}/slack/events"
    )
    app.run(host="0.0.0.0", port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
