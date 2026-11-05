"""Offline tests: every planted drift really fails, and the decoy and controls really work."""

from __future__ import annotations

import subprocess

import pytest

from lab_common import FIXTURE_DIR, extract_samples, run_sample, symptom_kind

# (doc_file, fence line) -> (expected exit is zero, expected stdout, expected kind)
EXPECTED = {
    ("docs/formatting.md", 7): (True, "2.5 m", None),
    ("docs/formatting.md", 20): (True, "1.235 km", "output_mismatch"),
    ("docs/parsing.md", 7): (True, "(12.0, 'cm')", None),
    ("docs/parsing.md", 22): (False, "", "bad_arguments"),
    ("docs/quickstart.md", 8): (True, "True", None),
    ("docs/quickstart.md", 21): (False, "", "missing_name"),
    ("docs/units.md", 6): (True, "('mm', 'cm', 'm', 'km', 'mi')", None),
}


def _pythons() -> list[str]:
    """Interpreters to test against: 3.10 to 3.13, when uv has them installed."""
    found = []
    for version in ("3.10", "3.11", "3.12", "3.13"):
        done = subprocess.run(["uv", "python", "find", "--no-project", version],
                              capture_output=True, text=True)
        if done.returncode == 0 and done.stdout.strip():
            found.append(done.stdout.strip())
    return found


def test_seven_samples_at_known_lines() -> None:
    samples = extract_samples()
    assert {(s.doc_file, s.line) for s in samples} == set(EXPECTED)


@pytest.mark.parametrize("python", _pythons())
def test_each_sample_behaves_as_planted(python: str) -> None:
    for sample in extract_samples():
        zero, stdout, kind = EXPECTED[(sample.doc_file, sample.line)]
        exit_status, out, err = run_sample(sample, python=python)
        assert (exit_status == 0) == zero, (sample, err)
        if zero:
            assert out.strip() == stdout
        assert symptom_kind(exit_status, out, err, sample.expected_output) == kind, (sample, err)


def test_at_least_python_310_and_313_available() -> None:
    versions = " ".join(_pythons())
    assert "3.10" in versions and "3.13" in versions, "run: uv python install 3.10 3.13"


def test_specific_errors() -> None:
    by_key = {(s.doc_file, s.line): s for s in extract_samples()}
    _, _, err = run_sample(by_key[("docs/quickstart.md", 21)])
    assert "AttributeError: module 'metrolen' has no attribute 'convert'" in err
    _, _, err = run_sample(by_key[("docs/parsing.md", 22)])
    assert "TypeError" in err and "strict" in err


def test_source_does_not_explain_its_own_drift() -> None:
    source = (FIXTURE_DIR / "metrolen" / "__init__.py").read_text(encoding="utf-8").lower()
    for word in ("v1", "version 1", "renamed", "alias", "removed", "deprecated", "strict", "convert("):
        assert word not in source, word


def test_changelog_discloses_only_some_changes() -> None:
    changelog = (FIXTURE_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "convert_units" in changelog and "3 decimal places" in changelog
    assert "strict" not in changelog, "drift 3 must only be findable by running"
    assert "UNITS" not in changelog, "the decoy must not be explained"


def test_fixture_is_small() -> None:
    files = [p for p in FIXTURE_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    total = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in files)
    assert total < 200, total
