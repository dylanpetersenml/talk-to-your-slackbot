"""
Slack Bolt app: listen for messages and use the message text as the question.

Run from repo root with the package on PYTHONPATH, e.g.:
  PYTHONPATH=talk-to-your-slackbot python talk-to-your-slackbot/slack_app.py

Requires SLACK_BOT_TOKEN and SLACK_APP_TOKEN (Socket Mode) in .env.
"""

import os
import re
import sys
from pathlib import Path

if __name__ == "__main__":
    pkg_dir = Path(__file__).resolve().parent
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))
    from dotenv import load_dotenv

    load_dotenv(pkg_dir.parent / ".env")
    # Use certifi's CA bundle so HTTPS works on macOS/Homebrew Python.
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from main import run_pipeline_from_slack

app = App(token=os.environ.get("SLACK_BOT_TOKEN", ""))


def _strip_mention(text: str) -> str:
    """Remove leading @bot mention from message text."""
    return re.sub(r"^\s*<@[A-Z0-9]+>\s*", "", text or "").strip()


@app.event("app_mention")
def handle_app_mention(event, *_):
    """Use the message text as the question and reply in thread."""
    if event.get("bot_id"):
        return
    text = _strip_mention(event.get("text", ""))
    if not text:
        return
    user_id = event.get("user", "")
    channel_id = event.get("channel", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    run_pipeline_from_slack(
        text=text,
        user_id=user_id,
        channel_id=channel_id,
        thread_ts=thread_ts,
    )


@app.event("message")
def handle_message(event, *_):
    """In DMs, use the message text as the question and reply."""
    if event.get("bot_id"):
        return
    if event.get("channel_type") != "im":
        return
    text = (event.get("text") or "").strip()
    if not text:
        return
    user_id = event.get("user", "")
    channel_id = event.get("channel", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    run_pipeline_from_slack(
        text=text,
        user_id=user_id,
        channel_id=channel_id,
        thread_ts=thread_ts,
    )


if __name__ == "__main__":
    app_token = os.environ.get("SLACK_APP_TOKEN", "").strip()
    if not app_token:
        print("SLACK_APP_TOKEN is not set. Set it for Socket Mode (xapp-...).")
        sys.exit(1)
    if not os.environ.get("SLACK_BOT_TOKEN", "").strip():
        print("SLACK_BOT_TOKEN is not set.")
        sys.exit(1)
    handler = SocketModeHandler(app, app_token)
    handler.start()
