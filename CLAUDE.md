# CLAUDE.md: Managed Agents lab ("From Calling Claude to Operating an Agent")

## What this project is

A 60-minute hands-on lab for engineers and solutions architects who have used the Messages API (and maybe the Agent SDK) but have never shipped an agent on **Claude Managed Agents**. Depth is 201: skip API-key basics and spend the time on the operating model.

**Theme:** what changes when you move from *calling* Claude to *operating* an agent. Every step maps to one row:

| Calling Claude | Operating an agent |
|---|---|
| A request and a response | A session with a lifecycle: create, run, idle, resume, delete |
| You write the loop | The loop runs on Anthropic's side; you watch it through events |
| Stateless; you resend the history | State lives on the server: history, sandbox files, outputs |
| You read the response | You stream events, steer, or interrupt mid-run |
| Your code runs the tools | You decide which tools it may use, and it runs them in a sandbox |
| Cost is per call | Cost and time are per session, so cleanup matters |

**The task learners run:** a Documentation Drift Agent. It loads a small library and its docs into the sandbox, runs every code sample in the docs, finds the ones that no longer match the code, and writes a drift report.

**Who teaches it:** another instructor, not the author. The lab must work for a learner with no one in the room.

## The most important rule: verify the API, don't guess it

Managed Agents is in **beta** and newer than most of your training data. Do not rely on memory for method names, request shapes, event types, or SDK behavior.

- Read the docs before writing any API code: start at <https://platform.claude.com/docs/en/managed-agents/overview> and the quickstart, sessions, tools, and reference pages it links to.
- Read **Verified platform behavior** below first. It summarizes what was confirmed against the live API while building this lab (it replaced the planned `notes/quickstart-notes.md`), and it is the source of truth where it conflicts with memory. The approved design is reflected in `docs/project-plan.md` and in this brief.
- All endpoints need the `managed-agents-2026-04-01` beta header. Check whether the installed SDK sets it automatically.
- If the docs and the plan disagree, **stop and say so** rather than working around it.

## Verified platform behavior

Confirmed against the live API in November 2026 with `anthropic` 2.5.0. Re-verify anything you change; the platform is in beta.

- **SDK and headers:** the SDK adds `managed-agents-2026-04-01` to `client.beta.agents/environments/sessions` calls. The session-scoped file listing needs it passed explicitly: `client.beta.files.list(scope_id=session_id, betas=["managed-agents-2026-04-01"])`.
- **Files:** a file mounted at `mount_path: /fixture/x.py` appears read-only at `/mnt/session/uploads/fixture/x.py`. There's no folder upload: one upload and one resource per file. The agent's outputs go to `/mnt/session/outputs/`.
- **Collecting outputs:** the session-scoped list also includes the mounted inputs, marked `downloadable: false` (downloading one returns 400). Outputs can take a few seconds after idle to be listed; retry briefly.
- **Sandbox:** the default `python3` is 3.11; 3.10 to 3.13 are installed. With `limited` networking and no hosts or package managers, there is no egress (DNS fails, `pip` finds nothing). The agent may try `pip` anyway.
- **Lifecycle:** a finished turn goes `idle` with `end_turn`; only archiving makes a session `terminated`. A running session can't be deleted or archived (400). `user.interrupt` brings it to idle in about a second, also with `end_turn`.
- **Steering:** a `user.message` sent while running is queued until the in-flight tool calls finish, then applied in the same turn. Sent after idle, it starts a new turn in the same session with the same sandbox.
- **Streaming:** the stream has no replay. Open it, list the history, and dedupe by event ID. A watcher that attaches to an idle session gets no events, so check status first. Several watchers can stream one session at once, and closing one doesn't affect the session.
- **Windows Ctrl+C:** a watcher detaches only after the next chunk arrives on the stream (several seconds).
- **Agents:** they can't be deleted, only archived (permanent). An update with an unchanged configuration does not create a new version; a changed one does, and new sessions use the latest.
- **Budgets:** a session at its budget goes idle with `budget_reached` and refuses new `user.message` events (400). The request that crosses the cap still completes, so the cost can overshoot by one request.
- **Errors:** a malformed ID returns 400 "The request was invalid"; a well-formed ID of a deleted resource returns 404.
- **Cost and time:** a full lab run on `claude-haiku-5-5` takes about a minute of agent time and costs about $0.01 at list prices.

