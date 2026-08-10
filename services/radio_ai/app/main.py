"""FastAPI entrypoint for the radio_ai service.

Stateless: takes one audio clip, returns one RadioAnalysisOutput. Owns
no telemetry, no incident memory, no cross-request state.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, UploadFile

from app.models import RadioAnalysisOutput

logger = logging.getLogger("radio_ai")

app = FastAPI(title="ApexSignal radio_ai")

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "fixtures"
    / "radio_analysis_output.sample.json"
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/radio/analyze", response_model=RadioAnalysisOutput)
async def analyze(incident_id: str, audio: UploadFile | None = None) -> RadioAnalysisOutput:
    """Analyze one radio clip.

    ANALYZE_MODE=fixture returns the frozen fixture unchanged so every
    downstream consumer can be built before ASR/tone models are wired
    up. ANALYZE_MODE=live is Workstream B's implementation target.
    """
    mode = os.environ.get("ANALYZE_MODE", "fixture")
    if mode == "fixture":
        payload = json.loads(FIXTURE_PATH.read_text())
        payload["incident_id"] = incident_id
        return RadioAnalysisOutput.model_validate(payload)

    raise NotImplementedError(
        "ANALYZE_MODE=live is not implemented yet. Wire up ASR + tone "
        "model inference here (Workstream B)."
    )
