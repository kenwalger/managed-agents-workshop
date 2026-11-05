"""Checkpoints for each lab step.

Two kinds of result:
  PASS / NOT YET  platform checkpoints: did you operate the platform correctly?
  AGENT:          what the agent found. Informational only: the agent can miss
                  things, which is exactly why its report is structured and checked.

Run:  uv run check.py <0-6 | stretch | summary>
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any, Callable

import anthropic
from jsonschema import Draft202012Validator

import lab_state
from lab_common import (OUTPUTS_DIR, REPORT_FILES, SCHEMA_PATH, Sample, event_to_dict, extract_samples,
                        list_events, make_client, run_sample, samples_in, symptom_kind)

DECOY_DOC = "docs/units.md"
WEB_TOOLS = ("web_search", "web_fetch")
SAMPLE_ERROR = re.compile(r"\b(?:AttributeError|ImportError|NameError|TypeError): [^\\\"]+")
Result = tuple[bool, list[str]]


# --- Pure helpers (unit-tested offline) ------------------------------------------


def effective_tools(agent: dict[str, Any]) -> dict[str, bool]:
    """Work out which built-in tools an agent really has enabled.

    :param agent: The agent as a dictionary (from ``agents.retrieve``).
    :returns: Tool name to enabled flag, for every tool the toolset mentions.
    """
    enabled: dict[str, bool] = {}
    for tool in agent.get("tools") or []:
        if tool.get("type") != "agent_toolset_20260401":
            continue
        default = (tool.get("default_config") or {}).get("enabled", True)
        for name in ("bash", "read", "write", "edit", "glob", "grep", "web_search", "web_fetch"):
            enabled[name] = default
        for config in tool.get("configs") or []:
            enabled[config["name"]] = config.get("enabled", default)
    return enabled


def permission_problems(agent: dict[str, Any], environment: dict[str, Any]) -> list[str]:
    """Explain what's wrong with the step 1 choices, without giving the answer.

    :param agent: The agent as a dictionary.
    :param environment: The environment as a dictionary.
    :returns: One hint per problem (empty when the choices are sound).
    """
    tools = effective_tools(agent)
    problems = []
    if not tools.get("bash"):
        problems.append("The agent can't run code, so it could only guess at drift by reading. "
                        "The task card says every finding must come from running a sample.")
    if any(tools.get(name) for name in WEB_TOOLS):
        problems.append("Your agent can reach the web, but nothing in this task needs it. Every enabled "
                        "tool is something a fetched page or a confused agent could misuse, and web "
                        "search costs money.")
    net = (environment.get("config") or {}).get("networking") or {}
    if net.get("type") != "limited" or net.get("allow_package_managers") or net.get("allowed_hosts"):
        problems.append("Code in the sandbox can reach the internet. The library is standard-library "
                        "only, so there's nothing to download, and open egress is how data leaves a sandbox.")
    return problems


def report_problems(report_path: Path, markdown_path: Path, schema: dict[str, Any]) -> list[str]:
    """Platform validation for step 5: files present, JSON valid against the contract.

    :param report_path: The downloaded drift-report.json.
    :param markdown_path: The downloaded drift-report.md.
    :param schema: The report schema.
    :returns: One message per problem (empty when the reports are usable).
    """
    missing = [p.name for p in (report_path, markdown_path) if not p.exists() or p.stat().st_size == 0]
    if missing:
        return [f"Missing or empty: {', '.join(missing)}. Run uv run 03_collect.py after the agent goes idle."]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"drift-report.json isn't valid JSON ({exc.msg} at line {exc.lineno})."]
    errors = sorted(Draft202012Validator(schema).iter_errors(report), key=lambda e: list(e.path))
    if errors:
        return [f"Schema: {'/'.join(map(str, e.path)) or '(top level)'}: {e.message}" for e in errors[:3]]
    markdown = markdown_path.read_text(encoding="utf-8")
    absent = sorted({r["doc_file"] for r in report["results"] if not r["matches_docs"]
                     and r["doc_file"] not in markdown and Path(r["doc_file"]).name not in markdown})
    if absent:
        return [f"drift-report.md doesn't mention {', '.join(absent)}, which the JSON reports as drifted."]
    return []


def match_results(report: dict[str, Any], samples: list[Sample]) -> dict[tuple[str, int], dict[str, Any]]:
    """Pair each fixture sample with the agent's result for it (same file, line within 2).

    :param report: The parsed drift report.
    :param samples: Samples from the local fixture.
    :returns: ``(doc_file, line)`` to the agent's result, for samples the agent reported.
    """
    matched = {}
    for sample in samples:
        candidates = [r for r in report.get("results", [])
                      if r.get("doc_file") == sample.doc_file and abs(r.get("sample_line", -99) - sample.line) <= 2]
        if candidates:
            matched[(sample.doc_file, sample.line)] = min(candidates, key=lambda r: abs(r["sample_line"] - sample.line))
    return matched


def analyze(report: dict[str, Any], samples: list[Sample],
            truth: dict[tuple[str, int], tuple[int, str, str]]) -> list[str]:
    """Compare the agent's report with ground truth. Informational: never gates.

    ``truth`` comes from running the trusted fixture samples locally. Nothing in
    the agent's report (including its ``command`` fields) is ever executed.

    :param report: The parsed drift report.
    :param samples: Samples from the local fixture.
    :param truth: ``(doc_file, line)`` to ``(exit_status, stdout, stderr)`` from local runs.
    :returns: Lines starting with ``AGENT:``.
    """
    matched = match_results(report, samples)
    true_kind = {(s.doc_file, s.line): symptom_kind(*truth[(s.doc_file, s.line)], s.expected_output) for s in samples}
    drifts = [k for k, kind in true_kind.items() if kind]
    lines = [f"AGENT: coverage: reported {len(matched)} of {len(samples)} doc samples"]

    found = [k for k in drifts if k in matched and matched[k].get("matches_docs") is False]
    right_kind = [k for k in found if matched[k].get("kind") == true_kind[k]]
    missed = [f"{d} line {n}" for d, n in drifts if (d, n) not in found]
    lines.append(f"AGENT: drifts found: {len(found)} of {len(drifts)}, kind correct for {len(right_kind)}"
                 + (f" (missed: {', '.join(missed)})" if missed else ""))

    decoy = [k for k in true_kind if k[0] == DECOY_DOC]
    for key in decoy:
        result = matched.get(key)
        if result is None:
            lines.append("AGENT: decoy: not reported, so there's no evidence it was run")
        elif result.get("matches_docs") is True:
            lines.append("AGENT: decoy: correctly reported as matching the docs")
        else:
            lines.append("AGENT: decoy: FLAGGED as drift, a false positive")
    false_pos = [f"{d} line {n}" for (d, n), kind in true_kind.items()
                 if kind is None and (d, n) in matched and matched[(d, n)].get("matches_docs") is False]
    lines.append(f"AGENT: false positives: {len(false_pos)}" + (f" ({', '.join(false_pos)})" if false_pos else ""))

    reproduced, differs = 0, []
    for key, result in matched.items():
        exit_status, stdout, _ = truth[key]
        same = (result.get("exit_status") == 0) == (exit_status == 0)
        if same and exit_status == 0:
            same = str(result.get("stdout", "")).strip() == stdout.strip()
        reproduced += same
        if not same:
            differs.append(f"{key[0]} line {key[1]}")
    lines.append(f"AGENT: evidence reproduced locally: {reproduced} of {len(matched)}"
                 + (f" (differs: {', '.join(differs)})" if differs else ""))

    consistent = sum(
        symptom_kind(r.get("exit_status", 0), str(r.get("stdout", "")), str(r.get("stderr", "")),
                     str(r.get("expected_output", ""))) == r.get("kind")
        for r in matched.values())
    lines.append(f"AGENT: kind agrees with the agent's own evidence: {consistent} of {len(matched)}")

    verified = [k for k in found if matched[k].get("fix_verified") is not None]
    lines.append(f"AGENT: fixes the agent verified by running them (fix_verified): {len(verified)} of {len(found)}")
    return lines


def tool_calls_while_detached(events: list[dict[str, Any]], attachments: list[dict[str, Any]]) -> int:
    """Count agent tool calls processed while no watcher was attached.

    :param events: Session events as dictionaries.
    :param attachments: ``watch_attachments`` from the lab state.
    :returns: The count. An attachment with no detach time counts as attached until the next one.
    """
    def when(text: str) -> datetime:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))

    windows = []
    for i, attachment in enumerate(attachments):
        end = attachment.get("detached_at") or (attachments[i + 1]["attached_at"] if i + 1 < len(attachments) else None)
        windows.append((when(attachment["attached_at"]), when(end) if end else datetime.max.replace(tzinfo=timezone.utc)))

    return sum(1 for e in events if e.get("type") == "agent.tool_use" and e.get("processed_at")
               and not any(start <= when(e["processed_at"]) <= end for start, end in windows))


# --- Steps ----------------------------------------------------------------------


def _session(state: dict[str, Any]) -> str:
    session_id = state.get("session_id")
    if not session_id:
        raise LookupError("No session saved. Run uv run 02_start.py.")
    return session_id


def step_0() -> Result:
    """Setup: key, SDK version, API reachable."""
    lines = []
    sdk = tuple(int(part) for part in version("anthropic").split(".")[:2])
    if sdk < (2, 5):
        return False, [f"NOT YET: anthropic {version('anthropic')} is too old. Run uv sync."]
    client = make_client()
    client.beta.agents.list(limit=1)
    lines.append(f"PASS: API key found (not shown), anthropic {version('anthropic')}, Managed Agents API reachable")
    return True, lines


def step_1() -> Result:
    """Define: agent and environment exist and follow least privilege."""
    state = lab_state.load()
    if not state.get("agent_id") or not state.get("environment_id"):
        return False, ["NOT YET: no agent or environment saved. Run uv run 01_define.py."]
    client = make_client()
    agent = client.beta.agents.retrieve(state["agent_id"]).to_dict(mode="json")
    environment = client.beta.environments.retrieve(state["environment_id"]).to_dict(mode="json")
    if agent.get("archived_at"):
        return False, ["NOT YET: the saved agent is archived. Run uv run 01_define.py to create a new one."]
    problems = permission_problems(agent, environment)
    if problems:
        return False, [f"NOT YET: {p}" for p in problems]
    tools = effective_tools(agent)
    optional = ", ".join(f"{n} {'on' if tools.get(n) else 'off'}" for n in ("read", "write", "edit", "glob", "grep"))
    return True, [f"PASS: agent version {agent['version']} can run code, has no web tools, and its sandbox has no egress",
                  f"INFO: other tools: {optional}. Either way is defensible: bash can read and write files too."]


def step_2() -> Result:
    """Start: session exists with a budget, the files mounted, and the task sent."""
    state = lab_state.load()
    client = make_client()
    session = client.beta.sessions.retrieve(_session(state)).to_dict(mode="json")
    expected = len(state.get("uploaded_file_ids", []))
    problems = []
    if not session.get("budget"):
        problems.append("The session has no budget. A budget can only be set when the session is created.")
    if expected == 0 or len(session.get("resources") or []) != expected:
        problems.append(f"Expected {expected} mounted files, found {len(session.get('resources') or [])}.")
    if not list_events(client, session["id"], types=["user.message"]):
        problems.append("No task was sent yet. uv run 02_start.py sends it right after creating the session.")
    if problems:
        return False, [f"NOT YET: {p}" for p in problems]
    cap = int(session["budget"]["max_list_cost"]["amount"]) / 100
    return True, [f"PASS: session {session['id']} is {session['status']}, with {expected} files mounted and a ${cap:.2f} cap"]


def step_3() -> Result:
    """Watch: watched at least twice; the agent ran a sample and hit an error."""
    state = lab_state.load()
    client = make_client()
    events = [event_to_dict(e) for e in list_events(client, _session(state))]
    attachments = state.get("watch_attachments", [])
    lines = []
    bash_calls = [e for e in events if e["type"] == "agent.tool_use" and e.get("name") == "bash"]
    errors = [match.group(0) for e in events if e["type"] == "agent.tool_result"
              for match in [SAMPLE_ERROR.search(json.dumps(e.get("content")))] if match]
    if len(attachments) < 2:
        lines.append(f"NOT YET: the watcher has attached {len(attachments)} time(s). Close it with Ctrl+C, then run "
                     "uv run watch.py again: the point is that the session doesn't depend on your watcher.")
    if not bash_calls:
        lines.append("NOT YET: the agent hasn't run any code yet. Give it a moment, then watch again.")
    if lines:
        return False, lines
    lines.append(f"PASS: watched {len(attachments)} times; the agent made {len(bash_calls)} bash calls")
    lines.append(f"INFO: tool calls the agent made while no watcher was attached: "
                 f"{tool_calls_while_detached(events, attachments)}")
    if errors:
        lines.append(f"INFO: first error a doc sample produced: {errors[0]}")
    return True, lines


def step_4() -> Result:
    """Continue: a second message was processed and its turn finished, in the same session."""
    state = lab_state.load()
    client = make_client()
    events = [event_to_dict(e) for e in list_events(client, _session(state))]
    order = {e["id"]: i for i, e in enumerate(events)}
    messages = [e for e in events if e["type"] == "user.message"]
    idles = [e for e in events if e["type"] == "session.status_idle"
             and (e.get("stop_reason") or {}).get("type") == "end_turn"]
    if len(messages) < 2:
        return False, ["NOT YET: only the original task has been sent. Send more work: uv run steer.py"]
    second = messages[1]
    if second.get("processed_at") is None or not any(order[i["id"]] > order[second["id"]] for i in idles):
        return False, ["NOT YET: your message is still being worked on. Wait until the watch terminal shows the "
                       "session idle, then check again."]
    first_idle = order[idles[0]["id"]]
    timing = ("arrived while the agent was running, and it was taken into account at the agent's next step"
              if order[second["id"]] < first_idle else
              "arrived after the first run finished, so it started a new turn")
    lines = [f"PASS: the same session handled {len(messages)} messages without starting over",
             f"INFO: your first follow-up {timing}"]
    if any(e["type"] == "user.interrupt" for e in events):
        lines.append("INFO: optional interrupt drill: done")
    return True, lines


def step_5() -> Result:
    """Collect: reports downloaded and valid. Agent analysis is printed but never gates."""
    report_path, markdown_path = (OUTPUTS_DIR / name for name in REPORT_FILES)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    problems = report_problems(report_path, markdown_path, schema)
    if problems:
        return False, [f"NOT YET: {p}" for p in problems]
    lines = ["PASS: both reports downloaded; drift-report.json matches the contract"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    samples = extract_samples()
    truth = {(s.doc_file, s.line): run_sample(s) for s in samples}
    return True, lines + analyze(report, samples, truth)


def step_6() -> Result:
    """Clean up: recording saved, session and uploads gone."""
    state = lab_state.load()
    if state.get("session_id"):
        return False, ["NOT YET: a session is still saved. Run uv run 04_cleanup.py."]
    deleted = state.get("deleted_session_id")
    if not deleted:
        return False, ["NOT YET: no session has been cleaned up yet. Run uv run 04_cleanup.py."]
    client = make_client()
    problems = []
    try:
        client.beta.sessions.retrieve(deleted)
        problems.append(f"Session {deleted} still exists.")
    except anthropic.NotFoundError:
        pass
    for file_id in state.get("deleted_file_ids", []):
        try:
            client.files.retrieve_metadata(file_id)
            problems.append(f"Uploaded file {file_id} still exists.")
        except anthropic.NotFoundError:
            pass
    recording = Path(state.get("recording_path", ""))
    if not recording.is_file():
        problems.append("No local recording. uv run 04_cleanup.py saves one before deleting.")
    if problems:
        return False, [f"NOT YET: {p}" for p in problems]
    kept = (f"INFO: still on the server for next time: agent {state['agent_id']}, environment "
            f"{state.get('environment_id')}. Remove them with uv run 04_cleanup.py --all."
            if state.get("agent_id") else "INFO: the environment is deleted and the agent archived (uv run 04_cleanup.py --all).")
    return True, [f"PASS: session deleted (404), uploads deleted, recording kept at {recording.name}", kept]


def fixed_docs_problems(pages: dict[str, str]) -> list[str]:
    """Statically check the agent's corrected doc pages. Never runs their code.

    :param pages: File name (for example ``fixed-quickstart.md``) to its text.
    :returns: One message per remaining drift or missing page.
    """
    problems = []
    for name in ("fixed-quickstart.md", "fixed-formatting.md", "fixed-parsing.md"):
        if name not in pages:
            problems.append(f"{name} not found in outputs/. Did the step 4 continuation finish? Then run uv run 03_collect.py.")
            continue
        samples = samples_in(pages[name], name)
        code = "\n".join(s.code for s in samples)
        if name == "fixed-quickstart.md" and ("metrolen.convert(" in code or "convert_units(" not in code):
            problems.append(f"{name}: the conversion sample still uses the old function name")
        if name == "fixed-formatting.md" and not any(
                "1.23456" in s.code and ("precision=2" in s.code or s.expected_output.strip() == "1.235 km")
                for s in samples):
            problems.append(f"{name}: the default-precision sample still shows output the code won't print")
        if name == "fixed-parsing.md" and "strict=" in code:
            problems.append(f"{name}: a sample still passes a parameter the function no longer accepts")
    return problems


def step_stretch() -> Result:
    """Stretch: the agent's fixed docs no longer contain the drifts. Reads only; never runs agent code."""
    pages = {p.name: p.read_text(encoding="utf-8") for p in OUTPUTS_DIR.glob("fixed-*.md")}
    problems = fixed_docs_problems(pages)
    if problems:
        return False, [f"NOT YET: {p}" for p in problems]
    return True, ["PASS: the fixed docs no longer contain the three drifts",
                  "INFO: this check reads the files; it never runs code the agent wrote. The agent ran it "
                  "in its sandbox, which is where untrusted code belongs."]


