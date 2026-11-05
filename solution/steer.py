"""Step 4: send the session more work from the command terminal, without starting over.

If the agent is still running, your message waits until its current step
finishes, then the agent takes it into account mid-run. If the agent has already
finished, your message starts a new turn in the same session: same sandbox,
same files, same conversation. Either way, nothing restarts.

Run:  uv run steer.py                 (sends the step 4 continuation below)
      uv run steer.py "your message"  (sends your own message)
      uv run steer.py --interrupt     (optional drill: stop the agent mid-step)
Check:  uv run check.py 4
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # solution/ sits one level below the shared modules

import argparse

import anthropic

import lab_state
from lab_common import make_client, run_step

CONTINUE_PROMPT = (
    "Now fix the docs. For each docs page with a sample that did not match, write a corrected "
    "copy of the whole page to /mnt/session/outputs/fixed-<page>.md (for example "
    "fixed-quickstart.md). Run every sample in your corrected pages the same way as before and "
    "confirm each prints the output the page shows. Then add a short Fixes section to "
    "drift-report.md listing what you changed."
)


def send_message(client: anthropic.Anthropic, session_id: str, text: str) -> None:
    """Send one user message to the session.

    :param client: An API client.
    :param session_id: The session ID.
    :param text: What you want the agent to do.
    """
    client.beta.sessions.events.send(session_id, events=[
        {"type": "user.message", "content": [{"type": "text", "text": text}]},
    ])


def send_interrupt(client: anthropic.Anthropic, session_id: str) -> None:
    """Ask the agent to stop what it's doing now. The session stays usable.

    :param client: An API client.
    :param session_id: The session ID.
    """
    client.beta.sessions.events.send(session_id, events=[{"type": "user.interrupt"}])


def main() -> None:
    """Send a message (or an interrupt) to the saved session."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", nargs="?", default=CONTINUE_PROMPT)
    parser.add_argument("--interrupt", action="store_true", help="stop the agent instead of sending a message")
    args = parser.parse_args()
    session_id = lab_state.load().get("session_id")
    if not session_id:
        raise SystemExit("No session saved yet. Run step 2 first: uv run 02_start.py")

    client = make_client()
    status = client.beta.sessions.retrieve(session_id).status
    if args.interrupt:
        send_interrupt(client, session_id)
        lab_state.append("steers", {"sent_at": lab_state.now(), "status_at_send": status, "interrupt": True})
        print(f"Sent an interrupt while the session was {status}. Watch it go idle in the watch terminal.")
        return

    send_message(client, session_id, args.message)
    lab_state.append("steers", {"sent_at": lab_state.now(), "status_at_send": status, "interrupt": False})
    if status == "running":
        print("The agent is running. Your message is queued and takes effect after its current step.")
    else:
        print(f"The session was {status}. Your message starts a new turn in the same session.")
    print("Follow it in the watch terminal (uv run watch.py), then: uv run check.py 4")


if __name__ == "__main__":
    run_step(main)
