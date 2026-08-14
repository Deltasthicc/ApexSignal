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
| 0. Pipeline runs | No exceptions on 3-5 real clips | 3/3 clips (`2018_Australian_Grand_Prix_DANRIC01_3_20180325_170323.mp3`, `2018_Bahrain_Grand_Prix_BREHAR01_28_20180408_181729.mp3`, `2018_Australian_Grand_Prix_MAXVER01_33_20180325_163337.mp3`), 0 exceptions, complete JSON per clip. Report: `day1_benchmark_report.json`. Required two env fixes first, both now pinned in `requirements.txt`: `torchcodec` was missing (torchaudio.load() needs it since torchaudio 2.9+) and `nvidia-cublas-cu12` was missing (ctranslate2/faster-whisper needs CUDA 12 cublas even though torch on this box is CUDA 13). | PASS |

**Note on tone scores (Gate 2 will need this):** the VoiceCLAP `AttributeScorer`'s raw dimensions are not bounded to `[0,1]` the way `ToneThresholds` assumes — observed `Arousal` values of 1.60 and 2.72 on these 3 clips, well past `AROUSAL_ELEVATED_THRESHOLD=0.6`. `tone.map_to_label()` clamps the returned `tone_score` to `[0,1]`, so any clip with `Arousal > 1` collapses to an identical `tone_score=1.0, tone_confidence=1.0` — no resolution above that point. Gate 2b's Spearman correlation must be computed against the raw `Arousal` value in `tone_raw_scores`, not the clamped `tone_score`, or it will be meaningless. (Note written when `AROUSAL_ELEVATED_THRESHOLD` was still 0.6 — see gate 2a below for the recalibration to 2.565. The clamping behavior itself is unchanged either way.)

## Gate 0.5 — single-speaker check (do this while listening for gate 2)

`MikCil/f1-team-radio` mixes engineer and driver voices within a single
clip (confirmed both in the dataset's own sourcing notes and directly
in our own extracted samples — the MAXVER01 status-update clip has
both). Neither `asr.py` nor `tone.py` does speaker separation. There's
no time to build real diarization before submission, so the mitigation
is curation, not code: when picking clips, prefer ones where the
**driver** is speaking for most/all of the clip's duration, and reject
or trim ones that are mostly back-and-forth dialogue. If a demo-critical
clip has real driver+engineer overlap, say so explicitly rather than
letting a tone score silently reflect the wrong (or a blended) voice.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 0.5. Every demo-critical clip is single-speaker (driver-dominant) | Yes/No, per clip | Not a per-clip yes/no yet — that's still a human listening call. Built a triage helper instead (`scripts/flag_multispeaker_candidates.py`, output in `gate0.5_multispeaker_triage.txt`): counts VAD speech-segment gaps ≥0.3s as a cheap proxy for possible turn-taking. **Not diarization** — it has no idea who's speaking, only how speech is chunked in time. 10/20 clips flagged; `MAXVER01_33_163337` came out #1 (7 segments) — matches this doc's own by-ear example of a confirmed mixed-speaker clip, which is a real (if small) validation the heuristic carries signal. | PENDING — use the triage list to prioritize which clips to double-check by ear, still your call per clip |

## Gate 1 — ASR quality (meaning-critical, not raw WER)

Manually correct the transcript for each benchmarked clip yourself; the
`MikCil/f1-team-radio` dataset's own transcripts are Cohere-generated,
not ground truth, so don't benchmark against them directly.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 1a. Normalized WER on Day-1 sample | ≤ 20% | Original run: 20.45% (352 ref words). Applied 3 fixes (see below), re-ran, re-measured with a corrected scorer (see note): **20.28%** (360 ref words — the corrected scorer also splits hyphenated words in the *reference* text, hence the different word count). Still 0.28pp over. | FAIL, marginal |
| 1b. Meaning-critical word accuracy | ≥ 90% (front, rear, traction, brakes, lock, tyres, grip, puncture, rain, power, engine, gearbox) | Original: 78.95% (15/19). After fixes: **84.21% (16/19)**. Remaining misses: `FERALO01_14_163419` ("front"/"tyres" — a genuinely garbled 26-word clip that stayed hard under every config I tried), `BREHAR01_28_181729` ("front" — "front left corner" heard as "the left corner"). | FAIL, improved |
| 1c. Meaning-changing errors on final demo clips | 0 | Not run — no final demo clips chosen yet. This needs a human decision about which specific incidents go in the actual demo; not something to pick unilaterally. | PENDING — needs a human call on which clips |

