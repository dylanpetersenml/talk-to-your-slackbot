"""Tests for the Input and Intake subsystem."""

from intake import (
    IntakeRejection,
    RawSlackInput,
    ValidatedInput,
    apply_guardrails,
    parse,
    process,
)


# --- Parser (length + format) ---


def test_parse_empty_rejected():
    raw = RawSlackInput(text="", user_id="U1")
    result = parse(raw)
    assert isinstance(result, IntakeRejection)
    assert result.code == "format"
    assert "empty" in result.reason.lower()


def test_parse_whitespace_only_rejected():
    raw = RawSlackInput(text="   \n\t  ")
    result = parse(raw)
    assert isinstance(result, IntakeRejection)
    assert result.code == "format"


def test_parse_valid_question_accepted():
    raw = RawSlackInput(text="  How did I lose this game?  ", user_id="U1", channel_id="C1")
    result = parse(raw)
    assert isinstance(result, ValidatedInput)
    assert result.text == "How did I lose this game?"
    assert result.user_id == "U1"
    assert result.channel_id == "C1"


def test_parse_too_long_rejected():
    from intake.parser import MAX_PROMPT_LENGTH

    raw = RawSlackInput(text="x" * (MAX_PROMPT_LENGTH + 1))
    result = parse(raw)
    assert isinstance(result, IntakeRejection)
    assert result.code == "length"
    assert str(MAX_PROMPT_LENGTH) in result.reason


def test_parse_control_chars_rejected():
    raw = RawSlackInput(text="How did I lose?\x00")
    result = parse(raw)
    assert isinstance(result, IntakeRejection)
    assert result.code == "format"


# --- Guardrails ---


def test_guardrails_pii_email_rejected():
    validated = ValidatedInput(text="Email me at foo@example.com about the game")
    result = apply_guardrails(validated)
    assert isinstance(result, IntakeRejection)
    assert result.code == "pii"


def test_guardrails_pii_phone_rejected():
    validated = ValidatedInput(text="Call me 555-123-4567 to discuss the match")
    result = apply_guardrails(validated)
    assert isinstance(result, IntakeRejection)
    assert result.code == "pii"


def test_guardrails_applicable_question_passes():
    validated = ValidatedInput(text="How did I lose this game?", user_id="U1")
    result = apply_guardrails(validated)
    assert result is validated


def test_guardrails_permission_denied_when_restricted(monkeypatch):
    monkeypatch.setenv("ALLOWED_SLACK_USER_IDS", "U1,U2")
    validated = ValidatedInput(text="How did I lose this game?", user_id="U99")
    result = apply_guardrails(validated)
    assert isinstance(result, IntakeRejection)
    assert result.code == "permission"


def test_guardrails_permission_all_when_env_unset(monkeypatch):
    monkeypatch.delenv("ALLOWED_SLACK_USER_IDS", raising=False)
    validated = ValidatedInput(text="How did I lose this game?", user_id="U99")
    result = apply_guardrails(validated)
    assert result is validated


def test_guardrails_not_applicable_rejected():
    validated = ValidatedInput(text="What is the capital of France?")
    result = apply_guardrails(validated)
    assert isinstance(result, IntakeRejection)
    assert result.code == "not_applicable"


# --- Full pipeline ---


def test_process_end_to_end_success():
    raw = RawSlackInput(text="Where did we give up the most points?", user_id="U1")
    result = process(raw)
    assert isinstance(result, ValidatedInput)
    assert "points" in result.text.lower()


def test_process_end_to_end_empty_rejected():
    raw = RawSlackInput(text="")
    result = process(raw)
    assert isinstance(result, IntakeRejection)
    assert result.code == "format"


def test_process_end_to_end_pii_rejected():
    raw = RawSlackInput(text="My email is a@b.com, how did I lose?")
    result = process(raw)
    assert isinstance(result, IntakeRejection)
    assert result.code == "pii"
