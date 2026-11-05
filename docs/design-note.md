# Design note: Calling Claude vs. Operating an Agent

*Claude Platform Enablement Challenge: Claude Managed Agents*  
*Ken W. Alger*

## 1. Premise

Our cohort knows how to *call* Claude: make a request, get a response, and maybe write a tool loop. They don't yet know how to *operate* an agent: start one, monitor it, guide it, collect what it produces, and clean up afterward.

This session focuses on getting learners to that point. Everything I include connects to this comparison:

| Calling Claude | Operating an agent |
|---|---|
| Send a request and receive a response | Create a session, run it, let it become idle, continue it, and end it |
| Implement the tool loop yourself | Let the agent execute its loop while you observe events |
| Manage conversation history yourself | Work with session state, history, sandbox files, and generated results |
| Read the response | Monitor events, steer the work, or interrupt it |
| Execute or host the tools | Select allowed tools and let the agent use them in a sandbox |
| Track usage per request | Monitor session usage, cost, and lifecycle |

That leads to the question of when to use Managed Agents. If you need a model request and response, use the Messages API. If you want to run an agent in your own process, consider the Agent SDK. If you want to operate an agent without hosting its execution environment, consider Managed Agents.

## 2. Who is this for, and how deep do we go?

- **Audience:** Engineers comfortable with APIs and solution architects familiar with the product. They have used the Messages API, and possibly the Agent SDK, but haven't worked with Managed Agents.
- **Knowledge level:** 201. I won't teach learners how to create an API key. I want to teach them how to operate an agent.
- **Instructor:** Another instructor should be able to deliver this session. That means providing speaker notes, an instructor guide, and a fallback if a live demonstration doesn't work. The lab should also tell a coherent story on its own.

## 3. What they should know after the session

1. Create an agent with a sandbox and give it only the permissions needed to complete a task.
2. Create a session, upload local files, and understand what each saved resource ID refers to.
3. Monitor an agent running autonomously, detach and reconnect to observation, and identify the events showing sample execution and errors.
4. Send a message to a session from another terminal and understand when the agent will process it.
5. Retrieve the agent's results, validate their structure against the report schema, and check their claims against trusted evidence.
6. Clean up the session's resources and understand what remains available afterward.

I also want learners to understand when Managed Agents is a better fit than the Messages API or Agent SDK, and when it isn't.

## 4. Decisions

These are the main decisions I made and how AI contributed.

| # | Decision | AI contribution | What I decided | Reasoning |
|---|---|---|---|---|
| 1 | Theme | The theme was mine. Claude helped develop the comparison table and suggested limiting the scope to one agent rather than production operations. | **Calling Claude to Operating an Agent.** Focus on one agent's lifecycle and explicitly exclude production operations. | Learners already know how to call Claude. The missing skill is operating an agent. |
| 2 | Lab domain | I considered five domains, and Claude helped evaluate them. | **Documentation Drift.** I created a fictional library, `metrolen`, with three planted documentation drifts, one decoy, and three working controls. | Learners must run documented examples and compare results with expectations. Managed Agents provides a sandbox and execution lifecycle; doing this with the Messages API alone would require us to build and host that infrastructure. Documentation drift is also a familiar problem. |
| 3 | Learner discovery | Claude suggested three options: least privilege, collecting results, and steering. It recommended least privilege. | Have learners determine which permissions the agent needs rather than giving them the answer immediately. | This is testable and reinforces the operator's responsibility. During testing, the agent attempted to install a package with `pip`, and the restricted environment blocked it. |
| 4 | Demonstration | Claude suggested a recorded session and later proposed using it as the primary demonstration. | Include a sanitized recording that can be replayed with `replay.py`, but retain a live demonstration as the preferred delivery approach and the recording as a fallback. | The recording works without an API key or network connection. It shows events from a previous execution, not a new agent run. |
| 5 | Lab feedback and testing | Claude Code implemented the tests under my direction. | Separate feedback about whether learners operated the agent correctly from feedback about the agent's findings. Validate reported findings against trusted lab fixtures. | A learner shouldn't fail the exercise simply because an agent produces a poor answer. The distinction also teaches why agent outputs need independent verification. |
| 6 | Lab format | I considered notebooks and scripts. | Use Python scripts with `uv run` and two terminals: a watch terminal and a command terminal. | Learners need to observe an agent while interacting with its session. Two terminals make that distinction visible. |
| 7 | Stack | No substantive AI recommendation. | Python 3.12+, `uv`, and the Anthropic SDK. | The stack should be familiar to the intended audience. |
| 8 | Presentation format | Claude initially proposed HTML. Claude Code helped create a Marp deck with speaker notes. | Keep the editable Marp Markdown deck alongside the lab, with HTML and PDF exports for delivery. | The materials remain easy to maintain, present, and hand off to another instructor. |

