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


def _confidence_from_margin(value: float, threshold: float, scale: float = 1.0) -> float:
    """How far past `threshold` `value` is, as a smooth 0-1 score.

    Replaces a hard `1.0 - arousal` / raw-value-as-score approach that
    silently degenerated to exactly 0.0 or 1.0 on every real clip once
    Day-1 data showed raw Arousal routinely exceeds 1.0 even for CALM
    clips (see VALIDATION_GATES.md gate 4) -- `1.0 - 1.9` clamped to 0
    every time, so the field carried no real gradation at all. A
    logistic margin gives a genuine gradient with no hard edge: 0.5 at
    the threshold, approaching 1/0 as `value` moves further past it.
    """
    import math

    return 1.0 / (1.0 + math.exp(-(value - threshold) / scale))


def map_to_label(scores: dict[str, float]) -> tuple[str, float, float]:
    """Raw VoiceCLAP scores -> (tone_label, tone_score, tone_confidence).

    Thresholds are calibrated from the Day-1 human-labeled sample (see
    ToneThresholds, VALIDATION_GATES.md gate 2/3) -- still n=20, revisit
    as more labeled clips accumulate.
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
        tone_score = _confidence_from_margin(fatigue, ToneThresholds.FATIGUE_THRESHOLD)
    elif arousal >= ToneThresholds.AROUSAL_ELEVATED_THRESHOLD:
        label = "ELEVATED_AROUSAL"
        tone_score = _confidence_from_margin(arousal, ToneThresholds.AROUSAL_ELEVATED_THRESHOLD)
    else:
        label = "CALM"
        tone_score = _confidence_from_margin(ToneThresholds.AROUSAL_ELEVATED_THRESHOLD, arousal)

    # Poor recording quality / high background noise doesn't change the
    # label, it lowers how much we trust it -- never silently hide that
    # a clip was too noisy to be confident about.
    noise_penalty = 1.0 - max(0.0, ToneThresholds.LOW_QUALITY_NOISE_FLOOR - quality)
    confidence = max(0.0, min(1.0, tone_score * noise_penalty))

    return label, float(tone_score), float(confidence)
