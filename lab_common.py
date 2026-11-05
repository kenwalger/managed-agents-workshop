"""Shared helpers for the lab scripts.

You don't need to edit this file. It holds the settings every step uses, a
readable one-line format for session events, and the code that reads the doc
samples straight from the local fixture (never from anything the agent wrote).
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import anthropic
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent
FIXTURE_DIR = REPO_ROOT / "fixture"
SCHEMA_PATH = REPO_ROOT / "report.schema.json"
OUTPUTS_DIR = REPO_ROOT / "outputs"
RECORDINGS_DIR = REPO_ROOT / "recordings"

load_dotenv(REPO_ROOT / ".env")

#: The model the drift agent uses. Override with the LAB_MODEL environment variable.
MODEL = os.environ.get("LAB_MODEL", "claude-haiku-5-5")

#: Spend cap for one session, in US cents, as a string ("50" is $0.50).
BUDGET_CENTS = os.environ.get("LAB_BUDGET_CENTS", "50")

#: Beta header for Managed Agents. The SDK adds it automatically on
#: client.beta.agents/environments/sessions calls; only the session-scoped file
#: listing needs it passed explicitly.
MANAGED_AGENTS_BETA = "managed-agents-2026-04-01"

#: Where the fixture and the report contract appear inside the sandbox.
SANDBOX_FIXTURE = "/mnt/session/uploads/fixture"
SANDBOX_SCHEMA = "/mnt/session/uploads/contract/report.schema.json"
SANDBOX_OUTPUTS = "/mnt/session/outputs"

REPORT_FILES = ("drift-report.json", "drift-report.md")

#: How the agent must classify a drifted sample. The task prompt and check.py
#: both use this table, so the contract and the checker can't disagree.
KIND_RULES = {
    "missing_name": "non-zero exit and stderr ends with AttributeError, ImportError, or NameError",
    "bad_arguments": "non-zero exit and stderr ends with TypeError",
    "output_mismatch": "exit 0 but stdout (trimmed) differs from the documented output (trimmed)",
    "other_error": "any other failure",
}


def make_client() -> anthropic.Anthropic:
    """Create an API client. The key comes from ANTHROPIC_API_KEY (environment or .env).

    :returns: A configured client.
    :raises SystemExit: If no API key is set.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("No ANTHROPIC_API_KEY found. Copy .env.example to .env and add your key.")
    return anthropic.Anthropic()


def console_url(session_id: str) -> str:
    """Return the Console link for watching a session in the browser.

    :param session_id: The session ID.
    :returns: A URL. Set LAB_WORKSPACE if your key isn't in the Default workspace.
    """
    workspace = os.environ.get("LAB_WORKSPACE", "default")
    return f"https://platform.claude.com/workspaces/{workspace}/sessions/{session_id}"


def run_step(main: Callable[[], None]) -> None:
    """Run a script's main function and turn common failures into clear messages.

    :param main: The script's entry point.
    :raises SystemExit: With a readable message instead of a traceback.
    """
    try:
        main()
    except NotImplementedError as exc:
        raise SystemExit(f"\n{exc}\nOpen the file, find the YOUR TURN function, and fill it in.") from None
    except anthropic.APIStatusError as exc:
        raise SystemExit(f"\nAPI error {exc.status_code}: {exc.message}") from None


# --- Doc samples (read from the trusted local fixture only) -------------------


@dataclass(frozen=True)
class Sample:
    """One runnable code sample from the fixture's docs."""

    doc_file: str
    line: int
    code: str
    expected_output: str


def extract_samples(fixture_dir: Path = FIXTURE_DIR) -> list[Sample]:
    """Read every ```python block and the ```text block after it from the fixture docs.

    :param fixture_dir: The fixture folder (contains ``docs/``).
    :returns: Samples in file and line order. ``line`` is the 1-based line of the opening fence.
    """
    samples: list[Sample] = []
    for doc in sorted((fixture_dir / "docs").glob("*.md")):
        samples += samples_in(doc.read_text(encoding="utf-8"), f"docs/{doc.name}")
    return samples


def samples_in(markdown: str, doc_file: str) -> list[Sample]:
    """Read the ```python blocks, each with the ```text block after it, from one Markdown page.

    :param markdown: The page's text.
    :param doc_file: The name to record on each sample.
    :returns: The page's samples in order.
    """
    lines = markdown.splitlines()
    samples, i = [], 0
    while i < len(lines):
        if lines[i].strip() == "```python":
            start = i + 1
            end = next(k for k in range(start, len(lines)) if lines[k].strip() == "```")
            j = next((k for k in range(end + 1, len(lines)) if lines[k].strip() == "```text"), None)
            out_end = next((k for k in range(j + 1, len(lines)) if lines[k].strip() == "```"), len(lines)) if j else end
            expected = "\n".join(lines[j + 1:out_end]) if j else ""
            samples.append(Sample(doc_file, start, "\n".join(lines[start:end]), expected))
            i = out_end
        i += 1
    return samples


