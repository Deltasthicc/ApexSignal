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

    # Backend selection for app/complaint_classifier.py::classify().
    # History: nli-base (Day-2 default) -> nli-xsmall (2026-08-14, gate
    # 6c: xsmall's corrected macro-F1 0.393 beat base's 0.258 by 13.5pp)
    # -> embedding (same day, gate 6d: a genuinely different
    # architecture -- sentence embeddings + prototype cosine similarity
    # -- measured macro-F1 0.454, beating xsmall by 6.1pp). See
    # VALIDATION_GATES.md gate 6d and GATE6_ERROR_ANALYSIS.md "Attempt
    # 4" for the full sweep this is based on. NLI stays selectable
    # (nli-base / nli-xsmall) in case a later experiment makes it
    # competitive again -- flip this back explicitly if so, with the
    # numbers recorded, not silently.
    #
    # Supersedes the old USE_CLASSIFIER_FALLBACK boolean (removed
    # 2026-08-14) -- this one switch now covers all three options that
    # flag only gated two of.
    CLASSIFIER_BACKEND = os.environ.get("CLASSIFIER_BACKEND", "embedding")

    # --- Embedding-prototype classifier backend (CLASSIFIER_BACKEND=embedding) --
    # Verified against the live HF Hub API before adoption (2026-08-14):
    # exists, ungated, Apache-2.0, sha as pinned below -- same bar every
    # other model in this file was held to. Already a dependency of
    # services/core_api's retrieval module, so not a new unknown to this
    # project's stack, just to radio_ai's own venv/requirements.txt.
    EMBEDDING_MODEL_ID = os.environ.get(
        "EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_MODEL_REVISION = os.environ.get(
        "EMBEDDING_MODEL_REVISION", "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
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

    Recalibrated from the Day-1 human-labeled sample (20 real F1 radio
    clips, see VALIDATION_GATES.md gate 2/3) -- the original 0.6/0.7
    starting guesses were carried over from VoiceCLAP's own eval-set
    stats (Arousal r=0.82, Fatigue_Exhaustion r=0.48), not this domain,
    and turned out to be badly miscalibrated: every one of the 20 real
    clips scored Arousal > 0.6, so the pipeline called almost everything
    "elevated" regardless of how it actually sounded (gate 2a: 40%
    agreement). n=20 is still small and this is one dataset/era of F1
    radio -- re-check this threshold as more labeled clips accumulate,
    don't treat it as final.
    """

    # Grid-searched against 20 human CALM/ELEVATED_AROUSAL labels to
    # maximize agreement -- 85% (17/20) across a 2.55-2.58 plateau, see
    # VALIDATION_GATES.md gate 2a. Was 0.6, which scored 40%.
    AROUSAL_ELEVATED_THRESHOLD = float(
        os.environ.get("AROUSAL_ELEVATED_THRESHOLD", "2.565")
    )
    # NEEDS_CALIBRATION STILL: none of the 20 Day-1 clips were actually
    # fatigued, so this sample has zero true positives to calibrate
    # against -- raising it to 1.1 only clears the 2 known false
    # positives at 0.7 (SEBVET01_5_172625, VALBOT01_77_172205, both
    # human-rated CALM). This does NOT mean fatigue detection works;
    # it means we haven't seen it fail again yet. Needs real fatigued
    # clips before this can be trusted. Bias toward precision, not
    # recall -- see charter risk register.
    FATIGUE_THRESHOLD = float(os.environ.get("FATIGUE_THRESHOLD", "1.1"))

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

    # Only used when CLASSIFIER_BACKEND is nli-base or nli-xsmall (see
    # ModelConfig) -- the embedding backend uses
    # EMBEDDING_SIMILARITY_MARGIN below instead. Calibrated from the
    # Gate 6 benchmark (58 human-labeled transcripts, see
    # VALIDATION_GATES.md gate 6). The first calibration pass (0.15)
    # was measured against a benchmark_classifier.py that didn't match
    # this module's actual candidate-label construction (bare taxonomy
    # keys vs. the real descriptive hypotheses complaint_classifier.py
    # uses) -- fixed 2026-08-14, re-swept. 0.45 was base's genuine best
    # point (macro-F1 0.258); 0.15 is xsmall's (macro-F1 0.393). Kept
    # here for whichever NLI variant gets selected via
    # CLASSIFIER_BACKEND; if you switch back to nli-xsmall, use 0.15,
    # not this default. n=58, one dataset -- revisit as more labeled
    # transcripts accumulate.
    NULL_THRESHOLD = float(os.environ.get("CLASSIFIER_NULL_THRESHOLD", "0.15"))

    # Similarity margin for the embedding-prototype backend
    # (app/complaint_classifier.py, CLASSIFIER_BACKEND=embedding).
    # Swept 0.00-0.30 against the same 58-example Gate 6 benchmark
    # (scripts/experiment_embedding_classifier.py) -- 0.16 is the
    # genuine best point (macro-F1 0.454). Sits on a noisy part of the
    # sweep curve (0.16->0.454, 0.18->0.384) -- n=58 is thin, see
    # GATE6_ERROR_ANALYSIS.md "Attempt 4" before trusting this past
    # this specific sample.
    EMBEDDING_SIMILARITY_MARGIN = float(
        os.environ.get("EMBEDDING_SIMILARITY_MARGIN", "0.16")
    )
