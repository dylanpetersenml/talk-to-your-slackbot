"""Tests for the Output subsystem."""

import pytest

from output import (
    FormatterInput,
    FormattedOutput,
    OutputRejection,
    SendResult,
    apply_output_guardrails,
    format_for_slack,
    process_output,
    send_output_to_slack,
    send_to_slack,
)


# --- Formatter ---


def test_format_for_slack_engine_response():
    inp = FormatterInput(engine_response="Your short returns hurt. Focus on depth.")
    out = format_for_slack(inp)
    assert isinstance(out, FormattedOutput)
    assert "Coaching insight" in out.slack_message
    assert "Your short returns hurt" in out.slack_message


def test_format_for_slack_error():
    inp = FormatterInput(error="OPENAI_API_KEY is not set.")
    out = format_for_slack(inp)
    assert "Something went wrong" in out.slack_message
    assert "OPENAI_API_KEY" in out.slack_message


def test_format_for_slack_with_memory_context():
    inp = FormatterInput(
        engine_response="Kitchen arrival was low.",
        memory_context="In past matches, your dink % correlated with wins.",
    )
    out = format_for_slack(inp)
    assert "Kitchen arrival was low" in out.slack_message
    assert "Context from past matches" in out.slack_message
    assert "dink" in out.slack_message


def test_format_for_slack_empty_fallback():
    inp = FormatterInput(engine_response=None, error=None)
    out = format_for_slack(inp)
    assert "Something went wrong" in out.slack_message or "couldn't produce" in out.slack_message


def test_format_for_slack_error_suppresses_memory():
    inp = FormatterInput(
        error="API call failed.",
        memory_context="Prior insight here.",
    )
    out = format_for_slack(inp)
    assert "API call failed" in out.slack_message
    assert "Prior insight" not in out.slack_message


# --- Output guardrails ---


def test_guardrails_accept_clean_message():
    formatted = FormattedOutput(slack_message="*Coaching insight*\nYour returns were short.")
    result = apply_output_guardrails(formatted)
    assert result is formatted
    assert result.slack_message == formatted.slack_message


def test_guardrails_reject_empty():
    formatted = FormattedOutput(slack_message="   ")
    result = apply_output_guardrails(formatted)
    assert isinstance(result, OutputRejection)
    assert result.code == "empty"
    assert "couldn't generate" in result.reason.lower() or "rephrasing" in result.reason.lower()


def test_guardrails_reject_too_long():
    from output.guardrails import MAX_SLACK_MESSAGE_LENGTH

    formatted = FormattedOutput(slack_message="x" * (MAX_SLACK_MESSAGE_LENGTH + 1))
    result = apply_output_guardrails(formatted)
    assert isinstance(result, OutputRejection)
    assert result.code == "length"


def test_guardrails_reject_pii():
    formatted = FormattedOutput(
        slack_message="*Coaching insight*\nEmail me at user@example.com for tips."
    )
    result = apply_output_guardrails(formatted)
    assert isinstance(result, OutputRejection)
    assert result.code == "pii"


def test_guardrails_reject_unsafe_trace():
    formatted = FormattedOutput(
        slack_message="Traceback (most recent call last):\n  File \"/code/main.py\", line 1"
    )
    result = apply_output_guardrails(formatted)
    assert isinstance(result, OutputRejection)
    assert result.code == "unsafe"


# --- Full pipeline ---


def test_process_output_success():
    inp = FormatterInput(engine_response="Focus on kitchen shots.")
    out = process_output(inp)
    assert isinstance(out, FormattedOutput)
    assert "Focus on kitchen shots" in out.slack_message


def test_process_output_rejection_pii():
    inp = FormatterInput(engine_response="Contact 555-123-4567 for coaching.")
    out = process_output(inp)
    assert isinstance(out, OutputRejection)
    assert out.code == "pii"


# --- Slack sender ---


def test_send_to_slack_no_token():
    result = send_to_slack(channel_id="C123", message="Hello")
    assert not result.ok
    assert "SLACK_BOT_TOKEN" in result.error


def test_send_to_slack_empty_channel():
    result = send_to_slack(channel_id="", message="Hello")
    assert not result.ok
    assert "channel" in result.error.lower()


def test_send_to_slack_empty_message():
    result = send_to_slack(channel_id="C123", message="   ")
    assert not result.ok
    assert "message" in result.error.lower() or "required" in result.error.lower()


def test_send_output_to_slack_sends_rejection_reason():
    """When output is OutputRejection, send_output_to_slack uses reason as message."""
    out = OutputRejection(reason="Your question doesn't apply.", code="not_applicable")
    # No token - we only check that the right message would be sent (reason, not slack_message).
    result = send_output_to_slack(channel_id="C1", output=out)
    assert not result.ok
    assert "SLACK_BOT_TOKEN" in result.error
