"""Gate 6: benchmark the complaint classifier against a human-labeled
worksheet (see build_classifier_worksheet.py). Computes macro-F1 and
NO_COMPLAINT F1 for both deberta-v3-base and deberta-v3-xsmall, AND
sweeps NULL_THRESHOLD to find the value that actually discriminates on
this domain -- the frozen 0.5 default was always a NEEDS_CALIBRATION
placeholder (see app/config.py), never validated, and the live
pipeline returning complaint_category=None on 40/40 real clips so far
is exactly the failure mode this sweep exists to catch: multi_label=True
scores each label's entailment independently (not a softmax that sums
to 1), so it is entirely plausible for every label, including
NO_COMPLAINT, to sit under 0.5 on short idiomatic radio phrasing. This
mirrors how AROUSAL_ELEVATED_THRESHOLD was calibrated in gate 2 -- grid
search against real human labels, not a guess.

Reimplements the same decision logic as app/complaint_classifier.py
(same ClassifierConfig constants: taxonomy wording, precedence order)
rather than calling it directly, so two different model_ids can be
benchmarked in one process without fighting that module's single
cached pipeline, and so the threshold can vary per sweep step without
touching global config state.

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
HYPOTHESES = [ClassifierConfig.TAXONOMY[label] for label in LABELS]
HYPOTHESIS_TO_LABEL = dict(zip(HYPOTHESES, LABELS))
THRESHOLD_SWEEP = [round(0.05 * i, 2) for i in range(1, 13)]  # 0.05 .. 0.60


def score_transcript(pipeline_obj, transcript: str) -> dict[str, float]:
    """One model call -> raw per-label scores. Cache this; it's the
    expensive part. Everything threshold-dependent happens on the
    cached result, not here.

    Passes the taxonomy's long descriptive text as candidate_labels
    (matching app/complaint_classifier.py's actual production
    behavior, and the project's own stated design -- "the taxonomy
    definition itself becomes the classifier input"), not the bare
    short keys this used to pass. Every Gate 6 number measured before
    this fix (the 0.15 threshold, both rejected experiments) was
    against a hypothesis construction that DIDN'T match production --
    see VALIDATION_GATES.md gate 6/7 for how the mismatch was found.
    """
    result = pipeline_obj(
        transcript,
        HYPOTHESES,
        hypothesis_template=ClassifierConfig.HYPOTHESIS_TEMPLATE,
        multi_label=True,
    )
    return {
        HYPOTHESIS_TO_LABEL[hyp]: score
        for hyp, score in zip(result["labels"], result["scores"])
    }


def decide(scored: dict[str, float], null_threshold: float) -> str:
    """Same decision rule as app/complaint_classifier.py::classify, but
    parameterized by threshold and always returning a label from LABELS
    (never None) -- the worksheet always has a human_label to compare
    against, including NO_COMPLAINT explicitly.
    """
    if scored.get("NO_COMPLAINT", 0.0) >= null_threshold:
        top_non_null = max((l for l in scored if l != "NO_COMPLAINT"), key=lambda l: scored[l])
        if scored["NO_COMPLAINT"] >= scored[top_non_null]:
            return "NO_COMPLAINT"

    for label in ClassifierConfig.PRECEDENCE_ORDER:
        if scored.get(label, 0.0) >= null_threshold:
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


def run_model(model_id: str, revision: str, examples: list[tuple[str, str]]) -> float:
    from transformers import pipeline

    print(f"\nLoading {model_id} ({revision[:8]})...")
    classifier = pipeline("zero-shot-classification", model=model_id, revision=revision)

    print(f"Scoring {len(examples)} examples (one model call each, cached for the sweep)...")
    cached_scores = [
        (true_label, score_transcript(classifier, transcript))
        for transcript, true_label in examples
    ]

    print(f"\n=== {model_id}: threshold sweep ===")
    print(f"{'threshold':<10} {'macro-F1':<10} {'NO_COMPLAINT F1':<16} {'accuracy':<10}")
    best_threshold, best_macro_f1, best_per_class = None, -1.0, None
    for threshold in THRESHOLD_SWEEP:
        predictions = [(true, decide(scored, threshold)) for true, scored in cached_scores]
        per_class_f1, macro_f1 = compute_f1(predictions)
        n_correct = sum(1 for true, pred in predictions if true == pred)
        accuracy = n_correct / len(predictions)
        marker = ""
        if macro_f1 > best_macro_f1:
            best_macro_f1, best_threshold, best_per_class = macro_f1, threshold, per_class_f1
            marker = "  <- best so far"
        print(f"{threshold:<10} {macro_f1:<10.3f} {per_class_f1['NO_COMPLAINT']:<16.3f} {accuracy:<10.1%}{marker}")

    print(f"\nBest threshold for {model_id}: {best_threshold} (macro-F1={best_macro_f1:.3f})")
    print("Per-class F1 at that threshold:")
    for label in LABELS:
        print(f"  {label:<28s} F1={best_per_class[label]:.3f}")

    best_predictions = [(true, decide(scored, best_threshold)) for true, scored in cached_scores]
    mistakes = [
        (t, tr, p) for (tr, t), (_, p) in zip(examples, best_predictions) if t != p
    ]
    if mistakes:
        print(f"Mistakes at best threshold ({len(mistakes)}):")
        for true, transcript, pred in mistakes[:15]:
            print(f"    [{true} -> {pred}] {transcript[:80]!r}")

    print(
        f"\nCurrent config default (NULL_THRESHOLD={ClassifierConfig.NULL_THRESHOLD}) "
        f"is {'the same as' if ClassifierConfig.NULL_THRESHOLD == best_threshold else 'DIFFERENT from'} "
        f"the best threshold found. If different, update NULL_THRESHOLD in "
        f".env / app/config.py to {best_threshold} before trusting live output."
    )

    return best_macro_f1


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
    print(
        f"base best macro-F1={base_f1:.3f}, xsmall best macro-F1={xsmall_f1:.3f}, "
        f"diff={diff_pp:.1f}pp (each at its own best threshold from the sweep above)"
    )
    if diff_pp < -3.0:
        print(
            "xsmall beats base by more than 3pp outright -- switch unconditionally "
            "(USE_CLASSIFIER_FALLBACK=true), the CPU-only tiebreaker doesn't apply "
            "when one model is just better. This is what happened on 2026-08-14: "
            "see VALIDATION_GATES.md gate 6c."
        )
    elif diff_pp <= 3.0:
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
