"""Read and write ``.lab-state.json``.

The IDs in this file are your handles on resources that live on Anthropic's
servers: the agent, the environment, the session, and the files you uploaded.
Lose the file and the resources still exist (and a running session still costs
money), so every script saves an ID the moment it creates something.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_PATH = Path(__file__).resolve().parent / ".lab-state.json"


def now() -> str:
    """Return the current UTC time in ISO 8601 format.

    :returns: A timestamp such as ``2026-11-05T16:40:00.123+00:00``.
    """
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def load(path: Path = STATE_PATH) -> dict[str, Any]:
    """Load the lab state.

    :param path: Where the state file lives.
    :returns: The saved state, or an empty dictionary if there is none yet.
    """
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save(state: dict[str, Any], path: Path = STATE_PATH) -> None:
    """Write the lab state.

    :param state: The full state to save.
    :param path: Where the state file lives.
    """
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def update(path: Path = STATE_PATH, **changes: Any) -> dict[str, Any]:
    """Change some keys in the lab state and save it.

    :param path: Where the state file lives.
    :param changes: Keys to set. A value of ``None`` removes the key.
    :returns: The updated state.
    """
    state = load(path)
    for key, value in changes.items():
        if value is None:
            state.pop(key, None)
        else:
            state[key] = value
    save(state, path)
    return state


def append(key: str, item: Any, path: Path = STATE_PATH) -> dict[str, Any]:
    """Append an item to a list in the lab state and save it.

    :param key: The list's key, for example ``"uploaded_file_ids"``.
    :param item: The item to append.
    :param path: Where the state file lives.
    :returns: The updated state.
    """
    state = load(path)
    state.setdefault(key, []).append(item)
    save(state, path)
    return state


def record_check(step: str, passed: bool, path: Path = STATE_PATH) -> None:
    """Remember the latest result of a platform checkpoint for ``check.py summary``.

    :param step: The step name, for example ``"3"``.
    :param passed: Whether the platform checkpoint passed.
    :param path: Where the state file lives.
    """
    state = load(path)
    state.setdefault("checkpoints", {})[step] = {"passed": passed, "at": now()}
    save(state, path)
