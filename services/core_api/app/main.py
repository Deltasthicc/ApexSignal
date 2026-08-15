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
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_settings
from app.models import IncidentAssessment

logger = logging.getLogger("core_api")

app = FastAPI(title="ApexSignal core_api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "contracts"
FIXTURES_DIR = CONTRACTS_DIR / "fixtures"
FIXTURE_PATH = FIXTURES_DIR / "incident_assessment.sample.json"
FIXTURE_MANIFEST_PATH = FIXTURES_DIR / "incident_manifest.sample.json"


def _fixture_assessment_payload(incident_id: str) -> dict:
    """Prefer a per-incident fixture (contracts/fixtures/incident_assessment/
    {id}.json) so the demo timeline can show distinct incidents; fall back
    to the single generic sample for any id without one, same as before."""
    per_incident = FIXTURES_DIR / "incident_assessment" / f"{incident_id}.json"
    if per_incident.exists():
        return json.loads(per_incident.read_text(encoding="utf-8"))
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["incident_id"] = incident_id
    return payload


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "evaluate_mode": os.environ.get("EVALUATE_MODE", "fixture"),
        "service": "core_api",
    }


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
        payload = _fixture_assessment_payload(incident_id)
        return IncidentAssessment.model_validate(payload)

    return _evaluate_live(incident_id)


@app.get("/v1/incidents/{incident_id}", response_model=IncidentAssessment)
async def get_incident(incident_id: str) -> IncidentAssessment:
    return await evaluate(incident_id)


@app.get("/v1/replay/frame")
async def replay_frame(index: int = 0) -> dict:
    """One manifest entry (radio + telemetry refs) by position.

    Documented in contracts/api_contract.md since Day 1 but previously
    unimplemented on core_api -- only mock_server served it. Fixture mode
    reads the bundled demo manifest; live mode reads Workstream A's real
    data/incident_manifest.json via the same settings the evaluate path
    uses, so this 404s with a clear message rather than fabricating a
    frame when that file is missing.
    """
    manifest = _load_manifest()
    if index < 0 or index >= len(manifest):
        raise HTTPException(status_code=404, detail="No frame at this index")
    return manifest[index]


@app.get("/v1/replay/manifest")
async def replay_manifest() -> list:
    """Full session manifest in one call, for the timeline UI."""
    return _load_manifest()


@app.get("/v1/live-pipeline")
async def live_pipeline_demo() -> list:
    """Real pipeline output (ASR, tone, classifier, retrieval) computed
    once against real MikCil/f1-team-radio broadcast clips by
    services/radio_ai/tone_test/run_live_pipeline_demo.py. Served over
    HTTP like every other incident record -- not bundled into the
    frontend as a hardcoded constant, and not live GPU inference on
    every request either; same deterministic-replay pattern as the rest
    of this API."""
    return json.loads((FIXTURES_DIR / "live_pipeline_demo.json").read_text(encoding="utf-8"))


def _load_manifest() -> list:
    mode = os.environ.get("EVALUATE_MODE", "fixture")
    if mode == "fixture":
        return json.loads(FIXTURE_MANIFEST_PATH.read_text(encoding="utf-8"))

    settings = load_settings()
    if not settings.manifest_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"incident manifest not found at {settings.manifest_path}. "
                f"Set CORE_API_MANIFEST_PATH, or run Workstream A's "
                f"build_incident_manifest.py."
            ),
        )
    return json.loads(settings.manifest_path.read_text(encoding="utf-8"))


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
