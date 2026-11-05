# Security policy

## Scope

This repository is an educational workshop, not a production agent service. The exercises can create billable cloud resources and execute code in a managed sandbox. Use only synthetic fixture data and a dedicated development API key with appropriate account-level controls.

## Reporting a vulnerability

Please **do not open a public issue** containing credentials, exploit details, or sensitive data. Use GitHub's **Report a vulnerability** / private vulnerability reporting feature if it is enabled for this repository. Otherwise, contact the repository maintainer privately through the contact information on their GitHub profile. Do not assume a guaranteed response time.

Include a minimal reproduction, affected files or versions, impact, and recommended mitigation if known. Never include live API keys or private user data.

## Safe workshop operation

- Keep `ANTHROPIC_API_KEY` in `.env` or your environment; never commit `.env`, logs containing secrets, or session state.
- Confirm `.env.example` contains placeholders only.
- Use the smallest tool permissions and network egress needed for the exercise.
- Use a session spend cap; check account-level limits independently.
- Review generated commands and files before executing or applying them locally.
- Delete unused sessions and uploaded files, and archive agents when appropriate.
- Treat agent-generated reports as untrusted data; verify against the provided fixture.
- `check.py` follows this rule: it reproduces evidence only by running samples it parses from the local `fixture/` folder, and it never runs the `command` fields or any other code from the agent's report. `check.py stretch` reads the agent's corrected docs without running them, and `replay.py` only prints recorded events.

## Supported versions

Only the current default branch is maintained. This workshop is a learning artifact and does not promise security fixes or long-term support for earlier revisions.
