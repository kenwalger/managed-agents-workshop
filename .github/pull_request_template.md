## What this changes and why

<!-- One learning or correctness issue per pull request. What does a learner notice? -->

## Testing

- [ ] `uv run pytest` passes (offline; no API calls)
- [ ] `git diff --check` is clean
- [ ] If `solution/` changed: ran `uv run solution/make_stubs.py`
- [ ] If a live step changed: ran it against the API, noted the SDK version and approximate cost, and deleted every session I created
- [ ] Learner-facing commands still work in Windows PowerShell as written in the README

## Security

- [ ] No API keys, `.env`, `.lab-state.json`, `outputs/`, or new recordings are included
- [ ] Agent-generated output is still treated as untrusted (nothing from a report is executed locally)
- [ ] No new dependencies, network requirements, or infrastructure (or explained below)

## AI assistance

<!-- If an AI tool helped, say which parts, and how you verified them. -->
