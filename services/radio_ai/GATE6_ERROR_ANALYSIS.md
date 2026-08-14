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

## 2026-08-14, continued: three more attempts against xsmall (the real production baseline, 0.393)

Everything above compared against `base`. Production is `xsmall` now
(see `app/config.py`, `USE_CLASSIFIER_FALLBACK=true`) with corrected
single-pass macro-F1 **0.393** -- that's the actual number the three
attempts below are measured against, per `VALIDATION_GATES.md` gate 6
"things worth trying," roughly in the given order of expected value.

### Attempt 1 (re-tried): fix hierarchical-gate stage 1 -- REJECTED

`scripts/experiment_hierarchical_gate_v2.py`. Stage 1's own error
analysis said it's overconfident on informational lines mentioning
mechanical vocabulary without complaining -- tried 4 stage-1 hypothesis
phrasings (original, "reporting vs relaying," "problem vs mention,"
"complaint vs observation") × a swept decision threshold (0.3-0.9,
28 combinations total) against `xsmall`, with stage 2's raw scores
cached once and reused across every combination.

**Best combination: `"complaint_vs_observation"` @ threshold 0.8,
macro-F1=0.281 -- a real -11.2pp regression vs. the 0.393 baseline.**
No phrasing/threshold combination beat single-pass. Per-class F1 at
best: MECHANICAL_OTHER 0.333, FRONT_TURNIN_BRAKE 0.500, EXIT_TRACTION_REAR
0.000, TYRE_GRIP_DEGRADATION 0.000, VISIBILITY_TRACK_CONDITION 0.000,
NO_COMPLAINT 0.854. This confirms (more thoroughly than the first
hierarchical attempt, which only tried one phrasing at a fixed 0.5
threshold and landed as "unresolved") that the architecture itself is
the problem, not the wording: splitting the decision removes
NO_COMPLAINT's ability to compete as an independent score against each
real category simultaneously, which is specifically what lets it win
on informational lines under the single-pass `multi_label=True` setup.
**Verdict updated from "unresolved" to rejected, for xsmall
specifically.**

### Attempt 2: per-category taxonomy descriptions, tuned individually -- REJECTED, worse than attempt 1

`scripts/experiment_refined_taxonomy.py`. Kept the winning single-pass
architecture, rewrote each category's `TAXONOMY` description to target
its own known failure: MECHANICAL_OTHER made to explicitly exclude
denied/hypothetical/third-party mentions; FRONT_TURNIN_BRAKE,
EXIT_TRACTION_REAR, TYRE_GRIP_DEGRADATION each given "even in a calm or
matter-of-fact tone" framing to catch muted complaints; NO_COMPLAINT
broadened to explicitly cover third-party/resolved/hypothetical
mentions. Full sweep re-run for both current and refined wording in
the same process for a fair same-run comparison.

**Result: macro-F1=0.167 at best threshold (0.6) -- a -22.6pp
regression, worse than doing nothing and worse than attempt 1.**
FRONT_TURNIN_BRAKE became a major new false-positive source on
celebratory/congratulatory messages with zero connection to
braking/turn-in -- e.g. `"Get in there, Lewis! What a way to win your
seventh..."` and `"Podium in Qatar! What the hell?... Great job"` both
misclassified as FRONT_TURNIN_BRAKE. Likely cause: adding "even in a
calm or matter-of-fact tone" to three category descriptions injected
generic conversational-tone semantic content that diluted entailment
specificity rather than sharpening it -- the fix for pattern 2 (muted
framing) actively broke pattern 1 (context-blindness) worse than
before, the opposite of the intent. **Rejected, and a specific lesson
for later: don't add tone/register descriptors to a zero-shot
hypothesis meant to discriminate on content.**

### Attempt 3 (skipped): more labeled data

Not attempted in this session -- requires human listening/reading to
produce new ground truth, which this project's standing rule (and this
gate's own guardrails) explicitly reserve for a human, not an AI
session. Genuinely skipped, not silently done and hidden.

### Attempt 4: a different model family (sentence embeddings + prototype similarity) -- REAL IMPROVEMENT, not yet adopted

`scripts/experiment_embedding_classifier.py`. Attempts 1-2 plateaued
(both rejected, both worse than baseline), which is exactly the
condition the gate's own guardrails set for trying a genuinely
different architecture rather than another zero-shot-NLI variant.

Model: `sentence-transformers/all-MiniLM-L6-v2`, verified against the
live HF Hub API before use (same bar every other model in this project
was held to): exists, ungated, Apache-2.0, sha
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Each category's existing
`TAXONOMY` description text becomes its prototype embedding (same text
the NLI approach already uses, so this isn't confounded by different
wording) -- cosine similarity between each transcript and all 6
prototypes, NO_COMPLAINT decided by a swept similarity margin against
the best real-category match.

