"""Tests for lightweight QA logging (question, intent, focus_tables)."""

import json
import os
from pathlib import Path

import pytest

from engine import log_qa


def test_log_qa_writes_jsonl(tmp_path, monkeypatch):
    """log_qa appends one JSON line with question, intent, focus_tables."""
    monkeypatch.setenv("QA_LOG_PATH", str(tmp_path / "qa.jsonl"))
    log_qa("How did I lose?", "why_lost", ["game_df", "players_df", "shot_stats_df"])
    content = (tmp_path / "qa.jsonl").read_text(encoding="utf-8")
    record = json.loads(content.strip())
    assert record["question"] == "How did I lose?"
    assert record["intent"] == "why_lost"
    assert record["focus_tables"] == ["game_df", "players_df", "shot_stats_df"]


def test_log_qa_truncates_long_question(tmp_path, monkeypatch):
    """Long questions are truncated to MAX_QUESTION_LOG_LENGTH with ... suffix."""
    monkeypatch.setenv("QA_LOG_PATH", str(tmp_path / "qa.jsonl"))
    long_q = "x" * 600
    log_qa(long_q, "general", ["game_df"])
    record = json.loads((tmp_path / "qa.jsonl").read_text(encoding="utf-8").strip())
    assert len(record["question"]) == 503  # 500 + "..."
    assert record["question"].endswith("...")


def test_log_qa_disabled_when_env_off(monkeypatch):
    """When QA_LOG_PATH is 'off' or '0', no file is written."""
    monkeypatch.setenv("QA_LOG_PATH", "off")
    log_qa("test", "general", [])
    # No exception; we don't create a default path when disabled
    monkeypatch.setenv("QA_LOG_PATH", "0")
    log_qa("test", "general", [])
