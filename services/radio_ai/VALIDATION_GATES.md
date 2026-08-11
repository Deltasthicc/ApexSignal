# Validation gates

Numeric go/no-go criteria for Workstream B. These exist so the Mask
cut decision and the model choices are mechanical, not a vibe call
made under demo-day pressure. Fill in the "Result" column as you run
each gate and keep this file as the record of why the stack looks the
way it does.

## Gate 0 — pipeline runs at all

Run `python scripts/benchmark_day1.py <clip1.wav> <clip2.wav> ...`
against 3-5 real F1 radio clips (see "Getting sample clips" in
`README.md`). Passes if it prints a complete JSON object per clip with
no exception. This is a smoke test, not a quality check.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 0. Pipeline runs | No exceptions on 3-5 real clips | | |

## Gate 1 — ASR quality (meaning-critical, not raw WER)

Manually correct the transcript for each benchmarked clip yourself; the
`MikCil/f1-team-radio` dataset's own transcripts are Cohere-generated,
not ground truth, so don't benchmark against them directly.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 1a. Normalized WER on Day-1 sample | ≤ 20% | | |
| 1b. Meaning-critical word accuracy | ≥ 90% (front, rear, traction, brakes, lock, tyres, grip, puncture, rain, power, engine, gearbox) | | |
| 1c. Meaning-changing errors on final demo clips | 0 | | |

## Gate 2 — acoustic tone, clear cases

Human-label 15-20 clips blind (without seeing model output) as
CALM / ELEVATED_AROUSAL / FATIGUED / AMBIGUOUS, plus a 1-5 arousal
rating. Two people independently, if possible.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 2a. Agreement with human consensus on clear CALM/ELEVATED cases | ≥ 75% | | |
| 2b. Spearman correlation, human 1-5 arousal vs. model Arousal score | ≥ 0.50 | | |

## Gate 3 — fatigue precision

Fatigue is the least-validated VoiceCLAP head (r=0.48 on its own eval
set, well below Arousal's r=0.82). Optimize for precision: a false
"fatigued" told to judges is worse than a missed one.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 3a. False positive FATIGUED on clips a human rated non-fatigued | As close to 0 as achievable | | |

## Gate 4 — degradation stability

Take 5 clean-ish clips, create additional copies with reasonable
bandwidth restriction / compression / added noise, compare tone output.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 4a. Median absolute score movement after degradation | ≤ 0.15 | | |
| 4b. Clips changing final tone class solely due to degradation | ≤ 1 of 5 | | |

## Gate 5 — Mask (text-tone disagreement) go/no-go

`ENABLE_TEXT_TONE_DISAGREEMENT` in `.env` stays `false` unless ALL of
gates 2a, 2b, and 4 pass. If any one fails, the field stays completely
absent from the JSON output, not `null` and not `"LOW"` — the contract
makes it optional exactly for this reason.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 5. All of 2a + 2b + 4 pass | Yes/No | | |

## Gate 6 — complaint classifier (Day 2)

Manually label ≥ 60 transcripts (10 per category + 10 NO_COMPLAINT).
Benchmark `deberta-v3-base-zeroshot-v1.1-all-33` against the xsmall
variant.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 6a. Macro-F1, base model | ≥ 0.80 | | |
| 6b. NO_COMPLAINT F1, base model | ≥ 0.85 | | |
| 6c. xsmall within 3pp of base AND service is CPU-only | Switch to xsmall via `USE_CLASSIFIER_FALLBACK=true` | | |

## Gate 7 — Day 5 holdout

Keep ≥ 20 clips untouched by any threshold tuning. Run them once,
unmodified, before final rehearsal. For every incident used in the
demo, record: source clip ID, timestamp, manually-checked transcript,
ASR model + pinned revision, tone model + pinned revision, thresholds
used, classifier model + pinned revision, final JSON. This is what
makes "every number traces to source data" true rather than asserted.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 7. Holdout run clean, provenance recorded for every demo clip | Yes/No | | |
