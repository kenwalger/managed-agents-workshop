# Presentation: From calling Claude to operating an agent

A 20-minute instructor-led session that leads into the 60-minute lab in the repository root.

| File | What it is |
|---|---|
| `slides.md` | 10 slides in Markdown, readable as-is on GitHub |
| `speaker-notes.md` | Timing, talk track, demo steps, and cautions for each slide |
| `diagrams/*.svg` | Resource model, session lifecycle, and steering timeline (editable SVG) |
| `../docs/instructor-guide.md` | The one-page instructor handoff |

## Presenting

**Present from `slides.pdf`** (any PDF viewer, full screen), or open `slides.html` in a browser. Both are exported from `slides.md` and need no tools; keep `slides.html` next to the `diagrams/` folder, which it loads the diagrams from.

To edit, change `slides.md`, which uses [Marp](https://marp.app/) conventions (`---` between slides, `marp: true` in the front matter); Marp is not a project dependency. Then re-export or present it directly:

- Open it in VS Code with the Marp extension and present from the preview.
- Re-export with Marp CLI: `npx @marp-team/marp-cli presentation/slides.md --html --allow-local-files -o presentation/slides.html`, and the same with `--pdf -o presentation/slides.pdf`.
- With no tools at all, present the Markdown and the SVGs directly from GitHub.

## Timing

The demo runs live by default, with the `solution/` scripts. If nothing appears in the watcher within about 30 seconds, or anything errors, switch to the recorded run (`uv run replay.py recordings/demo.jsonl`, under a minute, no key or network) and say it's a recording of a previous run.

| Slide | Minutes | Live demo (default) | Fallback: recording |
|---|---|---|---|
| 1 Title | 0:00 to 1:00 | | |
| 2 Three ways to put Claude to work | 1:00 to 3:30 | | |
| 3 The resource model | 3:30 to 5:30 | | |
| 4 Least privilege | 5:30 to 7:00 | `solution/02_start.py` at the end | |
| 5 Start the session, then watch it | 7:00 to 9:30 | `watch.py` | Run the replay; narrate turn 1 |
| 6 Detach, reattach, recover | 9:30 to 11:30 | Ctrl+C, `watch.py` again | None (learners do it in step 3) |
| 7 Send more work to the same session | 11:30 to 14:00 | `solution/steer.py`, `watch.py` | Scroll to the continuation turn |
| 8 Claims versus evidence | 14:00 to 16:30 | `solution/03_collect.py`, `check.py 5` | Show the recorded `check.py 5` output |
| 9 Done running is not done | 16:30 to 18:30 | `solution/04_cleanup.py` | |
| 10 Your turn | 18:30 to 20:00 | | |

## Presentation-to-lab mapping

| Slide | Concept | Learning outcome | Lab step and checkpoint |
|---|---|---|---|
| 2 | Messages API, Agent SDK, or Managed Agents | When to use Managed Agents (session only) | None: discussed, not checked |
| 3 | Agent, environment, session, files, events | LO2: start a session and name what each ID refers to | Step 2: `check.py 2` |
| 4 | Least-privilege tools and egress | LO1: configure only the tools and access the task needs | Step 1: `check.py 1` (and step 5 shows the task still succeeds) |
| 5 | Lifecycle, streamed events | LO3: follow a run and point to a sample's error | Step 3: `check.py 3` |
| 6 | Detach, reattach, history | LO3: detach and reattach without affecting the run | Step 3: `check.py 3` (watched twice) |
| 7 | Mid-run steering versus continuation; interrupt | LO4: continue the same session and say when a message takes effect | Step 4: `check.py 4`; interrupt is an optional drill |
| 8 | Outputs, claims versus evidence | LO5: retrieve outputs and verify them against a contract | Step 5: `check.py 5` (platform gate) plus `AGENT:` lines (information only) |
| 9 | Budgets, cleanup, finished versus done | LO6: clean up safely and say what remains | Step 6: `check.py 6` |
| 10 | The lab | All | Steps 0 to 6; stretch: `check.py stretch` (optional) |
