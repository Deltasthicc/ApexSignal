"""Gate 7: pull a batch of clips that were NOT part of Day-1 threshold
tuning (the 20 in human_labels.csv), run the live pipeline on them
exactly once, and write a full provenance report.

This automates everything gate 7 can be automated: picking clips your
own threshold-tuning never saw, running the frozen pipeline, and
recording every model id/revision/threshold used. It deliberately does
NOT try to automate the two things that still need a human:

1. Choosing which few of these are your actual demo clips -- a
   narrative/storytelling decision, not a technical one.
2. Manually correcting those chosen clips' transcripts by ear. The ASR
   transcript in this report is machine output, not verified, and is
   labeled as such in every row -- do not read it as ground truth.

Usage:
    python scripts/run_holdout_gate7.py --count 20 --out-dir holdout_audio --report HOLDOUT_REPORT.md
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import asr, complaint_classifier, tone  # noqa: E402
from app.audio_preprocessing import preprocess  # noqa: E402
from app.config import ClassifierConfig, ModelConfig, ToneThresholds  # noqa: E402
from app.pipeline import run_live_pipeline  # noqa: E402
from extract_audio_clips import main as extract_clips  # noqa: E402

ALREADY_USED_LABELS_CSV = Path(__file__).resolve().parents[1] / "human_labels.csv"

# Real F1 radio occasionally carries a genuine driver health/distress
# moment (e.g. a driver reporting they feel unwell and discussing
# retiring). That is not a mechanical complaint, and the charter is
# explicit that this project never diagnoses or exploits anything
# resembling a psychological/medical state. Keyword-flag these rows so
# they can't be mistaken for an ordinary candidate while scanning the
# table -- narrow and high-precision on purpose, not a general safety
# filter, so it doesn't need reviewing for false positives every run.
SENSITIVE_CONTENT_KEYWORDS = [
    "don't feel well", "not feeling well", "feel unwell", "feeling unwell",
    "retire", "retiring", "medical", "chest pain", "can't breathe",
    "dizzy", "hospital",
]


def flag_sensitive(transcript: str) -> bool:
    text = transcript.lower()
    return any(kw in text for kw in SENSITIVE_CONTENT_KEYWORDS)


def already_used_ids() -> set[str]:
    if not ALREADY_USED_LABELS_CSV.exists():
        return set()
    import csv

    with open(ALREADY_USED_LABELS_CSV, newline="", encoding="utf-8") as f:
        return {Path(row["clip_filename"]).stem for row in csv.DictReader(f)}


def all_dataset_ids(revision: str) -> list[str]:
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem()
    glob_pattern = f"datasets/{ModelConfig.DEV_DATASET_ID}@{revision}/data/train-*.parquet"
    ids = []
    for shard_path in sorted(fs.glob(glob_pattern)):
        with fs.open(shard_path, "rb") as fh:
            table = pq.read_table(fh, columns=["id"])
        ids.extend(table.column("id").to_pylist())
    return ids


def main(count: int, out_dir: Path, report_path: Path, seed: int) -> None:
    used = already_used_ids()
    print(f"{len(used)} clip(s) already used for threshold tuning, excluding them")

    print("Listing dataset ids...")
    candidates = [i for i in all_dataset_ids(ModelConfig.DEV_DATASET_REVISION) if i not in used]
    rng = random.Random(seed)
    holdout_ids = set(rng.sample(candidates, min(count, len(candidates))))
    print(f"Selected {len(holdout_ids)} holdout ids")

    out_dir.mkdir(parents=True, exist_ok=True)
    extract_clips(holdout_ids, out_dir, ModelConfig.DEV_DATASET_REVISION)

    print("\nWarming models...")
    asr.warm_up()
    tone.warm_up()
    complaint_classifier.warm_up()

    results = []
    for clip_path in sorted(out_dir.glob("*")):
        incident_id = clip_path.stem
        print(f"Running pipeline on {incident_id}...")
        waveform = preprocess(str(clip_path))
        result = run_live_pipeline(waveform, incident_id)
        results.append((clip_path, result))

    flagged_ids = [
        result.incident_id for _, result in results if flag_sensitive(result.transcript)
    ]

    lines = [
        "# Gate 7 holdout report",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat()}. "
        f"{len(results)} clip(s), none used in Day-1 threshold tuning "
        f"(see `human_labels.csv` for the excluded set).",
        "",
        "**Every transcript below is raw ASR output, not manually verified.** "
        "Before using any of these as an actual demo clip, listen to it and "
        "correct the transcript by hand -- that step is not done here.",
        "",
    ]
    if flagged_ids:
        lines += [
            "## ⚠️ Flagged: do not use for the demo",
            "",
            "The following clip(s) contain language matching a genuine driver "
            "health/distress moment, not a mechanical complaint. The project's "
            "own charter is explicit that this system never diagnoses or "
            "exploits anything resembling a psychological or medical state -- "
            "these are excluded from demo consideration, full stop, regardless "
            "of how interesting the tone/complaint output looks:",
            "",
        ]
        lines += [f"- `{incident_id}`" for incident_id in flagged_ids]
        lines.append("")
    lines += [
        "## Provenance (applies to every row below)",
        "",
        f"- ASR: `{ModelConfig.ASR_MODEL_ID}` @ `{ModelConfig.ASR_MODEL_REVISION}`",
        f"- Tone encoder: `{ModelConfig.TONE_ENCODER_ID}` @ `{ModelConfig.TONE_ENCODER_REVISION}`",
        f"- Tone heads: `{ModelConfig.TONE_HEADS_ID}` @ `{ModelConfig.TONE_HEADS_REVISION}`",
        f"- Classifier backend: `{ModelConfig.CLASSIFIER_BACKEND}`",
        (
            f"- Classifier: `{ModelConfig.EMBEDDING_MODEL_ID}` @ `{ModelConfig.EMBEDDING_MODEL_REVISION}`, "
            f"similarity margin: `{ClassifierConfig.EMBEDDING_SIMILARITY_MARGIN}`"
            if ModelConfig.CLASSIFIER_BACKEND == "embedding"
            else (
                f"- Classifier: `{ModelConfig.CLASSIFIER_FALLBACK_MODEL_ID}` @ "
                f"`{ModelConfig.CLASSIFIER_FALLBACK_MODEL_REVISION}`, "
                f"null threshold: `{ClassifierConfig.NULL_THRESHOLD}`"
                if ModelConfig.CLASSIFIER_BACKEND == "nli-xsmall"
                else (
                    f"- Classifier: `{ModelConfig.CLASSIFIER_MODEL_ID}` @ "
                    f"`{ModelConfig.CLASSIFIER_MODEL_REVISION}`, "
                    f"null threshold: `{ClassifierConfig.NULL_THRESHOLD}`"
                )
            )
        ),
        f"- Arousal threshold: `{ToneThresholds.AROUSAL_ELEVATED_THRESHOLD}`, "
        f"fatigue threshold: `{ToneThresholds.FATIGUE_THRESHOLD}`",
        "",
        "## Clips",
        "",
        "| id | ASR transcript (unverified) | tone_label | tone_score | complaint_category |",
        "|---|---|---|---|---|",
    ]
    for clip_path, result in results:
        transcript_escaped = result.transcript.replace("|", "\\|")
        id_cell = (
            f"⚠️ `{result.incident_id}`"
            if result.incident_id in flagged_ids
            else f"`{result.incident_id}`"
        )
        category_cell = (
            result.complaint_category.value if result.complaint_category else "None"
        )
        lines.append(
            f"| {id_cell} | {transcript_escaped} | {result.tone_label.value} | "
            f"{result.tone_score:.3f} | {category_cell} |"
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {report_path.resolve()}")
    print(
        "\nNext: read this report, pick 3-5 clips for the actual demo, listen "
        "to each one, and hand-correct its transcript before it goes in front "
        "of judges."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--out-dir", default="holdout_audio")
    parser.add_argument("--report", default="HOLDOUT_REPORT.md")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    main(args.count, Path(args.out_dir), Path(args.report), args.seed)
