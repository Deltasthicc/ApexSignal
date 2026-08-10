"""FastAPI entrypoint for the core_api service.

Owns incident memory, evidence fusion, and recurrence monitoring. Reads
telemetry from data/, calls services/radio_ai over HTTP for live radio
analysis, and never imports another service's internal modules.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI

from app.models import IncidentAssessment

logger = logging.getLogger("core_api")

app = FastAPI(title="ApexSignal core_api")

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "fixtures"
    / "incident_assessment.sample.json"
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/incidents/evaluate", response_model=IncidentAssessment)
async def evaluate(incident_id: str) -> IncidentAssessment:
    """Evaluate one incident and return its IncidentAssessment.

    EVALUATE_MODE=fixture returns the frozen fixture unchanged so
    apps/web and mock_server behave identically during early
    development. EVALUATE_MODE=live is Workstream C's implementation
    target: retrieval + baseline + lead-time fusion.
    """
    mode = os.environ.get("EVALUATE_MODE", "fixture")
    if mode == "fixture":
        payload = json.loads(FIXTURE_PATH.read_text())
        payload["incident_id"] = incident_id
        return IncidentAssessment.model_validate(payload)

    raise NotImplementedError(
        "EVALUATE_MODE=live is not implemented yet. Wire up incident "
        "memory retrieval and the evidence/lead-time engine here "
        "(Workstream C)."
    )


@app.get("/v1/incidents/{incident_id}", response_model=IncidentAssessment)
async def get_incident(incident_id: str) -> IncidentAssessment:
    return await evaluate(incident_id)
