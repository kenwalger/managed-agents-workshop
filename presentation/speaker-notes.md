# Speaker notes: From calling Claude to operating an agent

**Total:** 20 minutes, 10 slides. Times are cumulative.

## Demo modes

**Default: live.** Run the `solution/` scripts against the API (the learner copies stop at YOUR TURN). Live runs vary: the agent may finish before you reattach or steer, and its tool calls differ from run to run. Narrate what actually happens.

**Fallback: the recorded run.** `uv run replay.py recordings/demo.jsonl` replays a sanitized recording of a real lab session from November 5, 2026 (`claude-haiku-5-5`): the drift check, then a continuation turn. It needs no API key or network and takes under a minute.

**The switch rule:** if nothing appears in the watcher within about 30 seconds, or anything errors, switch to the recording. Say: "Here's a recording of a previous run of exactly this. Nothing is executing now." The screen agrees: the first line reads `Replaying 96 recorded events`, and every line starts with `replay` and the original time. After switching, follow the **Recording** notes on each slide.

**Before you start:**
- Two terminals in the repository folder, a **watch terminal** and a **command terminal**, with `.env` holding your key.
- `uv run check.py 1` passes (the agent and environment exist).
- No session is saved; if one is, run `uv run solution/04_cleanup.py`.
- Keep `uv run replay.py recordings/demo.jsonl` typed and ready in a third window.

**If you're running long:** compress slide 3 to one sentence, and say only the first and third bullets of slide 9. Don't cut slide 8: it carries the lab's main habit.

---

### 1. Title (0:00 to 1:00)

**Purpose:** frame the shift.

"You've all *called* Claude: send a request, get a response, and if there are tools, you run the loop. Today you'll *operate* an agent: start something that runs on its own, on Anthropic's side, watch it, send it more work, check what it produced, and clean up after it."

Name the example in one line: an agent that checks whether a library's documentation still matches its code by running every sample. "The library is fictional and tiny on purpose. Don't learn it; learn the operating model."

### 2. Three ways to put Claude to work (1:00 to 3:30)

**Purpose:** the "when to use it" answer, and when not to.

- Walk the table one row at a time, across the columns. The rows that change are *who runs the loop* and *where state lives*.
- With the Messages API, you hold a response. With the Agent SDK, you hold a running program on your own infrastructure. With Managed Agents, you hold a session ID: a handle on a sandbox, a conversation, and a bill on Anthropic's side.
- The test: if the task needs an agent to *do* things somewhere, for a while, without you hosting it, Managed Agents fits. Finding drift means running code, so this task needs a sandbox; a single Messages API call couldn't prove anything.
- **When not to use it** (one sentence): a low-latency single call is a Messages API request; if you need to control every step of the loop, run it yourself; and because sessions store their state, Managed Agents isn't eligible for ZDR or HIPAA coverage.

**Likely question:** "Why not the Agent SDK?" You'd host the loop and the execution environment yourself. Managed Agents runs both for you, and you operate it through IDs and events.

### 3. The resource model (3:30 to 5:30)

**Purpose:** five nouns, and which ones you keep.

- **Agent:** model, system prompt, tools. Versioned: change it and it gets a new version, and new sessions use the latest. An update that changes nothing doesn't create a new version.
- **Environment:** the sandbox template, including networking.
- **Session:** one run of an agent in an environment, with a spend cap. It holds the event history and a container where tools execute.
- **Files:** uploads mount read-only under `/mnt/session/uploads/`; the agent writes reports to `/mnt/session/outputs/`.
- **Events:** how you talk to it. You send `user.message`, and you read events back.

Summarize: agent and environment are defined once and reused; a session is one run; events are how you talk to it. Point at `.lab-state.json` on the left: "These IDs are your only handles. A running session costs money whether or not you're watching."

### 4. Least privilege (5:30 to 7:00)

**Purpose:** the work-it-out step, without giving away the answer.

- Stress that the defaults are permissive, and that's a choice you make, not a setting someone else made for you.
- The slide states the outcome only: no web tools, no network access out of the sandbox. Don't name the settings that produce it. Learners work those out in step 1.
- Tell the `pip install` story: it shows the agent will reach for the network if it can, and that the boundary held.

**Live, at the end of this slide (command terminal):** `uv run solution/02_start.py`. Say: "The task is sent. The agent is working now, and nobody is watching yet."

**Recording:** nothing to start; the replay begins on slide 5.

### 5. Start the session, then watch it (7:00 to 9:30)

**Purpose:** the lifecycle, and the stream as a view.

- On the diagram, a session starts **idle** and goes **running** when a message arrives. When a turn ends, it goes back to **idle**, ready for more work.
- **A failed turn is not the same as a terminated session.** If a turn hits an error, you see a `session.error` event, and that turn stops. The session is still a session, and you can look at it.
- **`terminated` is a separate, final status:** no new events are accepted. In this lab you reach it only by archiving; the platform can also terminate a session after an unrecoverable error.
- **Neither a failed turn nor `terminated` deletes anything.** The session resource and its history stay until *you* delete it, and only deletion returns 404.
- Runtime is billed only while running.

