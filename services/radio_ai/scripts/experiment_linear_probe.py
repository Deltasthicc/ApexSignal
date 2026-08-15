"""Gate 6 follow-up: a trained linear probe on frozen embeddings, with
L1/L2 regularization and a grid search over penalty strength -- the
specific approach requested in the 2026-08-15 team chat (Jagrav) as a
way to improve on the production embedding-prototype classifier
(macro-F1 0.454, see VALIDATION_GATES.md gate 6d).

Important distinction from every other Gate 6 experiment: the
production classifier and every prior experiment (NLI zero-shot,
prototype cosine similarity, hierarchical gates, richer prototypes,
ensembling) have ZERO trained/learnable parameters -- they compare a
transcript embedding against a FIXED prototype embedding. There is
nothing for L1/L2 to regularize in that architecture. This script is
the first Gate 6 attempt that actually trains a parametric model
(multinomial logistic regression) on the labeled examples, which is
what makes L1/L2 regularization and a hyperparameter grid search a
meaningful thing to run at all.

Evaluation method: leave-one-out cross-validation (LOOCV), not k-fold.
K-fold was already rejected for margin-tuning in gate 6e for the same
reason it would be wrong here: FRONT_TURNIN_BRAKE has 2 labeled
examples and TYRE_GRIP_DEGRADATION has 0 -- you cannot stratify either
into 5 folds. LOOCV lets all 58 examples serve as a held-out test
point exactly once, which is the only honest way to get a macro-F1
number out of a dataset this small and this imbalanced.

Hard ceiling this experiment cannot cross, stated up front rather than
discovered as a surprise in the mistakes list: TYRE_GRIP_DEGRADATION
has zero examples anywhere in the labeled set. No classifier -- linear
probe, embedding-prototype, zero-shot NLI, or anything else -- can
learn to predict a category it has never once seen labeled. That is a
missing-data problem, not a modeling problem, and this script will
never report a non-zero F1 for that class no matter how the grid
search comes out.

Usage:
    python scripts/experiment_linear_probe.py --worksheet labeling_pass_consensus_review.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark_classifier import LABELS, compute_f1  # noqa: E402

# Same embedding model + pinned revision already adopted in production
# (app/complaint_classifier.py, "embedding" backend) -- reusing it here
# means this experiment isn't confounded by also changing the encoder.
EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"

PENALTIES = ["l1", "l2"]
C_GRID = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]


def load_examples(worksheet_path: str) -> list[tuple[str, str]]:
    examples = []
    with open(worksheet_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["human_label"].strip()
            if label and label in LABELS:
                examples.append((row["transcription"], label))
    return examples


def main(worksheet_path: str) -> None:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import LeaveOneOut
    from sklearn.multiclass import OneVsRestClassifier

    examples = load_examples(worksheet_path)
    print(f"Loaded {len(examples)} labeled examples")

    label_counts = Counter(label for _, label in examples)
    print("Label distribution:", dict(label_counts))
    missing = [l for l in LABELS if label_counts.get(l, 0) == 0]
    if missing:
        print(
            f"\nHARD CEILING: {missing} have ZERO labeled examples. No model of "
            f"any kind can be trained to predict a class it has never seen. "
            f"This is a data problem, not something this experiment can fix.\n"
        )

    print(f"Loading {EMBEDDING_MODEL_ID} ({EMBEDDING_MODEL_REVISION[:8]})...")
    model = SentenceTransformer(EMBEDDING_MODEL_ID, revision=EMBEDDING_MODEL_REVISION)

    transcripts = [t for t, _ in examples]
    true_labels = np.array([l for _, l in examples])
    X = model.encode(transcripts, convert_to_numpy=True)

    loo = LeaveOneOut()
    n = len(examples)

    print(f"\n{'penalty':<10} {'C':<10} {'macro-F1':<10} {'accuracy':<10}")
    best_key, best_macro_f1, best_per_class, best_preds = None, -1.0, None, None

    for penalty in PENALTIES:
        for C in C_GRID:
            preds = [None] * n
            for train_idx, test_idx in loo.split(X):
                y_train = true_labels[train_idx]
                # A fold can only predict classes present in its own
                # training split -- sklearn handles this natively, no
                # special-casing needed, but it's *why* a held-out
                # FRONT_TURNIN_BRAKE example (n=2 total) is genuinely
                # hard: at best one other example of its own class
                # remains to learn from.
                # liblinear only does binary; OneVsRestClassifier reduces
                # the 5-class problem to 5 binary ones, which is also a
                # more forgiving fit than multinomial softmax at this
                # sample size (each sub-classifier only needs to separate
                # its class from the rest, not calibrate against all
                # others jointly).
                clf = OneVsRestClassifier(
                    LogisticRegression(
                        penalty=penalty,
                        C=C,
                        solver="liblinear",
                        class_weight="balanced",
                        max_iter=2000,
                    )
                )
                clf.fit(X[train_idx], y_train)
                preds[test_idx[0]] = clf.predict(X[test_idx])[0]

            rows = list(zip(true_labels.tolist(), preds))
            per_class_f1, macro_f1 = compute_f1(rows)
            accuracy = sum(1 for t, p in rows if t == p) / n
            marker = ""
            if macro_f1 > best_macro_f1:
                best_macro_f1 = macro_f1
                best_key = (penalty, C)
                best_per_class = per_class_f1
                best_preds = preds
                marker = "  <- best so far"
            print(f"{penalty:<10} {C:<10} {macro_f1:<10.3f} {accuracy:<10.1%}{marker}")

    penalty, C = best_key
    print(f"\nBest: penalty={penalty}, C={C}  macro-F1={best_macro_f1:.3f}")
    print("Per-class F1 (LOOCV):")
    for label in LABELS:
        print(f"  {label:<28s} F1={best_per_class[label]:.3f}")

    print(f"\nProduction baseline (embedding-prototype, gate 6d): macro-F1=0.454")
    print(f"Delta: {(best_macro_f1 - 0.454) * 100:+.1f}pp")

    mistakes = [
        (t, p, tr) for (t, p), tr in zip(zip(true_labels.tolist(), best_preds), transcripts) if t != p
    ]
    print(f"\nMistakes at best (penalty, C) ({len(mistakes)}):")
    for true, pred, transcript in mistakes:
        print(f"    [{true} -> {pred}] {transcript[:80]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", default="labeling_pass_consensus_review.csv")
    args = parser.parse_args()
    main(args.worksheet)
