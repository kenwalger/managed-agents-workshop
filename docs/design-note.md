# Design note: From Calling Claude to Operating an Agent

*Claude Platform Enablement Challenge: Claude Managed Agents*
*Ken W. Alger*

> Working draft. Sections marked **[fill in]** get completed during the build. Delete this line before submitting.

## 1. The premise

The cohort can already *call* Claude: send a request, read a response, maybe write a tool loop. What they haven't done is *operate* an agent: start something that runs on its own, watch it work, steer it, collect what it produced, and clean up after it.

This workshop is built around that shift. Every section of the session, every step of the lab, and every checkpoint maps to one row of this table:

| Calling Claude | Operating an agent |
|---|---|
| A request and a response | A session with a lifecycle: create, run, idle, resume, delete |
| You write the loop | The loop runs on Anthropic's side; you watch it through events |
| Stateless; you resend the history | State lives on the server: history, sandbox files, outputs |
| You read the response | You stream events, steer, or interrupt mid-run |
| Your code runs the tools | You decide which tools it may use, and it runs them in a sandbox |
| Cost is per call | Cost and time are per session, so cleanup matters |

The theme also answers "when do I reach for Managed Agents?" directly. If you only need to call Claude, use the Messages API. If you want the agent harness running in your own process, use the Agent SDK. If you want to operate an agent you don't have to host, use Managed Agents.

## 2. Audience and depth

- **Who:** strong general engineers and solutions architects. They've used the Messages API and possibly the Agent SDK, but have never shipped on Managed Agents.
- **Depth:** 201. No API-key basics; the time goes to the operating model and to judgment about when to use it.
- **Who teaches it:** another instructor, with one to two days to prepare. That shapes the demo fallback, the instructor guide, and how much the lab explains in its own words.

## 3. What learners can do afterward

**[fill in after the quickstart]** Draft:

1. Explain when Managed Agents fits better than the Messages API or the Agent SDK, and when it doesn't.
2. Create an agent, an environment, and a session, and say what each one is responsible for.
3. Run a task, follow its progress through the event stream, and steer or interrupt it.
4. Retrieve what the agent produced, and clean up the session.

## 4. Key decisions

The judgment calls behind the workshop. Each row records what an AI tool proposed (where one was involved), what shipped, and why.

| # | Decision                        | What AI proposed                                                                                                                                    | What I shipped                                                                                                               | Why                                                                                                                                     |
|---|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Theme                           | My idea. Claude proposed the calling-versus-operating table and a caution to scope "operating" to one agent's lifecycle, not production operations. | "From calling Claude to operating an agent," scoped to one agent's lifecycle, with production topics listed as out of scope. | It answers the "when to use it" question by construction, and it targets the cohort's actual gap: they've called Claude but never operated an agent. |
| 2 | Lab domain                      | N/A                                                                                                                                                 | Documentation Drift Agent                                                                                                    | A documention drift scenacrio is directly relevant to the audience.                                                                     |
| 3 | The "work it out yourself" step | **[fill in]**                                                                                                                                       | **[fill in]**                                                                                                                | **[fill in]**                                                                                                                           |
| 4 | Demo fallback                   | **[fill in]**                                                                                                                                       | **[fill in]**                                                                                                                | **[fill in]**                                                                                                                           |
| 5 | Checkpoint design               | **[fill in]**                                                                                                                                       | **[fill in]**                                                                                                                | **[fill in]**                                                                                                                           |
| 6 | Session format                  | Jupyter Notebook                                                                                                                                    | Scripts, not a notebook.                                                                                                     | Because operating an agen means the agent runs on its own while clients attach to it and a notebook cell can't show that.                                                                                                                                        |
| 7 | Tech Stack                      | N/A                                                                                                                                                 | Python 3.12, `uv`                                                                                                             |                                                                                                                                         |
| 8 | Deliverables | Recorded demo for the presentation | Slides only | For a twenty minute presentation, a recorded demo eats a lot of time |
| 9 | Session Format | Claude suggested a single HTML deck, Claude Code built a Marp deck sith separate speaker notes | Marp deck with speaker notes, exported to HTML and PDF | Versioned with the lab, readable as Markdown, and presentable without extra tools |
| 10 | Demo mode | Claude Code made the recorded replay the default | Live be default, recording as the fallback | The brief requires a live demo. The recording keeps its value as a reliable fallback |

## 5. Where I overrode the model

Specific places where AI-generated material was wrong, too generic, or not right for this audience, and what I did instead. Concrete examples, not a summary.

- Claude Code made the recorded replay the default demo. The brief requires a live demo, so I made live the default and kept the recording as the fallback, with a clear rule for when to switch.
- The least-privilege slide listed the exact settings learners have to work out in step 1, even though its own speaker notes said not to. I cut it back to the outcome.
- The “when to use it” slide had no “when not to use it.” I added it, because knowing when to choose something else is part of the judgment the session teaches.

## 6. How AI was used

**[fill in]** Draft:

- **Research:** Claude, checked against the Managed Agents docs. Anything not confirmed in the docs was verified by running it.
- **Building:** Claude Code built the lab from a written brief, in stages, and I reviewed each stage before it moved on.
- **Testing:** I piloted the lab myself as a learner, timed, before writing the instructor guide.
- **Not delegated:** the theme, the learning outcomes, the work-it-out step, the scope cuts, and every decision in section 4.

## 7. Pilot results

**[fill in]**

| | |
|---|---|
| Lab time (pilot) | **[fill in]** |
| Where I stalled | **[fill in]** |
| What changed because of it | **[fill in]** |
| API cost of one full run | **[fill in]** |

## 8. Scope

What this workshop deliberately leaves out, and why, is in [what-this-doesnt-cover.md](what-this-doesnt-cover.md).

## 9. Known limitations

**[fill in]** What I'd fix with more time, and the risks an instructor should know about (for example, the API is in beta and behavior may change between releases).

## 10. Time spent

**[fill in]** Actual focused hours, broken down by phase, against the roughly six-hour budget. If it went over, say by how much and where.
