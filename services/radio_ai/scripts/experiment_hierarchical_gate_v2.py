"""Gate 6 follow-up to experiment_hierarchical_gate.py: that experiment's
own error analysis found stage 1 (binary complaint/no-complaint) is the
specific weak point -- 24/58 wrong, overconfident on informational lines
that merely mention mechanical vocabulary without complaining
("We think Verstappen has some damage.", "Sebastian, we need to retire
the car in the garage."). This tries to fix stage 1 specifically, per
VALIDATION_GATES.md gate 6's "things worth trying #1":

1. Several stage-1 hypothesis phrasings, contrasting "reporting a
   problem" against "relaying information/status" more explicitly than
   the original pair did.
2. A swept stage-1 decision threshold (was hardcoded at >0.5) against
   each phrasing.

Targets deberta-v3-xsmall by default -- the actual current production
model (see app/config.py, USE_CLASSIFIER_FALLBACK=true) and the real
baseline to beat (single-pass macro-F1 0.393, see GATE6_ERROR_ANALYSIS.md).
Stage 2 (which of the 5 real categories) doesn't depend on the stage-1
hypothesis wording or threshold, so its raw scores are computed once
and reused across every combination -- same caching principle as
benchmark_classifier.py's threshold sweep.

Usage:
    python scripts/experiment_hierarchical_gate_v2.py --worksheet labeling_pass_consensus_review.csv
    python scripts/experiment_hierarchical_gate_v2.py --model base   # to also check base
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ClassifierConfig, ModelConfig  # noqa: E402
from benchmark_classifier import LABELS, compute_f1  # noqa: E402

REAL_CATEGORIES = [l for l in LABELS if l != "NO_COMPLAINT"]
REAL_CATEGORY_HYPOTHESES = [ClassifierConfig.TAXONOMY[l] for l in REAL_CATEGORIES]
REAL_HYPOTHESIS_TO_LABEL = dict(zip(REAL_CATEGORY_HYPOTHESES, REAL_CATEGORIES))

STAGE1_HYPOTHESIS_TEMPLATE = "This message {}."

STAGE1_CANDIDATES = {
    "original": (
        "describes a problem with the car",
        "is routine radio communication with no complaint",
    ),
    "reporting_vs_relaying": (
        "reports something currently wrong with the car",
        "relays strategy, timing, position, or status information with nothing wrong reported",
    ),
    "problem_vs_mention": (
        "reports an ongoing problem affecting the car right now",
        "mentions car-related topics only as routine information, not as a problem",
    ),
    "complaint_vs_observation": (
        "is the driver or team complaining about how the car is behaving",
        "is an observation, question, or instruction that does not complain about the car's behavior",
    ),
}

THRESHOLD_SWEEP = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

CORRECTED_SINGLE_PASS_BASELINE = {"base": 0.258, "xsmall": 0.393}


def load_examples(worksheet_path: str) -> list[tuple[str, str]]:
    examples = []
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if label and label in LABELS:
                examples.append((row["transcription"], label))
    return examples


def main(worksheet_path: str, model_key: str) -> None:
    examples = load_examples(worksheet_path)
    print(f"Loaded {len(examples)} labeled examples")
    print(f"Target model: {model_key}\n")

    from transformers import pipeline

    if model_key == "base":
        model_id, revision = ModelConfig.CLASSIFIER_MODEL_ID, ModelConfig.CLASSIFIER_MODEL_REVISION
    else:
        model_id, revision = ModelConfig.CLASSIFIER_FALLBACK_MODEL_ID, ModelConfig.CLASSIFIER_FALLBACK_MODEL_REVISION

    classifier = pipeline("zero-shot-classification", model=model_id, revision=revision)

    # Stage 2 raw scores: computed once, reused for every stage-1 candidate/threshold.
    print("Scoring stage 2 (category, given it IS a complaint) for all examples once...")
    stage2_cache = []
    for transcript, true_label in examples:
        stage2 = classifier(
            transcript, REAL_CATEGORY_HYPOTHESES, hypothesis_template=ClassifierConfig.HYPOTHESIS_TEMPLATE, multi_label=False
        )
        top_category = REAL_HYPOTHESIS_TO_LABEL[stage2["labels"][0]]
        stage2_cache.append(top_category)

    best_overall = {"macro_f1": -1.0, "candidate": None, "threshold": None, "per_class": None}

    for candidate_name, (complaint_hyp, no_complaint_hyp) in STAGE1_CANDIDATES.items():
        print(f"\n=== Stage-1 candidate: {candidate_name!r} ===")
        print(f"  complaint hypothesis: {complaint_hyp!r}")
        print(f"  no-complaint hypothesis: {no_complaint_hyp!r}")

        stage1_scores = []
        for transcript, true_label in examples:
            stage1 = classifier(
                transcript, [complaint_hyp, no_complaint_hyp],
                hypothesis_template=STAGE1_HYPOTHESIS_TEMPLATE, multi_label=False,
            )
            scored = dict(zip(stage1["labels"], stage1["scores"]))
            stage1_scores.append(scored[complaint_hyp])

        print(f"  {'threshold':<10} {'macro-F1':<10} {'accuracy':<10}")
        for threshold in THRESHOLD_SWEEP:
            predictions = []
            for (transcript, true_label), complaint_score, stage2_category in zip(examples, stage1_scores, stage2_cache):
                if complaint_score > threshold:
                    predictions.append((true_label, stage2_category))
                else:
                    predictions.append((true_label, "NO_COMPLAINT"))
            per_class_f1, macro_f1 = compute_f1(predictions)
            accuracy = sum(1 for t, p in predictions if t == p) / len(predictions)
            marker = ""
            if macro_f1 > best_overall["macro_f1"]:
                best_overall.update(
                    macro_f1=macro_f1, candidate=candidate_name, threshold=threshold, per_class=per_class_f1
                )
                marker = "  <- best overall so far"
            print(f"  {threshold:<10} {macro_f1:<10.3f} {accuracy:<10.1%}{marker}")

    baseline = CORRECTED_SINGLE_PASS_BASELINE[model_key]
    print(f"\n=== Best combination ===")
    print(f"candidate={best_overall['candidate']!r}  threshold={best_overall['threshold']}  macro-F1={best_overall['macro_f1']:.3f}")
    for label in LABELS:
        print(f"  {label:<28s} F1={best_overall['per_class'][label]:.3f}")
    print(f"\nSingle-pass baseline for {model_key}: {baseline:.3f}")
    print(f"Delta: {(best_overall['macro_f1'] - baseline) * 100:+.1f}pp")

    # Full mistake list at the best combination, for the record.
    complaint_hyp, no_complaint_hyp = STAGE1_CANDIDATES[best_overall["candidate"]]
    stage1_scores = []
    for transcript, true_label in examples:
        stage1 = classifier(
            transcript, [complaint_hyp, no_complaint_hyp],
            hypothesis_template=STAGE1_HYPOTHESIS_TEMPLATE, multi_label=False,
        )
        scored = dict(zip(stage1["labels"], stage1["scores"]))
        stage1_scores.append(scored[complaint_hyp])

    mistakes = []
    for (transcript, true_label), complaint_score, stage2_category in zip(examples, stage1_scores, stage2_cache):
        pred = stage2_category if complaint_score > best_overall["threshold"] else "NO_COMPLAINT"
        if pred != true_label:
            mistakes.append((true_label, pred, transcript))
    print(f"\nMistakes at best combination ({len(mistakes)}):")
    for true, pred, transcript in mistakes:
        print(f"    [{true} -> {pred}] {transcript[:80]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="labeling_pass_consensus_review.csv")
    parser.add_argument("--model", default="xsmall", choices=["base", "xsmall"])
    args = parser.parse_args()
    main(args.worksheet, args.model)
