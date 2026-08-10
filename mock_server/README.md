# mock_server — Workstream D

Fixture-backed stand-in for `services/core_api` and `services/radio_ai`.
Serves `contracts/fixtures/*` verbatim on the same paths the real
services expose, so `apps/web` never blocks on a backend service being
finished.

## Running locally

```bash
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

## Endpoints

Same shapes as `contracts/api_contract.md`:

- `GET /health`
- `POST /v1/radio/analyze` -> `contracts/fixtures/radio_analysis_output.sample.json`
- `POST /v1/incidents/evaluate` -> `contracts/fixtures/incident_assessment.sample.json`
- `GET /v1/incidents/{id}` -> same fixture
- `GET /v1/replay/frame?index=N` -> one entry from `contracts/fixtures/incident_manifest.sample.json`