**Fixes applied to get from 78.95%/20.45% to 84.21%/20.28% (`app/asr.py`, `app/audio_preprocessing.py`):**
1. **VAD trim padding.** `trim_silence()` was cutting exactly at the detected speech boundary. Verified directly on `LEWHAM01_44_171928`: the untrimmed clip transcribed "What's that?" correctly; the exactly-trimmed version silently dropped it, even though the VAD boundaries *did* include that utterance in-range — cutting flush against the onset changed how Whisper decoded it. Added a 0.2s padding buffer. (Traded off slightly on one other clip's wording — expected when tuning against n=20, net effect across the full set was positive.)
2. **F1-vocabulary `initial_prompt`.** Distil-whisper defaults to American spelling and has no F1 context, so "tyre/tyres" consistently came out "tire/tires" and driver names/jargon got mangled or hallucinated (`Verstappen`→"the Stappan", `damage`→"for Davids", `DRS`→"the RS"). Added an initial_prompt with driver surnames, British spelling cues, and F1 jargon (DRS, PU, quali, torque, brake, kerb, etc.).
3. **Fixed a bug in my own WER/critical-word scorer**, not the ASR: punctuation stripping was deleting hyphens instead of replacing them with a space, so "front-wing" became one token "frontwing" and silently failed to match "front" — that inflated the miss count on `MAXVER01_33_163337` for a reason that had nothing to do with the model. Also added standard spelled-number↔digit normalization (e.g. "eight"↔"8"), which is normal ASR-eval practice, not a leniency hack.

Also increased `beam_size` from faster-whisper's default (5) to 8 — modest, unclear standalone effect, kept since it didn't hurt the aggregate.

## Gate 2 — acoustic tone, clear cases

Human-label 15-20 clips blind (without seeing model output) as
CALM / ELEVATED_AROUSAL / FATIGUED / AMBIGUOUS, plus a 1-5 arousal
rating. Two people independently, if possible.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 2a. Agreement with human consensus on clear CALM/ELEVATED cases | ≥ 75% | **Recalibrated, re-run, re-confirmed.** Original run at `AROUSAL_ELEVATED_THRESHOLD=0.6`: 40% (8/20) — every one of the 20 clips scored above 0.6, so the threshold had zero discriminating power. Grid-searched the same 20 labels for the threshold value maximizing agreement: 85% (17/20) achieved across a plateau of 2.55-2.58; picked 2.565 (midpoint), now the default in `app/config.py`. Re-ran the full pipeline with the new default and re-measured directly (not just computed on paper): **85% (17/20)**. Remaining 3 misses: `KIMRAI01_7_162733` and `LEWHAM01_44_173536` (human ELEVATED, model CALM — both have unusually low raw Arousal for clips you rated elevated, 1.605 and 1.757), `SERPER01_11_161855` (human CALM, model ELEVATED, 2.634). n=20 from one dataset/era — treat 2.565 as a real improvement, not a final answer; recheck as more labeled clips accumulate. | **PASS** |
| 2b. Spearman correlation, human 1-5 arousal vs. model Arousal score | ≥ 0.50 | rho = 0.69 (n=20, using raw `tone_raw_scores.Arousal`, not the clamped `tone_score` — see note above) | PASS |

## Gate 3 — fatigue precision

Fatigue is the least-validated VoiceCLAP head (r=0.48 on its own eval
set, well below Arousal's r=0.82). Optimize for precision: a false
"fatigued" told to judges is worse than a missed one.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 3a. False positive FATIGUED on clips a human rated non-fatigued | As close to 0 as achievable | Original run at `FATIGUE_THRESHOLD=0.7`: 2/20 false positives (`SEBVET01_5_172625`, `VALBOT01_77_172205`, both human CALM). Raised the default to 1.1 (just above 1.075, the highest Fatigue_Exhaustion score seen anywhere in this sample) and re-ran: **0/20 false positives.** Important caveat, not just a formality: none of these 20 clips are actually fatigued, so this sample has zero true positives — 0 false positives here means "hasn't triggered incorrectly yet," not "fatigue detection works." Needs real fatigued clips before this threshold means anything beyond that. | Improved (0/20), but unvalidated for true positives |

## Gate 4 — degradation stability

Take 5 clean-ish clips, create additional copies with reasonable
bandwidth restriction / compression / added noise, compare tone output.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 4a. Median absolute score movement after degradation | ≤ 0.15 | Ran on 5 clips (`DANRIC01_3_170323`, `FERALO01_14_163419`, `BREHAR01_28_181729`, `VALBOT01_77_165927`, `LANSTR01_18_163831`), degraded via `scripts/degrade_audio.py` (3kHz low-pass + mu-law companding + additive noise at 12dB SNR — pure torchaudio/numpy, not ffmpeg, since system ffmpeg is broken on this box, see gate 0). Measured on `tone_score` (the actual JSON contract field). **First measurement was a false pass (0.0000 median)** — found `tone_score` was clamping to exactly 0.0 or 1.0 on every clip because `1.0 - arousal` assumed arousal is bounded to [0,1], which we'd already disproven in gate 2. Fixed `map_to_label()` to use a logistic margin from the threshold instead of a hard subtraction+clamp (`app/tone.py`), re-ran: **median movement 0.0168.** | PASS |
| 4b. Clips changing final tone class solely due to degradation | ≤ 1 of 5 | 1/5 — `LANSTR01_18_163831` flipped ELEVATED_AROUSAL→CALM (clean tone_score 0.608, degraded 0.510 — it was already right at the 0.5 decision boundary before degradation, so this isn't surprising). Passes exactly at the boundary; n=5 is small, treat "1/5" as fragile, not a comfortable margin. | PASS, marginal |

## Gate 5 — Mask (text-tone disagreement) go/no-go

`ENABLE_TEXT_TONE_DISAGREEMENT` in `.env` stays `false` unless ALL of
gates 2a, 2b, and 4 pass. If any one fails, the field stays completely
absent from the JSON output, not `null` and not `"LOW"` — the contract
makes it optional exactly for this reason.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 5. All of 2a + 2b + 4 pass | Yes/No | 2a: 85% (PASS). 2b: rho=0.69 (PASS). 4a: median movement 0.0168 (PASS). 4b: 1/5 class changes (PASS, but exactly at the boundary on only 5 clips — see gate 4b note on fragility). All three numeric criteria pass. **But this gate is necessary, not sufficient**: `app/main.py:91-98` raises `NotImplementedError` unconditionally when this flag is on, with an explicit comment that the text/tone comparison logic itself was never built, deliberately, until this gate passed. It's passed now, but the comparison logic still doesn't exist. Almost flipped the `.env` flag on the numeric result alone before checking `main.py` — would have broken every live request immediately. Did not touch `.env`. | **Numeric criteria: Yes. Flag: stays `false` — feature code doesn't exist yet. Implementing the actual comparison logic is the next real blocker, not a config change.** |

## Gate 6 — complaint classifier (Day 2)

Manually label ≥ 60 transcripts (10 per category + 10 NO_COMPLAINT).
Benchmark `deberta-v3-base-zeroshot-v1.1-all-33` against the xsmall
variant.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 6a. Macro-F1, base model | ≥ 0.80 | 0.356 at the best threshold found (0.15). Far below the 0.80 bar. | **FAIL** |
| 6b. NO_COMPLAINT F1, base model | ≥ 0.85 | 0.818 at threshold 0.15. Close but short. | **FAIL, marginal** |
| 6c. xsmall within 3pp of base AND service is CPU-only | Switch to xsmall via `USE_CLASSIFIER_FALLBACK=true` | base best macro-F1 0.356 (threshold 0.15) vs. xsmall best 0.300 (threshold 0.25) — 5.6pp gap, over the 3pp cutoff. | **PASS/RESOLVED — keep `deberta-v3-base`, do not switch to xsmall** |

**Real Gate 6 human labeling happened** (`labeling_pass_consensus_review.csv`, 58/60 labeled, 2 correctly left blank as too garbled to classify — checked myself that the labels weren't rubber-stamped against the keyword suggester: only 22/58 matched the suggestion). Sample is n=58, one short of the ≥60 target. Label distribution skewed heavily NO_COMPLAINT (44/58), zero surviving TYRE_GRIP_DEGRADATION examples after human review.

**`CLASSIFIER_NULL_THRESHOLD` recalibrated from this benchmark**: 0.5 → **0.15** (`app/config.py`), a genuine measured improvement (macro-F1 0.326 → 0.356), not an arbitrary pick — 0.15 was the actual best point in a 0.05-0.60 sweep, not a nearby round number.

**Two error patterns, kept on record for the next real fix (not noise, and not something a threshold change can fix):**
1. **False positives, context-blindness**: `NO_COMPLAINT → MECHANICAL_OTHER` on negated/reassuring/informational sentences containing mechanical vocabulary — e.g. *"Do you want a front wing change? No, not for now."*, *"Alex, do you think tyres are okay to push a little more..."* The model reacts to lexical presence of "front wing"/"tyres" over the sentence's actual meaning. 5 of 17 base-model mistakes at the best threshold are this shape.
2. **False negatives, muted framing**: both true `EXIT_TRACTION_REAR` examples stated matter-of-factly (*"the rear tyres are getting really hot, that's my main problem"*) were missed as `NO_COMPLAINT` — the model seems to want more emphatic complaint framing than real radio calls actually use.

These pull in opposite directions (over-trigger on vocabulary vs. under-trigger on calm phrasing), which is exactly why no single `NULL_THRESHOLD` value fixes both — that's a hypothesis-template/representation problem, next candidate fix. `FRONT_TURNIN_BRAKE` F1=0.000 is on record too, but n=2 true examples is noise, not a diagnosed failure — don't design around it yet.

Full sweep tables and mistake lists for both models, plus a tested (and rejected) hypothesis-template experiment: `GATE6_ERROR_ANALYSIS.md`. Short version of that experiment: tried a stricter template ("The driver is explicitly complaining about a failure with the {}") to fix pattern 1 — it made things worse, not better (macro-F1 0.356 → 0.143), collapsing every real complaint category to F1=0.000 while overcorrecting pattern 1. Keeping the original template.

## Gate 7 — Day 5 holdout

Keep ≥ 20 clips untouched by any threshold tuning. Run them once,
unmodified, before final rehearsal. For every incident used in the
demo, record: source clip ID, timestamp, manually-checked transcript,
ASR model + pinned revision, tone model + pinned revision, thresholds
used, classifier model + pinned revision, final JSON. This is what
makes "every number traces to source data" true rather than asserted.

| Gate | Threshold | Result | Verdict |
|---|---|---|---|
| 7. Holdout run clean, provenance recorded for every demo clip | Yes/No | Run on 2026-08-12 against 20 untouched clips (`HOLDOUT_REPORT.md`), one flagged and excluded for driver health/distress content per charter. But the run used `classifier null threshold: 0.5`, not the `0.15` Gate 6 later calibrated. | RUN, STALE CONFIG — re-run needed before this counts as done |

**Why not a clean PASS:** the run itself is real — 20 untouched clips, full model/revision provenance recorded, the sensitive clip correctly caught and excluded. But it predates the Gate 6 classifier recalibration (`NULL_THRESHOLD` 0.5 → 0.15), so every `complaint_category` in that report reflects the pre-calibration model and cannot be trusted as the final number. Re-run `scripts/run_holdout_gate7.py` with the current `app/config.py` thresholds on GPU hardware before quoting holdout classifier results anywhere. This previously read "PENDING — not run yet," which was stale: the run already happened, it just isn't on the final configuration.
