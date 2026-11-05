"""Offline test: 04_cleanup.py's cost summary reads the session's own usage report."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("cleanup", ROOT / "solution" / "04_cleanup.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


def test_cost_from_a_recorded_usage_report() -> None:
    """The session.usage event in the demo recording has the same usage shape as sessions.retrieve."""
    lines = (ROOT / "recordings" / "demo.jsonl").read_text(encoding="utf-8").splitlines()
    usage_event = [json.loads(line) for line in lines if '"session.usage"' in line][-1]
    text = cleanup.describe_cost({"usage": usage_event["usage"], "budget": usage_event["budget"]})
    assert text.startswith("Session cost: $0.01 at list prices (rounded to the nearest cent), against a $0.50 budget")
    assert "11,143 output" in text and "running time: 68 s" in text


def test_cost_without_budget_or_usage() -> None:
    assert cleanup.describe_cost({}).startswith("Session cost: $0.00 at list prices")
    assert "budget" not in cleanup.describe_cost({"usage": {"list_cost": {"amount": "3", "currency": "USD"}}})
