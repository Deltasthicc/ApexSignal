"""Speech-to-text stage: distil-large-v3.5-ct2 via faster-whisper, with
a small.en CPU fallback if the primary model is too slow on Day-1
hardware (flip USE_ASR_FALLBACK=true in .env; see config.py).
"""

from __future__ import annotations

import numpy as np

from app.config import ModelConfig

_model = None
_active_model_id = None


def _load_model():
    global _model, _active_model_id
    if _model is not None:
        return _model

    from faster_whisper import WhisperModel

    if ModelConfig.USE_ASR_FALLBACK:
        model_id = ModelConfig.ASR_FALLBACK_MODEL_ID
        revision = ModelConfig.ASR_FALLBACK_MODEL_REVISION
    else:
        model_id = ModelConfig.ASR_MODEL_ID
        revision = ModelConfig.ASR_MODEL_REVISION

    _model = WhisperModel(model_id, revision=revision, device="auto", compute_type="auto")
    _active_model_id = model_id
    return _model


def warm_up() -> None:
    """Call once at service startup so the first real request isn't
    also paying model download/load latency."""
    _load_model()


# Distil-whisper defaults to American spelling and has no F1-specific
# vocabulary, which measurably hurt Day-1 WER: "tyre/tyres" consistently
# came out "tire/tires", and driver surnames + jargon got mangled or
# hallucinated (Verstappen -> "the Stappan", damage -> "for Davids").
# initial_prompt biases decoding toward this vocabulary without
# retraining anything -- see VALIDATION_GATES.md gate 1 for before/after.
_F1_INITIAL_PROMPT = (
    "Formula 1 team radio transcript, British spelling: tyre, tyres, kerb, "
    "colour. Drivers: Verstappen, Ricciardo, Hamilton, Vettel, Raikkonen, "
    "Alonso, Perez, Bottas, Stroll, Ocon, Hartley, Leclerc, Hulkenberg. "
    "Terms: DRS, PU, quali, torque, undercut, box box box, pit board, gap, "
    "delta, puncture, oversteer, understeer, brake, braking, brake balance."
)


def transcribe(waveform: np.ndarray) -> tuple[str, str]:
    """16 kHz mono float32 array -> (transcript, model_id_used)."""
    model = _load_model()
    segments, _info = model.transcribe(
        waveform,
        language="en",
        vad_filter=False,
        beam_size=8,
        initial_prompt=_F1_INITIAL_PROMPT,
    )
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    return transcript, _active_model_id
