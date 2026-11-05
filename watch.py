"""Step 3: watch the agent work by streaming the session's events.

The agent loop runs on Anthropic's side. This script is only a viewer: close it
with Ctrl+C, reopen it, and the session carries on regardless. Each time it
attaches, it first prints what already happened (the history), then streams live.

Run:  uv run watch.py      Check (after watching twice):  uv run check.py 3
"""

from __future__ import annotations

import argparse
import time
from typing import Any

import anthropic

import lab_state
from lab_common import event_to_dict, format_event, list_events, make_client, run_step


def stamp(event: dict[str, Any]) -> str:
    """Return the HH:MM:SS part of an event's processed time.

    :param event: A plain event dictionary.
    :returns: A short time, or ``--:--:--`` for events still queued.
    """
    processed = event.get("processed_at")
    return processed[11:19] if processed else "--:--:--"


def show(event: Any, label: str) -> dict[str, Any]:
    """Print one event if the lab shows its type.

    :param event: An SDK event.
    :param label: ``earlier`` for history, ``live`` for streamed events.
    :returns: The event as a dictionary.
    """
    data = event_to_dict(event)
    line = format_event(data)
    if line:
        print(f"{label:>7} {stamp(data)}  {line}", flush=True)
    return data


def nothing_left_to_do(client: anthropic.Anthropic, session_id: str) -> tuple[bool, str]:
    """Report whether the session is idle with no message waiting to be processed.

    :param client: An API client.
    :param session_id: The session ID.
    :returns: ``(done, status)``.
    """
    status = client.beta.sessions.retrieve(session_id).status
    queued = [e for e in list_events(client, session_id, types=["user.message"]) if e.processed_at is None]
    return status in ("idle", "terminated") and not queued, status


def mark_detached(how: str) -> None:
    """Record when and how this watcher stopped watching.

    :param how: ``ctrl-c`` or ``finished``.
    """
    state = lab_state.load()
    if state.get("watch_attachments"):
        state["watch_attachments"][-1].update(detached_at=lab_state.now(), how=how)
        lab_state.save(state)


def watch(client: anthropic.Anthropic, session_id: str) -> None:
    """Attach to the session: print the history, then stream live events until there's nothing left.

    :param client: An API client.
    :param session_id: The session ID.
    """
    with client.beta.sessions.events.stream(session_id) as stream:
        # Open the stream first, then read the history, so nothing falls in the gap.
        history = list_events(client, session_id)
        seen = {event.id for event in history}
        lab_state.append("watch_attachments", {"attached_at": lab_state.now(), "history_events": len(history)})
        print(f"Attached to {session_id}. Catching up on {len(history)} earlier events:\n", flush=True)
        for event in history:
            show(event, "earlier")
        done, status = nothing_left_to_do(client, session_id)
        if done:
            print(f"\nThe session is {status} and nothing is queued. It did all of the above "
                  "without a watcher attached. Send it more work with steer.py.", flush=True)
            mark_detached("finished")
            return
        print("\n--- live (Ctrl+C to detach; the session keeps running) ---", flush=True)
        for event in stream:
            if getattr(event, "id", None) in seen or event.type in ("event_start", "event_delta"):
                continue
            seen.add(event.id)
            data = show(event, "live")
            if event.type == "session.status_terminated":
                break
            if event.type == "session.status_idle":
                reason = (data.get("stop_reason") or {}).get("type")
                if reason == "budget_reached":
                    print("\nThe session reached its spend cap and paused. See the README's troubleshooting.")
                    break
                if reason == "requires_action":
                    continue
                time.sleep(1.5)  # the idle event can arrive just before the status is queryable
                if nothing_left_to_do(client, session_id)[0]:
                    print("\nThe agent finished its turn and nothing else is queued.", flush=True)
                    break
    mark_detached("finished")


def main() -> None:
    """Attach to the saved session (or one given on the command line)."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("session_id", nargs="?", help="defaults to the session in .lab-state.json")
    args = parser.parse_args()
    session_id = args.session_id or lab_state.load().get("session_id")
    if not session_id:
        raise SystemExit("No session saved yet. Run step 2 first: uv run 02_start.py")
    client = make_client()
    try:
        watch(client, session_id)
    except KeyboardInterrupt:
        mark_detached("ctrl-c")
        print("\nDetached. The session keeps running on Anthropic's side. Reattach: uv run watch.py")


if __name__ == "__main__":
    run_step(main)
