"""Gate 6: benchmark the complaint classifier against a human-labeled
worksheet (see build_classifier_worksheet.py). Computes macro-F1 and
NO_COMPLAINT F1 for both deberta-v3-base and deberta-v3-xsmall, prints
a summary ready to paste into VALIDATION_GATES.md.

Reimplements the same decision logic as app/complaint_classifier.py
(same ClassifierConfig constants: taxonomy wording, precedence order,
null threshold) rather than calling it directly, so two different
model_ids can be benchmarked in one process without fighting that
module's single cached pipeline.

Usage:
    python scripts/benchmark_classifier.py --worksheet classifier_worksheet.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ClassifierConfig, ModelConfig  # noqa: E402

LABELS = list(ClassifierConfig.TAXONOMY.keys())  # includes NO_COMPLAINT


def classify_with(pipeline_obj, transcript: str) -> str:
    """Same decision rule as app/complaint_classifier.py::classify,
    but returns a label from LABELS directly (never None) since the
    worksheet always has a human_label to compare against, including
    NO_COMPLAINT explicitly -- no null/None special-casing needed here.
    """
    result = pipeline_obj(
        transcript,
        LABELS,
        hypothesis_template=ClassifierConfig.HYPOTHESIS_TEMPLATE,
        multi_label=True,
    )
    scored = dict(zip(result["labels"], result["scores"]))

    if scored.get("NO_COMPLAINT", 0.0) >= ClassifierConfig.NULL_THRESHOLD:
        top_non_null = max((l for l in scored if l != "NO_COMPLAINT"), key=lambda l: scored[l])
        if scored["NO_COMPLAINT"] >= scored[top_non_null]:
            return "NO_COMPLAINT"

    for label in ClassifierConfig.PRECEDENCE_ORDER:
        if scored.get(label, 0.0) >= ClassifierConfig.NULL_THRESHOLD:
            return label

    return "NO_COMPLAINT"


def compute_f1(rows: list[tuple[str, str]]) -> tuple[dict[str, float], float]:
    """rows: list of (true_label, predicted_label). Returns (per-class F1, macro-F1)."""
    tp = Counter()
    fp = Counter()
    fn = Counter()
    for true, pred in rows:
        if true == pred:
            tp[true] += 1
        else:
            fp[pred] += 1
            fn[true] += 1

    per_class_f1 = {}
    for label in LABELS:
        precision = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) else 0.0
        recall = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class_f1[label] = f1

    macro_f1 = sum(per_class_f1.values()) / len(per_class_f1)
    return per_class_f1, macro_f1


def run_model(model_id: str, revision: str, examples: list[tuple[str, str]]) -> None:
    from transformers import pipeline

    print(f"\nLoading {model_id} ({revision[:8]})...")
    classifier = pipeline("zero-shot-classification", model=model_id, revision=revision)

    predictions = []
    for transcript, true_label in examples:
        pred = classify_with(classifier, transcript)
        predictions.append((true_label, pred))

    per_class_f1, macro_f1 = compute_f1(predictions)

    print(f"\n=== {model_id} ===")
    for label in LABELS:
        print(f"  {label:<28s} F1={per_class_f1[label]:.3f}")
    print(f"  {'MACRO-F1':<28s} {macro_f1:.3f}")
    print(f"  {'NO_COMPLAINT F1':<28s} {per_class_f1['NO_COMPLAINT']:.3f}")

    n_correct = sum(1 for true, pred in predictions if true == pred)
    print(f"  accuracy: {n_correct}/{len(predictions)} ({n_correct / len(predictions):.1%})")

    mistakes = [(t, tr, p) for (tr, t), (_, p) in zip(examples, predictions) if t != p]
    if mistakes:
        print(f"  mistakes ({len(mistakes)}):")
        for true, transcript, pred in mistakes[:15]:
            print(f"    [{true} -> {pred}] {transcript[:80]!r}")

    return macro_f1


def main(worksheet_path: str) -> None:
    examples: list[tuple[str, str]] = []
    skipped = 0
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if not label:
                skipped += 1
                continue
            if label not in LABELS:
                print(f"WARNING: row {row['id']} has unrecognized human_label {label!r}, skipping")
                skipped += 1
                continue
            examples.append((row["transcription"], label))

    print(f"Loaded {len(examples)} labeled examples ({skipped} skipped/blank)")
    if len(examples) < 60:
        print(
            f"WARNING: gate 6 asks for >=60 labeled examples, only {len(examples)} "
            f"present. Results below are informative but the gate isn't fully met."
        )

    label_counts = Counter(label for _, label in examples)
    print("Label distribution:", dict(label_counts))

    base_f1 = run_model(
        ModelConfig.CLASSIFIER_MODEL_ID, ModelConfig.CLASSIFIER_MODEL_REVISION, examples
    )
    xsmall_f1 = run_model(
        ModelConfig.CLASSIFIER_FALLBACK_MODEL_ID,
        ModelConfig.CLASSIFIER_FALLBACK_MODEL_REVISION,
        examples,
    )

    print("\n=== Gate 6c decision ===")
    diff_pp = (base_f1 - xsmall_f1) * 100
    print(f"base macro-F1={base_f1:.3f}, xsmall macro-F1={xsmall_f1:.3f}, diff={diff_pp:.1f}pp")
    if diff_pp <= 3.0:
        print(
            "xsmall is within 3pp of base. Per VALIDATION_GATES.md gate 6c: "
            "switch to xsmall (USE_CLASSIFIER_FALLBACK=true) ONLY if the service "
            "is CPU-only. If you have GPU access for the demo, keep base."
        )
    else:
        print("xsmall is more than 3pp worse. Keep base regardless of CPU/GPU.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="classifier_worksheet.csv")
    args = parser.parse_args()
    main(args.worksheet)
