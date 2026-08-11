"""Frozen Workstream B stack configuration.

Every model/dataset ID here was verified against the live Hugging Face
Hub API on 2026-08-11: confirmed to exist, confirmed ungated, confirmed
license, and pinned to the commit SHA that was current at verification
time. Do not bump a revision without re-running the Day-1 validation
gates in ../VALIDATION_GATES.md against the new weights.

Thresholds marked NEEDS_CALIBRATION are placeholders. They must be set
from the Day-1 human-labeled validation sample before ANALYZE_MODE=live
is trusted for the demo; see VALIDATION_GATES.md.
"""

from __future__ import annotations

import os


class ModelConfig:
    # --- ASR --------------------------------------------------------
    ASR_MODEL_ID = os.environ.get(
        "ASR_MODEL_ID", "distil-whisper/distil-large-v3.5-ct2"
    )
    ASR_MODEL_REVISION = os.environ.get(
        "ASR_MODEL_REVISION", "9793ccc07920e0f830e1dba0343efcdf0ef8c903"
    )
    # CPU fallback if the primary model is too slow on Day-1 hardware.
    ASR_FALLBACK_MODEL_ID = os.environ.get(
        "ASR_FALLBACK_MODEL_ID", "Systran/faster-whisper-small.en"
    )
    ASR_FALLBACK_MODEL_REVISION = os.environ.get(
        "ASR_FALLBACK_MODEL_REVISION", "d1d751a5f8271d482d14ca55d9e2deeebbae577f"
    )
    USE_ASR_FALLBACK = os.environ.get("USE_ASR_FALLBACK", "false").lower() == "true"

    # --- Acoustic tone (VoiceCLAP encoder + attribute heads) --------
    TONE_ENCODER_ID = os.environ.get("TONE_ENCODER_ID", "laion/voiceclap-commercial")
    TONE_ENCODER_REVISION = os.environ.get(
        "TONE_ENCODER_REVISION", "c291e8b13f3bd06e2c917d389133ffabccd53b70"
    )
    TONE_HEADS_ID = os.environ.get(
        "TONE_HEADS_ID", "laion/voiceclap-commercial-attribute-heads"
    )
    TONE_HEADS_REVISION = os.environ.get(
        "TONE_HEADS_REVISION", "8441fbd4050fb670c34453d99b3fdae7e8513667"
    )

    # --- Complaint classification (zero-shot NLI) --------------------
    CLASSIFIER_MODEL_ID = os.environ.get(
        "CLASSIFIER_MODEL_ID", "MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33"
    )
    CLASSIFIER_MODEL_REVISION = os.environ.get(
        "CLASSIFIER_MODEL_REVISION", "613e8c52c33e2bc0677ada4ad760f693e5e0f581"
    )
    # CPU escape hatch if base DeBERTa is too slow. Only switch if base
    # is >3pp worse on the Day-2 taxonomy benchmark (see VALIDATION_GATES.md).
    CLASSIFIER_FALLBACK_MODEL_ID = os.environ.get(
        "CLASSIFIER_FALLBACK_MODEL_ID",
        "MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33",
    )
    CLASSIFIER_FALLBACK_MODEL_REVISION = os.environ.get(
        "CLASSIFIER_FALLBACK_MODEL_REVISION", "262ae02f29173eec1c250f90804dc7edc677dcff"
    )
    USE_CLASSIFIER_FALLBACK = (
        os.environ.get("USE_CLASSIFIER_FALLBACK", "false").lower() == "true"
    )

    # --- Development corpus ------------------------------------------
    DEV_DATASET_ID = os.environ.get("DEV_DATASET_ID", "MikCil/f1-team-radio")
    DEV_DATASET_REVISION = os.environ.get(
        "DEV_DATASET_REVISION", "a0b99e1a325d92d63b574541a24902a660a352ea"
    )

    # --- Feature flags -------------------------------------------------
    # Mask (text-tone disagreement) stays off until the Day-1 acoustic
    # validation gate passes. See VALIDATION_GATES.md, gate 5.
    ENABLE_TEXT_TONE_DISAGREEMENT = (
        os.environ.get("ENABLE_TEXT_TONE_DISAGREEMENT", "false").lower() == "true"
    )


