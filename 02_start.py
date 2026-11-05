"""Step 2: start a session, load the library into its sandbox, and send the drift task.

A session is one run of your agent inside your environment. Creating it gives
you a session ID: your handle on a sandbox, a conversation, and a bill that
exist on Anthropic's servers until you delete them.

Run:  uv run 02_start.py      Check:  uv run check.py 2
Then open a second terminal for step 3: uv run watch.py
"""

from __future__ import annotations

import argparse
from typing import Any

import anthropic

import lab_state
from lab_common import (BUDGET_CENTS, FIXTURE_DIR, KIND_RULES, SANDBOX_FIXTURE, SANDBOX_OUTPUTS,
                        SANDBOX_SCHEMA, SCHEMA_PATH, console_url, make_client, run_step)

TASK_PROMPT = f"""\
A small Python library and its documentation are mounted read-only at {SANDBOX_FIXTURE}
(the library is in metrolen/, the docs are in docs/). Check whether the documentation
still matches the code.

1. Run every ```python sample in docs/*.md on its own, with PYTHONPATH={SANDBOX_FIXTURE},
   using python3. Capture stdout, stderr, and the exit status of each run.
2. Compare each run with the output the docs show for that sample.
3. Write {SANDBOX_OUTPUTS}/drift-report.json following the JSON Schema at {SANDBOX_SCHEMA}.
   Include one result for EVERY sample you ran, including samples that match.
   doc_file is relative to the fixture folder (for example docs/quickstart.md), and
   sample_line is the line number of the sample's opening ```python fence.
   For a sample that does not match, set kind by what you observed:
{chr(10).join(f"   - {kind}: {rule}" for kind, rule in KIND_RULES.items())}
4. Check the JSON loads with python3's json module.
5. Write {SANDBOX_OUTPUTS}/drift-report.md: a short table of every sample and its
   result, then one section per mismatch with the command, what happened, and the fix.
"""


def upload_files(client: anthropic.Anthropic) -> list[dict[str, Any]]:
    """Upload the fixture and the report schema, and describe where each is mounted.

    :param client: An API client.
    :returns: Session resources: one ``file`` entry per uploaded file.
    """
    uploads = [(path, f"/fixture/{path.relative_to(FIXTURE_DIR).as_posix()}")
               for path in sorted(FIXTURE_DIR.rglob("*"))
               if path.is_file() and "__pycache__" not in path.parts]
    uploads.append((SCHEMA_PATH, "/contract/report.schema.json"))
    resources = []
    for path, mount_path in uploads:
        uploaded = client.files.upload(file=path)
        lab_state.append("uploaded_file_ids", uploaded.id)  # saved at once, so cleanup can find it
        resources.append({"type": "file", "file_id": uploaded.id, "mount_path": mount_path})
    print(f"Uploaded {len(resources)} files")
    return resources


def create_session(client: anthropic.Anthropic, agent_id: str, environment_id: str,
                   resources: list[dict[str, Any]]) -> Any:
    """Create a session for the agent, with the files mounted and a spend cap.

    :param client: An API client.
    :param agent_id: The agent to run (its latest version is used).
    :param environment_id: The environment to run it in.
    :param resources: The file resources from :func:`upload_files`.
    :returns: The new session.
    """
    # TODO: call client.beta.sessions.create(...) with agent=agent_id, environment_id=...,
    #       resources=..., a title, and a spend cap:
    #       budget={"type": "limit", "max_list_cost": {"amount": BUDGET_CENTS, "currency": "USD"}}
    # TODO: return the session.
    raise NotImplementedError("YOUR TURN (step 2): create the session in create_session(). The README shows the call.")


def main() -> None:
    """Start a session and send the drift task."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--new", action="store_true", help="start a new session even if one is saved")
    args = parser.parse_args()

    state = lab_state.load()
    if "agent_id" not in state or "environment_id" not in state:
        raise SystemExit("No agent or environment saved yet. Run step 1 first: uv run 01_define.py")
    if state.get("session_id") and not args.new:
        raise SystemExit(f"A session is already saved ({state['session_id']}). Finish the lab with it, "
                         "or clean it up with uv run 04_cleanup.py. To start another anyway: --new")

    client = make_client()
    # Watch and steer records belong to one session; clear the previous session's.
    lab_state.update(watch_attachments=None, steers=None, recording_path=None)
    resources = upload_files(client)
    session = create_session(client, state["agent_id"], state["environment_id"], resources)
    lab_state.update(session_id=session.id, session_agent_version=session.agent.version)
    print(f"Created session {session.id} (agent version {session.agent.version}, "
          f"budget ${int(BUDGET_CENTS) / 100:.2f}, status {session.status})")

    client.beta.sessions.events.send(session.id, events=[
        {"type": "user.message", "content": [{"type": "text", "text": TASK_PROMPT}]},
    ])
    print("Sent the drift task. The agent is working now, on Anthropic's side.")
    print(f"\nWatch in the browser: {console_url(session.id)}")
    print("Watch in a terminal:  uv run watch.py      Then: uv run check.py 2")


if __name__ == "__main__":
    run_step(main)
