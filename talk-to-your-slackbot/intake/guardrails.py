"""Intake guardrails: PII detection and permission/applicability checks."""

import os
import re
from .models import IntakeRejection, ValidatedInput

# Simple PII patterns (avoid logging or forwarding sensitive data).
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
# US SSN-like: 3-2-4 digits with optional separators.
SSN_RE = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
# US phone: 10 digits, optional parens/dashes/dots.
PHONE_RE = re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

# Keywords suggesting the question is about match/stats (PB Vision data).
APPLICABLE_KEYWORDS = frozenset(
    {
        "game", "match", "lose", "lost", "win", "won", "points", "score", "serving",
        "return", "returns", "kitchen", "dink", "drive", "shot", "shots", "rally",
        "error", "errors", "compare", "how", "why", "where", "when", "percentage",
        "stats", "statistics", "analysis", "review", "improve", "coach", "coaching",
    }
)


def _contains_pii(text: str) -> bool:
    """Return True if text appears to contain PII (email, SSN, phone)."""
    return bool(
        EMAIL_RE.search(text) or SSN_RE.search(text) or PHONE_RE.search(text)
    )


def _user_has_permission(user_id: str) -> bool:
    """
    Check whether the user is allowed to use the bot.

    If ALLOWED_SLACK_USER_IDS is set (comma-separated), only those users may proceed.
    If unset, all users are allowed (open workspace).
    """
    allowed = os.environ.get("ALLOWED_SLACK_USER_IDS", "").strip()
    if not allowed:
        return True
    return user_id.strip() in {u.strip() for u in allowed.split(",") if u.strip()}


def _question_applicable_to_stats(text: str) -> bool:
    """
    Heuristic: question seems to be about match/stats (PB Vision data).

    Returns True if the text contains at least one keyword suggesting
    match analysis (e.g. game, lose, points, serving). Question words
    alone (how, why, what) are not enough without a game-related keyword.
    """
    lower = text.lower().strip()
    words = set(re.findall(r"\w+", lower))
    return bool(words & APPLICABLE_KEYWORDS)


def apply_guardrails(validated: ValidatedInput) -> ValidatedInput | IntakeRejection:
    """
    Apply PII, permission, and applicability guardrails to validated input.

    Parameters
    ----------
    validated : ValidatedInput
        Output from the input parser.

    Returns
    -------
    ValidatedInput | IntakeRejection
        Same input if all guardrails pass, else a rejection with reason and code.
    """
    if _contains_pii(validated.text):
        return IntakeRejection(
            reason="Please don't include personal information (e.g. email, phone numbers) in your question.",
            code="pii",
        )

    if not _user_has_permission(validated.user_id):
        return IntakeRejection(
            reason="You don't have permission to use this bot in this workspace.",
            code="permission",
        )

    if not _question_applicable_to_stats(validated.text):
        return IntakeRejection(
            reason="Your question doesn't seem to be about this match or its statistics. "
            "Try asking about the game, shots, serving, returns, or points.",
            code="not_applicable",
        )

    return validated