## 5. Where I overrode or corrected AI output

- **Demo:** Claude Code proposed making the recorded session the primary demonstration. I preferred a live demonstration with the sanitized recording available as a fallback.
- **Least-privilege slide:** The first version revealed the answer to the lab's discovery exercise. I removed it so learners would still have to work out the permissions themselves.
- **When not to use Managed Agents:** The comparison slide explained when to use it but not when to avoid it. I added that distinction.
- **YOUR TURN prompts:** The instructions told learners to find a function called `YOUR TURN`, but the actual function is `choose_permissions()`. I caught this during my pilot and updated the prompts to name the correct file and function.
- **Cost:** The initial material mentioned an estimated cost but didn't ask learners to inspect their own session cost. I had Claude Code check the relevant documentation and added cost inspection to step 6.
- **Phase 1 prompt:** Claude's initial spike prompt didn't establish a stopping point or budget. I expanded it to define the limits, expected documentation, and tests.

## 6. Using AI

- **Planning:** I used Claude Desktop and ChatGPT to explore the session structure and learning objectives, then created the plan I followed.
- **Research:** I used Claude to learn about Managed Agents, cross-checked the information against documentation, and ran a Phase 1 spike in Claude Code to verify behavior.
- **Creation:** Claude Code implemented the lab, presentation, and instructor guide from requirements I supplied in `CLAUDE.md`. I worked in phases, reviewed the output, and provided corrections.
- **Testing:** I completed the lab as a learner, timed the experience, recorded points of confusion, and checked that session costs were visible.
- **Decisions I retained:** I chose the central theme, selected the lab domain, required a least-privilege discovery exercise, set the scope boundaries, and decided what evidence would count as a successful learner outcome. AI helped explore or implement some of these ideas, but I made the final decisions.
- **Repo Logo:** I used ChatGPT to generate the "Documentation Drift" logo for the repository.

## 7. Testing

| Observation | Result |
|---|---|
| Time to complete lab | About 25 minutes in my own pilot. Because I already knew the material, I expect an unfamiliar learner to need longer; the 60-minute target remains an estimate, not a measured learner result. |
| What tripped me up | The YOUR TURN instructions named a nonexistent function. One hint omitted `uv run`. I confused “Terminal 1” and “Terminal 2,” and steps 1 and 2 didn't identify which terminal to use. The lab didn't show session cost, and the initial `uv sync` delay made it unclear whether setup had stalled. |
| Changes I made | Named the exact files and functions in the prompts, checked commands for `uv run`, renamed the terminals “watch terminal” and “command terminal,” clarified which terminal to use, noted that `uv sync` can take 1–2 minutes, and added session cost feedback. |
| Agent reliability | In this pilot, the agent identified all three planted drifts and correctly treated the decoy as unchanged. This is one pilot run, not a reliability estimate. |
| Cost and duration | Approximately $0.01 at list price, with the agent running for about 54 seconds. |

## 8. What this doesn't cover

See [what-this-doesnt-cover.md](what-this-doesnt-cover.md) for more information.

## 9. Limitations

- **Beta API:** Behavior and interfaces may change. The instructor should verify the lab against the current API before delivery.
- **Short agent runs:** The agent may finish in under a minute, so learners might not see a steering message processed mid-run. The checkpoint accepts both mid-run steering and continuation in the same session, while reporting which occurred.
- **Nondeterministic execution:** Some runs batch the documentation samples into one command; others execute them individually.
- **Limited reliability evidence:** I would run more independent trials before making claims about how consistently the agent detects drift.
- **Ctrl+C on Windows:** Detaching from event observation can take several seconds.
- **Data-handling restrictions:** Managed sessions retain state and files. Instructors should verify current Zero Data Retention, HIPAA, and other compliance eligibility in the official platform documentation rather than assuming this workshop configuration qualifies.
- **Pilot environment:** My learner-style pilot was on Windows with PowerShell. Other environments were not covered by that pilot.

## 10. Time it took me to complete

| Measure | Time |
|---|---|
| Total elapsed time | 4.25 hours |
| Focused time | 3.75 hours |
| Remaining elapsed time | About 30 minutes waiting for Claude Code and live agent execution |
| Spike (focused) | 30 minutes |
| Design (focused) | 30 minutes |
| Lab build (focused) | 1.5 hours |
| Presentation/session (focused) | 15 minutes |
| Pilot (focused) | 45 minutes |
| Instructor handoff (focused) | 15 minutes |
