"""
Lightweight logging of question, detected intent, and focus tables.

Writes one JSON line per request to a file (default logs/qa.jsonl in repo root).
Set QA_LOG_PATH to override or set to empty to disable file logging.
"""

import json
import os
from pathlib import Path

# Truncate question in logs to keep entries small.
MAX_QUESTION_LOG_LENGTH = 500


def log_qa(question: str, intent: str, focus_tables: list[str]) -> None:
    """
    Append a single-line JSON log: question, intent, focus_tables.

    Does nothing if QA_LOG_PATH is set to "0", "off", "false", "no", or "disabled".
    Otherwise writes to QA_LOG_PATH if set, or to repo_root/logs/qa.jsonl by default.

    Parameters
    ----------
    question : str
        Validated user question (truncated in log if long).
    intent : str
        Detected intent tag from the planner.
    focus_tables : list of str
        Table names selected for this question.
    """
    path_env = os.environ.get("QA_LOG_PATH", "").strip().lower()
    if path_env in ("0", "false", "off", "no", "disabled"):
        return
    if path_env:
        log_path = Path(os.environ["QA_LOG_PATH"].strip())
    else:
        repo_root = Path(__file__).resolve().parent.parent.parent
        log_path = repo_root / "logs" / "qa.jsonl"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    q = question[:MAX_QUESTION_LOG_LENGTH] + ("..." if len(question) > MAX_QUESTION_LOG_LENGTH else "")
    record = {
        "question": q,
        "intent": intent,
        "focus_tables": focus_tables,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
