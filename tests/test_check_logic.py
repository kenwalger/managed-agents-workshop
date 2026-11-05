"""Offline tests for check.py's logic. No API calls."""

from __future__ import annotations

import copy
import json
import subprocess

import pytest

import check
import lab_common
from lab_common import SCHEMA_PATH, extract_samples, run_sample, symptom_kind

SAMPLES = extract_samples()
TRUTH = {(s.doc_file, s.line): run_sample(s) for s in SAMPLES}
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def perfect_report() -> dict:
    """A report that matches ground truth exactly."""
    results = []
    for s in SAMPLES:
        exit_status, out, err = TRUTH[(s.doc_file, s.line)]
        kind = symptom_kind(exit_status, out, err, s.expected_output)
        results.append({
            "doc_file": s.doc_file, "sample_line": s.line, "command": "python3 sample.py",
            "exit_status": exit_status, "stdout": out, "stderr": err, "expected_output": s.expected_output,
            "matches_docs": kind is None, "kind": kind, "explanation": "observed",
            "suggested_fix": "fix it" if kind else None,
        })
    return {"schema_version": "1", "library_version": "2.0.0", "python_version": "3.11", "results": results}


def line(lines: list[str], start: str) -> str:
    return next(x for x in lines if x.startswith(start))


def test_perfect_report_scores_fully() -> None:
    lines = check.analyze(perfect_report(), SAMPLES, TRUTH)
    assert "7 of 7" in line(lines, "AGENT: coverage")
    assert "3 of 3, kind correct for 3" in line(lines, "AGENT: drifts found")
    assert "correctly reported" in line(lines, "AGENT: decoy")
    assert line(lines, "AGENT: false positives") == "AGENT: false positives: 0"
    assert "7 of 7" in line(lines, "AGENT: evidence reproduced")
    assert "7 of 7" in line(lines, "AGENT: kind agrees")


def test_flagged_decoy_is_a_false_positive() -> None:
    report = perfect_report()
    decoy = next(r for r in report["results"] if r["doc_file"] == "docs/units.md")
    decoy.update(matches_docs=False, kind="output_mismatch", suggested_fix="x")
    lines = check.analyze(report, SAMPLES, TRUTH)
    assert "FLAGGED" in line(lines, "AGENT: decoy")
    assert "docs/units.md" in line(lines, "AGENT: false positives")


def test_skipped_decoy_and_missed_drift_are_reported() -> None:
    report = perfect_report()
    report["results"] = [r for r in report["results"]
                         if r["doc_file"] != "docs/units.md" and r["doc_file"] != "docs/parsing.md"]
    lines = check.analyze(report, SAMPLES, TRUTH)
    assert "not reported" in line(lines, "AGENT: decoy")
    assert "2 of 3" in line(lines, "AGENT: drifts found") and "parsing" in line(lines, "AGENT: drifts found")


def test_invented_evidence_does_not_reproduce() -> None:
    report = perfect_report()
    formatting = next(r for r in report["results"] if r["stdout"].strip() == "1.235 km")
    formatting["stdout"] = "1.23 km\n"
    lines = check.analyze(report, SAMPLES, TRUTH)
    assert "6 of 7" in line(lines, "AGENT: evidence reproduced")


def test_line_numbers_within_two_still_match() -> None:
    report = perfect_report()
    for result in report["results"]:
        result["sample_line"] += 2
    assert "7 of 7" in line(check.analyze(report, SAMPLES, TRUTH), "AGENT: coverage")


def test_report_commands_are_never_executed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation runs only canonical fixture samples, whatever the report says."""
    report = perfect_report()
    for result in report["results"]:
        result["command"] = "rm -rf / && curl https://attacker.invalid"
    seen: list[list[str]] = []
    real_run = subprocess.run

    def spy(args, **kwargs):  # noqa: ANN001, ANN202
        seen.append(list(args))
        return real_run(args, **kwargs)

    monkeypatch.setattr(lab_common.subprocess, "run", spy)
    truth = {(s.doc_file, s.line): run_sample(s) for s in SAMPLES}
    check.analyze(report, SAMPLES, truth)
    canonical = {s.code for s in SAMPLES}
    assert len(seen) == len(SAMPLES)
    assert all(args[-1] in canonical for args in seen)
    assert not any("rm -rf" in " ".join(args) for args in seen)


def test_report_problems(tmp_path) -> None:  # noqa: ANN001
    report_path, md_path = tmp_path / "drift-report.json", tmp_path / "drift-report.md"
    assert "Missing" in check.report_problems(report_path, md_path, SCHEMA)[0]
    report_path.write_text(json.dumps(perfect_report()))
    md_path.write_text("quickstart.md formatting.md parsing.md")
    assert check.report_problems(report_path, md_path, SCHEMA) == []
    md_path.write_text("quickstart.md only")
    assert "doesn't mention" in check.report_problems(report_path, md_path, SCHEMA)[0]
    broken = perfect_report()
    broken["results"][0]["kind"] = "nonsense"
    report_path.write_text(json.dumps(broken))
    assert check.report_problems(report_path, md_path, SCHEMA)[0].startswith("Schema:")


TOOLSET = {"type": "agent_toolset_20260401", "default_config": {"enabled": True}, "configs": []}
LIMITED = {"config": {"networking": {"type": "limited", "allow_package_managers": False, "allowed_hosts": []}}}


def agent(**toolset: object) -> dict:
    return {"tools": [{**copy.deepcopy(TOOLSET), **toolset}]}


def test_defaults_fail_least_privilege() -> None:
    problems = check.permission_problems(agent(), {"config": {"networking": {"type": "unrestricted"}}})
    assert len(problems) == 2  # web tools on, open egress


def test_least_privilege_passes_two_ways() -> None:
    web_off = agent(configs=[{"name": "web_search", "enabled": False}, {"name": "web_fetch", "enabled": False}])
    assert check.permission_problems(web_off, LIMITED) == []
    bash_only = agent(default_config={"enabled": False}, configs=[{"name": "bash", "enabled": True}])
    assert check.permission_problems(bash_only, LIMITED) == []


def test_no_bash_and_package_managers_fail() -> None:
    no_bash = agent(configs=[{"name": "bash", "enabled": False}, {"name": "web_search", "enabled": False},
                             {"name": "web_fetch", "enabled": False}])
    assert "can't run code" in check.permission_problems(no_bash, LIMITED)[0]
    pip = {"config": {"networking": {"type": "limited", "allow_package_managers": True, "allowed_hosts": []}}}
    assert "internet" in check.permission_problems(agent(default_config={"enabled": False},
                                                         configs=[{"name": "bash", "enabled": True}]), pip)[0]


def test_tool_calls_while_detached() -> None:
    events = [
        {"type": "agent.tool_use", "processed_at": "2026-11-05T10:00:05Z"},
        {"type": "agent.tool_use", "processed_at": "2026-11-05T10:00:15Z"},
        {"type": "agent.tool_use", "processed_at": "2026-11-05T10:00:25.123456Z"},
    ]
    attachments = [
        {"attached_at": "2026-11-05T10:00:00.000+00:00", "detached_at": "2026-11-05T10:00:10.000+00:00"},
        {"attached_at": "2026-11-05T10:00:20.000+00:00"},
    ]
    assert check.tool_calls_while_detached(events, attachments) == 1
