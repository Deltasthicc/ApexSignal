"""Gate 6 Part 2, item 1: the adopted embedding classifier (see
VALIDATION_GATES.md gate 6d) used the cheapest version of the idea --
each category's TAXONOMY description text alone, as its one prototype.
This tries richer prototypes: average the description embedding with
embeddings of real, already-human-labeled example utterances of that
category (from the same 58-example set -- no new label generated,
per this project's standing rule).

Leave-one-out, not naive averaging: if example i's own text were
included in its own true category's prototype while scoring example i,
that's leakage -- the prototype would partly be "does this text match
itself," inflating the measured macro-F1 for a reason that wouldn't
generalize. So for each example, its own category's prototype is built
from every OTHER same-category example, never itself. Categories with
too few examples to leave one out and have any left (TYRE_GRIP_DEGRADATION,
n=0; FRONT_TURNIN_BRAKE, n=2 -> 1 left after holdout) fall back to the
description-only prototype for that category on that example -- still a
real, honest, per-example computation, not skipped.

Usage:
    python scripts/experiment_richer_prototypes.py --worksheet labeling_pass_consensus_review.csv
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
MARGIN_SWEEP = [round(0.02 * i, 2) for i in range(0, 16)]  # 0.00 .. 0.30


def main(worksheet_path: str) -> None:
    examples = []
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if label and label in LABELS:
                examples.append((row["transcription"], label))
    print(f"Loaded {len(examples)} labeled examples")

    from sentence_transformers import SentenceTransformer, util

    print(f"Loading {ModelConfig.EMBEDDING_MODEL_ID} ({ModelConfig.EMBEDDING_MODEL_REVISION[:8]})...")
    model = SentenceTransformer(ModelConfig.EMBEDDING_MODEL_ID, revision=ModelConfig.EMBEDDING_MODEL_REVISION)

    description_embeddings = {
        label: model.encode(ClassifierConfig.TAXONOMY[label], convert_to_tensor=True) for label in LABELS
    }
    transcripts = [t for t, _ in examples]
    true_labels = [l for _, l in examples]
    transcript_embeddings = model.encode(transcripts, convert_to_tensor=True)

    # Per-category: indices of examples with that true label, for leave-one-out lookups.
    indices_by_label: dict[str, list[int]] = {label: [] for label in LABELS}
    for i, label in enumerate(true_labels):
        indices_by_label[label].append(i)

    print(f"\nExamples per category (for leave-one-out averaging): "
          f"{ {label: len(idxs) for label, idxs in indices_by_label.items()} }")

    # Cache per-example: best real-category label+score (with leave-one-out
    # richer prototypes), and NO_COMPLAINT's own richer-prototype score.
    cached = []
    fallback_count = 0
    for i in range(len(examples)):
        true_label = true_labels[i]

        def richer_prototype(label: str):
            nonlocal fallback_count
            other_idxs = [j for j in indices_by_label[label] if j != i]
            if not other_idxs:
                fallback_count += 1
                return description_embeddings[label]
            vectors = [description_embeddings[label]] + [transcript_embeddings[j] for j in other_idxs]
            return sum(vectors) / len(vectors)

        real_scores = {}
        for label in REAL_CATEGORIES:
            proto = richer_prototype(label)
            real_scores[label] = float(util.cos_sim(transcript_embeddings[i], proto)[0][0])
        best_real_label = max(real_scores, key=lambda l: real_scores[l])
        best_real_score = real_scores[best_real_label]

        no_complaint_proto = richer_prototype("NO_COMPLAINT")
        no_complaint_score = float(util.cos_sim(transcript_embeddings[i], no_complaint_proto)[0][0])

        cached.append((best_real_label, best_real_score, no_complaint_score))

    print(f"Fell back to description-only prototype {fallback_count} time(s) "
          f"(category had no OTHER same-category example to average with)")

    print(f"\n{'margin':<10} {'macro-F1':<10} {'accuracy':<10}")
    best_margin, best_macro_f1, best_per_class = None, -1.0, None
    for margin in MARGIN_SWEEP:
        predictions = []
        for (best_real_label, best_real_score, no_complaint_score), true_label in zip(cached, true_labels):
            if best_real_score > no_complaint_score + margin:
                predictions.append((true_label, best_real_label))
            else:
                predictions.append((true_label, "NO_COMPLAINT"))
        per_class_f1, macro_f1 = compute_f1(predictions)
        accuracy = sum(1 for t, p in predictions if t == p) / len(predictions)
        marker = ""
        if macro_f1 > best_macro_f1:
            best_macro_f1, best_margin, best_per_class = macro_f1, margin, per_class_f1
            marker = "  <- best so far"
        print(f"{margin:<10} {macro_f1:<10.3f} {accuracy:<10.1%}{marker}")

    print(f"\nBest margin: {best_margin}  macro-F1={best_macro_f1:.3f}")
    for label in LABELS:
        print(f"  {label:<28s} F1={best_per_class[label]:.3f}")

    print(f"\nDescription-only baseline (production, adopted 2026-08-14): 0.454")
    print(f"Delta: {(best_macro_f1 - 0.454) * 100:+.1f}pp")

    mistakes = []
    for (best_real_label, best_real_score, no_complaint_score), true_label, transcript in zip(cached, true_labels, transcripts):
        pred = best_real_label if best_real_score > no_complaint_score + best_margin else "NO_COMPLAINT"
        if pred != true_label:
            mistakes.append((true_label, pred, transcript))
    print(f"\nMistakes at best margin ({len(mistakes)}):")
    for true, pred, transcript in mistakes:
        print(f"    [{true} -> {pred}] {transcript[:80]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="labeling_pass_consensus_review.csv")
    args = parser.parse_args()
    main(args.worksheet)
