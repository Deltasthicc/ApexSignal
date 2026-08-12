"""Build a fast-to-fill labeling worksheet for Gate 6 (complaint
classifier benchmark) -- text only, no audio, no listening required.

Samples candidate transcripts from MikCil/f1-team-radio across the 5
taxonomy categories plus NO_COMPLAINT, and pre-fills a *suggested*
category from crude keyword matching. Deliberately crude, not a
semantic guess -- the suggestion exists to speed up reading, not to
replace your judgment. If the prefill were generated the same way the
real classifier "thinks" (i.e. a semantic read of the sentence), your
"confirm or fix" pass would be biased toward agreeing with the model
under test, and the benchmark would measure something close to
tautological. Keyword matching is a deliberately dumb, different
mechanism, precisely so your correction of it is real signal, not a
rubber stamp.

You still have to actually read each transcript and decide the correct
category yourself -- glancing at the suggestion and moving on defeats
the point of this gate.

Usage:
    python scripts/build_classifier_worksheet.py --per-category 10 --out classifier_worksheet.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ModelConfig  # noqa: E402

TAXONOMY_KEYWORDS = {
    "EXIT_TRACTION_REAR": [
        "rear", "wheelspin", "spinning", "oversteer", "traction", "sliding",
        "loose", "snap", "moving around",
    ],
    "FRONT_TURNIN_BRAKE": [
        "front", "understeer", "locking", "lock up", "turn in", "turn-in",
        "brake", "braking", "won't turn", "not rotating",
    ],
    "TYRE_GRIP_DEGRADATION": [
        "tyre", "tire", "grip", "degrad", "graining", "blister", "worn",
        "falling off", "gone off",
    ],
    "VISIBILITY_TRACK_CONDITION": [
        "rain", "wet", "spray", "visibility", "can't see", "standing water",
        "damp", "slippery", "debris", "puddle",
    ],
    "MECHANICAL_OTHER": [
        "vibration", "puncture", "damage", "gearbox", "engine", "steering",
        "smell", "smoke", "loose wheel", "power loss", "temperature",
    ],
}


def suggest_category(transcript: str) -> str:
    """First keyword match wins, in taxonomy order; NO_COMPLAINT if none."""
    text = transcript.lower()
    for category, keywords in TAXONOMY_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}", text) for kw in keywords):
            return category
    return "NO_COMPLAINT"


def main(per_category: int, out_path: str, seed: int) -> None:
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem()
    dataset_id = ModelConfig.DEV_DATASET_ID
    revision = ModelConfig.DEV_DATASET_REVISION
    glob_pattern = f"datasets/{dataset_id}@{revision}/data/train-*.parquet"

    shard_paths = sorted(fs.glob(glob_pattern))
    if not shard_paths:
        raise RuntimeError(f"No shards found for {glob_pattern}")

    buckets: dict[str, list[dict]] = {
        cat: [] for cat in list(TAXONOMY_KEYWORDS) + ["NO_COMPLAINT"]
    }

    for shard_path in shard_paths:
        print(f"Reading (columns only): {shard_path}")
        with fs.open(shard_path, "rb") as fh:
            table = pq.read_table(fh, columns=["id", "transcription"])
        for row in table.to_pylist():
            transcript = row["transcription"] or ""
            if not transcript.strip():
                continue
            category = suggest_category(transcript)
            buckets[category].append({"id": row["id"], "transcription": transcript})

    rng = random.Random(seed)
    rows_out = []
    for category, candidates in buckets.items():
        rng.shuffle(candidates)
        picked = candidates[:per_category]
        print(f"{category}: {len(candidates)} candidates, sampled {len(picked)}")
        for c in picked:
            rows_out.append(
                {
                    "id": c["id"],
                    "transcription": c["transcription"],
                    "suggested_category": category,
                    "human_label": "",
                    "notes": "",
                }
            )

    rng.shuffle(rows_out)  # don't label in category-sorted blocks, that's its own bias

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "transcription", "suggested_category", "human_label", "notes"]
        )
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"\nWrote {len(rows_out)} rows to {out_path}")
    print(
        "\nFill in human_label for each row: one of EXIT_TRACTION_REAR, "
        "FRONT_TURNIN_BRAKE, TYRE_GRIP_DEGRADATION, VISIBILITY_TRACK_CONDITION, "
        "MECHANICAL_OTHER, or NO_COMPLAINT. suggested_category is a rough "
        "keyword guess, often wrong on purpose -- read the transcript, don't "
        "just copy it. Leave a row's human_label blank and add a note if a "
        "transcript is too garbled/ambiguous to label confidently; those get "
        "excluded, not guessed."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-category", type=int, default=10)
    parser.add_argument("--out", default="classifier_worksheet.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.per_category, args.out, args.seed)
