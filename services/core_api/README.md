# services/core_api — Workstream C

Mission: the backend brain. Owns incident memory (ECHO LAP), telemetry
evidence, recurrence monitoring, and the lead-time calculation. Must be
testable with fixtures without waiting on `services/radio_ai`.

## Owns

This directory, `../evidence_memory/`, `../../storage/`, and
`../../tests/core_api/`.

## Tasks

- Define the incident schema and SQLite metadata store (`../../storage/`).
- Generate/store sentence embeddings for incident memory; build FAISS
  (or cosine) retrieval in `../evidence_memory/`.
- Implement semantic retrieval returning top-k historical candidates
  with separate evidence components, never a single opaque probability.
- Build telemetry fingerprint generation: normalize by track distance,
  resample speed/throttle/brake to a fixed number of points, standardize
  channels.
- Implement own-baseline comparison (is the driver behaving differently
  at this segment vs. a recent personal baseline) and historical-window
  similarity.
- Implement the lead-time calculation:
  `driver_warning_lead_time = first_observable_performance_change_time - radio_event_time`.
  If there is no clear later deterioration, return `null` and let the
  UI say "No measurable lead-time established." Never force a positive
  result.
- Implement background recurrence scanning against stored incident
  fingerprints, independent of new radio events.
- Fuse all evidence into one `IncidentAssessment`. Do not add a
  composite risk score; expose the components.
- Expose `POST /v1/incidents/evaluate`, `GET /v1/incidents/{id}`,
  `GET /v1/replay/frame`.

## Contract

Input: fixture or real `RadioAnalysisOutput` + a pre-cached telemetry
window. Output: `IncidentAssessment`. See `contracts/api_contract.md`.

## Independent test

With synthetic transcript/category/telemetry fixtures, this service can
store an incident, retrieve it, compare a later window, and produce an
assessment without `radio_ai` or `apps/web` running.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```
