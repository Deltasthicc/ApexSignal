"""Fixture-backed mock of core_api + radio_ai for frontend-first development.

Serves contracts/fixtures/* on the same paths the real services will
expose. apps/web should be able to run its entire golden path against
this server alone.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="ApexSignal mock_server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "contracts" / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _load_per_incident(subdir: str, incident_id: str, default_name: str):
    """Prefer contracts/fixtures/{subdir}/{incident_id}.json; fall back to
    the single generic sample so unknown ids still return a valid shape."""
    candidate = FIXTURES_DIR / subdir / f"{incident_id}.json"
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    payload = _load(default_name)
    payload["incident_id"] = incident_id
    return payload


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "evaluate_mode": "replay", "service": "apexsignal_replay_api"}


@app.post("/v1/radio/analyze")
def analyze(incident_id: str) -> dict:
    return _load_per_incident(
        "radio_analysis", incident_id, "radio_analysis_output.sample.json"
    )


@app.post("/v1/incidents/evaluate")
def evaluate(incident_id: str) -> dict:
    return _load_per_incident(
        "incident_assessment", incident_id, "incident_assessment.sample.json"
    )


@app.get("/v1/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict:
    return evaluate(incident_id)


@app.get("/v1/replay/frame")
def replay_frame(index: int = 0) -> dict:
    manifest = _load("incident_manifest.sample.json")
    if index < 0 or index >= len(manifest):
        raise HTTPException(status_code=404, detail="No frame at this index")
    return manifest[index]


@app.get("/v1/replay/manifest")
def replay_manifest() -> list:
    """Full session manifest in one call, so the timeline UI doesn't have
    to probe /v1/replay/frame one index at a time. Additive convenience
    endpoint -- same underlying fixture data as /v1/replay/frame."""
    return _load("incident_manifest.sample.json")


@app.get("/v1/live-pipeline")
def live_pipeline_demo() -> list:
    """Real pipeline output (ASR, tone, classifier, retrieval) computed
    once against real MikCil/f1-team-radio broadcast clips by
    services/radio_ai/tone_test/run_live_pipeline_demo.py, served here so
    the frontend fetches it over HTTP like every other incident record
    instead of bundling it as a hardcoded constant. Same "deterministic
    replay of real computed output" pattern as the rest of this server --
    not live GPU inference on every request, but not fabricated either."""
    return _load("live_pipeline_demo.json")


# Hugging Face Space mode: serve the exported Next.js site and the fixture API
# from one origin. Mount this last so /health and /v1/* keep route priority.
STATIC_SITE_DIR = Path(os.getenv("STATIC_SITE_DIR", ""))
if STATIC_SITE_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_SITE_DIR, html=True), name="frontend")
