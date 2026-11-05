# Project plan: Managed Agents workshop

**Due:** one calendar week from receipt (received Tuesday, November 3, 2026, so due by Tuesday, November 10). Confirm the exact deadline with Workwell.
**Budget:** about 6 focused hours. Keep a running timer and log actual time per phase; it goes in the design note.

## Deliverables

| # | Deliverable | Format | Notes |
|---|---|---|---|
| 1 | Session (20 min of material) | Markdown slides (Marp conventions) with speaker notes and SVG diagrams, in `presentation/` | Built to be presented by someone else. The demo runs live by default, with a recorded run as the fallback. |
| 2 | Hands-on lab (60 min of learner time) | Repo of small Python scripts, run with `uv run` | Setup, guided steps, checkpoints, one work-it-out step, a stretch goal. A learner can finish alone. |
| 3 | Instructor hand-off guide | About one page, Markdown | For an instructor new to Managed Agents, preparing one to two days ahead. |
| 4 | Design note | Markdown | Key decisions, where I overrode the model, pilot results, time spent. |

## Lab domain: the Documentation Drift Agent

Learners operate an agent that checks whether a small library's documentation still matches its code. The agent runs the code samples from the docs inside its sandbox, finds the ones that no longer work, and writes a drift report.

**Why this domain:** the task genuinely needs a sandboxed agent. Finding drift means *running* the samples, and that's something you can't do by calling Claude. It also gives the session its clearest answer to "when should I use Managed Agents?"

### The fixture

