# apps/web — Workstream D

The Pit-Wall Incident Inspector. One screen: a race replay timeline
with radio pins, an incident detail panel, a gold-incident lead-time
card, a Pit-Wall view toggle, and a clip upload panel. Not four module
tabs.

## Owns

This directory.

## Build against fixtures from Day 1

Never wait for a real backend endpoint to start UI work. Point
`NEXT_PUBLIC_CORE_API_BASE_URL` at `mock_server` (port 8000) until
`services/core_api` (port 8001) has a real implementation; the response
shape is identical either way because both serve `IncidentAssessment`.

## What the incident card must show

- Radio playback + transcript.
- Mandatory tone/arousal classification, with confidence.
- Normalized driver complaint category (reported phenomenon, not a
  diagnosis).
- Circuit segment and lap.
- Telemetry evidence: speed/throttle/brake overlay.
- Historical incident match with separate semantic/telemetry
  similarities, or a clear "no match" state.
- Measured warning lead time, or "No measurable lead-time established."
- Optional text-tone disagreement, only when the backend sends it.
- Confidence/uncertainty and a human-review recommendation.

No blank panels or spinners on the judged path; every state (loading,
empty, error, degraded-feature-off) needs an explicit UI.

## Running locally

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

## Independent test

The full UI runs against `mock_server` even if Workstreams A, B, and C
are offline.
