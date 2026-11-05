"""Offline tests for report.schema.json, including its matches_docs conditionals."""

from __future__ import annotations

import copy
import json

import pytest
from jsonschema import Draft202012Validator

from lab_common import SCHEMA_PATH

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)

PASSING = {
    "doc_file": "docs/units.md", "sample_line": 6, "command": "python3 s.py", "exit_status": 0,
    "stdout": "('mm', 'cm', 'm', 'km', 'mi')\n", "stderr": "",
    "expected_output": "('mm', 'cm', 'm', 'km', 'mi')", "matches_docs": True, "kind": None,
    "explanation": "Output matches.", "suggested_fix": None,
}
DRIFTED = {
    "doc_file": "docs/quickstart.md", "sample_line": 21, "command": "python3 s.py", "exit_status": 1,
    "stdout": "", "stderr": "AttributeError: module 'metrolen' has no attribute 'convert'",
    "expected_output": "5000.0", "matches_docs": False, "kind": "missing_name",
    "explanation": "The function is now convert_units.", "suggested_fix": "Use convert_units.",
}


def report(*results: dict) -> dict:
    return {"schema_version": "1", "library_version": "2.0.0", "python_version": "3.11.17",
            "results": list(results)}


def errors(doc: dict) -> list[str]:
    return [e.message for e in VALIDATOR.iter_errors(doc)]


def test_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(SCHEMA)


def test_good_report_validates() -> None:
    assert errors(report(PASSING, DRIFTED)) == []
    assert errors(report(PASSING, {**DRIFTED, "fix_verified": True})) == []


@pytest.mark.parametrize("change", [
    {"kind": None},                     # drift without a kind
    {"suggested_fix": None},            # drift without a fix
    {"suggested_fix": ""},              # drift with an empty fix
    {"kind": "renamed"},                # kind outside the enum
])
def test_drifted_result_must_be_consistent(change: dict) -> None:
    assert errors(report({**DRIFTED, **change}))


@pytest.mark.parametrize("change", [
    {"kind": "output_mismatch"},        # passing sample with a kind
    {"suggested_fix": "Change it."},    # passing sample with a fix
    {"fix_verified": True},             # passing sample with a verified fix
])
def test_passing_result_must_be_consistent(change: dict) -> None:
    assert errors(report({**PASSING, **change}))


@pytest.mark.parametrize("field", ["command", "exit_status", "stdout", "matches_docs", "kind"])
def test_required_fields(field: str) -> None:
    broken = copy.deepcopy(DRIFTED)
    del broken[field]
    assert errors(report(broken))


@pytest.mark.parametrize("doc_file", ["quickstart.md", "/mnt/session/uploads/fixture/docs/a.md", "docs/A.md"])
def test_doc_file_is_relative_to_fixture(doc_file: str) -> None:
    assert errors(report({**PASSING, "doc_file": doc_file}))


def test_no_extra_fields_and_no_empty_results() -> None:
    assert errors(report({**PASSING, "notes": "x"}))
    assert errors(report())
