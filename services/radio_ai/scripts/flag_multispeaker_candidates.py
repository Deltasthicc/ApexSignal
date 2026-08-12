"""Gate 0.5 helper, not a replacement for it: flags clips whose VAD
speech segmentation LOOKS like it could be multi-speaker back-and-forth
(multiple segments separated by real gaps), so a human doesn't have to
blindly re-listen to all 20 clips with equal suspicion. This is not
diarization -- it has no idea who is speaking, only how the speech is
chunked in time. A single continuous utterance and an engineer+driver
exchange can both produce 1 segment or many; treat this as a triage
signal to check first, not an answer.

Usage:
    python scripts/flag_multispeaker_candidates.py ../../data/audio/*.mp3
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from app.audio_preprocessing import _get_vad, load_mono_16k  # noqa: E402

GAP_THRESHOLD_S = 0.3  # gap between segments long enough to plausibly be a turn change


def analyze(path: str) -> dict:
    waveform = load_mono_16k(path)
    model, utils = _get_vad()
    get_speech_timestamps = utils[0]
    tensor = torch.from_numpy(waveform)
    timestamps = get_speech_timestamps(tensor, model, sampling_rate=16_000)

    gaps = []
    for a, b in zip(timestamps, timestamps[1:]):
        gap_s = (b["start"] - a["end"]) / 16_000
        if gap_s > 0:
            gaps.append(gap_s)

    turn_like_gaps = [g for g in gaps if g >= GAP_THRESHOLD_S]
    return {
        "path": path,
        "n_segments": len(timestamps),
        "gaps_s": [round(g, 2) for g in gaps],
        "turn_like_gap_count": len(turn_like_gaps),
    }


def main(paths: list[str]) -> None:
    results = [analyze(p) for p in paths]
    flagged = [r for r in results if r["turn_like_gap_count"] >= 1]

    print(f"{len(flagged)}/{len(results)} clip(s) have at least one gap >= {GAP_THRESHOLD_S}s "
          "between VAD speech segments -- worth checking for engineer+driver overlap first.\n")
    for r in sorted(results, key=lambda r: -r["turn_like_gap_count"]):
        flag = "FLAGGED" if r["turn_like_gap_count"] >= 1 else "       "
        print(f"{flag}  segments={r['n_segments']}  gaps={r['gaps_s']}  {Path(r['path']).name}")


if __name__ == "__main__":
    main(sys.argv[1:])
