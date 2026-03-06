"""Input parser: prompt length and format validation."""

import re
from .models import IntakeRejection, RawSlackInput, ValidatedInput

# Slack message text limit is 40000; we use a smaller limit for coach questions.
MAX_PROMPT_LENGTH = 2000

# Control characters and other non-printable that we don't allow in questions.
CONTROL_OR_INVALID_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def parse(raw: RawSlackInput) -> ValidatedInput | IntakeRejection:
    """
    Validate and normalize the raw Slack input.

    Checks prompt length and format (non-empty, valid text without control chars).
    Does not run guardrails (PII, permission, applicability); use the full
    intake pipeline for that.

    Parameters
    ----------
    raw : RawSlackInput
        The raw message from Slack.

    Returns
    -------
    ValidatedInput | IntakeRejection
        Validated input or a rejection with reason and code.
    """
    text = (raw.text or "").strip()

    if not text:
        return IntakeRejection(
            reason="Your message is empty. Please ask a question about the match (e.g. 'How did I lose this game?').",
            code="format",
        )

    if len(text) > MAX_PROMPT_LENGTH:
        return IntakeRejection(
            reason=f"Your message is too long (max {MAX_PROMPT_LENGTH} characters). Please shorten your question.",
            code="length",
        )

    if CONTROL_OR_INVALID_RE.search(text):
        return IntakeRejection(
            reason="Your message contains invalid characters. Please use plain text only.",
            code="format",
        )

    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return IntakeRejection(
            reason="Your message could not be processed. Please use valid text only.",
            code="format",
        )

    return ValidatedInput(
        text=text,
        user_id=raw.user_id,
        channel_id=raw.channel_id,
        thread_ts=raw.thread_ts,
    )
