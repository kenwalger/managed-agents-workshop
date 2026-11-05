"""Generate the learner scripts from the reference solution.

Each learner script is its solution script with one YOUR TURN function replaced by
its docstring, TODO comments, and a NotImplementedError. tests/test_stubs.py fails
if the learner files drift from what this script generates.

Run from the repo root:  uv run solution/make_stubs.py
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

SOLUTION = Path(__file__).resolve().parent
ROOT = SOLUTION.parent

STUBS: dict[str, tuple[str, list[str], str]] = {
    "01_define.py": ("choose_permissions", [
        "TODO: return (tools, networking).",
        "TODO: tools is a list with one {\"type\": \"agent_toolset_20260401\", ...} entry. Decide which",
        "      built-in tools the task card needs, and turn the rest off (see the README's links).",
        "TODO: networking is the environment's networking block. Decide how much internet the",
        "      sandbox should reach.",
    ], "YOUR TURN (step 1): choose the agent's tools and the sandbox's network access in choose_permissions()."),
    "02_start.py": ("create_session", [
        "TODO: call client.beta.sessions.create(...) with agent=agent_id, environment_id=...,",
        "      resources=..., a title, and a spend cap:",
        "      budget={\"type\": \"limit\", \"max_list_cost\": {\"amount\": BUDGET_CENTS, \"currency\": \"USD\"}}",
        "TODO: return the session.",
    ], "YOUR TURN (step 2): create the session in create_session(). The README shows the call."),
    "steer.py": ("send_message", [
        "TODO: send one event with client.beta.sessions.events.send(session_id, events=[...]).",
        "TODO: the event is {\"type\": \"user.message\", \"content\": [{\"type\": \"text\", \"text\": text}]}.",
    ], "YOUR TURN (step 4): send the message in send_message(). The README shows the call."),
    "03_collect.py": ("download_outputs", [
        "TODO: list the session's files:",
        "      client.beta.files.list(scope_id=session_id, betas=[MANAGED_AGENTS_BETA])",
        "TODO: skip files whose .downloadable is False (your own uploads appear in the list too).",
        "TODO: save each with client.files.download(file.id).write_to_file(destination / file.filename)",
        "      and return the list of paths you saved.",
    ], "YOUR TURN (step 5): download the session's output files in download_outputs()."),
    "04_cleanup.py": ("delete_session", [
        "TODO: delete the session with client.beta.sessions.delete(session_id).",
    ], "YOUR TURN (step 6): delete the session in delete_session()."),
}

_PATH_HACK = re.compile(r"\nimport sys\nfrom pathlib import Path\n\nsys\.path\.insert\(0, .*\n")


def make_stub(source: str, function: str, todos: list[str], message: str) -> str:
    """Replace one function's body with a docstring, TODO comments, and a NotImplementedError.

    :param source: The solution script's text.
    :param function: The YOUR TURN function's name.
    :param todos: TODO comment lines (without the leading ``# ``).
    :param message: The NotImplementedError message.
    :returns: The learner script's text.
    """
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    lines = source.splitlines()
    docstring = node.body[0]
    body_start, body_end = docstring.end_lineno, node.end_lineno  # keep the docstring lines
    indent = " " * (node.col_offset + 4)
    stub = [f"{indent}# {todo}" for todo in todos] + [f"{indent}raise NotImplementedError(\"{message}\")"]
    text = "\n".join(lines[:body_start] + stub + lines[body_end:]) + "\n"
    text = _PATH_HACK.sub("", text)
    if re.search(r"\bPath\b", text):  # the script still uses Path, so keep its import
        text = text.replace("\nimport anthropic\n", "from pathlib import Path\n\nimport anthropic\n", 1)
    return text


def generate() -> dict[str, str]:
    """Build every learner script from its solution.

    :returns: File name to learner script text.
    """
    out = {}
    for name, (function, todos, message) in STUBS.items():
        source = (SOLUTION / name).read_text(encoding="utf-8")
        out[name] = make_stub(source, function, todos, message)
    return out


if __name__ == "__main__":
    for name, text in generate().items():
        (ROOT / name).write_text(text, encoding="utf-8")
        print(f"wrote {name}")
