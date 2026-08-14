# Contributing

## Ownership map

Four workstreams, four folders. Do not edit another workstream's owned
folder to "quickly fix" something; change the contract in `contracts/`
or raise it with the owner instead.

| Workstream | Mission | Owns |
|---|---|---|
| **A — Data, Telemetry & Replay** | Curated, verified race dataset; deterministic replay assets | `data_pipeline/`, `data/`, `hf_dataset/` |
| **B — Radio & Language Intelligence** | Audio in, structured `RadioAnalysisOutput` out | `services/radio_ai/`, `tests/radio_ai/` |
| **C — Incident Memory & Core API** | Storage, retrieval, evidence fusion, recurrence monitoring | `services/core_api/`, `services/evidence_memory/`, `storage/`, `tests/core_api/` |
| **D — Product, UI & Deployment** | Single-screen Pit-Wall Incident Inspector; ships the whole thing | `apps/web/`, `mock_server/`, `deployment/` |

`contracts/` is shared. Changes there require agreement from every
workstream whose service reads or writes that contract.

## Branching

- `integration/main` — always-working branch. Everything gets merged here
  before the demo.
- `ws-a-data-replay` — Workstream A.
- `ws-b-radio-ai` — Workstream B.
- `ws-c-evidence-memory` — Workstream C.
- `ws-d-product-ui` — Workstream D.

Work on your workstream branch, open a PR into `integration/main`. Never
push directly to `integration/main`.

> **Note on `main`:** GitHub's default branch for this repo is `main`,
> not `integration/main`, and presentation-polish commits have been
> pushed directly to `main` outside this PR flow. The two branches
> share full history but `main` is currently ahead. CI now runs on
> both (`.github/workflows/tests.yml`), but until the team picks one
> branch as canonical, confirm which branch you're building on before
> assuming "integration/main" and "the deployed site" are the same
> commit.

## Integration principle

Integrate on Day 1 with mocks, not on Day 4 with finished modules.

1. Freeze `contracts/schemas` and `contracts/fixtures` first.
2. Workstream D builds the UI against fixtures immediately.
3. Workstream C builds `core_api` against fixture `RadioAnalysisOutput`
   and fixture telemetry, not against a live `radio_ai` service.
4. Workstream B builds `/v1/radio/analyze` against fixture audio.
5. Workstream A produces real replay assets matching the same schema.
6. Swap mock providers for real providers one interface at a time.
7. Every optional feature (text-tone disagreement, field context) sits
   behind a feature flag so it can be disabled without touching other
   code.

## Commit conventions

- Present tense, imperative mood: `Add lead-time calculation`, not
  `Added` or `Adding`.
- Conventional-commit prefixes: `feat:`, `fix:`, `docs:`, `test:`,
  `chore:`, `refactor:`.
- One logical change per commit. If the message needs "and," split it.

## Pull requests

- Title matches commit style, e.g. `feat(core_api): add recurrence monitor`.
- Description covers what changed, why, and how to test it.
- Request review from the owner of any folder your change touches
  outside your own workstream.

## Before you open a PR

- Backend: the affected service's tests pass (`pytest` inside that
  service's directory, or `tests/<service>/` for cross-service checks).
- Frontend: `npm run build` succeeds in `apps/web/`.
- No secrets or `.env` files staged. Check `git status` before committing.
- If you changed a file under `contracts/`, confirm every consumer of
  that contract still parses the new shape.

## Code style

- Python 3.11+, type hints on public functions, Pydantic v2 for schemas.
- Lazy-import heavy SDKs (Hugging Face models, FastF1 where avoidable)
  inside the function that needs them, not at module top level, so
  services stay importable and testable without every dependency
  installed.
- TypeScript strict mode in `apps/web/`.
- No secrets, ever, in code or commit history.
