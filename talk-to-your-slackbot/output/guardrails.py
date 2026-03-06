"""
Output guardrails: ensure accuracy and safety of formatted output before delivery.

Validates length, absence of PII, and that no raw stack traces or unsafe
content are included in the Slack message.
"""

import re

from .models import FormattedOutput, OutputRejection

# Slack message block text limit (conservative for a single message).
MAX_SLACK_MESSAGE_LENGTH = 4000

# Simple PII patterns (do not send to Slack).
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
SSN_RE = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
PHONE_RE = re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

# Patterns suggesting stack traces or internal paths (unsafe to show).
TRACE_RE = re.compile(
    r"(?:Traceback|File \".+?\"|line \d+|\.py[c]?:\d+|Exception:|Error:)\s*\n",
    re.IGNORECASE,
)
PATH_RE = re.compile(r"/[a-zA-Z0-9_./-]+\.(py|pyc|env)\b")


def _contains_pii(text: str) -> bool:
    """Return True if text appears to contain PII."""
    return bool(
        EMAIL_RE.search(text) or SSN_RE.search(text) or PHONE_RE.search(text)
    )


def _contains_unsafe_content(text: str) -> bool:
    """Return True if text looks like stack traces or internal paths."""
    return bool(TRACE_RE.search(text) or PATH_RE.search(text))


def apply_output_guardrails(
    formatted: FormattedOutput,
) -> FormattedOutput | OutputRejection:
    """
    Ensure formatted output is safe and accurate before delivery to Slack.

    Parameters
    ----------
    formatted : FormattedOutput
        The formatted slack_message from the formatter.

    Returns
    -------
    FormattedOutput | OutputRejection
        Same output if guardrails pass; otherwise a rejection with a safe
        fallback reason for the user.
    """
    msg = formatted.slack_message

    if not msg or not msg.strip():
        return OutputRejection(
            reason="I couldn't generate a response for this question. Please try rephrasing or check the match data.",
            code="empty",
        )

    if len(msg) > MAX_SLACK_MESSAGE_LENGTH:
        return OutputRejection(
            reason="The analysis was too long to send. Try a more specific question.",
            code="length",
        )

    if _contains_pii(msg):
        return OutputRejection(
            reason="The response contained sensitive information and was blocked. Please try a different question.",
            code="pii",
        )

    if _contains_unsafe_content(msg):
        return OutputRejection(
            reason="Something went wrong while preparing the response. Please try again.",
            code="unsafe",
        )

    return formatted
