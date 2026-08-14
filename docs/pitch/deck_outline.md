# ApexSignal — pitch deck outline

Twelve slides, built for a hackathon judging round (~3-5 minutes of
talking over the deck, plus the live demo separately). Each slide has
a one-line purpose, what goes on it, and speaker notes. Screenshots
referenced here must come from the actual deployed app — see
`docs/submission/checklist.md` for where to capture them.

---

## 1. Title

**Purpose:** identify the team and the one-line pitch fast.

- ApexSignal — The Silent Co-Driver
- Team name, all four members, workstream tags (A/B/C/D)
- One line: "Evidence-driven incident memory for the F1 pit wall"
- AI Race Month — GrandPrix Hackathon @ Paytm, Problem Statement 1

**Speaker notes:** Say the team name and the one-liner, nothing else.
Move fast, the hook is on slide 2.

## 2. The problem

**Purpose:** make the gap between driver feel and telemetry concrete.

- One real quote-style line: "Rear's moving." — subjective, arrives
  over radio, gets logged and moved on.
- Telemetry is dense and numeric. Radio is short and subjective.
  Nobody connects the two systematically.
- The cost: a driver can sense a problem laps before it shows up as a
  measurable lap-time change, and today that early warning is wasted.

**Speaker notes:** Keep this to 20 seconds. The problem is intuitive to
anyone who's watched a race; don't over-explain it.

## 3. The insight

**Purpose:** state the actual mechanism in one sentence before showing
architecture.

- "When a driver reports the same thing twice, that's a real signal —
  check whether the telemetry between those two reports actually
  changed."
- This is deliberately narrower than "predict problems before they
  happen." ApexSignal recognizes a recurrence faster once reported; it
  does not watch telemetry in the background waiting for one.

**Speaker notes:** This slide exists to pre-empt the "why didn't you
build a predictive monitor" question before a judge asks it.

## 4. Architecture

**Purpose:** show the three-stage pipeline without a slide full of
boxes-and-arrows nobody reads live.

```
Radio in  →  Radio Capture & Perception  →  Evidence Fusion  →  Incident Card
             (ASR + tone + taxonomy)        (baseline + retrieval)
```

- Radio Capture & Perception: Whisper ASR transcript + acoustic
  tone/arousal score + fixed 5-category complaint taxonomy.
- Evidence Fusion: own-baseline comparison (is this driver's telemetry
  different from their own recent laps at this segment) + historical
  retrieval (semantic + telemetry similarity to prior incidents).
- Incident Card: one screen, interpretation-safe wording, explicit null
  states instead of a forced answer.

**Speaker notes:** Emphasize "own baseline," not "population average" —
that's the detail that separates this from a generic anomaly detector.

## 5. Live demo (screenshot)

**Purpose:** anchor to the actual deployed product, not a mockup.

- Full-page screenshot of the live Pit-Wall Incident Inspector, Lap 17
  selected, showing the Gold Incident recurrence card.
- URL visible in the screenshot or captioned underneath:
  apex-signal-sigma.vercel.app

**Speaker notes:** "This isn't a mockup — that's the live public URL,
you can open it right now." Then actually switch to the live demo for
the interactive part of the walkthrough (see `demo_script.md`).

## 6. The evidence, not a verdict

**Purpose:** show the actual fields on the Incident Card and why they
matter individually.

- Baseline evidence: throttle-pickup delta, sector-time delta,
  `BEHAVIOR_CONSISTENT` / `NO_DEVIATION` / `INSUFFICIENT_DATA` — never
  collapsed into one score.
- Historical match: semantic similarity and telemetry similarity kept
  as two separate numbers, labeled `STRONG_PROTOTYPE_MATCH`, not
  "91% probability of the same fault."
- Lead time: measured seconds from this radio call to a later
  telemetry change that clears the driver's own noise floor, or an
  explicit "No measurable lead-time established" instead of a guess.

**Speaker notes:** This is the credibility slide. Read one honest null
state out loud — it lands better live than described.

## 7. What ApexSignal refuses to claim

**Purpose:** pre-empt the "so it detects lying/predicts failures"
question directly, before it's asked.

- No lie detection — tone is a labeled acoustic model score, not a
  deception signal.
- No diagnosis — "reported phenomenon," never "confirmed mechanical
  fault."