**Result: macro-F1=0.454 at margin=0.16 -- a real +6.1pp improvement
over the 0.393 baseline.** Per-class: MECHANICAL_OTHER 0.286,
FRONT_TURNIN_BRAKE 0.333, **EXIT_TRACTION_REAR 0.571** (0.000 in every
NLI attempt so far, including base and xsmall single-pass),
TYRE_GRIP_DEGRADATION 0.000 (still zero true examples in this sample,
undefined not failing), VISIBILITY_TRACK_CONDITION 0.727, NO_COMPLAINT
0.805.

Full margin sweep (0.00-0.30, step 0.02):
```
margin     macro-F1   accuracy
0.0        0.304      32.8%
0.02       0.315      34.5%
0.04       0.328      36.2%
0.06       0.357      44.8%
0.08       0.393      51.7%
0.1        0.421      56.9%
0.12       0.434      62.1%
0.14       0.446      65.5%
0.16       0.454      70.7%   <- best
0.18       0.384      69.0%
0.2        0.400      72.4%
0.22       0.367      77.6%
0.24       0.387      82.8%
0.26       0.341      81.0%
0.28       0.359      82.8%
0.3        0.359      82.8%
```
17 mistakes at margin=0.16:
```
[NO_COMPLAINT -> VISIBILITY_TRACK_CONDITION] 'So, stop. There is actually a small chance of rain in the race. Meteor France pu'
[MECHANICAL_OTHER -> FRONT_TURNIN_BRAKE] 'Engine feels poor on downshifts, pushing me forward.'
[NO_COMPLAINT -> MECHANICAL_OTHER] 'Sebastian, we need to retire the car in the garage. So, box box, the gearbox is '
[EXIT_TRACTION_REAR -> NO_COMPLAINT] 'Okay, Max, can we have a status update please? Yeah, the rear tires are getting '
[MECHANICAL_OTHER -> NO_COMPLAINT] 'Where are we losing? Why are we so slow? Okay, Pierre, so we did pick up some da'
[FRONT_TURNIN_BRAKE -> NO_COMPLAINT] 'I have no chance because we dropped the front wing way too much.'
[NO_COMPLAINT -> TYRE_GRIP_DEGRADATION] 'Alex, do you think tyres are okay to push a little more through 3 and maybe 13?'
[NO_COMPLAINT -> VISIBILITY_TRACK_CONDITION] 'We are expecting rain total up 50, expected rain total up 50.'
[NO_COMPLAINT -> FRONT_TURNIN_BRAKE] "They're very good. We'll go through the details once you're out of the car, but "
[NO_COMPLAINT -> EXIT_TRACTION_REAR] 'So that floor damage looks like it picked up at turn 8, so right hand side.'
[EXIT_TRACTION_REAR -> NO_COMPLAINT] 'Is the wind changing between 6 and 7? I had a bit of rear instability. Confirm. '
[NO_COMPLAINT -> VISIBILITY_TRACK_CONDITION] 'Threat of rain five to ten minutes hitting ten five seven.'
[NO_COMPLAINT -> TYRE_GRIP_DEGRADATION] 'Albums can be held up by Gasly on Old Tires, Daniel Lastlap, 49.6.'
[MECHANICAL_OTHER -> NO_COMPLAINT] 'I think I have still some damage. Balance is quite a bit off. Understood. We do '
[NO_COMPLAINT -> MECHANICAL_OTHER] 'and check the rear brakes, rear brake temperatures during these laps behind the '
[NO_COMPLAINT -> FRONT_TURNIN_BRAKE] 'Are you locked up and then just turn in very sharp?'
[NO_COMPLAINT -> TYRE_GRIP_DEGRADATION] "Yeah, that's the last few left. I had to go flat out. It was just really strange"
```

**Not adopted in production, deliberately, per this gate's own
guardrail ("flag it back, don't auto-correct").** Reasons to be
cautious about this specific number, not just excited about it:
- The margin sweep is noisy, not smooth (0.16 -> 0.454, 0.18 -> 0.384,
  partial recovery after) -- consistent with n=58 being thin enough
  that a single flipped example moves the curve visibly. Same
  overfitting exposure as every other Gate 6 sweep in this project
  (tuned and measured on the same 58 examples), not a new flaw unique
  to this approach, but worth naming since the improvement itself is
  the headline here.
- Adopting this for real means: adding `sentence-transformers` to
  `requirements.txt` (currently installed in this venv only, not
  committed), and rewriting `app/complaint_classifier.py`'s actual
  decision logic to a different architecture, not a config value --
  a bigger change than any prior Gate 6 fix.
- Even at 0.454, this is nowhere close to gate 6a's 0.80 target. Real,
  worth knowing about, not a fix for the underlying gap.

If this gets pursued further: try richer prototypes (a few real
example utterances per category averaged together, not just the
taxonomy description text alone) before concluding embeddings are the
answer -- this run used the cheapest possible version of the idea and
still beat the NLI baseline, which is itself informative.

**2026-08-14, adopted in production** (see `VALIDATION_GATES.md` gate
6d): the embedding-prototype backend above is now what
`app/complaint_classifier.py::classify()` actually runs
(`CLASSIFIER_BACKEND=embedding`). Ported the exact decision logic from
this script, then re-verified production `classify()` reproduces
macro-F1=0.4538 (rounds to 0.454) with identical per-class F1 -- the
same logic, confirmed, not re-derived from this writeup.