## Tech constraints

- Python 3.12+. Use `uv` for everything (`uv add`, `uv run`). No pip, no `requirements.txt`.
- Runtime: `anthropic` (2.5.0 or newer; it sets the beta header itself), `python-dotenv`, `jsonschema` (validates the report). Dev: `pytest`.
- API key from `ANTHROPIC_API_KEY`, loaded from `.env`. Commit `.env.example`, never `.env`.
- The model is one constant, overridable by environment variable: `LAB_MODEL`, default `claude-haiku-5-5` (approved; re-confirm after the Phase 5 hit-rate test). The session budget is `LAB_BUDGET_CENTS`, default `50` ($0.50).
- The author works on Windows with PowerShell. Every README command must work there.

## Code style

- Type hints and Sphinx-style docstrings (`:param:`, `:returns:`, `:raises:`) on every function.
- Clarity over brevity in learner-facing code. Learners copy what they see.
- American English. No em-dashes anywhere: code, comments, Markdown.

## Repository layout

```
managed-agents-lab/
├── README.md              # outcomes, prerequisites, setup, each step with expected output, troubleshooting
├── pyproject.toml
├── .env.example
├── 01_define.py           # create agent + environment (YOUR TURN: choose the tools)
├── 02_start.py            # start session, load fixture, send the drift task
├── watch.py               # stream events (terminal 1)
├── steer.py               # send a steering message (terminal 2)
├── 03_collect.py          # pull the reports out of the sandbox
├── 04_cleanup.py          # delete the session; confirm it's gone
├── replay.py              # replay a recorded session's events (demo fallback)
├── check.py               # checkpoints: check.py <step>, check.py summary
├── lab_state.py           # reads and writes .lab-state.json
├── lab_common.py          # shared settings, event formatting, trusted sample extraction
├── solution/              # reference versions of the learner scripts
├── fixture/
│   ├── <library>/         # v2 source
│   └── docs/              # v1-era docs with planted drift
├── report.schema.json     # the output contract
├── recordings/demo.jsonl  # known-good recorded run; the live demo's fallback (other recordings gitignored)
├── presentation/          # slides.md (+ exported slides.html, slides.pdf), speaker-notes.md, diagrams/
├── docs/instructor-guide.md  # one-page instructor handoff
└── tests/                 # offline tests only

`solution/make_stubs.py` generates the learner scripts from `solution/`; a test fails if they drift.
```

Gitignored: `.env`, `.lab-state.json`, `outputs/`, `recordings/*` (except `demo.jsonl`), `notes/`, `build-log.md`, `commit-message.txt`.

## The fixture

A tiny, fictional, **pure-Python, standard-library-only** library at version 2, with docs written for version 1. Name: `metrolen`, a length-conversion library (`unitwise` was rejected: it is a real Ruby units gem).

| Item | Example | Expected agent behavior |
|---|---|---|
| Drift 1 | A function renamed in v2 (`convert` became `convert_units`); the sample uses attribute access (`metrolen.convert(...)`) | Flag: sample raises `AttributeError` |
| Drift 2 | A default changed (precision 2 became 3) | Flag: sample runs, printed output doesn't match the docs |
| Drift 3 | A parameter removed (`parse_quantity(..., strict=True)`); not mentioned in the changelog | Flag: sample raises `TypeError` |
| Decoy | `metrolen.UNITS`, which the changelog makes look replaced by `supported_units()` but v2 kept | **Do not** flag |

