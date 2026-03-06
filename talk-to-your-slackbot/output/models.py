"""Data models for the Output subsystem."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FormatterInput:
    """
    Input to the output formatter: engine analysis plus optional prior context.

    Attributes
    ----------
    engine_response : str or None
        Natural-language analysis from the reasoner when successful.
    error : str or None
        User-friendly error message when the engine failed (e.g. no API key).
    memory_context : str or None
        Optional prior insights or patterns from Memory (multi-match context).
    """

    engine_response: str | None = None
    error: str | None = None
    memory_context: str | None = None


@dataclass(frozen=True)
class FormattedOutput:
    """
    Formatted message ready for Slack delivery.

    Attributes
    ----------
    slack_message : str
        Concise, structured text suitable for posting in a Slack channel.
    """

    slack_message: str


@dataclass(frozen=True)
class OutputRejection:
    """
    Result when output guardrails reject the formatted message.

    Attributes
    ----------
    reason : str
        Human-readable reason (safe fallback message for Slack).
    code : Literal
        Machine-readable code: "pii", "length", "unsafe", "empty".
    """

    reason: str
    code: Literal["pii", "length", "unsafe", "empty"]
