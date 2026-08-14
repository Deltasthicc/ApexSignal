# Gate 6 error analysis and threshold sweep — experiment notes

Generated 2026-08-12 from `labeling_pass_consensus_review.csv` (58
human-labeled transcripts, 2 correctly left blank as too garbled to
classify). See `VALIDATION_GATES.md` gate 6 for the summary; this file
keeps the full sweep tables and mistake lists so the exact failure
examples are available for whatever the next fix turns out to be.

## 2026-08-14 correction — everything below was measured against a bug

`scripts/benchmark_classifier.py` passed bare taxonomy keys as
candidate labels (`LABELS`), not the descriptive taxonomy text
(`TAXONOMY.values()`) that `app/complaint_classifier.py` actually uses
in production. That meant every sweep/experiment below never exercised
production's real code path — and production's real code path turned
out to have its own separate bug (a key-mismatch that made `classify()`
return `None` unconditionally, for every input, regardless of
threshold — see `VALIDATION_GATES.md` gate 6 for the full story).

Both bugs are now fixed. The sections below are kept as a record of
what was tried and are marked superseded where the underlying numbers
changed; corrected results are added alongside, not written over the
old ones, so the history of what happened is still traceable.

## Threshold sweep, `deberta-v3-base-zeroshot-v1.1-all-33`

**SUPERSEDED by the correction above — table below was measured
against the pre-fix mismatched hypothesis construction.**

| threshold | macro-F1 | NO_COMPLAINT F1 | accuracy |
|---|---|---|---|
| 0.05 | 0.324 | 0.750 | 58.6% |
| 0.10 | 0.285 | 0.818 | 69.0% |
| **0.15** | **0.356** | 0.818 | 70.7% |
| 0.20 | 0.301 | 0.835 | 72.4% |
| 0.25 | 0.308 | 0.848 | 74.1% |
| 0.30 | 0.328 | 0.860 | 75.9% |
| 0.35 | 0.328 | 0.860 | 75.9% |
| 0.40 | 0.328 | 0.860 | 75.9% |
| 0.45 | 0.326 | 0.851 | 75.9% |
| 0.50 (old default) | 0.326 | 0.851 | 75.9% |
| 0.55 | 0.326 | 0.851 | 75.9% |
| 0.60 | 0.326 | 0.851 | 75.9% |

Best: **0.15**, macro-F1=0.356. Per-class F1 at 0.15: MECHANICAL_OTHER
0.167, FRONT_TURNIN_BRAKE 0.000 (n=2, noise), EXIT_TRACTION_REAR 0.400,
TYRE_GRIP_DEGRADATION 0.000 (n=0 true examples, undefined not failing),
VISIBILITY_TRACK_CONDITION 0.750, NO_COMPLAINT 0.818.

17 mistakes at threshold 0.15:
```
[NO_COMPLAINT -> VISIBILITY_TRACK_CONDITION] 'Lando, if we can look after the front left a bit and keep Stroll behind, that wi'
[NO_COMPLAINT -> MECHANICAL_OTHER] 'Sebastian, we need to retire the car in the garage. So, box box, the gearbox is '
[EXIT_TRACTION_REAR -> NO_COMPLAINT] 'Okay, Max, can we have a status update please? Yeah, the rear tires are getting '
[NO_COMPLAINT -> MECHANICAL_OTHER] 'I need engine. Copy that, Lance. Strat seven, strat seven to charge some more.'
[MECHANICAL_OTHER -> NO_COMPLAINT] 'Where are we losing? Why are we so slow? Okay, Pierre, so we did pick up some da'
[FRONT_TURNIN_BRAKE -> NO_COMPLAINT] 'I have no chance because we dropped the front wing way too much.'
[NO_COMPLAINT -> MECHANICAL_OTHER] 'Do you want a front wing change? No, not for now. Copy that. So driving through '
[NO_COMPLAINT -> MECHANICAL_OTHER] 'Alex, do you think tyres are okay to push a little more through 3 and maybe 13?'
[NO_COMPLAINT -> TYRE_GRIP_DEGRADATION] 'Two cars ahead, older tyres. Safety car is entering the pit lane now. Safety car'
[NO_COMPLAINT -> MECHANICAL_OTHER] "They're very good. We'll go through the details once you're out of the car, but "
[EXIT_TRACTION_REAR -> MECHANICAL_OTHER] 'Is the wind changing between 6 and 7? I had a bit of rear instability. Confirm. '
[MECHANICAL_OTHER -> NO_COMPLAINT] 'Okay, understood. Got a lot of vibrations.'
[MECHANICAL_OTHER -> NO_COMPLAINT] 'I think I have still some damage. Balance is quite a bit off. Understood. We do '
[EXIT_TRACTION_REAR -> NO_COMPLAINT] 'Okay, Kimi, still P11, your safety car window is closed, how are your tires? Yea'
[VISIBILITY_TRACK_CONDITION -> NO_COMPLAINT] 'Starting to rain a bit.'
```

## Threshold sweep, `deberta-v3-xsmall-zeroshot-v1.1-all-33`

