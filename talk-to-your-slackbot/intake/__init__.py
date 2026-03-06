"""
Input and Intake subsystem.

Validates Slack user input (length, format), then applies guardrails
(PII detection, permission check, applicability to match stats) so that
only properly formatted and validated text proceeds to the engine.
"""

from .models import (
    IntakeRejection,
    RawSlackInput,
    ValidatedInput,
)
from .parser import parse
from .guardrails import apply_guardrails


def process(raw: RawSlackInput) -> ValidatedInput | IntakeRejection:
    """
    Run the full intake pipeline: parse then guardrails.

    Parameters
    ----------
    raw : RawSlackInput
        Raw message from Slack (text, user_id, channel_id, thread_ts).

    Returns
    -------
    ValidatedInput | IntakeRejection
        Validated input to pass to the engine, or a rejection with a
        user-facing reason and code.
    """
    parsed = parse(raw)
    if isinstance(parsed, IntakeRejection):
        return parsed
    return apply_guardrails(parsed)


__all__ = [
    "process",
    "parse",
    "apply_guardrails",
    "RawSlackInput",
    "ValidatedInput",
    "IntakeRejection",
]
