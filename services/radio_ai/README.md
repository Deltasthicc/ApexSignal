# services/radio_ai — Workstream B

Mission: convert one radio clip into a stable `RadioAnalysisOutput`.
Stateless. Owns no race telemetry and no incident memory.

## Owns

This directory and `../../tests/radio_ai/`.

## Tasks

- Load and warm the Hugging Face Whisper ASR model at server startup.
- Produce a transcript from audio; keep the manually verified transcript
  from the incident manifest alongside it for evaluation, never
  substitute one for the other silently.
- Load and validate the acoustic arousal/tone model on real F1-style
  clips before trusting it. This is the mandatory PS1 output; keep it
  even if The Mask is cut.
- Implement the coarse tone/arousal output with confidence.
- Implement complaint classification into the frozen 4-5 category
  taxonomy in `contracts/api_contract.md`.
- Implement text-tone disagreement as an optional, non-blocking field.
- Expose `POST /v1/radio/analyze`.
- Benchmark cold-start and per-clip latency; warm models on startup, not
  on first request.

## Contract

Input: audio bytes/path + `incident_id`. Output: `RadioAnalysisOutput`,
see `contracts/api_contract.md` and
`contracts/schemas/radio_analysis_output.schema.json`.

## Independent test

Run against fixture audio and return valid JSON while Workstreams A, C,
and D are entirely absent. `app/main.py` ships with a
`ANALYZE_MODE=fixture` mode that returns
`contracts/fixtures/radio_analysis_output.sample.json` so this is true
from Day 1.

## Cut rule

If the acoustic tone model is unstable on real F1-style audio, drop
`text_tone_disagreement` only. ASR, tone/arousal, and complaint
classification still ship; those three are load-bearing for PS1
compliance.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8002
```