## 2026-08-14, Part 2: pushing past 0.454 (production baseline)

Three more things tried, in the order suggested. All measured directly
against the 58-example benchmark, same rigor as everything above.

### Item 1: richer prototypes (description + real example text) -- REJECTED, small regression

`scripts/experiment_richer_prototypes.py`. Each category's prototype
becomes the description embedding averaged with embeddings of its
*other* already-labeled examples from the same 58-example set --
**leave-one-out**, not naive averaging: while scoring example i, its
own text is never part of its own category's prototype (that would be
scoring "does this match itself," inflating the number for a reason
that wouldn't generalize to a new clip). `TYRE_GRIP_DEGRADATION` (n=0)
and, for each individual example, whichever category has no *other*
same-category example left after holdout, correctly falls back to the
description-only prototype -- 58 such fallbacks total, all attributable
to `TYRE_GRIP_DEGRADATION`'s zero examples (58 examples x 1 category
with zero others = 58, not a bug).

**Result: macro-F1=0.442 at best margin 0.04 -- a real -1.2pp
regression** vs. the production description-only baseline (0.454). Not
uniform: `MECHANICAL_OTHER` improved (0.500 vs 0.286) but
`FRONT_TURNIN_BRAKE` collapsed to F1=0.000 (was 0.333) -- likely
because n=2 is too thin for leave-one-out averaging to help; averaging
with a single noisy other example can shift the prototype in an
unhelpful direction rather than genuinely generalizing. Net effect
roughly cancels out to a small loss. **Rejected** -- richer prototypes
built from this specific 58-example set don't help; more/better
labeled data per category, not more averaging tricks on the same thin
data, is the likely real lever (see item 4).

### Item 2: ensemble of NLI-xsmall and embedding -- REJECTED, despite genuinely disjoint mistakes

Checked the actual mistake sets before building anything, per this
gate's own rule ("only worth trying if the mistake lists are actually
different"): xsmall @ 0.15 has 21 mistakes, embedding @ 0.16 has 17,
and only **9 overlap** -- 20 of 29 unique wrong examples (69%) are
genuinely disjoint, comfortably past the bar for trying an ensemble.

Tested a simple, predefined rule (decided before looking at results,
specifically to avoid overfitting the rule itself to this exact set):
if both models agree, use it; if one says a real category and the
other says `NO_COMPLAINT`, trust the real-category call; if both name
*different* real categories, default to embedding's (the higher
aggregate scorer, the actual production choice).

**Result: macro-F1=0.432 -- a real -2.2pp regression vs. embedding
alone** (though still beats xsmall alone's 0.393). `NO_COMPLAINT` F1
dropped to 0.722 (from embedding's 0.805) -- "any positive detection
wins" picks up genuine disjoint catches, but just as often it also
promotes one model's *wrong* category claim over the other's *correct*
`NO_COMPLAINT`, since disjoint mistakes include cases where one model
is right and the other is confidently wrong, not just cases where they
usefully complement each other. **Rejected.** Disjoint mistakes were a
necessary condition for an ensemble to be worth trying, not a
sufficient one -- this specific combination rule doesn't turn that
disjointness into a net win.

### Item 3: margin robustness -- reported plainly, no meaningful cross-validation possible

The adopted margin (0.16) sits on a visibly noisy stretch of the sweep
curve:

```
margin  macro-F1
0.12    0.434
0.14    0.446
0.16    0.454   <- adopted
0.18    0.384
0.20    0.400
```

Considered k-fold cross-validation per the gate's suggestion, but it
isn't meaningful here: `FRONT_TURNIN_BRAKE` has exactly 2 examples and
`TYRE_GRIP_DEGRADATION` has 0 -- there's no way to stratify even a
small number of folds without leaving a category entirely absent from
some folds' training data, which wouldn't measure robustness so much
as measure the absence of data. Reporting the neighborhood plainly
instead, per the gate's own fallback instruction: **0.16 is a real
local best, not a stable plateau** -- treat the margin as "somewhere
in 0.12-0.16," not as a precise, load-bearing constant, until there's
enough labeled data to cross-validate for real.

### Item 4: honest conclusion -- plateaued, and the real bottleneck is named

Items 1-3 all either regressed or didn't survive scrutiny. **This is
the real ceiling of what's achievable by modeling tricks on the
current 58-example set, not a gap to keep chasing with a fifth
architecture.** The actual bottleneck is the labeled data itself: 44 of
58 examples are `NO_COMPLAINT`, `FRONT_TURNIN_BRAKE` has 2,
`TYRE_GRIP_DEGRADATION` has 0. No amount of prototype engineering,
ensembling, or margin tuning can teach a model to recognize a category
it has zero or two real examples of. Gate 6a's 0.80 target very likely
needs a larger, more balanced labeled set before it needs another
modeling idea -- see `VALIDATION_GATES.md` gate 6 "things worth
trying" item 3 (more labeled data), still not attempted this session
for the same standing reason: it needs a human, not code.
