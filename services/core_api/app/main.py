"""FastAPI entrypoint for the core_api service.

Owns incident memory, evidence fusion, and recurrence monitoring. Reads
telemetry from data/, consumes services/radio_ai output as JSON matching
the frozen contract, and never imports another service's internal
modules.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.config import load_settings
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
    development. EVALUATE_MODE=live runs the real pipeline: telemetry
    fingerprint, ECHO LAP retrieval, own-baseline comparison, lead time,
    and recurrence state.
    """
    mode = os.environ.get("EVALUATE_MODE", "fixture")
    if mode == "fixture":
        payload = json.loads(FIXTURE_PATH.read_text())
        payload["incident_id"] = incident_id
        return IncidentAssessment.model_validate(payload)

    return _evaluate_live(incident_id)


@app.get("/v1/incidents/{incident_id}", response_model=IncidentAssessment)
async def get_incident(incident_id: str) -> IncidentAssessment:
    return await evaluate(incident_id)


def _evaluate_live(incident_id: str) -> IncidentAssessment:
    """Run the live evidence pipeline for one stored incident.

    Imports stay inside this function so that fixture mode and /health
    never pull in pandas, torch, or a sentence-transformer. Missing
    inputs surface as 404/422 with the specific path or contract
    violation named, rather than as a 500.
    """
    from app import db
    from app.pipeline import (
        EvaluationError,
        EvaluationInputs,
        evaluate_incident,
        load_radio_analysis,
        resolve_telemetry_path,
    )

    settings = load_settings()
    connection = db.connect(settings.db_path)
    try:
        record = db.get_incident(connection, incident_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"incident {incident_id} is not in the store. Load the "
                    f"manifest first: python -m app.ingest"
                ),
            )

        prior_records = db.query_incidents(
            connection,
            exclude_incident_id=incident_id,
            before_event_time_ms=record.event_time_ms,
        )

        try:
            radio = load_radio_analysis(incident_id, settings)
            telemetry_path = resolve_telemetry_path(record, settings)
            inputs = EvaluationInputs(
                record=record,
                radio=radio,
                telemetry_path=telemetry_path,
                prior_records=tuple(prior_records),
                telemetry_root=settings.telemetry_root,
            )
            return evaluate_incident(inputs)
        except EvaluationError as exc:
            logger.warning("cannot evaluate %s: %s", incident_id, exc)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        connection.close()
