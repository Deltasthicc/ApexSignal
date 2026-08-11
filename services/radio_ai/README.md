# services/radio_ai — Workstream B

Mission: convert one radio clip into a stable `RadioAnalysisOutput`.
Stateless. Owns no race telemetry and no incident memory.

## Frozen stack (verified against the live Hugging Face Hub API, 2026-08-11)

Every ID below was checked to actually exist, checked for gating, and
pinned to the commit SHA current at verification time. See `.env.example`
for the exact revisions.

| Stage | Model | License | Gated |
|---|---|---|---|
| ASR | [`distil-whisper/distil-large-v3.5-ct2`](https://huggingface.co/distil-whisper/distil-large-v3.5-ct2) | MIT | No |
| ASR fallback (CPU-slow escape hatch) | [`Systran/faster-whisper-small.en`](https://huggingface.co/Systran/faster-whisper-small.en) | MIT | No |
| Acoustic tone (encoder) | [`laion/voiceclap-commercial`](https://huggingface.co/laion/voiceclap-commercial) | CC-BY-4.0 | No |
| Acoustic tone (attribute heads) | [`laion/voiceclap-commercial-attribute-heads`](https://huggingface.co/laion/voiceclap-commercial-attribute-heads) | Apache-2.0 | No |
| Complaint classifier | [`MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33`](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33) | MIT | No |
| Classifier CPU fallback | [`MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33`](https://huggingface.co/MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33) | MIT | No |
| Dev/eval corpus | [`MikCil/f1-team-radio`](https://huggingface.co/datasets/MikCil/f1-team-radio) (14,681 clips, 149 GPs, 43 drivers, 2018-03-25 to 2025-12-07, MP3 16kHz) | CC-BY-4.0 (uploader tag; underlying broadcasts credited to F1 — see caveat below) | No |

**Why VoiceCLAP over the charter's original `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim`:**
audEERING's model is CC-BY-NC-SA-4.0 ("research purpose only" per its own
repo) and outputs arousal/dominance/valence with no fatigue dimension.
VoiceCLAP's attribute heads are commercially licensed and expose
`Fatigue_Exhaustion` and `Arousal` directly, plus `Recording_Quality`
and `Background_Noise` as a built-in confidence signal. Its own
published eval: Arousal r=0.82, Fatigue_Exhaustion r=0.48 — real, but
not on F1 audio. Keep `audeering/...` around only as a Day-1 comparator
if you want a second opinion, never as the shipped model.

**Why zero-shot NLI over embedding-prototype classification:** the
5-category taxonomy definitions become the classifier input directly.
No prototype set to build, no cosine threshold to hand-tune, no
aggregation rule to invent for edge cases. See `app/config.py`'s
`ClassifierConfig.TAXONOMY` for the exact wording in use.

**Dataset provenance caveat:** `MikCil/f1-team-radio`'s CC-BY-4.0 tag is
the uploader's license choice; the same card credits Formula 1 for the
original broadcasts. Use it freely for development and benchmarking.
For the actual public demo clip, prefer hackathon-provided audio or get
explicit team sign-off on provenance — don't let this slide to Day 5.

## Owns

This directory and `../../tests/radio_ai/`.

## Architecture

```text
audio file
  -> app/audio_preprocessing.py   (mono, 16kHz, Silero VAD trim)
  -> app/asr.py                   (distil-large-v3.5-ct2 via faster-whisper)
  -> app/tone.py                  (VoiceCLAP AttributeScorer -> label mapping)
  -> app/complaint_classifier.py  (DeBERTa zero-shot NLI -> taxonomy + precedence)
  -> RadioAnalysisOutput
```

`app/config.py` holds every model ID, pinned revision, and threshold in
one place. Thresholds marked `NEEDS_CALIBRATION` are placeholders —
see `VALIDATION_GATES.md` before trusting them past a smoke test.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8002
```

`ANALYZE_MODE=fixture` (the default) needs no model downloads at all —
useful for Workstreams C and D to keep building against this service
immediately. Flip to `ANALYZE_MODE=live` in `.env` once you're ready to
run the real pipeline; the first request after that will download and
cache all three models (VoiceCLAP encoder + heads is the biggest at
~110M params for the encoder), which takes a while on first run.

## Day-1 workflow

1. Get 3-5 real F1 radio clips (see "Getting sample clips" below).
2. `python scripts/benchmark_day1.py clip1.wav clip2.mp3 ...` — runs the
   full pipeline locally (no server needed) and writes
   `day1_benchmark_report.json`.
3. Fill in `VALIDATION_GATES.md` by hand against your own listening and
   labeling. The script does not grade itself.
4. If gates 2, 3, and 4 pass, you may enable
   `ENABLE_TEXT_TONE_DISAGREEMENT=true` on Day 4. If any fail, it stays
   off and the field is omitted from the JSON entirely.

## Getting sample clips

Two options, both requiring a Hugging Face account (see root
`.env.example` and the note on tokens below):

- **Manual:** browse
  [`MikCil/f1-team-radio`](https://huggingface.co/datasets/MikCil/f1-team-radio)
  in the HF dataset viewer, listen to a few, download 3-5 you can
  personally vouch for as intelligible.
- **Keyword-assisted shortlist:** `python scripts/shortlist_candidate_clips.py --out candidates.csv`
  pulls only the text metadata (not audio) and keyword-matches
  transcripts against the taxonomy, so you're not scrolling through
  14,681 rows blind. **This script has not been run in this session** —
  no local Python/ML environment was available to test it. Sanity
  check the first run; if it pulls the full ~2.5 GB dataset instead of
  just metadata, the comment at the bottom of the script has a
  `datasets`-library fallback.

Either way: keyword/text matching only narrows the list. You still have
to listen to each candidate before trusting it.

## On the Hugging Face token

You need a **read-scoped** token, not your write token, for everything
in this service — downloading public, ungated models and datasets.
Create one at https://huggingface.co/settings/tokens (fine-grained,
read-only) and put it in `.env` as `HF_TOKEN`. Your write token isn't
needed here at all; see the note in the main chat response for where a
write token actually applies (Workstream A's optional HF dataset
upload, or a Hugging Face Space deployment under Workstream D).

## Contract

Input: audio bytes/path + `incident_id`. Output: `RadioAnalysisOutput`,
see `contracts/api_contract.md` and
`contracts/schemas/radio_analysis_output.schema.json`.

## Independent test

Fixture mode returns valid JSON with zero model dependencies, so this
is true from Day 1 regardless of live-pipeline progress:

```bash
pytest tests/
```

## Cut rule

If the acoustic tone model fails `VALIDATION_GATES.md` gates 2/3/4 on
real F1-style audio, drop `text_tone_disagreement` only —
`ENABLE_TEXT_TONE_DISAGREEMENT` stays `false`. ASR, tone/arousal, and
complaint classification still ship; those three are load-bearing for
PS1 compliance and don't depend on the Mask gate passing.
