"""Runs the ENTIRE real pipeline -- ASR, tone, complaint classification,
semantic retrieval -- against real F1 broadcast audio from
candidate_audio_review/, all locally on CPU. No fixtures, no
hand-typed numbers. Produces live_pipeline_demo.json for the frontend.

Retrieval uses the real two-gate rule from
services/evidence_memory/retrieval.py (category match AND cosine
similarity >= 0.40), applied honestly: if nothing clears the gate, the
match is null, not forced.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from app import tone
from app.complaint_classifier import classify

TARGET_SR = 16_000
CLIPS_DIR = Path(__file__).resolve().parents[1] / "candidate_audio_review"
SIMILARITY_THRESHOLD = 0.40

FLAGSHIP_ID = "2023_Monaco_Grand_Prix_NICHUL01_27_20230528_144112"


def load_mono_16k(path: Path) -> np.ndarray:
    data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if data.ndim == 2:
        data = data.mean(axis=1)
    if sr != TARGET_SR:
        from math import gcd

        g = gcd(sr, TARGET_SR)
        data = resample_poly(data, TARGET_SR // g, sr // g).astype(np.float32)
    return data


def run_asr(model, path: Path) -> str:
    segments, _info = model.transcribe(str(path), language="en", beam_size=5)
    return " ".join(seg.text.strip() for seg in segments).strip()


def main() -> None:
    from faster_whisper import WhisperModel
    from sentence_transformers import SentenceTransformer, util

    print("Loading faster-whisper (small.en, CPU)...")
    asr_model = WhisperModel("small.en", device="cpu", compute_type="int8")

    mp3_files = sorted(CLIPS_DIR.glob("*.mp3"))
    print(f"Found {len(mp3_files)} real clips in {CLIPS_DIR}")

    records = []
    for path in mp3_files:
        clip_id = path.stem
        print(f"\n--- {clip_id} ---")
        wav = load_mono_16k(path)

        transcript = run_asr(asr_model, path)
        print(f"ASR: {transcript!r}")

        tone_scores = tone.score_waveform(wav)
        tone_label, tone_score, tone_confidence = tone.map_to_label(tone_scores)
        print(f"tone: {tone_label} ({tone_score:.3f}, conf {tone_confidence:.3f})")

        category, category_confidence = classify(transcript)
        print(f"category: {category} ({category_confidence})")

        records.append(
            {
                "id": clip_id,
                "src": f"/audio/live_demo/{clip_id}.mp3",
                "transcript": transcript,
                "tone_label": tone_label,
                "tone_score": round(tone_score, 3),
                "tone_confidence": round(tone_confidence, 3),
                "category": category,
                "category_confidence": round(category_confidence, 3) if category_confidence else None,
            }
        )

    print("\n=== Retrieval: real two-gate rule (category match AND cosine >= 0.40) ===")
    embed_model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
    )
    transcripts = [r["transcript"] for r in records]
    embeddings = embed_model.encode(transcripts, convert_to_tensor=True)
    sim_matrix = util.cos_sim(embeddings, embeddings)

    for i, rec in enumerate(records):
        best_j, best_sim = None, -1.0
        for j, other in enumerate(records):
            if i == j or rec["category"] is None or other["category"] != rec["category"]:
                continue
            sim = float(sim_matrix[i][j])
            if sim > best_sim:
                best_sim, best_j = sim, j
        if best_j is not None and best_sim >= SIMILARITY_THRESHOLD:
            rec["echo_match"] = {
                "id": records[best_j]["id"],
                "transcript": records[best_j]["transcript"],
                "similarity": round(best_sim, 3),
            }
        else:
            rec["echo_match"] = None

    flagship = next((r for r in records if r["id"] == FLAGSHIP_ID), records[0])
    print(f"\nFlagship ({flagship['id']}) echo_match: {flagship['echo_match']}")

    out = {"flagship_id": flagship["id"], "clips": records}
    out_path = Path(__file__).parent / "live_pipeline_demo.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
