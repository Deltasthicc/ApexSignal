# Gate 6 error analysis and threshold sweep — experiment notes

Generated 2026-08-12 from `labeling_pass_consensus_review.csv` (58
human-labeled transcripts, 2 correctly left blank as too garbled to
classify). See `VALIDATION_GATES.md` gate 6 for the summary; this file
keeps the full sweep tables and mistake lists so the exact failure
examples are available for whatever the next fix turns out to be.

## Threshold sweep, `deberta-v3-base-zeroshot-v1.1-all-33`

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

Best: **0.25**, macro-F1=0.300 — 5.6pp below base's 0.356. Gate 6c:
keep base, xsmall not adopted regardless of CPU/GPU (>3pp gap).

Per-class F1 at 0.25: MECHANICAL_OTHER 0.200, FRONT_TURNIN_BRAKE 0.444,
EXIT_TRACTION_REAR 0.000, TYRE_GRIP_DEGRADATION 0.000,
VISIBILITY_TRACK_CONDITION 0.400, NO_COMPLAINT 0.753.

## Two error patterns identified, threshold can't fix either

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

**Result: rejected. Stricter template is a clear regression, not an
improvement.**

| template | best threshold | macro-F1 | NO_COMPLAINT F1 | every other category's F1 |
|---|---|---|---|---|
| baseline (`"This message is about {}."`) | 0.15 | **0.356** | 0.818 | 0.000-0.750 |
| stricter (`"The driver is explicitly complaining..."`) | 0.10 | **0.143** | 0.857 | **0.000 across all five** |

The stricter template did fix some of pattern 1 (e.g. "Do you want a
front wing change? No, not for now." → correctly NO_COMPLAINT now).
But it overcorrected so hard that every real complaint category
collapsed to F1=0.000 -- including flipping a previously-*correct*
prediction to wrong (`"Generally the traction is going off."` was
correctly EXIT_TRACTION_REAR at baseline, became NO_COMPLAINT under
the stricter template). Requiring "explicitly complaining about a
failure" is too high a bar for how drivers actually phrase real-time
radio complaints -- calm, factual statements are the norm, not the
exception, which is exactly pattern 2's problem, now made worse across
the board rather than fixed for pattern 1 alone.

**Conclusion: keep the baseline template and `NULL_THRESHOLD=0.15`.**
Fixing the two patterns for real likely needs per-category label
descriptions tuned individually (not one global template swap), a
hierarchical gate (detect "is there a complaint at all" separately
from "which category"), or more labeled data before either is worth
trusting -- not a quick template edit. Recorded here so this exact
negative result doesn't get re-discovered by re-running the same
experiment later.
