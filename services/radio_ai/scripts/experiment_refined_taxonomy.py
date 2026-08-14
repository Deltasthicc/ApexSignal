"""Gate 6 follow-up #2: experiment_hierarchical_gate_v2.py confirmed the
single-pass multi_label architecture beats hierarchical splitting no
matter how stage 1 is phrased (-11.2pp best case, see
GATE6_ERROR_ANALYSIS.md). This keeps that winning architecture and
instead tunes each category's own TAXONOMY description individually,
targeting the two known error patterns directly:

1. MECHANICAL_OTHER false positives on negated/reassuring/third-party
   mentions ("Do you want a front wing change? No, not for now.",
   "We think Verstappen has some damage.") -- revised to explicitly
   require an active fault on the driver's OWN car, not a hypothetical,
   denied, resolved, or another car's issue.
2. EXIT_TRACTION_REAR / FRONT_TURNIN_BRAKE / TYRE_GRIP_DEGRADATION false
   negatives on calm, matter-of-fact complaints ("the rear tyres are
   getting really hot, that's my main problem") -- revised to explicitly
   include calm/factual framing, not just intense language.
3. NO_COMPLAINT strengthened to explicitly cover third-party/resolved/
   hypothetical mentions, so it can keep winning against MECHANICAL_OTHER
   on exactly the sentences that trip it up.

Does NOT modify app/config.py -- tests the revised wording in-memory
first, same rule as every other Gate 6 change this project makes.

Usage:
    python scripts/experiment_refined_taxonomy.py --worksheet labeling_pass_consensus_review.csv --model xsmall
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ClassifierConfig, ModelConfig  # noqa: E402
from benchmark_classifier import LABELS, THRESHOLD_SWEEP, compute_f1, decide  # noqa: E402

REFINED_TAXONOMY = {
    "MECHANICAL_OTHER": (
        "a new, currently active mechanical or system fault on the "
        "driver's own car right now: an engine, gearbox, steering, or "
        "brake-system malfunction, a puncture, damage, or abnormal "
        "vibration or temperature -- not something already fixed, "
        "denied, hypothetical, or affecting a different car"
    ),
    "FRONT_TURNIN_BRAKE": (
        "the driver reporting, even in a calm or matter-of-fact tone, "
        "that the front of the car is not turning in, is locking under "
        "braking, or has lost grip on entry"
    ),
    "EXIT_TRACTION_REAR": (
        "the driver reporting, even in a calm or matter-of-fact tone, "
        "that the rear of the car feels unstable, is spinning, sliding, "
        "or lacks traction under power or on corner exit"
    ),
    "TYRE_GRIP_DEGRADATION": (
        "the driver reporting, even in a calm tone, that overall tyre "
        "grip is fading, or tyres are overheating, graining, or wearing "
        "out -- not better described by another category"
    ),
    "VISIBILITY_TRACK_CONDITION": (
        "the driver or team reporting that it is currently raining, "
        "there is spray, standing water, a slippery surface, debris, or "
        "reduced visibility on track right now -- not a forecast or "
        "hypothetical discussion of weather"
    ),
    "NO_COMPLAINT": (
        "strategy discussion, acknowledgement, an instruction, timing "
        "or position information, encouragement, a description of "
        "another car's situation, a resolved or hypothetical issue, or "
        "ordinary traffic information -- with no new problem currently "
        "affecting the speaker's own car"
    ),
}


def score_transcript(pipeline_obj, transcript: str, hypotheses: list[str], hypothesis_to_label: dict[str, str]) -> dict[str, float]:
    result = pipeline_obj(
        transcript, hypotheses, hypothesis_template=ClassifierConfig.HYPOTHESIS_TEMPLATE, multi_label=True
    )
    return {hypothesis_to_label[h]: s for h, s in zip(result["labels"], result["scores"])}


def run_sweep(name: str, taxonomy: dict[str, str], classifier, examples: list[tuple[str, str]]) -> tuple[float, float, dict]:
    hypotheses = [taxonomy[l] for l in LABELS]
    hyp_to_label = dict(zip(hypotheses, LABELS))

    cached_scores = [(true, score_transcript(classifier, transcript, hypotheses, hyp_to_label)) for transcript, true in examples]

    print(f"\n=== {name}: threshold sweep ===")
    print(f"{'threshold':<10} {'macro-F1':<10} {'accuracy':<10}")
    best_threshold, best_macro_f1, best_per_class = None, -1.0, None
    for threshold in THRESHOLD_SWEEP:
        predictions = [(true, decide(scored, threshold)) for true, scored in cached_scores]
        per_class_f1, macro_f1 = compute_f1(predictions)
        accuracy = sum(1 for t, p in predictions if t == p) / len(predictions)
        marker = ""
        if macro_f1 > best_macro_f1:
            best_macro_f1, best_threshold, best_per_class = macro_f1, threshold, per_class_f1
            marker = "  <- best so far"
        print(f"{threshold:<10} {macro_f1:<10.3f} {accuracy:<10.1%}{marker}")

    print(f"\nBest for {name}: threshold={best_threshold}  macro-F1={best_macro_f1:.3f}")
    for label in LABELS:
        print(f"  {label:<28s} F1={best_per_class[label]:.3f}")

    best_predictions = [(true, decide(scored, best_threshold)) for true, scored in cached_scores]
    mistakes = [(t, tr, p) for (tr, t), (_, p) in zip(examples, best_predictions) if t != p]
    print(f"Mistakes at best threshold ({len(mistakes)}):")
    for true, transcript, pred in mistakes:
        print(f"    [{true} -> {pred}] {transcript[:80]!r}")

    return best_threshold, best_macro_f1, best_per_class


def main(worksheet_path: str, model_key: str) -> None:
    examples = []
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if label and label in LABELS:
                examples.append((row["transcription"], label))
    print(f"Loaded {len(examples)} labeled examples, target model={model_key}")

    from transformers import pipeline

    if model_key == "base":
        model_id, revision = ModelConfig.CLASSIFIER_MODEL_ID, ModelConfig.CLASSIFIER_MODEL_REVISION
    else:
        model_id, revision = ModelConfig.CLASSIFIER_FALLBACK_MODEL_ID, ModelConfig.CLASSIFIER_FALLBACK_MODEL_REVISION
    classifier = pipeline("zero-shot-classification", model=model_id, revision=revision)

    _, current_f1, _ = run_sweep("current TAXONOMY (baseline, re-measured here for a fair same-run comparison)", ClassifierConfig.TAXONOMY, classifier, examples)
    _, refined_f1, _ = run_sweep("REFINED TAXONOMY", REFINED_TAXONOMY, classifier, examples)

    print(f"\n=== Comparison ===")
    print(f"current: {current_f1:.3f}")
    print(f"refined: {refined_f1:.3f}")
    print(f"delta: {(refined_f1 - current_f1) * 100:+.1f}pp")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="labeling_pass_consensus_review.csv")
    parser.add_argument("--model", default="xsmall", choices=["base", "xsmall"])
    args = parser.parse_args()
    main(args.worksheet, args.model)
