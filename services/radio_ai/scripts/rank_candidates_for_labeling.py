"""Corpus-building follow-up to shortlist_candidate_clips.py, requested
2026-08-15 (Shashwat, team chat: "I don't have the incidents corpus...
if you can try finding them").

shortlist_candidate_clips.py's keyword matching is deliberately loose
(its own docstring says so) and it shows in practice: of the 4,297
candidates it wrote from MikCil/f1-team-radio, most FRONT_TURNIN_BRAKE
and TYRE_GRIP_DEGRADATION "matches" are keyword coincidences, not real
complaints -- e.g. "these tyres are going to be fine to the end...
wear was good" matched TYRE_GRIP_DEGRADATION on the word "tyres" alone
despite being the opposite of a complaint. Handing a human 1,400+ text
rows to skim for two categories is a bad use of the actual scarce
resource here (human listening time, see labeling_pass_consensus_review.csv:
FRONT_TURNIN_BRAKE has 2 real labeled examples, TYRE_GRIP_DEGRADATION
has 0).

This script does NOT assign labels -- it only re-ranks the existing
keyword shortlist by cosine similarity to each category's real
prototype embedding (the exact ones production `classify()` already
uses, CLASSIFIER_BACKEND=embedding), so a human reviewer sees the most
plausible candidates for the two starved categories first instead of
wading through keyword noise. Final labeling is still a human call --
this only triages the queue. No audio is downloaded or listened to by
this script; it only re-scores the text already in the shortlist CSV.

Usage:
    python scripts/rank_candidates_for_labeling.py --candidates candidates_local.csv \
        --categories FRONT_TURNIN_BRAKE TYRE_GRIP_DEGRADATION --top 30
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ClassifierConfig  # noqa: E402

EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def main(candidates_path: str, categories: list[str], top_n: int, out_path: str) -> None:
    from sentence_transformers import SentenceTransformer, util

    rows = []
    with open(candidates_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["transcription"]:
                rows.append(row)
    print(f"Loaded {len(rows)} candidate rows from {candidates_path}")

    print(f"Loading {EMBEDDING_MODEL_ID} ({EMBEDDING_MODEL_REVISION[:8]})...")
    model = SentenceTransformer(EMBEDDING_MODEL_ID, revision=EMBEDDING_MODEL_REVISION)

    transcripts = [r["transcription"] for r in rows]
    transcript_embeddings = model.encode(transcripts, convert_to_tensor=True, show_progress_bar=True)

    out_rows = []
    for category in categories:
        if category not in ClassifierConfig.TAXONOMY:
            print(f"WARNING: {category!r} not in taxonomy, skipping")
            continue
        prototype_text = ClassifierConfig.TAXONOMY[category]
        prototype_embedding = model.encode(prototype_text, convert_to_tensor=True)
        scores = util.cos_sim(transcript_embeddings, prototype_embedding).squeeze(1)

        ranked = sorted(zip(rows, scores.tolist()), key=lambda rs: rs[1], reverse=True)
        print(f"\n=== Top {top_n} candidates for {category} ===")
        for row, score in ranked[:top_n]:
            print(f"  {score:.3f}  {row['transcription'][:90]!r}")
            out_rows.append(
                {
                    "target_category": category,
                    "similarity": f"{score:.3f}",
                    "id": row["id"],
                    "driver_id": row["driver_id"],
                    "grand_prix": row["grand_prix"],
                    "transcription": row["transcription"],
                    "human_label": "",  # deliberately blank -- a human fills this in after listening
                }
            )

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "target_category", "similarity", "id", "driver_id",
                "grand_prix", "transcription", "human_label",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"\nWrote {len(out_rows)} ranked candidates to {out_path}")
    print(
        "This is a triaged queue to LISTEN TO, not a labeled dataset -- "
        "'human_label' is blank on purpose. A transcript alone can look "
        "like a match and still be wrong once you hear the actual clip "
        "(sarcasm, a third-party mention, a resolved complaint, etc.)."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", default="candidates_local.csv")
    parser.add_argument(
        "--categories", nargs="+",
        default=["FRONT_TURNIN_BRAKE", "TYRE_GRIP_DEGRADATION"],
    )
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--out", default="candidates_ranked_for_review.csv")
    args = parser.parse_args()
    main(args.candidates, args.categories, args.top, args.out)
