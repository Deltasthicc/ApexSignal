"""Gate 6 follow-up #4 (per VALIDATION_GATES.md gate 6, "things worth
trying"): items 1 (hierarchical gate, both stage-1 phrasing variants)
and 2 (per-category taxonomy refinement) both plateaued -- rejected,
confirmed regressions (see GATE6_ERROR_ANALYSIS.md). This tries a
genuinely different model family instead of another zero-shot-NLI
variant: sentence embeddings + prototype cosine similarity.

Model: sentence-transformers/all-MiniLM-L6-v2, verified against the
live HF Hub API before use (2026-08-14): exists, ungated, Apache-2.0,
sha 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 -- same verification bar
every other model in this project was held to (see app/config.py).

Each category's TAXONOMY description text becomes its prototype
embedding (same text the NLI approach already uses, so this isn't
also confounded by different category wording). NO_COMPLAINT is
handled by a similarity margin: if the best real-category similarity
doesn't exceed the runner-up (which includes NO_COMPLAINT's own
prototype) by enough, or NO_COMPLAINT's own similarity wins outright,
predict NO_COMPLAINT. Sweeps that margin threshold the same way every
other Gate 6 threshold was swept.

NOT added to requirements.txt -- this is an experiment, not an adopted
dependency. Only worth formalizing if the result actually beats 0.393.

Usage:
    python scripts/experiment_embedding_classifier.py --worksheet labeling_pass_consensus_review.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ClassifierConfig  # noqa: E402
from benchmark_classifier import LABELS, compute_f1  # noqa: E402

EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"

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

    print(f"Loading {EMBEDDING_MODEL_ID} ({EMBEDDING_MODEL_REVISION[:8]})...")
    model = SentenceTransformer(EMBEDDING_MODEL_ID, revision=EMBEDDING_MODEL_REVISION)

    prototype_texts = [ClassifierConfig.TAXONOMY[l] for l in LABELS]
    prototype_embeddings = model.encode(prototype_texts, convert_to_tensor=True)

    transcripts = [t for t, _ in examples]
    true_labels = [l for _, l in examples]
    transcript_embeddings = model.encode(transcripts, convert_to_tensor=True)

    similarity = util.cos_sim(transcript_embeddings, prototype_embeddings)  # [n_examples, n_labels]

    # Cache per-example: best real-category label+score, and NO_COMPLAINT's own score.
    no_complaint_idx = LABELS.index("NO_COMPLAINT")
    real_indices = [LABELS.index(l) for l in REAL_CATEGORIES]

    cached = []
    for i in range(len(examples)):
        row = similarity[i]
        real_scores = {REAL_CATEGORIES[j]: float(row[idx]) for j, idx in enumerate(real_indices)}
        best_real_label = max(real_scores, key=lambda l: real_scores[l])
        best_real_score = real_scores[best_real_label]
        no_complaint_score = float(row[no_complaint_idx])
        cached.append((best_real_label, best_real_score, no_complaint_score))

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

    print(f"\nSingle-pass NLI baseline (xsmall): 0.393")
    print(f"Delta: {(best_macro_f1 - 0.393) * 100:+.1f}pp")

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
