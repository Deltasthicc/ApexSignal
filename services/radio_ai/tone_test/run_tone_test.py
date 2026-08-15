"""One-off local feasibility test: can VoiceCLAP run on CPU on this
laptop (no GPU, no ffmpeg/torchcodec)? Loads audio via soundfile
instead of torchaudio (torchcodec needs system ffmpeg, not installed
here), resamples with scipy, then reuses the real app/tone.py scoring
code unmodified.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from app import tone

TARGET_SR = 16_000


def load_mono_16k_no_torchaudio(path: str) -> np.ndarray:
    data, sr = sf.read(path, dtype="float32", always_2d=False)
    if data.ndim == 2:
        data = data.mean(axis=1)
    if sr != TARGET_SR:
        from math import gcd

        g = gcd(sr, TARGET_SR)
        data = resample_poly(data, TARGET_SR // g, sr // g).astype(np.float32)
    return data


if __name__ == "__main__":
    for name in ["calm_test", "urgent_test"]:
        path = Path(__file__).parent / f"{name}.mp3"
        print(f"\n=== {name} ===")
        wav = load_mono_16k_no_torchaudio(str(path))
        print(f"waveform shape={wav.shape}, duration={len(wav)/TARGET_SR:.2f}s")

        scores = tone.score_waveform(wav)
        print("raw scores:", scores)
        label, tone_score, confidence = tone.map_to_label(scores)
        print(f"tone_label={label}  tone_score={tone_score:.3f}  confidence={confidence:.3f}")