Rules: runnable with `PYTHONPATH` alone (no install, no network). Every drift must be provable by running a sample, not by reading. Keep it under about 200 lines total, so a run takes minutes. Each doc sample shows its expected output, so drift 2 is detectable.

## The output contract

The task prompt tells the agent to write:

- `drift-report.json`, matching `report.schema.json`: one result per sample run, passing samples included (so a skipped decoy can be told from a passed one), with the doc file, the sample's fence line, the command, exit status, stdout, stderr, whether it matches, a `kind` classified by the observed symptom, and a suggested fix.
- `drift-report.md`, a readable version.

Keep the schema minimal. Checkpoints identify drifts by doc file and kind, never by the agent's wording.

## Scripts and state

- Each script does one step and saves any IDs it creates to `.lab-state.json` through `lab_state.py`. The IDs are the learner's handles on server-side resources, so say that in the README.
- `watch.py` and `steer.py` run in separate terminals at the same time. Closing and reopening `watch.py` must not affect the session. This is the core demonstration of "operating," so verify it works.
- `04_cleanup.py` records the session's events to `recordings/` first, interrupts it if running, deletes it, and confirms it's gone. The agent and environment are reused across runs (`--all` removes them; agents can only be archived).
- `watch.py` replays history on every attach and exits cleanly when the session is idle with nothing queued, so short runs and late reattachment both work.

## Checkpoints (`check.py`)

- `uv run check.py <step>` prints `PASS: ...` or `NOT YET: ...` with a specific hint for platform checkpoints, and `AGENT: ...` lines for agent-analysis results, which never gate. `uv run check.py summary` lists every step.
- The step 1 check confirms the agent has the tools the task needs and that **web tools are off** (the work-it-out step is choosing the tools).
- The step 5 platform check passes when both reports are downloaded and the JSON is schema-valid. Drifts found, decoy, false positives, and evidence are `AGENT:` lines. Evidence is reproduced only by running samples parsed from the trusted local fixture, never anything from the agent's report.
- The step 4 check passes when a second message was processed in the same session and its turn finished, whether it arrived mid-run or after idle.
- Hints for API plumbing can give exact code. Hints for the lesson itself (which tools, why) say what's wrong and why, without the answer.

## Lab-authoring rules

- Build the reference solution first; derive the learner versions from it.
- Learner stubs contain only a docstring, TODO comments, and `raise NotImplementedError("YOUR TURN: ...")`.
- Label any step that fails on purpose "EXPECTED TO FAIL" in the README.
- Offline tests (fixture behavior, schema, check logic) must never call the API.

## Live API rules

- **Ask before running anything that creates agents, environments, or sessions.** These cost money and the author is tracking spend.
- **Delete every session you create** before ending a stage, and report what you deleted.
- Never print or log the API key.

## Build stages

Stop after each stage, summarize, and wait.

1. **Fixture and contract (offline):** the library, the docs with planted drift, `report.schema.json`, and tests proving each drift really fails and the decoy really works.
2. **Reference solution:** `solution/` scripts working end to end against the live API (with permission), plus `replay.py`.
3. **Learner version and checks:** stubs, `check.py`, `lab_state.py`, tests for the check logic.
4. **README:** setup (PowerShell first), each step with expected output, troubleshooting.

## Reporting and git

- **Do not run `git add`, `git commit`, or `git push`.** At the end of each stage, write the commit message to `commit-message.txt` (subject of 72 characters or fewer, imperative mood, short body) and list the files to stage.
- Never add `Co-Authored-By`, `Claude-Session`, "Generated with Claude Code," or any other AI attribution.
- Append to `build-log.md` after each stage: what you built, anything in the docs that differed from this brief, and every place you chose differently than asked and why. The author uses this for the design note, so be specific.

## Definition of done

- `uv sync` then `uv run pytest` passes from a fresh clone, with no API calls.
- The solution scripts run end to end, and the agent finds all three drifts without flagging the decoy.
- The learner version stops at each YOUR TURN with a clear message.
- README setup works in PowerShell exactly as written.
- No sessions left running.