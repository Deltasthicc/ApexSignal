"""Fixture-backed mock of core_api + radio_ai for frontend-first development.

Serves contracts/fixtures/* on the same paths the real services will
expose. apps/web should be able to run its entire golden path against
this server alone.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="ApexSignal mock_server")

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "contracts" / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES_DIR / name).read_text())


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/radio/analyze")
def analyze(incident_id: str) -> dict:
    payload = _load("radio_analysis_output.sample.json")
    payload["incident_id"] = incident_id
    return payload


@app.post("/v1/incidents/evaluate")
def evaluate(incident_id: str) -> dict:
    payload = _load("incident_assessment.sample.json")
    payload["incident_id"] = incident_id
    return payload


@app.get("/v1/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict:
    return evaluate(incident_id)


@app.get("/v1/replay/frame")
def replay_frame(index: int = 0) -> dict:
    manifest = _load("incident_manifest.sample.json")
    if index < 0 or index >= len(manifest):
        raise HTTPException(status_code=404, detail="No frame at this index")
    return manifest[index]
