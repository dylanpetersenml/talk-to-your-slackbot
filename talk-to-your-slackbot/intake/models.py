"""Data models for the Input and Intake subsystem."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class RawSlackInput:
    """
    Raw user input as received from Slack.

    Attributes
    ----------
    text : str
        The user's question or message (e.g. "How did I lose this game?").
    user_id : str, optional
        Slack user ID for permission checks.
    channel_id : str, optional
        Slack channel ID.
    thread_ts : str, optional
        Thread timestamp when the message is in a thread.
    """

    text: str
    user_id: str = ""
    channel_id: str = ""
    thread_ts: str | None = None


@dataclass(frozen=True)
class ValidatedInput:
    """
    Input that passed intake validation and is safe to send to the engine.

    Attributes
    ----------
    text : str
        Sanitized, validated question text.
    user_id : str
        Slack user ID.
    channel_id : str
        Slack channel ID.
    thread_ts : str | None
        Thread timestamp if in a thread.
    """

    text: str
    user_id: str = ""
    channel_id: str = ""
    thread_ts: str | None = None


@dataclass(frozen=True)
class IntakeRejection:
    """
    Result when intake validation fails.

    Attributes
    ----------
    reason : str
        Human-readable reason for rejection (for Slack response).
    code : Literal["length" | "format" | "pii" | "permission" | "not_applicable"]
        Machine-readable rejection code.
    """

    reason: str
    code: Literal["length", "format", "pii", "permission", "not_applicable"]
