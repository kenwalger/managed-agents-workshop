# What this workshop doesn't cover

This workshop teaches one thing well: **operating one agent through its whole lifecycle** on Claude Managed Agents. Everything below was left out on purpose. Each item says why, and where to go next.

The instructor can use this page to answer "does this cover X?" quickly, and to point learners somewhere useful when the answer is no.

## Production operations

**Monitoring, alerting, scaling, rate-limit planning, and on-call.**
"Operating" here means running one agent from start to finish, not running a fleet in production. Those topics need their own session, and they depend on each team's own infrastructure.
*Next:* the Managed Agents reference, especially rate limits.

## Self-hosted sandboxes

**Running sessions on your own infrastructure instead of Anthropic's cloud sandbox.**
Setup varies by environment and would use most of the lab's 60 minutes. The lab uses the managed cloud sandbox so everyone starts from the same place. The session mentions self-hosting as an option for compliance or data-residency needs.
*Next:* the self-hosted sandboxes guide.

## Research-preview features

**MCP tunnels and dreaming.**
These capabilities are outside the workshop's tested scope. They introduce additional configuration and operational considerations beyond the single-agent lifecycle taught here.
*Next:* the Managed Agents documentation for current feature availability and access requirements.

## Scheduled deployments

**Running agents on a recurring cron schedule.**
Worth knowing it exists, and the session mentions it. But a scheduled run doesn't show its results within a 60-minute lab, and it adds cleanup risk if a learner forgets to remove it.
*Next:* the scheduled deployments guide.
Scheduled deployments are outside the scope of this workshop.

## Building custom tools and MCP servers

**Writing your own MCP server or tool provider.**
The lab uses the built-in tools (bash and file operations) so the focus stays on operating the agent. Writing an MCP server is a separate skill.
*Next:* the MCP documentation.

## Agent SDK in depth

**Building with the Agent SDK.**
The session compares the SDK with Managed Agents so learners can choose between them. It doesn't teach the SDK itself.
*Next:* the Agent SDK documentation.

## Multi-agent systems

**Orchestrating several agents that work together.**
Learners should operate one agent confidently before coordinating several.

## Evaluating agent quality

**Building eval sets, grading agent output, and catching regressions across model versions.**
The lab's checkpoints confirm that the learner's build works. They don't measure how good the agent's work is. Evaluation is its own discipline.

## Compliance and data handling, in depth

**Data retention policies, ZDR, HIPAA, and governance.**
The instructor should know one fact, and the session states it: because sessions store their state, Managed Agents is not currently eligible for Zero Data Retention or HIPAA BAA coverage. Learners can delete sessions and uploaded files through the API. Anything beyond that belongs with each team's own compliance process.
*Next:* the API and data retention documentation.

## Cloud platform differences

**Claude Platform on AWS and Claude models on Google Cloud.**
Managed Agents is available on both, with some differences in features and session behavior. The lab uses the Claude API directly so everyone has the same experience.
*Next:* the Managed Agents sections of the AWS and Google Cloud guides.

## Cost optimization

**Tuning model choice, compaction, and caching for cost.**
The lab covers the one cost habit that matters most at this level: delete sessions you're done with. Deeper tuning is a production concern.
