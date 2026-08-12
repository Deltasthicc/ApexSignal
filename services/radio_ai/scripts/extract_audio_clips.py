"""Pull specific rows' actual audio bytes out of MikCil/f1-team-radio by
`id` (the dataset's own row id, e.g. from candidates.csv produced by
shortlist_candidate_clips.py) and write them to local files.

The audio column is stored as {bytes, path} per row -- this writes the
raw bytes out unchanged, no decode/re-encode, so what you get is
exactly the source file.

Downloads whichever parquet shard(s) contain your target ids (each
shard is ~500MB, mostly audio bytes; there are 5 shards). Stops early
once every requested id is found, so if your ids cluster in one shard
you don't pay for all five.

Usage:
    python scripts/extract_audio_clips.py --ids INC-0001 INC-0042 --out ../../data/audio/
    # or read ids from the shortlist CSV's first column:
    python scripts/extract_audio_clips.py --ids-from candidates.csv --limit 20 --out ../../data/audio/
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ModelConfig  # noqa: E402


def main(target_ids: set[str], out_dir: Path, revision: str) -> None:
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem()
    dataset_id = ModelConfig.DEV_DATASET_ID
    glob_pattern = f"datasets/{dataset_id}@{revision}/data/train-*.parquet"
    shard_paths = sorted(fs.glob(glob_pattern))
    if not shard_paths:
        raise RuntimeError(f"No shards found for {glob_pattern}")

    out_dir.mkdir(parents=True, exist_ok=True)
    remaining = set(target_ids)
    found = {}

    for shard_path in shard_paths:
        if not remaining:
            break
        print(f"Reading {shard_path} ({len(remaining)} id(s) still wanted)...")
        with fs.open(shard_path, "rb") as fh:
            table = pq.read_table(fh, columns=["id", "audio", "transcription"])

        for row in table.to_pylist():
            if row["id"] not in remaining:
                continue
            audio = row["audio"]
            suffix = Path(audio["path"]).suffix if audio.get("path") else ".mp3"
            out_path = out_dir / f"{row['id']}{suffix}"
            out_path.write_bytes(audio["bytes"])
            found[row["id"]] = row["transcription"]
            remaining.discard(row["id"])
            print(f"  wrote {out_path} -- transcript (Cohere ASR, unverified): {row['transcription']!r}")

    if remaining:
        print(f"\nNot found in any shard: {sorted(remaining)}")
    print(f"\nExtracted {len(found)}/{len(target_ids)} clip(s) to {out_dir.resolve()}")
    print(
        "Listen to each one and manually correct the transcript by ear "
        "before using it for VALIDATION_GATES.md -- the printed "
        "transcript above is Cohere-generated, not ground truth."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="*", default=[], help="Dataset row ids to extract")
    parser.add_argument(
        "--ids-from", help="CSV with an 'id' column (e.g. candidates.csv from the shortlist script)"
    )
    parser.add_argument("--limit", type=int, default=None, help="Cap ids read from --ids-from")
    parser.add_argument("--out", default="clips", help="Output directory")
    parser.add_argument("--revision", default=ModelConfig.DEV_DATASET_REVISION)
    args = parser.parse_args()

    ids = set(args.ids)
    if args.ids_from:
        with open(args.ids_from, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if args.limit:
            rows = rows[: args.limit]
        ids |= {row["id"] for row in rows}

    if not ids:
        parser.error("Provide --ids and/or --ids-from")

    main(ids, Path(args.out), args.revision)
