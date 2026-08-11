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
from app.config import ModelConfig
from app.models import RadioAnalysisOutput

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

    transcript, asr_model_used = asr.transcribe(waveform)
    logger.info("asr model used: %s", asr_model_used)

    tone_scores = tone.score_waveform(waveform)
    tone_label, tone_score, tone_confidence = tone.map_to_label(tone_scores)

    complaint_category, category_confidence = complaint_classifier.classify(transcript)

    payload = {
        "incident_id": incident_id,
        "transcript": transcript,
        "tone_label": tone_label,
        "tone_score": tone_score,
        "tone_confidence": tone_confidence,
        "complaint_category": complaint_category,
        "category_confidence": category_confidence,
    }
    if ModelConfig.ENABLE_TEXT_TONE_DISAGREEMENT:
        # Deliberately not implemented until the Day-1 acoustic gate
        # passes -- see VALIDATION_GATES.md gate 5. Wire in the
        # semantic-concern vs. arousal comparison here once it does.
        raise NotImplementedError(
            "ENABLE_TEXT_TONE_DISAGREEMENT is on but the comparison logic "
            "isn't implemented. Do not flip this flag before the Day-1 "
            "gate passes and the comparison is built."
        )

    return RadioAnalysisOutput.model_validate(payload)