STEPS: dict[str, Callable[[], Result]] = {
    "0": step_0, "1": step_1, "2": step_2, "3": step_3, "4": step_4, "5": step_5, "6": step_6,
    "stretch": step_stretch,
}


def summary() -> None:
    """Print the latest platform result for every step."""
    results = lab_state.load().get("checkpoints", {})
    for step in STEPS:
        entry = results.get(step)
        mark = "not run" if entry is None else ("PASS" if entry["passed"] else "NOT YET")
        print(f"  step {step:<8} {mark}")
    steers = lab_state.load().get("steers", [])
    print(f"  optional  interrupt drill {'done' if any(s.get('interrupt') for s in steers) else 'skipped'}")


def main() -> None:
    """Run one checkpoint, or the summary."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", choices=[*STEPS, "summary"])
    args = parser.parse_args()
    if args.step == "summary":
        summary()
        return
    try:
        passed, lines = STEPS[args.step]()
    except LookupError as exc:
        passed, lines = False, [f"NOT YET: {exc}"]
    except anthropic.NotFoundError:
        passed, lines = False, ["NOT YET: the saved session no longer exists. Start a new one: uv run 02_start.py --new"]
    except anthropic.BadRequestError as exc:
        passed, lines = False, [f"NOT YET: the API rejected a saved ID ({exc.message}). Check .lab-state.json."]
    lab_state.record_check(args.step, passed)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
