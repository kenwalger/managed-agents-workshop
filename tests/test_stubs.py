"""Offline tests: learner scripts are derived from the solution and stop with a clear YOUR TURN."""

from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("make_stubs", ROOT / "solution" / "make_stubs.py")
make_stubs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_stubs)


@pytest.mark.parametrize("name", list(make_stubs.STUBS))
def test_learner_file_matches_generated_stub(name: str) -> None:
    generated = make_stubs.generate()[name]
    assert (ROOT / name).read_text(encoding="utf-8") == generated, \
        f"{name} drifted from the solution. Run: uv run solution/make_stubs.py"


@pytest.mark.parametrize("name", list(make_stubs.STUBS))
def test_stub_body_is_docstring_and_raise_only(name: str) -> None:
    function = make_stubs.STUBS[name][0]
    tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    assert len(node.body) == 2
    assert isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)
    raised = node.body[1]
    assert isinstance(raised, ast.Raise) and raised.exc.func.id == "NotImplementedError"
    assert raised.exc.args[0].value.startswith("YOUR TURN")


def test_only_one_your_turn_per_script() -> None:
    for name in make_stubs.STUBS:
        assert (ROOT / name).read_text(encoding="utf-8").count("raise NotImplementedError") == 1, name


def test_stub_stops_with_a_clear_message(tmp_path: Path) -> None:
    """The learner sees YOUR TURN, not a traceback. Uses a fake key; no API call is made."""
    env = {**os.environ, "ANTHROPIC_API_KEY": "test-key-not-real"}
    done = subprocess.run([sys.executable, str(ROOT / "01_define.py")], capture_output=True, text=True,
                          cwd=tmp_path, env=env, timeout=60)
    assert done.returncode != 0
    assert "YOUR TURN (step 1)" in done.stderr
    assert "Traceback" not in done.stderr
