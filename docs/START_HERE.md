# ApexSignal — Start Here

*One document to actually understand the whole project: what it is, why it exists, and how it's built. Written 2026-08-15. If you only read one file in this repo, read this one.*

---

# Part 1 — The Product Pitch

## The problem, in plain English

An F1 car streams hundreds of numeric channels a second — speed, throttle, brake pressure, tyre temps, the works. Engineers on the pit wall stare at graphs all race long.

But the driver notices things the graphs haven't caught up to yet. "Rear's moving." "No front." "Same thing again." That's a human sensor reporting a problem *before* it's visible in the data — except it arrives as a fuzzy, emotional, six-word radio call, not a clean signal. Today, that radio call and the telemetry graph live in two completely separate worlds. Nobody systematically connects "what the driver just said" to "what the car is about to show."

That's the gap. **ApexSignal closes it.**

## The pitch

> **The car has telemetry. The driver has feel. ApexSignal connects the two — with memory and evidence.**

ApexSignal listens to team radio, works out *what* the driver is actually reporting (not just *how* they sound), lines that report up against the car's own telemetry, and checks its memory: has this exact car-and-driver combination shown this exact pattern before? If a driver calls in "rear's moving again," ApexSignal doesn't just transcribe it — it pulls up the last time this driver reported the same thing, shows whether the telemetry today looks like it did back then, and tells the engineer how much warning the driver's call gave before the car's performance actually changed.

It was built in ~5 days for **AI Race Month — GrandPrix Hackathon @ Paytm**, against **Problem Statement 1: "The Silent Co-Driver."** The official brief only asked for transcript + a calm/stressed/tired label next to a lap-time chart. ApexSignal ships that as the floor, then builds a genuinely differentiated product on top of it.

## What actually happens, end to end

1. **A radio call comes in.** ("Rear is moving again when I get back on throttle.")
2. **Speech becomes text.** An ASR model transcribes it.
3. **The voice is scored for tone.** Calm / elevated arousal / fatigued, with a confidence number — this is the hackathon's mandatory output.
4. **The complaint gets normalized.** Free-form driver language is mapped into one of five fixed categories (rear traction, front/braking, tyre degradation, visibility/track condition, or general mechanical) — never a made-up diagnosis, just "this is the kind of thing being reported."
5. **The car's own telemetry is checked against the driver's own recent baseline** at that exact circuit segment — not against "how the car should behave" in the abstract, but against how *this driver, this session* has been doing there.
6. **Memory kicks in.** ApexSignal searches past incidents for anything that sounds like this complaint *and* looks like this complaint in the telemetry. If it finds one, it surfaces it as evidence, with two separate similarity scores (does it sound alike, does it look alike) — never blended into one fake confidence number.
7. **Lead time gets measured**, when the data supports it: how many seconds passed between the driver's warning and the moment the telemetry first, measurably, got worse.
8. **Everything lands on one screen** — the Pit-Wall Incident Inspector — as a single incident card: transcript, tone, category, evidence, historical match, lead time, and a plain-English interpretation. No four disconnected feature tabs, no black-box risk score.

## The innovation, specifically

Four hackathon-brainstorm concepts (nicknamed ECHO LAP, RacePulse, FEEL2PHYSICS, and The Mask) got merged into one coherent product instead of shipping as four disconnected demos:

