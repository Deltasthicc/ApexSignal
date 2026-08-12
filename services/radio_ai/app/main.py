"""FastAPI entrypoint for the radio_ai service.

Stateless: takes one audio clip, returns one RadioAnalysisOutput. Owns
no telemetry, no incident memory, no cross-request state.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile

from app import asr, complaint_classifier, tone
from app.audio_preprocessing import preprocess
from app.models import RadioAnalysisOutput
from app.output_store import write_radio_analysis
from app.pipeline import run_live_pipeline

logger = logging.getLogger("radio_ai")

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "fixtures"
    / "radio_analysis_output.sample.json"
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.environ.get("ANALYZE_MODE", "fixture") == "live":
        logger.info("ANALYZE_MODE=live: warming ASR, tone, and classifier models")
        asr.warm_up()
        tone.warm_up()
        complaint_classifier.warm_up()
    yield


app = FastAPI(title="ApexSignal radio_ai", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/radio/analyze", response_model=RadioAnalysisOutput)
async def analyze(incident_id: str, audio: UploadFile | None = None) -> RadioAnalysisOutput:
    """Analyze one radio clip.

    ANALYZE_MODE=fixture (default) returns the frozen fixture unchanged
    so every downstream consumer can be built before models are wired
    up. ANALYZE_MODE=live runs the real ASR -> tone -> classification
    pipeline; requires `audio` to be supplied.

    In live mode, the result is also written to disk as
    {incident_id}.json under RADIO_ANALYSIS_OUTPUT_DIR (default
    data/radio_analysis/) -- core_api reads from there directly rather
    than calling this endpoint, so calling this endpoint is not the
    only way output reaches core_api. See contracts/api_contract.md,
    "Output location." Fixture mode never writes to shared disk state.
    """
    mode = os.environ.get("ANALYZE_MODE", "fixture")
    if mode == "fixture":
        payload = json.loads(FIXTURE_PATH.read_text())
        payload["incident_id"] = incident_id
        return RadioAnalysisOutput.model_validate(payload)

    if audio is None:
        raise ValueError("ANALYZE_MODE=live requires an uploaded audio file")

    with tempfile.NamedTemporaryFile(suffix=Path(audio.filename or "clip.wav").suffix) as tmp:
        tmp.write(await audio.read())
        tmp.flush()
        waveform = preprocess(tmp.name)

    result = run_live_pipeline(waveform, incident_id)
    write_radio_analysis(result)
    return result
