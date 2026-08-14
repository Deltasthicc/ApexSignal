"""Gate 6 Part 2, item 2: does combining NLI-xsmall and the adopted
embedding classifier beat either alone? Checked first whether their
mistakes actually overlap (see GATE6_ERROR_ANALYSIS.md "Item 2") --
only 9 of 29 unique wrong examples do, so this was worth trying per
this gate's own rule ("only worth trying if the mistake lists are
actually different").

Combination rule, decided BEFORE looking at the result (to avoid
overfitting the rule itself to this exact 58-example set):
1. Both models agree -> use it.
2. One says a real category, the other says NO_COMPLAINT -> trust the
   real-category call (favor detection).
3. Both name different real categories -> default to embedding's (the
   higher aggregate scorer, the actual production choice).

Usage:
    python scripts/experiment_ensemble.py --worksheet labeling_pass_consensus_review.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import complaint_classifier  # noqa: E402
from app.config import ModelConfig  # noqa: E402
from benchmark_classifier import LABELS, compute_f1, decide, score_transcript  # noqa: E402


def main(worksheet_path: str) -> None:
    examples = []
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if label and label in LABELS:
                examples.append((row["transcription"], label))
    print(f"Loaded {len(examples)} labeled examples")
    print(f"Production backend right now: {ModelConfig.CLASSIFIER_BACKEND}")

    from transformers import pipeline

    xsmall = pipeline(
        "zero-shot-classification",
        model=ModelConfig.CLASSIFIER_FALLBACK_MODEL_ID,
        revision=ModelConfig.CLASSIFIER_FALLBACK_MODEL_REVISION,
    )

    predictions = []
    both_real_disagree = 0
    xsmall_mistakes, embedding_mistakes = set(), set()

    for transcript, true_label in examples:
        emb_pred, _ = complaint_classifier.classify(transcript)
        emb_pred = emb_pred if emb_pred else "NO_COMPLAINT"
        if emb_pred != true_label:
            embedding_mistakes.add(transcript)

        scored = score_transcript(xsmall, transcript)
        xs_pred = decide(scored, 0.15)
        if xs_pred != true_label:
            xsmall_mistakes.add(transcript)

        if emb_pred == xs_pred:
            final = emb_pred
        elif emb_pred == "NO_COMPLAINT":
            final = xs_pred
        elif xs_pred == "NO_COMPLAINT":
            final = emb_pred
        else:
            both_real_disagree += 1
            final = emb_pred  # predefined tiebreak, see module docstring

        predictions.append((true_label, final))

    overlap = xsmall_mistakes & embedding_mistakes
    only_xsmall = xsmall_mistakes - embedding_mistakes
    only_embedding = embedding_mistakes - xsmall_mistakes
    print(f"\nxsmall mistakes: {len(xsmall_mistakes)}  embedding mistakes: {len(embedding_mistakes)}")
    print(f"overlap (both wrong): {len(overlap)}  only-xsmall-wrong: {len(only_xsmall)}  only-embedding-wrong: {len(only_embedding)}")

    per_class_f1, macro_f1 = compute_f1(predictions)
    accuracy = sum(1 for t, p in predictions if t == p) / len(predictions)
    print(f"\nEnsemble macro-F1={macro_f1:.3f}  accuracy={accuracy:.1%}")
    print(f"Cases where both predicted different real categories (tiebreak used): {both_real_disagree}")
    for label in LABELS:
        print(f"  {label:<28s} F1={per_class_f1[label]:.3f}")

    print(f"\nembedding alone: 0.454   xsmall alone: 0.393")
    print(f"Ensemble delta vs embedding (the better single model): {(macro_f1 - 0.454) * 100:+.1f}pp")

    mistakes = [(t, tr, p) for (tr, t), (_, p) in zip(examples, predictions) if t != p]
    print(f"\nMistakes ({len(mistakes)}):")
    for true, transcript, pred in mistakes:
        print(f"    [{true} -> {pred}] {transcript[:80]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="labeling_pass_consensus_review.csv")
    args = parser.parse_args()
    main(args.worksheet)