- **Memory** (ECHO LAP): incidents aren't judged in isolation — every new report is checked against everything reported before.
- **Meaning** (FEEL2PHYSICS): the driver's words get normalized into a fixed, defensible taxonomy instead of being reduced to a sentiment score.
- **Evidence** (RacePulse): instead of a single opaque "risk score," every claim is broken into inspectable, separately-labeled components — this is the part built to survive a skeptical judge asking "why?"
- **Voice honesty** (The Mask): an optional, feature-flagged check for when what the driver *says* and how they *sound* disagree — deliberately shipped off by default until real-clip testing proved it reliable (it wasn't yet — see Part 2).

## What ApexSignal deliberately does **not** claim

This is as important as what it does. The team was explicit about this from day one, and it shows real product maturity:

- **No lie detection.** No psychological diagnosis. No fatigue scoring presented as fact.
- **No confirmed mechanical fault.** It never says "differential failure confirmed" — only "reported phenomenon" and "behavior consistent with a complaint."
- **No autonomous strategy decisions.** This is a decision-support tool for a human engineer, not an agent making pit calls.
- **No grip-coefficient estimation.**
- **Similarity scores are never dressed up as probabilities.** "This sounds 88% like a past incident" is a model score about wording and telemetry shape — not an 88% chance the two share a mechanical cause. The UI is required to preserve that distinction everywhere.
- **It can't catch a recurrence before the driver reports it a second time.** The original design (a background process constantly watching telemetry independent of radio) was cut for scope; what shipped only compares telemetry *when a new radio event triggers the check*. It recognizes a recurrence faster once the driver calls it in again — it doesn't get there first. This is a real, documented scope cut, not marketing spin.

That restraint is a big part of what makes this feel like a real product idea rather than a hackathon toy dressed up in confident language.

## Who is this for?

The F1 pit wall — race engineers and strategists who are already flooded with numeric data and structurally can't also carefully listen to tone-of-voice on every radio call while doing their day job. ApexSignal is the layer that turns "the driver said something concerning" into "here's the specific historical precedent and the specific telemetry evidence for why it matters right now."

## Why this is genuinely different (say this part slowly)

The brief for PS1 ("The Silent Co-Driver") literally only asks for: transcript + a calm/stressed/tired label, next to a lap-time chart. That's a solvable weekend project with an off-the-shelf ASR model and an off-the-shelf emotion model. Most teams in the room will ship close to exactly that. Here's the honest comparison:

| What the brief asks for | What a typical team ships | What ApexSignal ships |
|---|---|---|
| Transcript | Whisper output, verbatim | Whisper output, verbatim (same floor) |
| Tone label | Emotion model → CALM/STRESSED/TIRED badge | Same, plus a *calibrated, validated* threshold (not the model's raw default) and a confidence number that's honest about audio quality |
| "Insight" | A dashboard tile that says the label out loud | A structured complaint category, memory of every past incident, telemetry cross-check against the driver's *own* baseline, a lead-time number, and a recurrence state — each one independently inspectable |
| Confidence | One number, usually not explained | Every number is decomposed: semantic similarity ≠ telemetry similarity ≠ tone confidence ≠ category confidence. Never blended into one score a judge can't interrogate |
| Failure handling | Rarely discussed | `INSUFFICIENT_DATA`, `NO_DEVIATION`, `None` lead time, and a documented, honest 0.393 macro-F1 classifier miss are all first-class, visible outcomes — not hidden |

The actual thesis is: **a single opaque "risk score" is a hackathon-demo crowd-pleaser and a production liability.** Anyone who has worked in a regulated, high-stakes decision environment — which is exactly the audience judging this — knows that a model producing a confident-looking number nobody can decompose is the thing that gets an incident-review committee to shut a system off. ApexSignal is built the other way: every number traces back to a specific, nameable piece of evidence, and the system says "I don't know" out loud (`INSUFFICIENT_DATA`, `None` lead time, no match) rather than manufacturing a fake positive to look impressive. That is a deliberate product-maturity choice, not a limitation to apologize for — and it's the single strongest thing to lead with if the room is full of people who evaluate risk systems for a living.

The other genuine differentiator: **memory.** Nearly every other team's system judges each radio call in isolation. ApexSignal is the only one (by design) that asks "has this exact car-and-driver shown this exact pattern before, and if so, how much warning did the driver give us last time?" That's the ECHO LAP idea, and it's what turns a transcription-plus-label tool into something that actually changes what an engineer does in the next 30 seconds.

## Honest state of the product (read this before demoing it to anyone)

This section exists because the project's own internal audit is unusually candid about it, and that honesty deserves to survive into this document too.

- **The public demo is a deterministic, contract-validated historical replay**, not a live AI system processing real audio in real time. Three curated incidents (`INC-114`, `INC-117`, `INC-145`) play from pre-computed fixture data — including one deliberate negative example (no match, no lead time) so the demo doesn't only show positive results.
- **The real AI backend exists in code and is genuinely substantial** (ASR, acoustic tone model, complaint classifier, semantic + telemetry retrieval, baseline/lead-time math) — but it is not what's running behind the public URL. It's been run and validated against real F1 radio clips on a GPU box, with real, published, currently-mediocre accuracy numbers (see Part 2's Validation Gates section).
- **The complaint classifier does not yet meet its own quality bar** (macro-F1 0.454 against a target of 0.80, as of the 2026-08-14 embedding-prototype backend — up from an earlier 0.393 on zero-shot NLI, then genuinely plateaued after three further tuning attempts all regressed). The team found and fixed a real bug where it was silently returning nothing for every input, then re-measured honestly and reported the number is still not good enough — rather than quietly hiding that. See Part 2 for the full history.
- **The reference audio clip is synthesized TTS, and that is now a closed, researched decision, not a placeholder.** Two independent legal-research passes (2026-08-15) concluded no real F1 team radio clip clears a defensible bar for public redistribution — F1's own content guidelines prohibit it, no team or dataset carries a real reuse license, and Indian fair-dealing exceptions don't survive public web deployment. Do not swap in a real broadcast clip for demo "authenticity" without an actual written license from Formula One Management.
- **This is a hackathon MVP with unusually good documentation of its own limitations**, which is worth more than it sounds — most hackathon projects don't have a `VALIDATION_GATES.md` with real pass/fail numbers instead of vibes.

---

# Part 2 — Technical Deep Dive

## Is this "using AI/ML"? Yes — here's exactly where

| Task | Model | Kind | Status |
|---|---|---|---|
| Speech-to-text | `distil-whisper/distil-large-v3.5-ct2` (via `faster-whisper`/CTranslate2), CPU fallback `Systran/faster-whisper-small.en` | Pretrained transformer ASR, pinned to a specific commit SHA | Validated on real F1 clips; WER 20.28% (target ≤20%, marginal fail) |
| Acoustic tone/arousal | `laion/voiceclap-commercial` encoder + attribute heads | Pretrained speech-emotion model | Validated; 85% agreement with human labels after recalibrating the decision threshold |
| Complaint classification | Production as of 2026-08-14: `sentence-transformers/all-MiniLM-L6-v2` embeddings + per-category prototype cosine similarity ("embedding" backend). Zero-shot NLI (`MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33`) kept as a `CLASSIFIER_BACKEND` fallback option, not the default. | Pretrained sentence embeddings, prototype similarity (no fine-tuning) | Validated; macro-F1 0.454 (target ≥0.80, real fail, but a genuine +6.1pp improvement over the prior NLI backend's 0.393 — see Validated ML Results below) |
| Semantic incident similarity | `sentence-transformers/all-MiniLM-L6-v2` | Pretrained sentence embeddings + cosine similarity | Working; threshold empirically measured over 247 hand-written phrase pairs |
| Telemetry similarity | No model — deterministic signal processing (resample by distance, z-score standardize, channel-wise cosine) | Classical, not ML | Working |
| Baseline deviation / lead time | No model — robust statistics (median + MAD-based thresholding) | Classical, not ML | Working |
| Recurrence detection | No model for the radio-repeat check — a literal, inspectable regex keyword list (deliberately not an ML classifier, so a judge can read the whole decision rule in ten seconds) | Rule-based | Working |

So: **yes, real Hugging Face models do real inference** (ASR, tone, zero-shot classification, sentence embeddings) — this isn't a "fake AI" hackathon submission. But the *product's actual intelligence* — what makes it useful rather than just a transcription tool — is mostly **classical statistics and explicit rules on top of those model outputs**, by deliberate design. The team's own reasoning (see `services/evidence_memory/`): a black-box similarity or risk score can't survive a judge asking "why," so every number is decomposed into something inspectable.

## Repository layout (who owns what)

```
apexsignal/
├── contracts/         Frozen JSON schemas + fixtures every workstream builds against
├── data_pipeline/      Dataset curation, FastF1 caching, replay asset generation
├── data/                Audio clips, radio-analysis outputs, telemetry, incident manifest
├── hf_dataset/          Hugging Face dataset artifact scaffold (not yet published)
├── services/
│   ├── radio_ai/        ASR + tone/arousal + complaint classification (stateless FastAPI)
│   ├── core_api/         Incident storage, evidence fusion, recurrence, lead-time (FastAPI)
│   └── evidence_memory/  Library: embeddings, retrieval, baseline math, telemetry fingerprints
├── storage/              SQLite schema for incident metadata
├── apps/web/             Pit-Wall Incident Inspector (Next.js 16 / React 18 / TypeScript / Tailwind)
├── mock_server/          Fixture-backed stand-in for core_api + radio_ai (FastAPI)
├── deployment/           Docker Compose + Hugging Face Space config
└── tests/                Cross-cutting integration tests
```

No service imports another service's code directly — everything talks through the JSON contracts frozen in `contracts/`. This was a deliberate structural choice for a 4-person hackathon team: each person owns a folder, integration happens through fixtures from day one, and nobody is ever blocked waiting on someone else's half-finished module.

## Full tech stack

| Layer | Choice |
|---|---|
| Backend services | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| Telemetry | FastF1, pandas, NumPy, SciPy |
| ASR | `distil-whisper/distil-large-v3.5-ct2` via `faster-whisper` (CTranslate2) |
| Acoustic tone | `laion/voiceclap-commercial` (VoiceCLAP encoder + attribute heads), via `transformers` + `torchaudio`/`torchcodec` |
| Complaint classification | `sentence-transformers/all-MiniLM-L6-v2` embedding + prototype cosine similarity (production, since 2026-08-14); zero-shot NLI DeBERTa kept as a fallback backend option |
| Semantic embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Retrieval | Brute-force cosine similarity over an in-memory list (not FAISS — see below) |
| Metadata store | SQLite (`storage/incidents.db`) |
| Frontend | Next.js 16 (Turbopack), React 18, TypeScript, Tailwind CSS |
| Deployment | Docker Compose locally; Vercel (frontend), Render (replay API), optional Hugging Face Space |

**Why not FAISS despite it being in the original plan?** The actual corpus is 15–25 incidents. FAISS earns its complexity around 10⁵ vectors — this is four orders of magnitude short. Brute-force cosine over a Python list is microseconds and has no index to build or keep in sync with SQLite. This is called out in the code as an intentional scope decision, not an unfinished integration.

## The two JSON contracts everything is built on

**`RadioAnalysisOutput`** — produced by `radio_ai`, consumed by `core_api`:

```jsonc
{
  "incident_id": "INC-017",
  "transcript": "Rear is moving again on throttle.",
  "tone_label": "ELEVATED_AROUSAL",     // CALM | ELEVATED_AROUSAL | FATIGUED — mandatory PS1 output
  "tone_score": 0.73,
  "tone_confidence": 0.61,
  "complaint_category": "EXIT_TRACTION_REAR",  // or null if not a complaint
  "category_confidence": 0.86,
  "text_tone_disagreement": "MODERATE"  // optional, omitted entirely if The Mask is disabled
}
```

The 5-category taxonomy is frozen: `EXIT_TRACTION_REAR`, `FRONT_TURNIN_BRAKE`, `TYRE_GRIP_DEGRADATION`, `VISIBILITY_TRACK_CONDITION`, `MECHANICAL_OTHER` (fallback, used sparingly).

Interesting integration detail: `core_api` doesn't call `radio_ai` over HTTP for this. `radio_ai` writes one JSON file per incident to `data/radio_analysis/{incident_id}.json`, and `core_api` reads it straight off disk. This means `core_api`'s own test suite and evaluation can run completely standalone, with zero other services alive — a small but genuinely good decoupling decision for a team building four services in parallel.

**`IncidentAssessment`** — produced by `core_api`, consumed by the frontend:

```jsonc
{
  "incident_id": "INC-031",
  "lap": 31,
  "segment": "T7_EXIT",
  "reported_phenomenon": "EXIT_TRACTION_REAR",
  "baseline_evidence": {
    "throttle_pickup_delta_pct": -11.0,
    "sector_delta_s": 0.18,
    "status": "BEHAVIOR_CONSISTENT"     // | NO_DEVIATION | INSUFFICIENT_DATA
  },
  "echo_match": {                       // or null if nothing cleared the retrieval bar
    "incident_id": "INC-017",
    "semantic_similarity": 0.88,
    "telemetry_similarity": 0.81,
    "same_segment": true,
    "label": "STRONG_PROTOTYPE_MATCH"
  },
  "driver_warning_lead_time_s": 42,     // or null, explicitly, if no measurable lead time
  "recurrence_state": "POSSIBLE_RECURRENCE",  // | NONE | CONFIRMED_BY_RADIO
  "human_message": "Behavior is consistent with a previously reported concern; review recommended."
}
```

## How the evidence engine actually works (the real IP here)

This is the part of the codebase worth reading directly if you want to understand what's genuinely thoughtful about this project. It lives in `services/evidence_memory/`.

**Own-baseline comparison** (`baseline.py`) — never compares a driver to another driver or to a model of "correct" driving. It compares the driver's current lap at a segment to their own median over their last 5 laps at that same segment. A deviation only counts if it clears a threshold derived from the *driver's own consistency* (median absolute deviation, scaled to a robust standard deviation, floored at 0.05s) — so a naturally scrappy driver doesn't get flagged for being themselves, and a naturally metronomic driver doesn't get false-positived by rounding noise. Needs 3+ clean baseline laps or it honestly reports `INSUFFICIENT_DATA` instead of guessing.

**Lead time** (`lead_time.py`) — `first_observable_performance_change_time − radio_event_time`. A single slow lap is never enough (could be traffic, a yellow-flag lift, one scrappy lap) — the deviation must persist for 2 consecutive laps. If nothing qualifies, the result is `None`, explicitly, with a plain-English reason — never forced into a fake positive number just to make the demo look better.

**Retrieval gate** (`retrieval.py`) — this one has a real measured finding behind it: the team ran MiniLM cosine similarity over 247 hand-written F1-radio phrase pairs and found that semantic similarity *alone* cannot reliably separate "the same complaint repeated" from "a different complaint that happens to use similar words" — a cross-category pair scored *higher* than a genuine same-category repeat. So the actual gate is two independent conditions that must both hold: (1) the driver's classifier-assigned category matches, and (2) cosine similarity clears an empirically-set threshold (0.40). Telemetry similarity is deliberately *not* part of the gate — a driver repeating a complaint while the car looks different is treated as a real, interesting case worth surfacing, not something to filter out.

**Recurrence state machine** (`recurrence.py`) — three states, each requiring specific, named evidence:
- `CONFIRMED_BY_RADIO`: the driver's own words say "again"/"still"/"same thing" (via a plain regex list you can read end-to-end in ten seconds, deliberately not a model) **and** a prior incident of the same category is on record.
- `POSSIBLE_RECURRENCE`: a same-segment prior incident was retrieved, its telemetry window is comparable (fingerprint similarity ≥ 0.90 — this is a *comparability* check, "are we looking at the same corner," not a severity score), and the car is currently deviating from the driver's own baseline.
- `NONE`: everything else, with a specific stated reason logged either way.

Also worth noting: telemetry fingerprint similarity was measured to separate *corners* well (0.99 same corner vs. 0.73 different corner) but barely separates a clean lap from a deteriorated lap at the *same* corner (0.008 apart) — so it's explicitly used only as a "are we comparing the right stretch of track" gate, never as evidence of severity. That distinction is deliberate and documented, not incidental.

## Database

SQLite, created at runtime by `core_api` (`storage/schema.sql`):

```sql
CREATE TABLE incidents (
    incident_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    driver TEXT NOT NULL,
    event_time_ms INTEGER NOT NULL,
    lap INTEGER NOT NULL,
    segment TEXT NOT NULL,
    transcript TEXT NOT NULL,
    complaint_category TEXT NOT NULL,
    telemetry_window_path TEXT NOT NULL,
    embedding_index INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE recurrence_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggering_incident_id TEXT NOT NULL,
    matched_incident_id TEXT NOT NULL,
    telemetry_similarity REAL NOT NULL,
    flagged_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_state TEXT NOT NULL DEFAULT 'PENDING',
    FOREIGN KEY (matched_incident_id) REFERENCES incidents (incident_id)
);
```

Embeddings themselves live in an in-memory vector list at process runtime, not in SQLite — the DB holds metadata and an `embedding_index` pointer.

## API surface

| Service | Endpoint | Method | Returns |
|---|---|---|---|
| `radio_ai` | `/health` | GET | `{"status": "ok"}` |
| `radio_ai` | `/v1/radio/analyze` | POST | `RadioAnalysisOutput` |
| `core_api` | `/health` | GET | service status + `evaluate_mode` |
| `core_api` | `/v1/incidents/evaluate` | POST | `IncidentAssessment` |
| `core_api` | `/v1/incidents/{id}` | GET | `IncidentAssessment` |
| `core_api` | `/v1/replay/frame` | GET `?index=N` | next replay frame (radio + telemetry) |
| `core_api` | `/v1/replay/manifest` | GET | full session manifest in one call |
| `mock_server` | same paths as above | — | fixture data verbatim (contract-validated) |

## The frontend: Pit-Wall Incident Inspector

Single-page Next.js app (`apps/web`). Notable pieces:
- **`RaceReplayBackground`** — an animated, data-driven race replay (21 bundled historical races, circuit geometry sourced from `TUMFTM/racetrack-database`) running behind the UI as ambient visual, not decoration pulled from a stock asset.
- **`SessionGrid` / `LiveInspector` / `EvidenceStory`** — the incident timeline, the live single-incident card, and a narrative walkthrough of the evidence chain.
- **Pit-Wall mode toggle** — a before/after comparison view.
- **Resilient by design**: every remote call has an embedded fixture fallback baked into the client, so the UI stays interactive even if the backend (Render free tier) is cold-starting or briefly down. The page reports its data-source mode (`API replay` vs `local replay`) so this fallback is disclosed, not hidden.

## Validated ML results (real numbers, run against real F1 radio clips)

From `services/radio_ai/VALIDATION_GATES.md`, dated 2026-08-14, GPU box run (RTX 5090):

| Gate | Target | Result | Verdict |
|---|---|---|---|
| ASR normalized WER | ≤20% | 20.28% | Fail (marginal) |
| ASR meaning-critical word accuracy | ≥90% | 84.21% | Fail |
| Tone: agreement with human labels (CALM/ELEVATED) | ≥75% | 85% (n=20) | Pass |
| Tone: Spearman correlation vs. human 1–5 arousal rating | ≥0.50 | 0.69 | Pass |
| Fatigue false-positive rate | as close to 0 as achievable | 0/20 (but zero true fatigued clips in sample — unvalidated for true positives) | Pass, unproven |
| Tone stability under audio degradation | median drift ≤0.15 | 0.017 | Pass |
| Complaint classifier macro-F1 (production, embedding backend, as of 2026-08-14) | ≥0.80 | 0.454 | **Fail, real gap, but a genuine +6.1pp improvement over the prior 0.393 (xsmall NLI) backend** |
| Complaint classifier NO_COMPLAINT F1 (embedding backend) | ≥0.85 | 0.805 | Fail (was 0.780 on the prior backend) |

Three things worth calling out because they reflect well on the engineering discipline here, not just the numbers:

1. **A real bug was found and fixed mid-project**: the classifier was matching model output against the wrong dictionary keys and silently returning `None` for *every single input, at every threshold* — meaning every `complaint_category` in the committed data was a bug artifact, not a model judgment. It was found, fixed, and every affected gate was honestly re-run and re-reported — including the fact that the corrected number (macro-F1 0.393) was still well below target.
2. **The classifier backend was then swapped and the swap is honestly characterized as mixed, not a clean win.** On 2026-08-14 the team replaced zero-shot NLI with an embedding-prototype classifier (sentence-transformer cosine similarity against per-category prototype text), raising macro-F1 from 0.393 to 0.454 — a real, re-verified improvement. But the Gate 7 holdout re-run on the new backend changed 6 of 20 predictions: 2 genuine fixes, 1 genuine category-correctness improvement, but 2–3 genuine *misses* the old backend used to catch. Three further tuning attempts after that (richer prototypes, an NLI+embedding ensemble, margin sensitivity sweeps) all *regressed* performance — a real, measured plateau, not an abandoned effort. The team's own conclusion: the bottleneck is now the labeled dataset itself (58 examples, 44 of them `NO_COMPLAINT`, zero `TYRE_GRIP_DEGRADATION`), not the modeling approach — more labeled data is the next lever, and that explicitly needs a human, not more code.
3. **The Mask (text-tone disagreement) numerically passed its go/no-go gates but still didn't ship** — because the actual comparison logic was never implemented, and the team caught that distinction (passing calibration ≠ having working code) before flipping the feature flag on. It currently raises `NotImplementedError` if force-enabled.

## What's real vs. what's demo-fixture right now

| Claim | Reality |
|---|---|
| Public Vercel + Render demo | Live, real, and serves genuine contract-validated fixture data — 3 curated incidents, deterministically replayed |
| "AI processes live audio on the public site" | **No.** The public backend runs in fixture/replay mode, not live inference |
| Real ASR/tone/classifier pipeline | Exists, runs, and has been validated against real audio on a GPU box — but is not deployed publicly (GPU-hosting cost/complexity, and classifier quality isn't there yet) |
| Full incident corpus (15–25 target) | Not yet built — only 3 demo incidents are fully curated end-to-end; a larger raw radio-analysis batch exists but is disconnected from a complete manifest |
| Hugging Face Space | A static build exists with embedded fixture data (no live backend call) |
| FAISS-scale retrieval | Not needed yet — see the brute-force cosine explanation above |

If you're demoing this to someone, the accurate framing is: **"a fully designed, partially-real AI pipeline behind a genuine, working, evidence-driven product experience, currently presented through a deterministic reference replay."** That's a legitimately strong hackathon submission — just don't call the public demo "live AI."

---

# Part 3 — Run It Locally

Verified working on this machine (Windows, Python 3.12.10, Node v24.14.1) right now — both services below are actually running as of this session.

## Fastest path — one screen, zero ML dependencies (recommended)

This runs the **entire real UI** — replay timeline, radio pins, tone/complaint classification, baseline evidence, the lead-time card, the Pit-Wall toggle — against real contract-validated fixture data. No GPU, no model downloads, no other service required.

**Terminal 1 — mock_server (serves fixture data on :8000):**
```powershell
cd mock_server
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

**Terminal 2 — web app (:3000):**
```powershell
cd apps/web
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Then open **http://localhost:3000**.

*(I just ran exactly this on your machine — `curl http://localhost:8000/health` returned `{"status":"ok","evaluate_mode":"replay",...}` and the web app returned HTTP 200 at `localhost:3000` in about 7 seconds. Both are currently still running in the background from this session.)*

## Full stack — real `core_api` (fixture-evaluated, no GPU needed)

Adds the actual evidence-engine service (not just static fixture files) — still `EVALUATE_MODE=fixture` by default, so no telemetry/ML corpus is required, but this exercises the real Python evidence pipeline.

```powershell
# Terminal 1
cd services/core_api
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8001

# Terminal 2
cd mock_server
pip install -r requirements.txt
uvicorn server:app --reload --port 8000

# Terminal 3
cd apps/web
npm install
npm run dev
# then set NEXT_PUBLIC_CORE_API_BASE_URL=http://localhost:8001 in apps/web/.env.local
```

162 backend tests pass against this (5 more require `sentence-transformers` and skip cleanly without it).

## Docker Compose (all fixture services, one command)

```powershell
docker compose -f deployment/docker-compose.yml up --build
```

Brings up `mock_server` (:8000), `core_api` (:8001, fixture mode), and `web` (:3000). The real `services/radio_ai` (Whisper + tone + classifier, GPU-oriented) is opt-in:

```powershell
docker compose -f deployment/docker-compose.yml --profile live up --build
```

## Running the real ML pipeline (radio_ai) — heavier, needs a real GPU

Only relevant if you want to reproduce the actual model inference, not just consume its output. Needs `torch`, `torchaudio`, `torchcodec`, `transformers`, `faster-whisper`, plus a Hugging Face token in `services/radio_ai/.env` — see `services/radio_ai/README.md` and `VALIDATION_GATES.md` for the full setup and the "getting sample clips" instructions. This is GPU-oriented and not required for the UI/demo path above.

## Verification

```powershell
python scripts/run_test_suites.py
cd apps/web
npm run build
```

## To stop the servers I started this session

They're running in background shells; close the terminal windows, or `Ctrl+C` in each, or kill the `uvicorn`/`node` processes for ports 8000 and 3000.

---

---

# Part 4 — Presentation & Demo Prep

*This is the part to actually rehearse. Everything above is reference material; this is the checklist.*

## A. Defending this in the room

Paytm is a fintech company judging an AI hackathon — expect the panel to include people who evaluate risk/decision systems for a living, not just ML folks. That audience grills on **rigor and honesty**, not on whether the demo looks slick. Lean into that; it's this project's actual strength. Rehearse these out loud, don't just read them.

**"Is this real AI, or just a Whisper wrapper with a sentiment badge?"**
Both, honestly, and say so: yes, real pretrained models do real inference (ASR, VoiceCLAP acoustic tone, zero-shot DeBERTa classification, MiniLM embeddings — see Part 2's model table). But the *product's actual intelligence* — own-driver baselines, lead-time math, the two-gate recurrence check — is deliberately classical statistics and inspectable rules on top of those model outputs, not another model. That's not a cop-out; it's the point: a black-box score can't survive "why," and this system is built so every number can be traced to a named piece of evidence.

**"Your complaint classifier fails its own bar — macro-F1 0.454 against a target of 0.80. Why should we trust anything downstream of it?"**
Don't dodge this one — it's the strongest card in the deck if played straight, and it's gotten even stronger to tell since it was last rehearsed. Say: we found and fixed a real bug where it was silently returning nothing for every input (0.393 corrected baseline), then swapped the whole classifier architecture to an embedding-prototype approach and re-measured honestly at 0.454 — a real +6.1pp gain. Then we tried three more tuning ideas and all three made it *worse*, so we stopped and reported the plateau instead of chasing a fifth idea to look busy. That's a team that knows exactly where its weak link is, has the number, and knows the actual fix (more labeled data, not more modeling tricks) rather than guessing. Then pivot: the rest of the pipeline (tone at 85% agreement, retrieval, baseline math) doesn't depend on the classifier being right to be individually inspectable and correct.

**"The public demo isn't live AI — isn't that just smoke and mirrors?"**
No — say exactly what it is: a deterministic, contract-validated replay of real pipeline output, including one deliberate negative example so it isn't cherry-picked to only show hits. The real pipeline exists, runs, and has been validated on a GPU box against real F1 audio (cite WER 20.28%, tone 85% agreement) — it's just not deployed publicly, for GPU-hosting cost and because the classifier isn't good enough yet to put in front of a judge live. That's an infra/cost tradeoff, not a fabrication.

**"Why zero-shot instead of fine-tuning the classifier?"**
There is no labeled F1-radio complaint dataset. Fine-tuning would need one, and fabricating labels to hit a hackathon deadline would be the actual sin here, not shipping a mediocre zero-shot number honestly. Zero-shot NLI also means the taxonomy definitions *are* the classifier input — change the taxonomy wording, the classifier changes with zero retraining. That's a real engineering tradeoff, not a shortcut.

**"How do you know your thresholds (arousal 2.565, retrieval 0.40) aren't just overfit to a tiny sample?"**
They're not claimed to be final — n=20 for tone, n=247 phrase pairs for retrieval, and the code/docs say explicitly "revisit as more labeled data accumulates." The point being defended isn't "these thresholds are correct forever," it's "every threshold in this system was empirically measured against real data and is documented with its sample size, not hand-picked to make the demo look good."

**"What's the business case — who pays for this?"**
F1 teams already pay for trackside sensors, one-off telemetry consultants, and strategist headcount specifically to catch exactly this kind of signal. This is a much cheaper add-on to infrastructure they already run, sitting on top of the radio feed and telemetry they already capture — not a new hardware sale.

**"What would you build next with more time?"**
In order: (1) get the classifier to a usable macro-F1 with a bigger labeled set, (2) build the full 15–25 incident corpus instead of 3, (3) the background-watcher mode that was cut for scope — comparing telemetry continuously instead of only when a new radio call triggers it, which is what would let it catch a recurrence *before* the driver calls it in a second time.

## B. Demo punch list — what to test, build, and show

**1. Rehearse the fixture-replay walkthrough itself, on the real deployed URLs, not just localhost.** Open the actual Vercel site cold, and time the Render free-tier cold start — know how many seconds of silence to expect and have a sentence ready to fill it ("the backend's a free-tier box, waking up now — while it does, here's the part that matters...") instead of standing there awkwardly.

**2. Have one full local screen-recording of the entire demo succeeding, end to end, as an offline backup.** Conference wifi failing mid-demo is the single most common way a good hackathon project looks bad — a pre-recorded fallback removes that risk entirely.

**3. Rehearse the "what this deliberately does not claim" section fluently.** It's the most sophisticated point in the pitch and the easiest to fumble if you're paraphrasing live. Practice saying "no lie detection, no confirmed mechanical fault, no autonomous decisions" as one smooth breath, not something you're reconstructing on the spot.

**4. Walk through all three demo incidents and know *why* each one was chosen** — INC-114/117 are a genuine recurrence pair (same driver, same corner, "same thing again" language), INC-145 is the deliberate negative example. Judges will ask "show me one where it *didn't* find a match" — have that ready, don't scramble to find it live.

## C. The calm-vs-urgent voice question — done, built into the live UI, 2026-08-15

**This is now shipped, not speculative.** `apps/web/src/components/ToneComparison.tsx`, wired into the Architecture section (`PipelineSection.tsx`, right under the taxonomy box, id `#pipeline`) — visible in the normal page scroll, no separate slide needed.

**What it actually is:** two short synthesized clips (Edge TTS, `en-GB-RyanNeural`, same engine as the existing reference clip — see `THIRD_PARTY_NOTICES.md`), differing only in delivery (rate/pitch/volume), run through the real production tone-scoring code (`services/radio_ai/app/tone.py`, unmodified) **on this laptop, on CPU, with no GPU box needed** — that assumption from the first draft of this section turned out to be wrong; `torchaudio`/`torchcodec` needed system ffmpeg (not installed), but decoding via `soundfile` + `scipy` resampling sidesteps that entirely, and VoiceCLAP itself loads and runs fine on CPU for a 3-second clip. Reproduce with `python services/radio_ai/tone_test/run_tone_test.py`.

**The real, measured numbers** (not fabricated, not tuned to hit a target):

| | Calm clip | "Urgent" clip |
|---|---|---|
| Transcript | "Box this lap, tyres are fine." | "Rear is moving, rear is moving, get me in now!" |
| Arousal (raw) | 0.531 | 1.827 |
| tone_label | CALM | CALM |
| tone_score / confidence | 0.884 | 0.676 |

**Neither crosses `AROUSAL_ELEVATED_THRESHOLD` (2.565).** This was a real decision point, not an oversight: after two honest attempts at pushing the TTS delivery further (rate/pitch/volume, the only levers the free Edge TTS endpoint exposes — no SSML "shouting"/"angry" styles available), the second, more extreme attempt actually scored *lower* Arousal (1.107) than the first. Rather than keep tuning until something crossed the line — which is exactly the "force a fake positive to make the demo look better" move this project explicitly refuses to do everywhere else (see Part 1) — the honest result was shipped instead. It's arguably the stronger point to make to a judge anyway: a **3.4× real shift in the raw score** (0.531 → 1.827) and confidence in "calm" dropping from 88% to 68% is genuine, reproducible sensitivity to delivery — and the fact that a louder, faster synthesized voice *doesn't* fool the model into a false `ELEVATED_AROUSAL` call is evidence the threshold (calibrated on 20 real human-labeled F1 clips, not on TTS) is doing its job, not being naive about volume/pitch as a proxy for real distress.

**One line to have ready if a judge asks "so can it tell an angry driver from a calm one, live, right now?":** *"Scroll down — that's not a mockup, it's real output from our production tone model, computed on this laptop. Neither clip crosses our elevated-arousal threshold, because that threshold is calibrated on real human panic, not on a synthesized voice — but look at the raw number: it moved 3.4× just from changing delivery. That's the model doing real, measured work, and refusing to be fooled by a crude loudness proxy. We could have kept tuning the TTS until something flipped to ELEVATED_AROUSAL and looked more impressive — we didn't, on purpose, for the same reason nothing else in this system reports a fake positive."*

**Still true, unchanged:** the public Vercel/Render demo still only replays pre-computed fixture JSON — this local tone-model result isn't wired into the deployed backend, it's a static, pre-computed pair of clips + numbers on the page, same spirit as the rest of the fixture-driven demo (see Part 1/2, "What's real vs. what's demo-fixture"). And the three curated incident-replay demos (`INC-114/117/145`) are still all `ELEVATED_AROUSAL` with no `CALM` example among them — this tone-comparison block is a separate, standalone piece of evidence sitting in the architecture section, not a fourth incident in the replay timeline.

---

*This document was generated by reading the full source tree, all four workstreams' code, the frozen contracts, the validation gates, and the project's own internal audit — and then actually installing and running the fastest local path to confirm the commands above work as written.*
