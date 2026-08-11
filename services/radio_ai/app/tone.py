"""Acoustic tone/arousal stage: VoiceCLAP encoder + attribute heads.

Uses the official reference implementation (voiceclap_heads.py,
laion/voiceclap-commercial-attribute-heads) rather than reimplementing
head-loading, since that file already encodes the exact normalization
contract the heads were trained against.

This is the mandatory PS1 output (calm/stressed/tired) and the least
validated part of the whole pipeline on this specific audio domain --
see VALIDATION_GATES.md before trusting AROUSAL_ELEVATED_THRESHOLD and
FATIGUE_THRESHOLD past a Day-1 smoke test.
"""

from __future__ import annotations

import numpy as np

from app.config import ModelConfig, ToneThresholds

_scorer = None

TONE_DIMS = ["Arousal", "Fatigue_Exhaustion", "Recording_Quality", "Background_Noise"]


def _load_scorer():
    global _scorer
    if _scorer is not None:
        return _scorer

    from huggingface_hub import hf_hub_download

    heads_module_path = hf_hub_download(
        ModelConfig.TONE_HEADS_ID,
        "voiceclap_heads.py",
        revision=ModelConfig.TONE_HEADS_REVISION,
    )

    import importlib.util

    spec = importlib.util.spec_from_file_location("voiceclap_heads", heads_module_path)
    voiceclap_heads = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(voiceclap_heads)

    heads_path = hf_hub_download(
        ModelConfig.TONE_HEADS_ID, "heads.pt", revision=ModelConfig.TONE_HEADS_REVISION
    )
    _scorer = voiceclap_heads.AttributeScorer(
        repo_id=ModelConfig.TONE_HEADS_ID,
        encoder_id=ModelConfig.TONE_ENCODER_ID,
        heads_path=heads_path,
    )
    return _scorer


def warm_up() -> None:
    _load_scorer()


def score_waveform(waveform: np.ndarray) -> dict[str, float]:
    """16 kHz mono float32 array -> raw scores for TONE_DIMS."""
    scorer = _load_scorer()
    scores = scorer.score(waveform, dims=TONE_DIMS)
    return {dim: float(scores[dim]) for dim in TONE_DIMS}


def map_to_label(scores: dict[str, float]) -> tuple[str, float, float]:
    """Raw VoiceCLAP scores -> (tone_label, tone_score, tone_confidence).

    Thresholds are NEEDS_CALIBRATION placeholders (see ToneThresholds).
    Fatigue is checked first and biased toward precision per the
    charter's risk register: a false "fatigued" is worse than a missed
    one in front of judges.
    """
    arousal = scores["Arousal"]
    fatigue = scores["Fatigue_Exhaustion"]
    noise = scores["Background_Noise"]
    quality = scores["Recording_Quality"]

    if fatigue >= ToneThresholds.FATIGUE_THRESHOLD:
        label = "FATIGUED"
        tone_score = fatigue
    elif arousal >= ToneThresholds.AROUSAL_ELEVATED_THRESHOLD:
        label = "ELEVATED_AROUSAL"
        tone_score = arousal
    else:
        label = "CALM"
        tone_score = 1.0 - arousal

    # Poor recording quality / high background noise doesn't change the
    # label, it lowers how much we trust it -- never silently hide that
    # a clip was too noisy to be confident about.
    noise_penalty = 1.0 - max(0.0, ToneThresholds.LOW_QUALITY_NOISE_FLOOR - quality)
    confidence = max(0.0, min(1.0, tone_score * noise_penalty))

    return label, float(max(0.0, min(1.0, tone_score))), float(confidence)
