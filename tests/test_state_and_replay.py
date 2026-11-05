"""Offline tests for lab_state.py, replay.py, and event formatting."""

from __future__ import annotations

from pathlib import Path

import pytest

import lab_state
import replay
from lab_common import RECORDINGS_DIR, format_event


def test_state_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    assert lab_state.load(path) == {}
    lab_state.update(path, agent_id="agent_1", session_id="sesn_1")
    lab_state.append("uploaded_file_ids", "file_1", path)
    lab_state.update(path, session_id=None)
    assert lab_state.load(path) == {"agent_id": "agent_1", "uploaded_file_ids": ["file_1"]}


def test_pauses_follow_processed_at_and_are_capped() -> None:
    events = [{"processed_at": "2026-11-05T10:00:00Z"}, {"processed_at": "2026-11-05T10:00:01.5Z"},
              {"processed_at": None}, {"processed_at": "2026-11-05T10:01:00Z"}]
    assert replay.pauses(events) == [0.0, 1.5, 0.0, replay.MAX_PAUSE_SECONDS]
    assert replay.pauses(events, speed=3)[1] == pytest.approx(0.5)


def test_redact_removes_key_like_strings() -> None:
    fake_key = "sk-" + "ant-" + "not-a-real-key_123"  # built at runtime so secret scanners don't flag the repo
    data = {"content": [{"text": f"key {fake_key} here"}]}
    assert "sk-ant" not in str(replay.redact(data))


def test_format_event_shows_the_lab_essentials() -> None:
    assert format_event({"type": "agent.tool_use", "name": "bash", "input": {"command": "python3 a.py"}}) \
        == "tool:    bash: python3 a.py"
    traceback = {"type": "agent.tool_result", "content": [
        {"type": "text", "text": "Traceback (most recent call last):\n  ...\nTypeError: bad"}]}
    assert format_event(traceback) == "result:  ERROR TypeError: bad"
    assert "queued" in format_event({"type": "user.message", "processed_at": None,
                                     "content": [{"type": "text", "text": "hi"}]})
    assert format_event({"type": "span.model_request_start"}) is None


DEMO = RECORDINGS_DIR / "demo.jsonl"


@pytest.mark.skipif(not DEMO.exists(), reason="demo recording not created yet")
def test_demo_recording_is_clean_and_replayable() -> None:
    text = DEMO.read_text(encoding="utf-8")
    for forbidden in ("sk-ant-", "C:\\\\Users", "/Users/", "ANTHROPIC_API_KEY="):
        assert forbidden not in text, forbidden
    events = replay.load(DEMO)
    lines = [format_event(e) for e in events]
    assert any(ln and ln.startswith("tool:    bash") for ln in lines)
    assert any(ln and "ERROR" in ln for ln in lines)
    assert sum(1 for e in events if e["type"] == "user.message") >= 2
