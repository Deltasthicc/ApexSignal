"""Gate 4 (VALIDATION_GATES.md): create degraded copies of clean clips to
test tone-score stability under bandwidth restriction / compression /
noise, without depending on system ffmpeg (broken on this box -- see
VALIDATION_GATES.md gate 0 history). Pure torchaudio/numpy instead.

Usage:
    cd services/radio_ai
    python scripts/degrade_audio.py clip1.mp3 clip2.mp3 ...

Writes <name>_degraded.wav next to each input.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import soundfile as sf
import torch
import torchaudio

from app.audio_preprocessing import TARGET_SAMPLE_RATE, load_mono_16k


def degrade(waveform: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE, snr_db: float = 12.0) -> np.ndarray:
    tensor = torch.from_numpy(waveform)

    # Bandwidth restriction: low-pass at 3000 Hz, typical of compressed
    # radio/telephone-quality audio (vs. ~8000 Hz Nyquist at 16 kHz).
    tensor = torchaudio.functional.lowpass_biquad(tensor, sample_rate, cutoff_freq=3000.0)

    # Compression artifact: mu-law encode/decode roundtrip (companding,
    # same family of lossy nonlinear quantization as real codecs use).
    encoded = torchaudio.functional.mu_law_encoding(tensor, quantization_channels=256)
    tensor = torchaudio.functional.mu_law_decoding(encoded, quantization_channels=256)

    # Additive noise at a fixed SNR relative to this clip's own power,
    # rather than a fixed absolute noise level (so a loud clip and a
    # quiet clip get comparably audible degradation).
    signal_power = tensor.pow(2).mean()
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = torch.randn_like(tensor) * noise_power.sqrt()
    tensor = tensor + noise

    return tensor.clamp(-1.0, 1.0).numpy().astype(np.float32)


def main(paths: list[str]) -> None:
    for path in paths:
        waveform = load_mono_16k(path)
        degraded = degrade(waveform)
        out_path = Path(path).with_name(Path(path).stem + "_degraded.wav")
        sf.write(out_path, degraded, TARGET_SAMPLE_RATE)
        print(f"{path} -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
