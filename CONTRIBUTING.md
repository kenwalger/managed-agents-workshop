# Contributing

Thanks for your interest. This project is a focused educational workshop for learning the lifecycle of Claude Managed Agents. Small, reproducible improvements are welcome.

## Before proposing a change

Please open an issue to discuss changes that alter the learning objectives, lab sequence, report contract, or API architecture. Typo fixes and clear documentation corrections can be proposed directly.

## Local setup

1. Install Python 3.12 and [`uv`](https://docs.astral.sh/uv/).
2. Clone the repository and run `uv sync`.
3. Copy `.env.example` to `.env` only if you need live API exercises; provide your own development API key.
4. Run the offline tests before proposing changes: `uv run pytest` (no API calls, no key needed).

The workshop fixture is designed for Python 3.10+; the development environment targets Python 3.12. The fixture tests also run under 3.10 and 3.13 when uv has them installed (`uv python install 3.10 3.13`).

The learner scripts at the repository root are generated from the reference versions in `solution/`. Edit `solution/`, then run `uv run solution/make_stubs.py`; `tests/test_stubs.py` fails if the two drift apart.

## Pull requests

- Keep changes scoped to one learning or correctness issue.
- Explain the learner-facing impact and how you verified the change.
- Prefer offline tests for fixtures, validation, and formatting.
- If a live API test is necessary, report the SDK version, approximate cost, and observed behavior without exposing credentials or session data.
- Do not add unnecessary dependencies, production infrastructure, or network requirements.
- Update learner and instructor documentation when behavior changes.

## AI-assisted contributions

AI assistance is welcome. Review and test generated changes yourself; describe significant AI-assisted work and any relevant verification in the pull request. Do not submit unreviewed output.

## Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