**SUPERSEDED by the correction above.**

Best (old, wrong methodology): 0.25, macro-F1=0.300 — 5.6pp below
base's (also wrong) 0.356. Gate 6c conclusion at the time: keep base.

Per-class F1 at 0.25: MECHANICAL_OTHER 0.200, FRONT_TURNIN_BRAKE 0.444,
EXIT_TRACTION_REAR 0.000, TYRE_GRIP_DEGRADATION 0.000,
VISIBILITY_TRACK_CONDITION 0.400, NO_COMPLAINT 0.753.

## Corrected threshold sweeps, 2026-08-14 (real production hypothesis construction)

| threshold | base macro-F1 | base NO_COMPLAINT F1 | xsmall macro-F1 | xsmall NO_COMPLAINT F1 |
|---|---|---|---|---|
| 0.05 | 0.150 | 0.421 | 0.211 | 0.606 |
| 0.10 | 0.208 | 0.508 | 0.382 | 0.759 |
| 0.15 | 0.199 | 0.523 | **0.393** | 0.780 |
| 0.20 | 0.218 | 0.609 | 0.393 | 0.780 |
| 0.25 | 0.227 | 0.648 | 0.329 | 0.771 |
| 0.30 | 0.235 | 0.685 | 0.329 | 0.771 |
| 0.35 | 0.252 | 0.720 | 0.283 | 0.795 |
| 0.40 | 0.257 | 0.737 | 0.283 | 0.795 |
| **0.45** | **0.258** | 0.737 | 0.285 | 0.809 |
| 0.50 | 0.258 | 0.737 | 0.310 | 0.835 |
| 0.55 | 0.258 | 0.737 | 0.325 | 0.826 |
| 0.60 | 0.217 | 0.727 | 0.387 | 0.839 |

**Best for base: 0.45, macro-F1=0.258.** Per-class F1: MECHANICAL_OTHER
0.240, FRONT_TURNIN_BRAKE 0.000 (n=2, noise), EXIT_TRACTION_REAR 0.000,
TYRE_GRIP_DEGRADATION 0.000 (n=0 true examples), VISIBILITY_TRACK_CONDITION
0.571, NO_COMPLAINT 0.737. Now the real default in `app/config.py`.

**Best for xsmall: 0.15, macro-F1=0.393 — beats base by 13.5pp.** This
reverses the previous (wrong-methodology) Gate 6c conclusion.
Per-class F1: MECHANICAL_OTHER 0.111, FRONT_TURNIN_BRAKE 0.800,
EXIT_TRACTION_REAR 0.000, TYRE_GRIP_DEGRADATION 0.000,
VISIBILITY_TRACK_CONDITION 0.667, NO_COMPLAINT 0.780. **Not switched to
in production** — this reverses an explicit prior "lock in base"
decision and needs a human call, not an automatic flip. See
`VALIDATION_GATES.md` gate 6c.

25 mistakes for base at threshold 0.45:
```
[NO_COMPLAINT -> MECHANICAL_OTHER] "Copy, yeah, we couldn't keep up with Alban. It was a good decision to let him go"
[VISIBILITY_TRACK_CONDITION -> NO_COMPLAINT] "Small drops of rain. It doesn't look like there's much on the radar."
[NO_COMPLAINT -> MECHANICAL_OTHER] 'Leclerc 0.9, turn 11, 12 with stronger gust of tailwind, same snap on the other '
[NO_COMPLAINT -> MECHANICAL_OTHER] 'Sebastian, we need to retire the car in the garage. So, box box, the gearbox is '
[EXIT_TRACTION_REAR -> MECHANICAL_OTHER] 'Okay, Max, can we have a status update please? Yeah, the rear tires are getting '
[NO_COMPLAINT -> MECHANICAL_OTHER] 'I need engine. Copy that, Lance. Strat seven, strat seven to charge some more.'
[MECHANICAL_OTHER -> NO_COMPLAINT] 'Where are we losing? Why are we so slow? Okay, Pierre, so we did pick up some da'
[FRONT_TURNIN_BRAKE -> MECHANICAL_OTHER] 'I have no chance because we dropped the front wing way too much.'
[NO_COMPLAINT -> MECHANICAL_OTHER] 'Do you want a front wing change? No, not for now. Copy that. So driving through '
[EXIT_TRACTION_REAR -> NO_COMPLAINT] 'Generally the traction is going off.'
[NO_COMPLAINT -> MECHANICAL_OTHER] 'We think Verstappen has some damage.'
[NO_COMPLAINT -> VISIBILITY_TRACK_CONDITION] 'Still happy on the full wet. Yeah, no chance on the inter. Understood.'
[NO_COMPLAINT -> MECHANICAL_OTHER] "They're very good. We'll go through the details once you're out of the car, but "
[NO_COMPLAINT -> MECHANICAL_OTHER] 'So that floor damage looks like it picked up at turn 8, so right hand side.'
[EXIT_TRACTION_REAR -> NO_COMPLAINT] 'Is the wind changing between 6 and 7? I had a bit of rear instability. Confirm. '
```

## Two error patterns identified, threshold can't fix either