- No composite risk score — every component stays visible and
  separate.
- No recurrence prediction — recurrence is flagged reactively, after a
  second radio report, not by a standing background monitor.

**Speaker notes:** Say this plainly and move on fast. Judges read
restraint as rigor, not as a weaker product.

## 8. Validated, not asserted

**Purpose:** show the numeric gates exist and some genuinely failed —
because an audit trail with failures in it is more credible than one
that only reports wins.

- ASR: normalized WER 20.28% (target ≤20%, marginal miss), 84.21%
  meaning-critical word accuracy (front/rear/tyres/etc.)
- Acoustic tone: 85% agreement with human-labeled clear cases after
  real threshold calibration (not a guessed default)
- Complaint classifier: macro-F1 0.393 on the corrected benchmark
  (target 0.80 — the honest gap, not hidden)
- A real code bug was found and fixed mid-validation (a classifier
  key-mismatch that silently zeroed out every prediction) — the fix
  and the corrected numbers are both in the repo's own validation log

**Speaker notes:** Don't round the classifier number up. The gap is the
credibility. Say "we know exactly where this doesn't work yet and by
how much" — that's a stronger claim than pretending it's solved.

## 9. Tech stack

**Purpose:** one slide, dense, for the technical judges.

| Layer | Choice |
|---|---|
| ASR | `distil-whisper/distil-large-v3.5-ct2` (faster-whisper/CTranslate2) |
| Acoustic tone | VoiceCLAP encoder + attribute heads |
| Complaint classifier | DeBERTa-v3 zero-shot NLI (xsmall in production) |
| Telemetry / retrieval | FastF1, own-baseline deviation, semantic + telemetry similarity |
| Backend | Python 3.11, FastAPI, Pydantic, SQLite |
| Frontend | Next.js 16, React, TypeScript, Tailwind |
| Deployment | Vercel (frontend), Render (replay API), Hugging Face Space (offline-safe backup) |

**Speaker notes:** Don't read the whole table out loud. Point at ASR
and classifier rows only if asked what's underneath the demo.

## 10. What's shipped vs. what's roadmap

**Purpose:** the single most important slide for avoiding an
overclaiming challenge from a judge.

- **Shipped and tested:** full contract-validated pipeline (209
  backend tests), the public replay demo, circuit atlas (25
  source-derived centerlines, 21 full historical race recaps built
  from real lap-by-lap timing), CI, the model stack benchmarked
  end-to-end on real audio.
- **Not yet shipped:** a real curated incident (the 3 demo incidents
  are contract-validated reference fixtures, not a live-processed real
  case), classifier accuracy above 0.393, a persistent production
  deployment of the real (non-fixture) backend.

**Speaker notes:** Say this without apologizing for it. A four-person
team building a working, honestly-scoped MVP with numeric validation
in five days is the actual achievement — frame it that way, not as a
list of shortcomings.

## 11. Why this team

**Purpose:** close the credibility loop — this wasn't luck, it's how
the team works.

- One example of a caught-and-fixed bug (the classifier key-mismatch)
  as proof the validation process actually functions, not just exists
  on paper.
- Four independent workstreams, one frozen contract layer — the
  product came together because ownership boundaries were enforced,
  not improvised at the end.

**Speaker notes:** Keep this to 15 seconds. It's a trust-builder, not a
resume slide.

## 12. Team + links

**Purpose:** closing slide, always on screen during Q&A.

- Four names, workstream tags
- Live site: apex-signal-sigma.vercel.app
- Source: github.com/Deltasthicc/ApexSignal
- Hugging Face Space: huggingface.co/spaces/Deltasthic/ApexSignal

**Speaker notes:** Leave this slide up for the entire Q&A. Judges
should be able to type the URL while asking questions.

---

## Design constraints

- Dark background, red accent (`#e10600`), monospace type — match the
  deployed app's own visual language so the deck and the live demo
  don't feel like two different products.
- Every number on every slide must trace to a file in this repo
  (`VALIDATION_GATES.md`, `GATE6_ERROR_ANALYSIS.md`, or a live
  screenshot). If a number can't be pointed to, cut the slide, don't
  round it into plausibility.
- No slide should take longer than 20 seconds to talk through. If a
  slide needs more, it's two slides.
