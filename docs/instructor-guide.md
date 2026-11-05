# Instructor guide (one page)

**What this teaches:** moving from *calling* Claude to *operating* a Managed Agents session: start it, watch it, send it more work, verify its report, clean up. A 20-minute session (`presentation/`) leads into a 60-minute lab (`README.md`).

**Prerequisites:** `uv` (installs Python 3.12 if needed), git or the repo ZIP, a Managed Agents API key, and two terminals (watch and command) in the repo folder.

**Prep, one to two days ahead:**
1. Clone the repo (or ZIP) to a short path; `uv sync` (first run: a minute or two); key in `.env`; `uv run check.py 0`.
2. Run the lab once with the `solution/` scripts (about 10 minutes, $0.01) until `uv run check.py summary` is all PASS, ending with `uv run solution/04_cleanup.py` so no session stays saved.
3. Read `presentation/speaker-notes.md`; rehearse the live demo, and the fallback: `uv run replay.py recordings/demo.jsonl`.

**Timeline:**

| Time | What |
|---|---|
| 0:00 to 0:20 | Session: slides 1 to 4; live demo on slides 4 to 9; handoff on slide 10 |
| 0:20 to 0:25 | Setup (step 0) |
| 0:25 to 1:10 | Steps 1 to 6: define 10, start 5, watch 8, continue 8, collect 7, clean up 5 |
| 1:10 to 1:20 | Buffer, the stretch goal, questions |

**Slides and demo:** present from `presentation/slides.pdf` (or `slides.html` in a browser); no Marp needed. Run the demo live with the `solution/` scripts (learner copies stop at YOUR TURN). If nothing appears in the watcher within about 30 seconds, or anything errors, switch to `uv run replay.py recordings/demo.jsonl` and say it's a recording of a previous run.

**Where learners get stuck, and what to say:**
- **`YOUR TURN` error, or step 1 failing with the defaults:** expected. For step 1, don't give the configuration; ask what the task card needs.
- **"My steer didn't change anything mid-run":** messages wait for the agent's in-flight tool calls, or start a new turn if it already finished. Both pass step 4.
- **Ctrl+C is slow on Windows:** it detaches when the next data arrives, which takes a few seconds.
- **The agent tries `pip install` and fails:** that's the no-egress sandbox from step 1 working.
- **The agent missed a drift or flagged the decoy:** they still pass; discuss why the report is checked.

**Recovery:**
- **`API error 400: The request was invalid`:** usually a mangled ID in `.lab-state.json`.
- **"Session no longer exists":** `uv run 02_start.py --new`.
- **"Cannot delete session while it is running":** run `uv run 04_cleanup.py` again; it interrupts first.
- **Spend cap reached (`budget_reached`):** clean up, then start a new session (cap: $0.50, `LAB_BUDGET_CENTS`).
- **A learner is badly behind:** let them copy that one function from `solution/`.

**Cleanup and cost:** learners run `uv run 04_cleanup.py`, then `uv run check.py 6`; at the end, `uv run 04_cleanup.py --all` deletes the environment and archives the agent. Expect $0.01 to $0.05 per learner on `claude-haiku-5-5`; idle sessions keep their data until deleted.
