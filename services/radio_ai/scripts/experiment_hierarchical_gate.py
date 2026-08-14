"""One-off experiment: does splitting classification into two stages --
(1) binary "is this a complaint at all?" then (2) "which of the 5
categories?" only if stage 1 says yes -- beat the current single-pass
multi_label=True approach? This was the second candidate fix noted in
GATE6_ERROR_ANALYSIS.md alongside the (rejected) hypothesis-template
change. Tested directly against the same 58 labeled examples, not
reasoned about.

Usage:
    python scripts/experiment_hierarchical_gate.py --worksheet labeling_pass_consensus_review.csv
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

STAGE1_HYPOTHESIS = "This message {}."
STAGE1_LABELS = ["describes a problem with the car", "is routine radio communication with no complaint"]
STAGE1_COMPLAINT_LABEL = "describes a problem with the car"


def load_examples(worksheet_path: str) -> list[tuple[str, str]]:
    examples = []
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if label and label in LABELS:
                examples.append((row["transcription"], label))
    return examples


def main(worksheet_path: str) -> None:
    examples = load_examples(worksheet_path)
    print(f"Loaded {len(examples)} labeled examples\n")

    from transformers import pipeline

    classifier = pipeline(
        "zero-shot-classification",
        model=ModelConfig.CLASSIFIER_MODEL_ID,
        revision=ModelConfig.CLASSIFIER_MODEL_REVISION,
    )

    predictions = []
    stage1_calls = []
    for transcript, true_label in examples:
        # Stage 1: binary, single-label (softmax over exactly 2 options,
        # not independent multi_label scores) -- this is the actual
        # structural change, not just a relabeled hypothesis.
        stage1 = classifier(transcript, STAGE1_LABELS, hypothesis_template=STAGE1_HYPOTHESIS, multi_label=False)
        stage1_scored = dict(zip(stage1["labels"], stage1["scores"]))
        is_complaint = stage1_scored[STAGE1_COMPLAINT_LABEL] > 0.5
        stage1_calls.append((transcript, true_label, is_complaint, stage1_scored[STAGE1_COMPLAINT_LABEL]))

        if not is_complaint:
            predictions.append((true_label, "NO_COMPLAINT"))
            continue

        # Stage 2: which of the 5 real categories -- single-label over
        # just those 5, argmax (we've already decided it IS a complaint).
        # Uses the taxonomy's rich descriptive text as candidate_labels,
        # matching production (app/complaint_classifier.py) -- passing
        # bare short keys here was the same construction mismatch fixed
        # there and in benchmark_classifier.py.
        stage2 = classifier(
            transcript, REAL_CATEGORY_HYPOTHESES, hypothesis_template=ClassifierConfig.HYPOTHESIS_TEMPLATE, multi_label=False
        )
        top_category = REAL_HYPOTHESIS_TO_LABEL[stage2["labels"][0]]  # pipeline sorts by score descending
        predictions.append((true_label, top_category))

    per_class_f1, macro_f1 = compute_f1(predictions)
    accuracy = sum(1 for t, p in predictions if t == p) / len(predictions)

    print(f"=== Hierarchical gate result ===")
    print(f"macro-F1={macro_f1:.3f}  accuracy={accuracy:.1%}")
    for label in LABELS:
        print(f"  {label:<28s} F1={per_class_f1[label]:.3f}")

    # 0.258 is the corrected baseline (single-pass multi_label, threshold
    # 0.45) after the classify() key-mismatch fix -- see VALIDATION_GATES.md
    # gate 6. The pre-fix 0.356 was never real; don't reintroduce it here.
    CORRECTED_BASELINE_MACRO_F1 = 0.258
    print(f"\nBaseline (single-pass multi_label, threshold 0.45) is macro-F1={CORRECTED_BASELINE_MACRO_F1} -- see GATE6_ERROR_ANALYSIS.md")
    print(f"Delta: {(macro_f1 - CORRECTED_BASELINE_MACRO_F1) * 100:+.1f}pp")

    stage1_wrong = [
        (t, tl, ic, score) for t, tl, ic, score in stage1_calls
        if (tl == "NO_COMPLAINT") != (not ic)
    ]
    print(f"\nStage 1 (binary complaint detection) errors: {len(stage1_wrong)}/{len(examples)}")
    for transcript, true_label, is_complaint, score in stage1_wrong[:15]:
        print(f"  true={true_label:<28s} stage1_said_complaint={is_complaint}  score={score:.3f}  {transcript[:60]!r}")

    mistakes = [(t, tr, p) for (tr, t), (_, p) in zip(examples, predictions) if t != p]
    print(f"\nFull mistakes ({len(mistakes)}):")
    for true, transcript, pred in mistakes:
        print(f"    [{true} -> {pred}] {transcript[:80]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="labeling_pass_consensus_review.csv")
    args = parser.parse_args()
    main(args.worksheet)
