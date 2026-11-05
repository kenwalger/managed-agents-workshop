"""Step 5: download the agent's reports from the sandbox.

The agent wrote its reports inside the sandbox, on Anthropic's servers. Anything
it saves under /mnt/session/outputs/ can be listed and downloaded through the
Files API, scoped to your session.

Run:  uv run 03_collect.py      Check:  uv run check.py 5
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # solution/ sits one level below the shared modules

import time

import anthropic

import lab_state
from lab_common import MANAGED_AGENTS_BETA, OUTPUTS_DIR, REPORT_FILES, make_client, run_step


def download_outputs(client: anthropic.Anthropic, session_id: str, destination: Path) -> list[Path]:
    """Download every file the session wrote to /mnt/session/outputs/.

    :param client: An API client.
    :param session_id: The session ID.
    :param destination: The local folder to save into.
    :returns: The paths written.
    """
    saved = []
    files = client.beta.files.list(scope_id=session_id, betas=[MANAGED_AGENTS_BETA])
    for file in files:
        if not file.downloadable:  # the list also includes your own uploads, which can't be downloaded
            continue
        path = destination / file.filename
        client.files.download(file.id).write_to_file(path)
        saved.append(path)
    return saved


def main() -> None:
    """Download the reports, retrying briefly while the files finish indexing."""
    session_id = lab_state.load().get("session_id")
    if not session_id:
        raise SystemExit("No session saved yet. Run step 2 first: uv run 02_start.py")
    client = make_client()
    status = client.beta.sessions.retrieve(session_id).status
    if status == "running":
        print("The agent is still working, so the reports may be incomplete. You can collect again later.")
    OUTPUTS_DIR.mkdir(exist_ok=True)
    saved: list[Path] = []
    for _ in range(6):  # files can take a few seconds to appear after the session goes idle
        saved = download_outputs(client, session_id, OUTPUTS_DIR)
        if set(REPORT_FILES) <= {path.name for path in saved}:
            break
        time.sleep(2)
    for path in saved:
        print(f"Saved {path.relative_to(OUTPUTS_DIR.parent)} ({path.stat().st_size} bytes)")
    if not saved:
        print("No output files yet. Is the agent finished? Check the watch terminal, then try again.")
        return
    print("\nNext: uv run check.py 5")


if __name__ == "__main__":
    run_step(main)
