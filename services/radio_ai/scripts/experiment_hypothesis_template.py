"""One-off experiment, not a permanent script: does a stricter NLI
hypothesis template reduce the two Gate 6 error patterns (context-blind
false positives on negated/informational mechanical vocabulary, and
missed matter-of-fact complaints)? Reuses benchmark_classifier.py's
exact scoring/decision/F1 code so the comparison is apples-to-apples,
just with ClassifierConfig.HYPOTHESIS_TEMPLATE swapped at runtime --
does not touch app/config.py.

Usage:
    python scripts/experiment_hypothesis_template.py --worksheet labeling_pass_consensus_review.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ClassifierConfig, ModelConfig  # noqa: E402
from benchmark_classifier import LABELS, THRESHOLD_SWEEP, compute_f1, decide, score_transcript  # noqa: E402

TEMPLATES = {
    "baseline": "This message is about {}.",
    "stricter": "The driver is explicitly complaining about a failure with the {}.",
}


def sweep_best(cached_scores):
    best_threshold, best_macro_f1, best_per_class = None, -1.0, None
    for threshold in THRESHOLD_SWEEP:
        predictions = [(true, decide(scored, threshold)) for true, scored in cached_scores]
        per_class_f1, macro_f1 = compute_f1(predictions)
        if macro_f1 > best_macro_f1:
            best_macro_f1, best_threshold, best_per_class = macro_f1, threshold, per_class_f1
    return best_threshold, best_macro_f1, best_per_class


def main(worksheet_path: str) -> None:
    examples: list[tuple[str, str]] = []
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if label and label in LABELS:
                examples.append((row["transcription"], label))
    print(f"Loaded {len(examples)} labeled examples\n")

    from transformers import pipeline

    classifier = pipeline(
        "zero-shot-classification",
        model=ModelConfig.CLASSIFIER_MODEL_ID,
        revision=ModelConfig.CLASSIFIER_MODEL_REVISION,
    )

    results = {}
    for name, template in TEMPLATES.items():
        ClassifierConfig.HYPOTHESIS_TEMPLATE = template
        print(f"Scoring with template {name!r}: {template!r}")
        cached_scores = [
            (true_label, score_transcript(classifier, transcript)) for transcript, true_label in examples
        ]
        best_threshold, best_macro_f1, best_per_class = sweep_best(cached_scores)
        results[name] = (best_threshold, best_macro_f1, best_per_class, cached_scores)
        print(f"  best threshold={best_threshold}  macro-F1={best_macro_f1:.3f}")
        for label in LABELS:
            print(f"    {label:<28s} F1={best_per_class[label]:.3f}")
        print()

    base_threshold, base_f1, _, base_scores = results["baseline"]
    strict_threshold, strict_f1, _, strict_scores = results["stricter"]

    print(f"=== Comparison ===")
    print(f"baseline template: best macro-F1={base_f1:.3f} @ threshold={base_threshold}")
    print(f"stricter template: best macro-F1={strict_f1:.3f} @ threshold={strict_threshold}")
    print(f"delta: {(strict_f1 - base_f1) * 100:+.1f}pp")

    # Did the specific mistakes change, not just the aggregate?
    base_preds = dict(zip((t for t, _ in examples), (decide(s, base_threshold) for _, s in base_scores)))
    strict_preds = dict(zip((t for t, _ in examples), (decide(s, strict_threshold) for _, s in strict_scores)))
    flipped = [
        (transcript, true, base_preds[transcript], strict_preds[transcript])
        for transcript, true in examples
        if base_preds[transcript] != strict_preds[transcript]
    ]
    print(f"\n{len(flipped)} example(s) changed prediction between templates:")
    for transcript, true, b, s in flipped:
        print(f"  true={true:<28s} baseline={b:<20s} stricter={s:<20s} {transcript[:70]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="labeling_pass_consensus_review.csv")
    args = parser.parse_args()
    main(args.worksheet)
