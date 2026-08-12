"""Run the live pipeline on chosen clips and write each result to
data/radio_analysis/{incident_id}.json -- the file location core_api
actually reads from (settled 2026-08-12; see contracts/api_contract.md
and services/core_api/app/pipeline.py::load_radio_analysis).

Use this once you've listened to and labeled your clips, and know the
final incident_id each one corresponds to (from Workstream A's
incident manifest, once it exists -- coordinate with Jagrav on the
actual INC-xxx ids rather than using the raw dataset row ids here).

Usage, one clip:
    python scripts/generate_radio_analysis.py --clip ../../data/audio/foo.mp3 --incident-id INC-017

Usage, a mapping file (JSON: {"INC-017": "path/to/clip.mp3", ...}):
    python scripts/generate_radio_analysis.py --mapping clips_to_incidents.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.audio_preprocessing import preprocess  # noqa: E402
from app.output_store import write_radio_analysis  # noqa: E402
from app.pipeline import run_live_pipeline  # noqa: E402
from app import asr, complaint_classifier, tone  # noqa: E402


def process_one(clip_path: str, incident_id: str) -> Path:
    waveform = preprocess(clip_path)
    result = run_live_pipeline(waveform, incident_id)
    written_path = write_radio_analysis(result)
    print(f"{incident_id}: {clip_path} -> {written_path}")
    print(f"  transcript: {result.transcript!r}")
    print(f"  tone: {result.tone_label} (score={result.tone_score:.2f}, confidence={result.tone_confidence:.2f})")
    print(f"  complaint: {result.complaint_category}")
    return written_path


def main(pairs: list[tuple[str, str]]) -> None:
    print("Warming models (one-time cold-start cost)...", file=sys.stderr)
    asr.warm_up()
    tone.warm_up()
    complaint_classifier.warm_up()

    for clip_path, incident_id in pairs:
        process_one(clip_path, incident_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip", help="Path to a single audio clip")
    parser.add_argument("--incident-id", help="incident_id for --clip")
    parser.add_argument("--mapping", help="JSON file: {incident_id: clip_path, ...}")
    args = parser.parse_args()

    pairs: list[tuple[str, str]] = []
    if args.mapping:
        mapping = json.loads(Path(args.mapping).read_text())
        pairs.extend((clip_path, incident_id) for incident_id, clip_path in mapping.items())
    if args.clip:
        if not args.incident_id:
            parser.error("--clip requires --incident-id")
        pairs.append((args.clip, args.incident_id))

    if not pairs:
        parser.error("Provide --clip + --incident-id, and/or --mapping")

    main(pairs)