def run_sample(sample: Sample, fixture_dir: Path = FIXTURE_DIR, python: str = sys.executable,
               timeout: float = 20) -> tuple[int, str, str]:
    """Run one trusted sample locally with PYTHONPATH set to the fixture.

    Only call this with samples from :func:`extract_samples`. Never run code or
    commands taken from an agent's report.

    :param sample: A sample read from the local fixture.
    :param fixture_dir: The fixture folder.
    :param python: The interpreter to use.
    :param timeout: Seconds before the run is abandoned.
    :returns: ``(exit_status, stdout, stderr)``.
    """
    env = {**os.environ, "PYTHONPATH": str(fixture_dir), "PYTHONDONTWRITEBYTECODE": "1"}
    done = subprocess.run([python, "-c", sample.code], capture_output=True, text=True,
                          env=env, timeout=timeout, cwd=fixture_dir)
    return done.returncode, done.stdout, done.stderr


def symptom_kind(exit_status: int, stdout: str, stderr: str, expected_output: str) -> str | None:
    """Classify a sample run by its observed symptom, using :data:`KIND_RULES`.

    :param exit_status: The process exit status.
    :param stdout: Captured standard output.
    :param stderr: Captured standard error.
    :param expected_output: The output the docs show.
    :returns: A kind, or ``None`` if the run matches the docs.
    """
    if exit_status == 0:
        return None if stdout.strip() == expected_output.strip() else "output_mismatch"
    last = stderr.strip().splitlines()[-1] if stderr.strip() else ""
    if last.startswith(("AttributeError", "ImportError", "ModuleNotFoundError", "NameError")):
        return "missing_name"
    if last.startswith("TypeError"):
        return "bad_arguments"
    return "other_error"


# --- Events --------------------------------------------------------------------


def event_to_dict(event: Any) -> dict[str, Any]:
    """Convert an SDK event (or an already-plain dictionary) to plain JSON data.

    :param event: An event from the stream, the event list, or a recording.
    :returns: A dictionary.
    """
    if isinstance(event, dict):
        return event
    return event.to_dict(mode="json")


def _text_of(blocks: Any) -> str:
    if not isinstance(blocks, list):
        return ""
    return "\n".join(b.get("text", "") for b in blocks if isinstance(b, dict)).strip()


def _one_line(text: str, limit: int = 140) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def format_event(event: Any) -> str | None:
    """Describe an event in one line, or return None for events the lab doesn't show.

    :param event: An SDK event or a plain dictionary.
    :returns: A short description, or ``None``.
    """
    e = event_to_dict(event)
    kind = e.get("type")
    if kind == "agent.message":
        return f"agent:   {_one_line(_text_of(e.get('content')), 200)}"
    if kind == "agent.tool_use":
        tool_input = e.get("input") or {}
        detail = tool_input.get("command") or tool_input.get("file_path") or str(tool_input)
        return f"tool:    {e.get('name')}: {_one_line(str(detail))}"
    if kind == "agent.tool_result":
        text = _text_of(e.get("content"))
        if "Traceback" in text:
            error = [ln for ln in text.splitlines() if ln.strip()][-1]
            return f"result:  ERROR {_one_line(error)}"
        flag = "tool error: " if e.get("is_error") else ""
        return f"result:  {flag}{_one_line(text or '(no output)', 100)}"
    if kind == "user.message":
        queued = " (queued)" if e.get("processed_at") is None else ""
        return f"you:     {_one_line(_text_of(e.get('content')), 100)}{queued}"
    if kind == "user.interrupt":
        return "you:     interrupt"
    if kind == "session.status_running":
        return "session: running"
    if kind == "session.status_idle":
        return f"session: idle (stop reason: {(e.get('stop_reason') or {}).get('type')})"
    if kind == "session.status_terminated":
        return "session: terminated"
    if kind == "session.error":
        return f"session: ERROR {_one_line(str(e.get('error')))}"
    return None


def list_events(client: anthropic.Anthropic, session_id: str, **filters: Any) -> list[Any]:
    """Fetch a session's full event history, oldest first.

    :param client: An API client.
    :param session_id: The session ID.
    :param filters: Extra filters, for example ``types=["agent.tool_use"]``.
    :returns: Every matching event (the SDK follows pagination).
    """
    return list(client.beta.sessions.events.list(session_id, order="asc", **filters))