class ToneThresholds:
    """Arousal/fatigue -> {CALM, ELEVATED_AROUSAL, FATIGUED} mapping.

    VoiceCLAP's own model card warns against thresholding raw regression
    scores without domain calibration. These starting points come from
    the head-level validation stats published in the attribute-heads
    config (Arousal r=0.82, Fatigue_Exhaustion r=0.48 on the model's own
    eval set, not on F1 radio) and MUST be recalibrated from the Day-1
    human-labeled sample before they're trusted for anything but a smoke
    test. Do not ship these unchanged past Day 1.
    """

    # NEEDS_CALIBRATION: starting guess only.
    AROUSAL_ELEVATED_THRESHOLD = float(
        os.environ.get("AROUSAL_ELEVATED_THRESHOLD", "0.6")
    )
    # NEEDS_CALIBRATION: fatigue is the least-validated head (r=0.48).
    # Bias toward precision, not recall -- see charter risk register.
    FATIGUE_THRESHOLD = float(os.environ.get("FATIGUE_THRESHOLD", "0.7"))

    # Recording_Quality / Background_Noise scores below this suppress
    # confidence rather than the label itself -- a noisy clip doesn't
    # mean "calm," it means "uncertain."
    LOW_QUALITY_NOISE_FLOOR = float(
        os.environ.get("LOW_QUALITY_NOISE_FLOOR", "0.3")
    )


class ClassifierConfig:
    """Fixed 5-category taxonomy + precedence. See contracts/api_contract.md.

    Wording and precedence order per the Day-2 sign-off draft; treat as
    pending team approval, not silently final -- flag any change back
    to the contract if the taxonomy wording shifts.
    """

    HYPOTHESIS_TEMPLATE = "This message is about {}."

    TAXONOMY: dict[str, str] = {
        "MECHANICAL_OTHER": (
            "an explicit mechanical or system problem: engine, gearbox, "
            "steering, brake-system malfunction, puncture, damage, or "
            "abnormal vibration or temperature"
        ),
        "FRONT_TURNIN_BRAKE": (
            "understeer, front locking, front-grip loss, or poor rotation "
            "associated with braking, entry, or turn-in"
        ),
        "EXIT_TRACTION_REAR": (
            "rear instability, wheelspin, oversteer, or poor traction "
            "associated with power application or corner exit"
        ),
        "TYRE_GRIP_DEGRADATION": (
            "general tyre deterioration, overheating, graining, wear, or "
            "falling grip not better described by another category"
        ),
        "VISIBILITY_TRACK_CONDITION": (
            "rain, spray, standing water, a slippery surface, debris, or "
            "a visibility or track-condition problem"
        ),
        "NO_COMPLAINT": (
            "strategy discussion, acknowledgement, an instruction, timing "
            "information, encouragement, or ordinary traffic information "
            "with no reported problem"
        ),
    }

    # Applied when multiple categories score above NULL_THRESHOLD; first
    # match in this order wins. Keeps interpretation consistent across
    # ambiguous messages instead of leaving it to model score noise.
    PRECEDENCE_ORDER = [
        "MECHANICAL_OTHER",
        "FRONT_TURNIN_BRAKE",
        "EXIT_TRACTION_REAR",
        "TYRE_GRIP_DEGRADATION",
        "VISIBILITY_TRACK_CONDITION",
    ]

    # NEEDS_CALIBRATION from the Day-2 60-90 example benchmark.
    NULL_THRESHOLD = float(os.environ.get("CLASSIFIER_NULL_THRESHOLD", "0.5"))
