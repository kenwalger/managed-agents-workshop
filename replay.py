"""Replay a recorded session from a local file, or record one from a live session.

Recordings are plain JSONL: one session event per line. 04_cleanup.py records
your session before deleting it, and recordings/demo.jsonl is a known-good run
for the instructor's demo fallback.

Replay:  uv run replay.py recordings/demo.jsonl [--speed 2]
Record:  uv run replay.py --export <session_id> [--out recordings/my-run.jsonl]
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from lab_common import RECORDINGS_DIR, event_to_dict, format_event, list_events, make_client, run_step

MAX_PAUSE_SECONDS = 3.0
_SECRET = re.compile(r"sk-ant-[A-Za-z0-9_\-]+")


def redact(value: Any) -> Any:
    """Replace anything that looks like an Anthropic API key, at any depth.

    :param value: Event data.
    :returns: The same data with key-like strings replaced.
    """
    if isinstance(value, str):
        return _SECRET.sub("[REDACTED]", value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def export(client: anthropic.Anthropic, session_id: str, out: Path) -> int:
    """Save a session's full event history to a local JSONL file.

    :param client: An API client.
    :param session_id: The session to record.
    :param out: Where to write the recording.
    :returns: The number of events written.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    events = list_events(client, session_id)
    with out.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(redact(event_to_dict(event))) + "\n")
    return len(events)


def load(path: Path) -> list[dict[str, Any]]:
    """Read a recording.

    :param path: A JSONL recording.
    :returns: The events, in order.
    """
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pauses(events: list[dict[str, Any]], speed: float = 1.0) -> list[float]:
    """Work out how long to wait before showing each event.

    :param events: Recorded events.
    :param speed: Playback speed (2 means twice as fast).
    :returns: One pause in seconds per event, capped at MAX_PAUSE_SECONDS.
    """
    result, previous = [], None
    for event in events:
        current = event.get("processed_at")
        moment = datetime.fromisoformat(current.replace("Z", "+00:00")) if current else None
        gap = (moment - previous).total_seconds() if moment and previous else 0.0
        result.append(min(max(gap, 0.0) / speed, MAX_PAUSE_SECONDS))
        previous = moment or previous
    return result


def play(path: Path, speed: float) -> None:
    """Print a recording at roughly its original pace.

    :param path: A JSONL recording.
    :param speed: Playback speed.
    """
    events = load(path)
    print(f"Replaying {len(events)} recorded events from {path} (speed {speed}x)\n", flush=True)
    for event, pause in zip(events, pauses(events, speed)):
        line = format_event(event)
        if line:
            time.sleep(pause)
            print(f"replay {(event.get('processed_at') or '')[11:19]}  {line}", flush=True)


def main() -> None:
    """Replay a file, or export a session to a file."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("recording", nargs="?", type=Path, help="a .jsonl recording to replay")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--export", metavar="SESSION_ID", help="record a live session instead")
    parser.add_argument("--out", type=Path, help="where --export writes (default recordings/<id>.jsonl)")
    args = parser.parse_args()
    if args.export:
        out = args.out or RECORDINGS_DIR / f"{args.export}.jsonl"
        count = export(make_client(), args.export, out)
        print(f"Recorded {count} events to {out}")
    elif args.recording:
        play(args.recording, args.speed)
    else:
        parser.error("give a recording to replay, or --export SESSION_ID")


if __name__ == "__main__":
    run_step(main)
