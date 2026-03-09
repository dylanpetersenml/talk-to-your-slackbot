"""
Slack sender: post the formatted output to a Slack channel (optionally in a thread).

Uses the Slack Web API (chat.postMessage) with a bot token from the environment.
"""

import os
import ssl
from dataclasses import dataclass

import certifi

from .models import FormattedOutput, OutputRejection


@dataclass
class SendResult:
    """
    Result of attempting to send a message to Slack.

    Attributes
    ----------
    ok : bool
        True if the message was posted successfully.
    error : str or None
        User-friendly error message when send failed (e.g. token missing, API error).
    """

    ok: bool
    error: str | None = None


def send_to_slack(
    channel_id: str,
    message: str,
    thread_ts: str | None = None,
) -> SendResult:
    """
    Post a message to a Slack channel, optionally as a thread reply.

    Parameters
    ----------
    channel_id : str
        Slack channel ID (e.g. C0XXXXXX). Required for delivery.
    message : str
        Message text (supports Slack mrkdwn: *bold*, _italic_, etc.).
    thread_ts : str, optional
        Parent message timestamp to reply in a thread.

    Returns
    -------
    SendResult
        ok=True when sent; ok=False with error set when token missing or API fails.
    """
    if not channel_id or not channel_id.strip():
        return SendResult(ok=False, error="channel_id is required to send to Slack.")

    if not message or not message.strip():
        return SendResult(ok=False, error="Message text is required.")

    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        return SendResult(
            ok=False,
            error="SLACK_BOT_TOKEN is not set. Set it to post responses to Slack.",
        )

    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
    except ImportError:
        return SendResult(
            ok=False,
            error="slack_sdk is not installed. Install with: poetry add slack-sdk",
        )

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    client = WebClient(token=token, ssl=ssl_context)
    payload = {
        "channel": channel_id.strip(),
        "text": message.strip(),
    }
    if thread_ts and thread_ts.strip():
        payload["thread_ts"] = thread_ts.strip()

    try:
        client.chat_postMessage(**payload)
        return SendResult(ok=True)
    except SlackApiError as e:
        err_msg = (e.response.get("error") if e.response else None) or str(e)
        return SendResult(
            ok=False,
            error=f"Slack API error: {err_msg}",
        )
    except Exception as e:
        return SendResult(
            ok=False,
            error=f"Failed to send to Slack: {str(e).strip() or 'Unknown error'}",
        )


def send_output_to_slack(
    channel_id: str,
    output: FormattedOutput | OutputRejection,
    thread_ts: str | None = None,
) -> SendResult:
    """
    Send the pipeline output to Slack (formatted message or rejection reason).

    Parameters
    ----------
    channel_id : str
        Slack channel ID.
    output : FormattedOutput | OutputRejection
        Result from process_output: either the formatted message or a rejection.
    thread_ts : str, optional
        Parent message ts for thread reply.

    Returns
    -------
    SendResult
        ok=True when sent; otherwise error message for logging/fallback.
    """
    if isinstance(output, OutputRejection):
        message = output.reason
    else:
        message = output.slack_message
    return send_to_slack(channel_id=channel_id, message=message, thread_ts=thread_ts)
