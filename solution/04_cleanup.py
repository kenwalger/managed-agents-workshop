"""Step 6: keep a local copy of the session, then delete it.

Deleting a session is permanent: its conversation, its sandbox, and the files the
agent wrote are gone. So this script records the session's events to
recordings/ first. A running session can't be deleted, so it is interrupted first.

The agent and environment are kept so you can run the lab again. To remove them
too, add --all (the agent is archived: agents can't be deleted, and archiving is
permanent).

Run:  uv run 04_cleanup.py [--all]      Check:  uv run check.py 6
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # solution/ sits one level below the shared modules

import argparse
import time

import anthropic

import lab_state
from lab_common import RECORDINGS_DIR, make_client, run_step
from replay import export


def delete_session(client: anthropic.Anthropic, session_id: str) -> None:
    """Delete the session permanently.

    :param client: An API client.
    :param session_id: The session ID.
    """
    client.beta.sessions.delete(session_id)


def wait_until_not_running(client: anthropic.Anthropic, session_id: str, seconds: float = 30) -> str:
    """Interrupt a running session and wait for it to stop.

    :param client: An API client.
    :param session_id: The session ID.
    :param seconds: How long to wait.
    :returns: The final status.
    """
    status = client.beta.sessions.retrieve(session_id).status
    if status == "running":
        print("The session is running. Interrupting it first...")
        client.beta.sessions.events.send(session_id, events=[{"type": "user.interrupt"}])
    deadline = time.monotonic() + seconds
    while status == "running" and time.monotonic() < deadline:
        time.sleep(1)
        status = client.beta.sessions.retrieve(session_id).status
    return status


def is_gone(client: anthropic.Anthropic, session_id: str) -> bool:
    """Confirm the session no longer exists.

    :param client: An API client.
    :param session_id: The session ID.
    :returns: True if retrieving it returns 404.
    """
    try:
        client.beta.sessions.retrieve(session_id)
    except anthropic.NotFoundError:
        return True
    return False


def main() -> None:
    """Record, delete, and confirm."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="also delete the environment and archive the agent")
    args = parser.parse_args()
    state = lab_state.load()
    client = make_client()

    session_id = state.get("session_id")
    if session_id and not is_gone(client, session_id):
        recording = RECORDINGS_DIR / f"{session_id}.jsonl"
        print(f"Recorded {export(client, session_id, recording)} events to {recording.relative_to(RECORDINGS_DIR.parent)}")
        lab_state.update(recording_path=str(recording))
        status = wait_until_not_running(client, session_id)
        if status == "running":
            raise SystemExit("The session is still running. Wait a moment and run this again.")
        delete_session(client, session_id)
    if session_id:
        if not is_gone(client, session_id):
            raise SystemExit(f"Session {session_id} still exists. Did delete_session() delete it?")
        print(f"Deleted session {session_id} (it now returns 404)")
        lab_state.update(session_id=None, deleted_session_id=session_id)

    for file_id in lab_state.load().get("uploaded_file_ids", []):
        try:
            client.files.delete(file_id)
        except anthropic.NotFoundError:
            pass
    if state.get("uploaded_file_ids"):
        print(f"Deleted {len(state['uploaded_file_ids'])} uploaded files")
        lab_state.update(deleted_file_ids=state["uploaded_file_ids"], uploaded_file_ids=None)

    if args.all:
        if state.get("environment_id"):
            client.beta.environments.delete(state["environment_id"])
            print(f"Deleted environment {state['environment_id']}")
        if state.get("agent_id"):
            client.beta.agents.archive(state["agent_id"])
            print(f"Archived agent {state['agent_id']} (agents can't be deleted)")
        lab_state.update(environment_id=None, agent_id=None, agent_version=None)
    else:
        print(f"Kept agent {state.get('agent_id')} and environment {state.get('environment_id')} for next time.")
    print("\nNext: uv run check.py 6")


if __name__ == "__main__":
    run_step(main)