**Live (watch terminal):** `uv run watch.py`. It prints `earlier` events, then `live` ones. Point at a `tool: bash` line running a sample and the `result:` that follows: "It ran the samples; it didn't guess." The agent may already be finished; that's normal and sets up the next slide. **If nothing appears within about 30 seconds, switch to the recording.**

**Recording:** run `uv run replay.py recordings/demo.jsonl` and say it's a recording of a previous run. It finishes in under a minute and stays on screen; narrate slides 5 to 7 from it.
- **Point at the start:** `session: running`, then `you:` (the task).
- **Point at the sample runs:** the `tool: bash` line that writes and runs `/tmp/run_samples.py`, its `result:` line, then the agent's "Seven samples ran; three fail to match." This agent batched all seven samples into one script; live runs often run them one by one.
- **Point at the blocked install:** the `pip install jsonschema` attempt failing (no egress).

### 6. Detach, reattach, recover (9:30 to 11:30)

**Purpose:** "closing the watcher doesn't affect the session" and how to reconnect without losing events.

- The stream is a view. Closing it does not stop, pause, or interrupt the session.
- The stream doesn't replay, so a reconnecting client lists the history and skips what it has seen. That's the code on the slide, and what `watch.py` does.
- An idle session sends no new events; `watch.py` checks the status and exits rather than waiting forever.

**Live:** press Ctrl+C in the watch terminal (on Windows it can take a few seconds), then run `uv run watch.py` again. The second attach replays the history.

**Recording:** a recording can't show a live detach. Say: "In the lab, you'll do this yourself in step 3: Ctrl+C, then reopen, and the history is still there."

**Don't say:** "Ctrl+C pauses the agent" or "the session stops when you disconnect." Neither is true.

### 7. Send more work to the same session (11:30 to 14:00)

**Purpose:** continuation versus mid-run steering.

- **Mid-run:** a message is queued until the agent's in-flight tool calls finish, then taken into account at its next step, in the same turn. In testing that wait was 13.8 seconds. It is not immediate.
- **After idle:** the message starts a new turn in the same session, with the same sandbox, files, and history.
- **Interrupt** is different: it stops the agent within about a second, and the session stays usable. It's an optional drill in the lab.

**Live (command terminal):** `uv run solution/steer.py`. The script prints whether the session was running or idle when the message was sent. Show the new turn in the watch terminal with `uv run watch.py`.

**Recording:** scroll the replay output to the second `you:` line, the continuation ("Now fix the docs..."). In this recording it arrived after the first turn finished, so it started a new turn; point at the `write: .../fixed-*.md` lines that follow. "Same session, same sandbox: it edited files it had created earlier."

**Say:** "The lab's check passes either way. Which one you get depends on timing, and the check tells you."

### 8. Claims versus evidence (14:00 to 16:30)

**Purpose:** the habit the lab is built around.

- **The report is a claim.** Schema-valid means well-formed, not correct.
- **`AGENT:` lines compare the claim with ground truth**, which `check.py` gets by running the trusted fixture samples on this machine. It never runs commands or code from the agent's report: that's untrusted output.
- **The fixture has a decoy:** a sample that looks outdated but works. Flagging it would be a false positive.

**Live:** `uv run solution/03_collect.py`, then `uv run check.py 5`. Read the `PASS` line, then the `AGENT:` lines.

**Recording:** show this output from the recorded run's checkpoint, and say it's from that prior run:

```text
PASS: both reports downloaded; drift-report.json matches the contract
AGENT: coverage: reported 7 of 7 doc samples
AGENT: drifts found: 3 of 3, kind correct for 3
AGENT: decoy: correctly reported as matching the docs
AGENT: false positives: 0
AGENT: evidence reproduced locally: 7 of 7
```

**Don't promise results.** In testing, the agent found 3 of 3 drifts and passed the decoy in two runs. Say exactly that. If a learner's agent misses something, they still pass the platform checkpoint, and the miss is the lesson.

### 9. Done running is not done (16:30 to 18:30)

**Purpose:** a completed run versus an operationally finished session.

- "Finished" is idle. Idle doesn't cost runtime, but the session still exists, with its data, until you delete it.
- **The budget is a guardrail, not an exact stop:** the request that crosses it still completes.
- **Keep what you need before you delete:** deletion is permanent. `04_cleanup.py` records the session first; that's how the fallback recording was made.
- **Agents can only be archived,** so the lab reuses one agent across runs.

**Live:** `uv run solution/04_cleanup.py`. It saves a recording, deletes the session, confirms 404, and deletes the uploads.

**Recording:** describe the cleanup from the slide. If you started a live session before switching, clean it up after the presentation with `uv run solution/04_cleanup.py`.

### 10. Your turn (18:30 to 20:00)

**Purpose:** a clean handoff into the lab.

- Two terminals, both in the repository folder: the watch terminal and the command terminal.
- `YOUR TURN` messages are expected until you fill in that step's function.
- Step 1 is the one you work out yourself; the README gives code shapes for the others.
- `AGENT:` lines never block you.
- Stretch: `uv run check.py stretch` reads the agent's fixed docs; it never runs them.
- Start with `uv run check.py 0`.
