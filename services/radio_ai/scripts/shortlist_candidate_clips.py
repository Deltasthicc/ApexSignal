"""Pull just the text metadata (not audio) from MikCil/f1-team-radio and
keyword-match transcripts against the taxonomy to produce a candidate
shortlist for manual listening.

This does NOT replace human judgment -- it only narrows ~14,700 clips
down to a few hundred worth listening to. You still have to listen to
each shortlisted clip and confirm it's intelligible, acoustically
clear, and actually representative before it becomes a Day-1 or demo
clip. Keyword matching on Cohere-generated transcripts will have noise
in both directions: false matches on incidental word use, and missed
matches on paraphrased complaints.

NOTE: this script has not been execution-tested in this session (no
local Python/ML environment was available to run it against). Sanity
check the first run: if column-pruned reads aren't actually avoiding
the ~2.5 GB audio payload, `pip install datasets` and switch to
`load_dataset(..., streaming=True)` iterating text columns only as a
fallback -- see the comment at the bottom of main().

Usage:
    pip install pyarrow huggingface_hub fsspec
    python scripts/shortlist_candidate_clips.py --out candidates.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ModelConfig  # noqa: E402

TEXT_COLUMNS = [
    "id",
    "driver_id",
    "grand_prix",
    "race_id",
    "session_date",
    "message_timestamp",
    "transcription",
]

# Loose keyword sets per category. Deliberately over-inclusive -- this
# is a shortlist, not a classifier. Refine after seeing real matches.
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


def match_categories(transcript: str) -> list[str]:
    text = transcript.lower()
    return [
        category
        for category, keywords in TAXONOMY_KEYWORDS.items()
        if any(re.search(rf"\b{re.escape(kw)}", text) for kw in keywords)
    ]


def main(out_path: str, revision: str) -> None:
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem()
    dataset_id = ModelConfig.DEV_DATASET_ID
    glob_pattern = f"datasets/{dataset_id}@{revision}/data/train-*.parquet"

    print(f"Listing shards: {glob_pattern}")
    shard_paths = fs.glob(glob_pattern)
    if not shard_paths:
        raise RuntimeError(
            f"No shards found for {glob_pattern}. Check the dataset revision "
            f"in .env (DEV_DATASET_REVISION) is still current."
        )
    print(f"Found {len(shard_paths)} shard(s)")

    rows_written = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(TEXT_COLUMNS + ["matched_categories"])

        for shard_path in shard_paths:
            print(f"Reading (columns only): {shard_path}")
            with fs.open(shard_path, "rb") as fh:
                table = pq.read_table(fh, columns=TEXT_COLUMNS)
            for row in table.to_pylist():
                matches = match_categories(row["transcription"] or "")
                if matches:
                    writer.writerow([row[col] for col in TEXT_COLUMNS] + ["|".join(matches)])
                    rows_written += 1

    print(f"Wrote {rows_written} candidate rows to {out_path}")
    print(
        "\nNext: open the CSV, pick 15-20 across categories + a few "
        "ambiguous ones, and actually listen to each before using it "
        "for Day-1 validation or the demo."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="candidates.csv")
    parser.add_argument("--revision", default=ModelConfig.DEV_DATASET_REVISION)
    args = parser.parse_args()
    main(args.out, args.revision)
