"""The actual ASR -> tone -> classification pipeline, factored out of
main.py so both the HTTP endpoint and offline batch scripts
(scripts/generate_radio_analysis.py, scripts/benchmark_day1.py) call
the same code path instead of two copies drifting apart.
"""

from __future__ import annotations

import logging

import numpy as np

from app import asr, complaint_classifier, tone
from app.config import ModelConfig
from app.models import RadioAnalysisOutput

logger = logging.getLogger("radio_ai")


def run_live_pipeline(waveform: np.ndarray, incident_id: str) -> RadioAnalysisOutput:
    """Run the real (non-fixture) pipeline on a preprocessed waveform."""
    transcript, asr_model_used = asr.transcribe(waveform)
    logger.info("asr model used: %s", asr_model_used)

    tone_scores = tone.score_waveform(waveform)
    tone_label, tone_score, tone_confidence = tone.map_to_label(tone_scores)

    complaint_category, category_confidence = complaint_classifier.classify(transcript)

    if ModelConfig.ENABLE_TEXT_TONE_DISAGREEMENT:
        # Deliberately not implemented until the Day-1 acoustic gate
        # passes -- see VALIDATION_GATES.md gate 5.
        raise NotImplementedError(
            "ENABLE_TEXT_TONE_DISAGREEMENT is on but the comparison logic "
            "isn't implemented. Do not flip this flag before the Day-1 "
            "gate passes and the comparison is built."
        )

    return RadioAnalysisOutput.model_validate(
        {
            "incident_id": incident_id,
            "transcript": transcript,
            "tone_label": tone_label,
            "tone_score": tone_score,
            "tone_confidence": tone_confidence,
            "complaint_category": complaint_category,
            "category_confidence": category_confidence,
        }
    )
