"""Normalize a radio clip to what every downstream model expects:
mono, 16 kHz, with leading/trailing silence and static trimmed by VAD.

Both VoiceCLAP and the Whisper family expect 16 kHz mono. Silero VAD
trims dead air before ASR, which is where Whisper hallucinates most
(see VALIDATION_GATES.md, gate 3).
"""

from __future__ import annotations

import numpy as np

TARGET_SAMPLE_RATE = 16_000

_vad_model = None
_vad_utils = None


def load_mono_16k(path: str) -> np.ndarray:
    """Load an audio file (wav/mp3/whatever ffmpeg/torchaudio can read)
    as a mono float32 numpy array at 16 kHz.
    """
    import torchaudio

    waveform, sample_rate = torchaudio.load(path)
    if waveform.dim() == 2:
        waveform = waveform.mean(0)
    if sample_rate != TARGET_SAMPLE_RATE:
        waveform = torchaudio.functional.resample(
            waveform, sample_rate, TARGET_SAMPLE_RATE
        )
    return waveform.numpy().astype(np.float32)


def _get_vad():
    global _vad_model, _vad_utils
    if _vad_model is None:
        import torch

        _vad_model, _vad_utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
    return _vad_model, _vad_utils


def trim_silence(waveform: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """Strip leading/trailing non-speech using Silero VAD.

    Falls back to returning the input unchanged if no speech segment is
    detected at all -- an all-static clip should still reach the ASR
    stage and produce an empty/low-confidence transcript rather than a
    hard failure.
    """
    import torch

    model, utils = _get_vad()
    get_speech_timestamps = utils[0]
    tensor = torch.from_numpy(waveform)
    timestamps = get_speech_timestamps(tensor, model, sampling_rate=sample_rate)
    if not timestamps:
        return waveform
    # Cutting exactly at the VAD boundary changes how Whisper decodes the
    # onset word (verified on a real clip: trimming to the exact boundary
    # silently dropped the first utterance entirely, even though it was
    # inside the detected speech window -- padding by ~0.2s recovered it).
    pad = int(0.2 * sample_rate)
    start = max(0, timestamps[0]["start"] - pad)
    end = min(len(waveform), timestamps[-1]["end"] + pad)
    return waveform[start:end]


def preprocess(path: str, apply_vad: bool = True) -> np.ndarray:
    waveform = load_mono_16k(path)
    if apply_vad:
        waveform = trim_silence(waveform)
    return waveform