(Re-confirmed present in the corrected 2026-08-14 mistake list too --
these are real patterns in the model's behavior, not an artifact of
either bug.)

1. **Context-blind false positives** (`NO_COMPLAINT → MECHANICAL_OTHER`
   etc.): mechanical vocabulary triggers a category even when the
   sentence negates, questions, or reassures rather than complains --
   *"Do you want a front wing change? No, not for now."*
2. **Muted-framing false negatives** (`EXIT_TRACTION_REAR → NO_COMPLAINT`):
   matter-of-fact complaints stated without emphatic language get
   missed -- *"the rear tyres are getting really hot, that's my main
   problem."*

These pull in opposite directions, which is exactly why they showed up
as a hypothesis to test with a stricter template rather than more
threshold tuning.

## Experiment: stricter hypothesis template (tested, rejected)

Hypothesis: replace `"This message is about {}."` with `"The driver is
explicitly complaining about a failure with the {}."` to force more
semantic strictness and reduce pattern 1 (context-blind false
positives), per the theory that NLI zero-shot models over-weight
lexical overlap. Tested directly against the same 58 examples with the
same sweep methodology (`scripts/experiment_hypothesis_template.py`),
not just reasoned about.

**Result at the time: rejected. Stricter template looked like a clear
regression.** Re-run 2026-08-14 with the corrected hypothesis
construction (this script imports `score_transcript` directly from
`benchmark_classifier`, so it inherited that fix automatically) —
**same verdict holds, different magnitude:**

| template | best threshold | macro-F1 | NO_COMPLAINT F1 |
|---|---|---|---|
| baseline (corrected) | 0.45 | **0.258** | 0.737 |
| stricter (`"The driver is explicitly complaining..."`) | 0.55 | **0.161** | 0.753 |

Still a real regression (-9.7pp under the corrected setup, vs. the
originally-measured -21.3pp under the wrong one — smaller magnitude,
same direction, same conclusion). The stricter template still fixes
some context-blind false positives while breaking real complaints
elsewhere -- e.g. `"We think Verstappen has some damage."` correctly
flips to NO_COMPLAINT, but `"Generally the traction is going off."`
flips from correct (EXIT_TRACTION_REAR) to wrong (MECHANICAL_OTHER).

**Conclusion unchanged: keep the baseline template.** `NULL_THRESHOLD`
is now 0.45, not 0.15 (see the correction section above).

## Experiment: hierarchical gate (tested, also rejected)

Second candidate fix: split into (1) binary "is this a complaint at
all?" (single-label softmax over 2 options, not independent multi_label
scores) then (2) "which of the 5 categories?" only if stage 1 says yes.
Theory: a genuine either/or decision at stage 1 should be more decisive
than 6 independent entailment scores all fighting the same 0.15
threshold. Tested against the same 58 examples
(`scripts/experiment_hierarchical_gate.py`).

**Result at the time: rejected, looked like a clear regression** (0.242
vs. a wrongly-measured 0.356 baseline, -11.4pp). Stage 2 of this script
also had the same bare-key mismatch as the original `benchmark_classifier.py`
(stage 1's binary hypotheses were always custom text, unaffected).
Fixed and re-run 2026-08-14:

**Corrected result: macro-F1 = 0.259, accuracy 50.0%.** Compared
against the *corrected* single-pass baseline (0.258, not the old wrong
0.356), this is a statistical tie — **verdict changes from "rejected,
clear regression" to "unresolved, no clear win or loss."** The
script's own printed "Delta: -9.7pp" is comparing against a stale
hardcoded number left in the script and should be ignored; the real
comparison is 0.259 vs 0.258.

Stage 1 (binary complaint detection) is still the weak link -- 24/58
wrong, still overconfident on informational lines:
```
true=NO_COMPLAINT  stage1_said_complaint=True  score=0.995  'We think Verstappen has some damage.'
true=NO_COMPLAINT  stage1_said_complaint=True  score=0.999  'Sebastian, we need to retire the car in the garage. So, box '
true=NO_COMPLAINT  stage1_said_complaint=True  score=0.989  'Two cars ahead, older tyres. Safety car is entering the pit '
```

**Current state: the stricter-template idea is rejected (confirmed
twice now), the hierarchical-gate idea is neither confirmed nor
rejected** -- it's not clearly better, but it's also not clearly worse
than the single-pass approach anymore, which is a different thing to
tell someone than "already tried, doesn't work." Worth a proper
re-look (e.g. fixing stage 1's overconfidence specifically) if this
gate gets revisited, rather than treating it as closed.

Current best-known production configuration: single-pass
`multi_label=True`, baseline hypothesis template, `NULL_THRESHOLD=0.45`
with `deberta-v3-base` -- though `deberta-v3-xsmall` now measurably
outperforms base (see the correction section above) and that
comparison hasn't been acted on pending a human decision. Next things
worth trying: per-category label descriptions tuned individually, a
fixed (less overconfident) stage-1 binary gate, or more labeled data --
n=58 with 44/58 being one class is a thin basis for any of these
changes to generalize confidently either way.