A tiny, fictional, pure-Python library at version 2, with documentation that was written for version 1: `metrolen`, a length-conversion library. Seven doc samples on four pages: three drifts, one decoy, three passing controls. A partial changelog discloses drifts 1 and 2 and hints at the decoy, but not drift 3, so only running finds it. Compatible with Python 3.10 and newer (the sandbox's default `python3` is 3.11).

| Item | What it is | What the agent should do |
|---|---|---|
| Drift 1 | A function was renamed in v2; the docs still use the old name | Flag it: the sample raises `AttributeError` |
| Drift 2 | A default value changed; the docs' sample output no longer matches | Flag it: the sample runs but prints different output |
| Drift 3 | A parameter was removed or its return type changed | Flag it: the sample raises `TypeError` or breaks downstream |
| Decoy | A doc sample that looks suspicious but still works correctly | **Not** flag it |

Design rules for the fixture:

- **Pure Python, standard library only.** The sandbox can run it with `PYTHONPATH` and no `pip install`, so no network access is needed.
- **Every drift is something the sandbox can prove.** Each one makes a sample fail or print the wrong output, so the agent finds it by running code, not by guessing from the text.
- **The decoy tests for false positives.** An agent that flags everything shouldn't pass.
- **Small.** Three or four doc pages, one module, under about 200 lines total, so a run takes minutes, not tens of minutes.

### The output contract

The task prompt asks the agent to write two files:

- **`drift-report.json`**, in a schema the lab gives learners: one entry per finding, with the doc file, the sample, what happened, and the suggested fix. The checkpoints read this file, so grading is deterministic even though the agent's wording isn't.
- **`drift-report.md`**, a human-readable version for people.

Requiring structured output an agent can be checked against is itself a teaching point: it's how you verify an agent's work without reading every word of it.

## Lab format: scripts, not a notebook

The lab is a set of small Python scripts, one per step, run from the terminal with `uv run`.

**Why:** operating an agent means the agent runs on its own while clients attach to it. Scripts show that directly. Learners stream events in one terminal (`watch.py`), steer from a second (`steer.py`), and can close the watcher and reopen it while the session keeps running. A notebook can't show this well: a running cell blocks the kernel, so steering mid-run would need threads or stopping and restarting the stream.

**Also:**

- **It matches the audience.** Engineers who ship this will write scripts and services, not notebooks.
- **It avoids the notebook problems from the first lab:** hidden kernel state, Jupyter tokens, and wrong-kernel errors.
- **The state file teaches something.** Each step saves the agent, environment, and session IDs to `.lab-state.json`. Those IDs are the learner's handles on resources that live on the server.

**Checkpoints:** `uv run check.py <step>` prints `PASS` or `NOT YET` with a hint, and `uv run check.py summary` lists every step at the end. The README shows the expected output for each step, which takes the place of a notebook's rendered output on GitHub.

**Fallback:** if phase 1 shows you can't disconnect from and reconnect to a running session, switch to a notebook and drop the two-terminal design. Log the switch in the design note.

## The six hours

| Phase | Budget | Work | Output |
|---|---|---|---|
| 1. Quickstart | 0:45 | Run the official quickstart. Then test the fixture question: can the sandbox run a small local Python package? Log every point of friction. | Friction log; demo rehearsal done |
| 2. Design | 0:45 | Outcomes, lab arc, work-it-out step, stretch goal, fixture spec, report schema. Write decisions into the design note as they're made. | Lab outline; fixture spec; design note rows 3 to 6 |
| 3. Lab build | 2:00 | Write the Claude Code brief. Build the fixture and reference solution first, then the learner version. Review each stage. | Working lab repo |
| 4. Session | 1:00 | Deck, live demo script, replay fallback. | Session ready to present |
| 5. Pilot | 0:45 | Do the lab as a learner, timed, from a clean setup. Run the drift task at least three times to measure how reliably the agent finds all three drifts. Fix what the pilot shows. | Pilot notes; hit rate; fixes |
| 6. Hand-off | 0:30 | One-page guide; finish the design note. | Guide; final design note |
| | **5:45** | | |

**If running over:** cut the stretch goal before cutting the pilot. An untested lab is a bigger risk than a missing stretch.

## Phase 1: verify in the quickstart

Answer these before designing anything. The answers decide the lab.

**Platform basics**

- [ ] How long does creating an environment take? Can learners create one during the lab, or should setup create it ahead of time?
- [ ] What do the events look like? Which event types will learners actually need to read?
- [ ] How do steering and interrupting work in practice? How quickly does the agent respond?
- [ ] How does a session end? What does idle look like, and how does resuming work?
- [ ] How are the built-in tools turned on or restricted? Can web access be turned off?
- [ ] Is there a way to cap a session's run time or cost?
- [ ] What does one short session cost? Estimate the per-learner cost for the guide.
- [ ] Python SDK: which version, and does it set the beta header automatically?
- [ ] Which errors are likely? (Wrong IDs, missing beta header, a session that's already ended.)
- [ ] Can a past session's event history be fetched in full? (Needed for the demo fallback.)
- [ ] Can you disconnect from a running session's event stream and reconnect without affecting the session? (The two-terminal lab design depends on it.)
- [ ] Can a second client send a steering event while the first is streaming?

**Specific to the drift fixture**

- [ ] How do you put a folder of files (the library and its docs) into the sandbox?
- [ ] Does the sandbox have Python 3.12 or newer? Can it run the package with `PYTHONPATH` alone?
- [ ] How do you get `drift-report.json` and `drift-report.md` back out of the sandbox?
- [ ] Without web access, does the agent still complete the task? (It should; nothing in it needs the web.)
- [ ] Run a rough version of the drift task once: how long does it take, and does the agent find the drifts unprompted?

**Fallback:** if the sandbox can't run the fixture cleanly, switch to the Incident Investigation domain (a planted root cause in log files). The lab arc stays the same; only the fixture changes. Log the switch in the design note.

## Lab arc (draft)

One section per row of the "calling vs. operating" table. Each ends with a "you know it worked when..." checkpoint.

| Step | Script | Row of the table | Learner does | Checkpoint (draft) |
|---|---|---|---|---|
| 0. Setup | `check.py 0` | | Key, SDK, a check that the beta API is reachable | Setup check passes |
| 1. Define | `01_define.py` | You decide the tools | Create the drift agent (system prompt, tools) and an environment | Both IDs saved to `.lab-state.json`; the agent has only the tools you chose |
| 2. Start | `02_start.py` | A session with a lifecycle | Start a session, load the fixture, send the drift task | The session is running and the fixture files are in the sandbox |
| 3. Watch | `watch.py` (terminal 1) | The loop runs on Anthropic's side | Stream events and print the ones that matter. Close the watcher and reopen it. | Watched at least twice; the reattached watcher replays the history, including the agent running a doc sample and the error it got back. Works even if the run finished while detached (it often takes under a minute). |
| 4. Continue | `steer.py` (terminal 2) | Steer or interrupt mid-run | Send the same session more work (write corrected doc pages) | A second message was handled in the same session without starting over. The check reports whether it arrived mid-run or after idle; both pass. Interrupt is an optional drill (`steer.py --interrupt`). |
| 5. Collect | `03_collect.py` | State lives on the server | Get both report files out of the sandbox | Platform: both reports downloaded and schema-valid. Agent analysis (informational `AGENT:` lines): three drifts found, decoy not flagged, evidence reproduced locally from the trusted fixture. |
| 6. Clean up | `04_cleanup.py` | Cost is per session | Delete the session; confirm it's gone | No sessions left running |
| Stretch | `check.py stretch` | | Review the corrected doc pages the agent wrote in step 4 | The fixed pages no longer contain the drifts (checked statically; agent-written code is never run locally) |

### Work-it-out step

**Default: least privilege (step 1).** The lab tells learners what the task needs (run code, read and write files) but not which tools to enable or how much network access to allow. They decide, and the checkpoint confirms that bash is on, web tools are off, and the sandbox has no egress; step 5 confirms the task still succeeds. It's deterministic to check and teaches a real operating habit. **Chosen.**

**Alternatives, if the quickstart shows something more confusing:**

- **Get the output back (step 5):** the agent wrote the reports in the sandbox; the learner works out how to retrieve them.
- **Steer correctly (step 4):** the agent heads the wrong way; the learner works out how to redirect it without starting over.

### Stretch goal: candidates

- **Write the fix (chosen, adapted):** the step 4 continuation has the agent write corrected doc pages and run them in its sandbox; `check.py stretch` checks them statically. They are never run locally, because the agent wrote them.
- **Scheduled drift check:** a scheduled deployment that runs the check weekly. This is the most realistic use of scheduling, but include it only if it can be shown quickly and torn down safely.
- **Resume:** now the core of step 4, not a stretch.

## Session plan (20 minutes, draft)

| Minutes | Segment |
|---|---|
| 0 to 3 | The shift: from calling Claude to operating an agent |
| 3 to 7 | When to use it: Messages API, Agent SDK, or Managed Agents. The test: does the task need the agent to *do* things somewhere, for a while? |
| 7 to 11 | How it works: agent, environment, session, events |
| 11 to 17 | Live demo with the `solution/` scripts in two terminals: the agent runs the doc samples, hits the broken ones, writes the report, then handles a continuation in the same session (Haiku often finishes in under a minute). Fallback: replay `recordings/demo.jsonl`, clearly labeled as a recording. |
| 17 to 20 | What operating means for you (cleanup, cost, data handling), then on to the lab |

**Optional callback (one line):** "With the Messages API, you'd call Claude to look something up. Here, the agent does the work: it runs the code and reports back."

**Demo:** `uv run replay.py recordings/demo.jsonl` replays a known-good recorded run from a local file, with no API key or network needed. It is the fallback for the live demo: switch to it if nothing appears in the watcher within about 30 seconds, or anything errors. Instructors can record their own rehearsal with `uv run replay.py --export <session-id>` (and `04_cleanup.py` records every session before deleting it). Verified in phases 1 and 3.

Using the lab's scripts for the demo means the instructor rehearses with exactly the tools learners will use.

## Instructor guide (outline)

- What the workshop teaches, in two sentences
- Prep checklist for one to two days ahead (run the lab once; record the demo session)
- Timeline for the session and the lab
- The three places learners get stuck, and what to say (likely one: learners need two terminals open, both in the project folder)
- When the demo breaks: the replay fallback
- **When the agent misses a drift or flags the decoy:** treat it as a teaching moment. This is why the report is structured and checked, and why you verify agents rather than trusting them. Point to the pilot hit rate in the design note.
- Cost per learner, and cleanup at the end
- Likely questions ("Why not the Agent SDK?", "Is this ZDR-eligible?", "Couldn't a script find these drifts?")

## Lab repository layout (draft)

```
managed-agents-lab/
├── README.md              # outcomes, prerequisites, setup, each step with expected output, troubleshooting
├── pyproject.toml         # uv project, Python 3.12+
├── .env.example
├── 01_define.py           # create agent + environment (YOUR TURN: choose the tools)
├── 02_start.py            # start session, load fixture, send the drift task
├── watch.py               # stream events (terminal 1)
├── steer.py               # send a steering message (terminal 2)
├── 03_collect.py          # pull the reports out of the sandbox
├── 04_cleanup.py          # delete the session; confirm it's gone
├── replay.py              # replay a recorded session's events (demo fallback)
├── check.py               # checkpoints: check.py <step>, check.py summary
├── lab_state.py           # reads and writes .lab-state.json (agent, environment, session IDs)
├── lab_common.py          # shared settings, event formatting, trusted sample extraction
├── solution/              # reference versions of the learner scripts
├── fixture/
│   ├── <library>/         # v2 source
│   └── docs/              # v1-era documentation with planted drift
├── report.schema.json     # the output contract
├── recordings/demo.jsonl  # known-good recorded run (demo fallback)
├── tests/                 # offline tests only
├── presentation/          # slides.md (+ exported slides.html, slides.pdf), speaker-notes.md, diagrams/
└── docs/
    └── instructor-guide.md
```

`.lab-state.json` is gitignored. Learner stubs follow the same rules as the first lab: they raise `NotImplementedError("YOUR TURN: ...")` until filled in.

## Lab-authoring rules (carried over from the first lab)

- Build the reference solution first; derive the learner version from it.
- Every learner stub fails loudly with a "YOUR TURN" message.
- Label intended failures "EXPECTED TO FAIL."
- Checkpoints say what's wrong and how to fix it, not just that something failed.
- A summary at the end shows what's done.
- Pilot it before anyone else sees it.

## Submission checklist

- [ ] Session, lab repo, guide, and design note all present
- [ ] Lab runs from a clean clone with the README's instructions
- [ ] No API keys anywhere in the repo or its history
- [ ] Design note: actual hours, the hit rate from the pilot, and overrides listed
- [ ] All links work with view access
- [ ] Every session created during the build is deleted
- [ ] Sent to Workwell before the deadline