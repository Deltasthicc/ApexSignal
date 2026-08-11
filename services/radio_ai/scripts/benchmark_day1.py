"""Day-1 benchmark: run local audio clips through the full radio_ai
pipeline (preprocess -> ASR -> tone -> complaint classification) and
print the resulting JSON for each, plus write a combined report.

Usage:
    cd services/radio_ai
    python scripts/benchmark_day1.py clip1.wav clip2.mp3 ...

Requires ANALYZE_MODE=live model dependencies installed (see
requirements.txt) and HF_TOKEN set if any repo needs authentication
(none of the currently pinned models do, but set it anyway -- see
README.md). This script talks to the pipeline modules directly, not
over HTTP, so it can run without the FastAPI server up.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import asr, complaint_classifier, tone  # noqa: E402
from app.audio_preprocessing import preprocess  # noqa: E402


def benchmark_clip(path: str) -> dict:
    t0 = time.perf_counter()
    waveform = preprocess(path)
    t_preprocess = time.perf_counter()

    transcript, asr_model_used = asr.transcribe(waveform)
    t_asr = time.perf_counter()

    tone_scores = tone.score_waveform(waveform)
    tone_label, tone_score, tone_confidence = tone.map_to_label(tone_scores)
    t_tone = time.perf_counter()

    complaint_category, category_confidence = complaint_classifier.classify(transcript)
    t_classify = time.perf_counter()

    return {
        "clip_path": path,
        "transcript": transcript,
        "asr_model_used": asr_model_used,
        "tone_label": tone_label,
        "tone_score": round(tone_score, 4),
        "tone_confidence": round(tone_confidence, 4),
        "tone_raw_scores": {k: round(v, 4) for k, v in tone_scores.items()},
        "complaint_category": complaint_category,
        "category_confidence": (
            round(category_confidence, 4) if category_confidence is not None else None
        ),
        "timing_s": {
            "preprocess": round(t_preprocess - t0, 3),
            "asr": round(t_asr - t_preprocess, 3),
            "tone": round(t_tone - t_asr, 3),
            "classify": round(t_classify - t_tone, 3),
            "total": round(t_classify - t0, 3),
        },
    }


def main(paths: list[str]) -> None:
    print(f"Warming models (one-time cold-start cost)...", file=sys.stderr)
    warm_t0 = time.perf_counter()
    asr.warm_up()
    tone.warm_up()
    complaint_classifier.warm_up()
    print(f"Models warm in {time.perf_counter() - warm_t0:.1f}s\n", file=sys.stderr)

    results = []
    for path in paths:
        print(f"--- {path} ---")
        result = benchmark_clip(path)
        print(json.dumps(result, indent=2))
        results.append(result)
        print()

    report_path = Path("day1_benchmark_report.json")
    report_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote combined report to {report_path.resolve()}")
    print(
        "\nNext step: fill in VALIDATION_GATES.md by hand with your "
        "own labels for these clips. This script does not grade itself."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clips", nargs="+", help="Paths to local audio files")
    args = parser.parse_args()
    main(args.clips)
