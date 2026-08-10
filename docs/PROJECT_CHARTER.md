# ApexSignal — Project Charter

**Subtitle:** Driver Feedback Memory & Early-Warning Intelligence for the Pit Wall  
**Hackathon:** AI Race Month — GrandPrix Hackathon @ Paytm  
**Official Anchor:** Problem Statement 1 — The Silent Co-Driver  
**Team Size:** 4 developers  
**Project Status:** Final build charter / scope lock

> **Tagline:** The car has telemetry. The driver has feel. ApexSignal connects the two — with memory and evidence.

## 1. Executive Summary

**ApexSignal** is an AI-assisted Formula 1 pit-wall decision-support system that transforms each driver radio message into a structured, evidence-backed incident record. It combines the strongest ideas from four prior concepts — **ECHO LAP**, **RacePulse**, **FEEL2PHYSICS**, and **The Mask** — but presents them as one coherent product rather than four separate features.

The system transcribes radio audio, estimates acoustic tone/arousal, interprets ambiguous driver language into a small operational complaint taxonomy, aligns the report with telemetry and lap context, retrieves similar historical incidents, and monitors later telemetry for patterns that resemble earlier driver-reported concerns. It reports **measured lead time**, **behavior consistent with a complaint**, **probable recurrence**, and **text–tone disagreement**. It does **not** claim lie detection, psychological diagnosis, confirmed mechanical faults, exact grip estimation, or autonomous race strategy.

The central thesis is simple:

> **The driver is an additional sensor. The value is not merely in hearing the radio; it is in giving subjective driver feedback structured meaning, memory, and measurable telemetry context.**

## 2. Final Problem Statement

Formula 1 teams have dense telemetry, but the driver can often perceive a change in handling, grip, braking, tyre behavior, visibility, or vehicle response before that concern is obvious in a lap-time graph. The problem is that driver feedback arrives as short, subjective and context-dependent radio language — “rear’s moving,” “can’t lean on it,” “no front,” “same thing again” — while telemetry arrives as numerical streams.

Conventional radio analysis usually treats each message in isolation: transcribe it, attach an emotion/tone label, and place it beside lap time. That leaves four important questions unanswered:

1. **What operational problem is the driver actually describing?**
2. **What observable telemetry evidence is consistent with that report?**
3. **Has a semantically and behaviorally similar incident happened before?**
4. **Did the driver provide useful warning before an observable performance change, or is a previously reported pattern beginning to recur?**

**ApexSignal solves this gap by turning driver radio into structured incident memory connected to telemetry evidence.** It is a human-in-the-loop decision-support system: it surfaces evidence and uncertainty for the pit wall; it does not output mechanical diagnoses or autonomous strategy decisions.

### Submission-ready one-paragraph problem statement

> **ApexSignal is a Silent Co-Driver system that gives subjective driver radio feedback structured meaning, memory, and measurable telemetry evidence. Team radio is transcribed and scored for acoustic tone/arousal, then driver language is normalized into a small set of operational complaint categories. Each incident is connected to its lap, circuit segment, telemetry window and performance context, stored as searchable memory, and compared with later events. ApexSignal can retrieve probable historical matches, quantify how much warning a radio complaint provided before an observable performance change, and flag when current behavior resembles a previously reported incident. Every output is presented as evidence, similarity, or measured lead time — never as a confirmed mechanical diagnosis or hidden psychological state.**

## 3. Strategic Relevance

ApexSignal directly satisfies **Problem Statement 1 — The Silent Co-Driver** because the product accepts driver radio, performs speech-to-text, produces a tone/arousal signal, and correlates the event with lap/telemetry performance. It extends the baseline in a disciplined way: the mandatory tone label is an input, not the headline innovation.

The project is differentiated from a generic “AI race engineer” or sentiment dashboard in four ways:

- **Meaning:** FEEL2PHYSICS converts subjective driver language into structured operational complaint categories.
- **Memory:** ECHO LAP retrieves similar prior incidents using semantic and telemetry context.
- **Evidence:** RacePulse’s core idea becomes the **Evidence & Lead-Time Engine**, which measures observable support and warning lead time instead of inventing a black-box “risk score.”
- **Voice context:** The Mask becomes a cautious **Voice–Content Consistency** signal that identifies text–tone disagreement without calling it lie detection.

## 4. Source Concept Mapping

The project is one product. The four source concepts are internal design lineage, not separate tabs or separate products.

| Placeholder | Source concept | Final professional capability |
|---|---|---|
| **[PROJECT_1_NAME]** | ECHO LAP | Incident Memory & Recurrence Retrieval |
| **[PROJECT_2_NAME]** | RacePulse | Evidence & Lead-Time Engine |
| **[PROJECT_3_NAME]** | FEEL2PHYSICS | Driver Feedback Normalizer |
| **[PROJECT_4_NAME]** | The Mask | Voice–Content Consistency |

**User-facing product name:** **ApexSignal**. Do not use “RacePulse” as both the product name and an internal layer.

## 5. Scope: What Ships and What Does Not

### Must ship

- Radio audio ingestion and Hugging Face ASR.
- Mandatory acoustic tone/arousal output with confidence/uncertainty.
- A fixed 4–5 category driver complaint taxonomy.
- Telemetry/lap alignment for a manually verified incident corpus.
- Historical incident memory and semantic retrieval.
- Telemetry similarity against a retrieved incident.
- Driver-warning lead-time calculation where the historical data supports it.
- One unified incident card in a single-screen pit-wall dashboard.
- Deterministic historical replay with no live FastF1 network dependency during the demo.

### Ships only after the core is stable

- Text–Tone Disagreement / The Mask.
- Field Context: whether a similar telemetry anomaly appears on other cars. This is the only surviving GripSwarm-lite idea and is a supporting evidence point, not “grip estimation.”

### Explicitly excluded

- Full GRIPSWARM or any friction/grip coefficient estimator.
- Weather Whiplash as a second official problem statement.
- Crowd Flow Optimiser.
- Pit-stop strategy optimizer or Monte Carlo race strategist.
- Rival intent prediction.
- Driver psychological profiling, fatigue diagnosis, or lie detection.
- Mechanical fault diagnosis (“rear differential failure confirmed”).
- Large LLM-generated race-engineer advice.
- More than five complaint categories.
- A magic composite “risk score” whose weights cannot be defended.

## 6. Architecture: Build as Parallel Branches, Not a Fragile Linear Chain

The demo can be narrated sequentially, but the software should be decoupled. After radio ingestion, independent branches run in parallel so one weak component cannot break the entire system.

```text
                    ┌──────────────────────────┐
                    │  Curated Race Replay    │
                    │ radio + timestamp +     │
                    │ pre-cached telemetry    │
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 │                                │
        ┌────────▼────────┐              ┌────────▼────────┐
        │ HF Whisper ASR  │              │ Acoustic Model  │
        │ transcript      │              │ arousal/tone    │
        └────────┬────────┘              └────────┬────────┘
                 │                                │
        ┌────────▼────────────────────────────────▼───────┐
        │         Radio Perception Record                │
        │ transcript + tone + event/race identifiers    │
        └────────┬──────────────────────────────┬────────┘
                 │                              │
      ┌──────────▼──────────┐        ┌──────────▼──────────┐
      │ Driver Feedback     │        │ Voice–Content       │
      │ Normalizer          │        │ Consistency         │
      │ (FEEL2PHYSICS)      │        │ (The Mask; optional)│
      └──────────┬──────────┘        └──────────┬──────────┘
                 │                              │
                 └──────────────┬───────────────┘
                                │
                   ┌────────────▼────────────┐
                   │ Incident Memory         │
                   │ (ECHO LAP)              │
                   │ semantic + telemetry    │
                   └────────────┬────────────┘
                                │
                   ┌────────────▼────────────┐
                   │ Evidence & Lead-Time    │
                   │ Engine                  │
                   │ baseline + similarity  │
                   └────────────┬────────────┘
                                │
                   ┌────────────▼────────────┐
                   │ Unified Incident Card   │
                   │ evidence + uncertainty │
                   └─────────────────────────┘

Separate background path:
pre-cached telemetry stream → Recurrence Monitor → possible historical-pattern alert
```

### Two operational flows

**Flow A — Incident capture:** radio event → transcript/tone → complaint category → telemetry context → historical retrieval → incident stored.

**Flow B — Recurrence monitoring:** new telemetry window → compare with stored incident fingerprints → flag a possible recurrence → retrieve prior radio context → wait for later radio/telemetry to strengthen or weaken the hypothesis.

This second flow is essential. Without it, the system cannot honestly claim to surface a recurrence before the driver reports the issue again.

## 7. Data Strategy

### 7.1 Core data sources

| Data source | Use | Owner | Demo policy |
|---|---|---|---|
| Hugging Face F1 team-radio dataset | Audio clips, transcripts/timestamps where available; source material for ASR, taxonomy and memory | Workstream A/B | Curate a small verified subset; do not ingest the entire corpus live |
| FastF1 | Speed, throttle, brake, gear/RPM where useful, lap/sector timing, track position/context | Workstream A/C | Download and cache before demo |
| Project incident manifest | Ground-truth mapping between audio, driver, session, lap/segment, telemetry window and manual notes | Workstream A | This is the authoritative demo dataset |
| Optional self-recorded/mock radio | Bench-test The Mask and live-mic fallback without relying on broadcast rights/quality | Workstream B | Clearly label as simulated/demo audio |
| OpenF1 (optional only) | Metadata fallback if a required race/session field is easier to obtain | Workstream A | Never create a second online dependency for the demo |

### 7.2 Critical correction: do not use Spa 2021 by default

Spa 2021 is a poor primary demo candidate for this specific project because there was essentially no normal green-flag race evolution. ApexSignal needs repeated radio/handling concerns plus meaningful lap/telemetry evolution. Select **[PRIMARY_SESSION]** and **[PRIMARY_DRIVER]** only after validating the data.

### 7.3 Session-selection gate

A session is acceptable only if all of the following are true:

1. FastF1 telemetry for the selected driver is complete enough for speed/throttle/brake and lap/sector comparison.
2. At least two radio moments relate to a recurring or comparable concern.
3. The lap/time context can be verified manually from trustworthy commentary, timing data, or dataset timestamps.
4. The selected moments produce a coherent 90–120 second demo story.

Use **one primary demo session**. The 15–25 incident memory corpus may include one or two supporting sessions if a single race does not contain enough clean examples.

### 7.4 Incident manifest schema

Each curated incident should contain:

```json
{
  "incident_id": "INC-017",
  "session_id": "[PRIMARY_SESSION]",
  "driver": "[PRIMARY_DRIVER]",
  "event_time_ms": 0,
  "lap": 17,
  "sector_or_corner": "T7_EXIT",
  "audio_path": "data/audio/INC-017.wav",
  "verified_transcript": "Rear is moving on throttle.",
  "complaint_label": "EXIT_TRACTION_REAR",
  "telemetry_window_path": "data/telemetry/INC-017.parquet",
  "tyre_compound": "OPTIONAL",
  "tyre_age_laps": null,
  "lap_delta_s": null,
  "verification_notes": "Lap/time manually verified"
}
```

The manifest is the source of truth. No UI number should exist unless it can be traced to this data or to a documented model output.

## 8. Technical Stack

### Core backend/data

- **Python 3.11+**
- **FastF1** for telemetry and timing extraction.
- **pandas / NumPy / SciPy** for telemetry normalization, rolling baselines and similarity.
- **FastAPI + Pydantic + Uvicorn** for API contracts and orchestration.
- **SQLite** for incident metadata.
- **FAISS** (or simple cosine search for the small corpus) for semantic incident retrieval.
- **Parquet/JSON** for deterministic cached race data.

### Hugging Face / AI

- **ASR:** `openai/whisper-small` or another validated Whisper-family model from the Hugging Face Hub.
- **Acoustic arousal/tone candidate:** `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim`; validate on real F1-style audio before making The Mask load-bearing.
- **Semantic embeddings:** `sentence-transformers/all-MiniLM-L6-v2` or an equivalent small sentence-transformer from the Hub.
- **FEEL2PHYSICS classification:** lightweight zero-shot NLI model or embedding-to-prototype classification against curated category descriptions. Select the simpler method that wins the Day-1 benchmark.
- **HF Datasets:** publish or load the project’s curated incident subset through the `datasets` library if time permits, giving the team a reproducible data artifact.
- **HF Spaces:** optional final deployment surface; local Docker remains the demo fallback.

### Frontend

- **Next.js + React + TypeScript**
- **Tailwind CSS** for fast, consistent layout.
- **Recharts** (or equivalent) for speed/throttle/brake and lap/sector plots.
- **WebSocket/SSE** for deterministic replay updates.

### Quality and deployment

- **pytest** for backend unit/integration tests.
- **Vitest/Playwright** for essential UI checks if time allows.
- **Docker / Docker Compose** for reproducible local execution.
- Cache models and all race data before the presentation; the demo must not depend on external network calls.

## 9. Core Concepts and How They Are Used

### 9.1 Mandatory PS1 tone analysis

The official tone/stress output remains visible, but the scientifically safer internal representation is **acoustic arousal / tone deviation with confidence**. If the UI maps that into coarse labels such as calm/stressed/tired for brief compliance, the team must present those labels as model classifications with uncertainty, not psychological truth.

### 9.2 FEEL2PHYSICS: fixed taxonomy

Use a maximum of 4–5 categories. Recommended initial set:

1. **EXIT_TRACTION_REAR** — rear instability / traction complaint on corner exit.
2. **FRONT_TURNIN_BRAKE** — front-end, turn-in, stopping or braking complaint.
3. **TYRE_GRIP_DEGRADATION** — loss of tyre performance / grip degradation complaint.
4. **VISIBILITY_TRACK_CONDITION** — visibility or track-condition-related complaint.
5. **MECHANICAL_OTHER** — optional fallback bucket, used sparingly.

Output: `reported_phenomenon`, not `diagnosed_fault`.

### 9.3 The Mask: Voice–Content Consistency

Compute a **Text–Tone Disagreement** signal from two independently generated quantities: semantic concern intensity from the transcript and acoustic arousal/deviation from the audio. Use Low/Moderate/High or a clearly labeled prototype score. Never call it deception, hidden panic, or lie detection.

The Mask is optional because acoustic emotion models may be out-of-domain on compressed helmet radio. Validate on several real clips on Day 1. If unstable, keep raw tone/arousal for PS1 compliance and remove the disagreement feature.

### 9.4 ECHO LAP: memory and retrieval

For each incident, store:

- transcript embedding,
- complaint category,
- circuit segment,
- telemetry fingerprint,
- lap/sector context,
- available tyre context,
- subsequent performance outcome.

Retrieval should return the top candidate(s) with separate evidence components rather than hiding everything behind a magic probability. If a single “contextual similarity” percentage is shown, label it **prototype similarity score**, not probability of the same mechanical cause.

### 9.5 RacePulse idea: Evidence & Lead-Time Engine

This layer answers two independent questions:

- **Own-baseline evidence:** is the driver currently behaving differently at the same circuit segment relative to a recent personal/session baseline?
- **Historical-match evidence:** does the telemetry window resemble the stored window surrounding a prior complaint?

A defensible lead-time metric is:

`driver_warning_lead_time = first_observable_performance_change_time - radio_event_time`

The “observable performance change” threshold must be defined before the demo using a transparent baseline method (for example, a robust deviation from prior valid laps at the same segment). If there is no clear later deterioration, display **“No measurable lead-time established”** rather than forcing a positive result.

### 9.6 Telemetry fingerprints

For comparable circuit segments:

- normalize by track distance rather than raw clock time,
- resample speed/throttle/brake to a fixed number of points,
- standardize channels,
- calculate channel-by-channel similarity,
- display the components so judges can see why two incidents were considered similar.

Do not infer steering angle, tyre temperature, wheel slip, or mechanical component state if those channels are not present.

## 10. Unified Product Experience

The frontend must be one **Pit-Wall Incident Inspector**, not four module tabs.

A single card should display:

- radio playback + transcript,
- mandatory tone/arousal classification,
- normalized driver complaint category,
- circuit segment and lap,
- telemetry evidence with speed/throttle/brake overlay,
- historical incident match with separate semantic/telemetry similarities,
- measured warning lead time if established,
- optional text–tone disagreement,
- confidence/uncertainty and a human-review recommendation.

Example wording:

> **Possible recurring exit-traction concern — review recommended**  
> Driver report: “Rear is moving again when I get back on throttle.”  
> Reported phenomenon: Exit traction / rear instability.  
> Historical memory: Strong match to Incident INC-017 at the same circuit segment.  
> Observable evidence: throttle pickup is later than the driver’s recent segment baseline.  
> Lead time: 42 s in this replay before the defined performance-change threshold.  
> Interpretation: behavior is consistent with a previously reported concern; mechanical cause is not determined.

## 11. Four Independent Workstreams

### Workstream A — Data, Telemetry & Deterministic Replay

**Mission:** create the authoritative, verified race dataset that every other workstream can consume without making live network calls.

**Own these files only:**

```text
/data_pipeline/
/data/
/hf_dataset/
```

**Tasks:**

- Choose and verify `[PRIMARY_SESSION]` and `[PRIMARY_DRIVER]` using the session-selection gate.
- Curate 15–25 incidents total; mark 4–6 as demo-critical.
- Download and cache FastF1 telemetry before integration.
- Cut/normalize audio clips and create the incident manifest.
- Pre-compute telemetry windows around each incident.
- Build deterministic replay files/stream: radio events + telemetry frames in timestamp order.
- Create the project-specific Hugging Face dataset artifact/dataset card if time permits.
- Manually verify lap/timestamp alignment for every demo-critical incident.

**Inputs:** public radio data, FastF1, optional OpenF1 metadata.  
**Outputs:** `incident_manifest.json/csv`, audio files, Parquet telemetry windows, replay stream, fixture data.  
**Independent test:** a script can replay the primary session and print the correct lap/event/telemetry record without any AI service running.  
**Definition of done:** the demo can run completely offline from these assets and every demo-critical timestamp is manually verified.

### Workstream B — Radio & Language Intelligence Service

**Mission:** convert one radio clip into a stable, structured perception record. This combines the audio/language portions of The Mask and FEEL2PHYSICS without owning race telemetry or memory.

**Own these files only:**

```text
/services/radio_ai/
/tests/radio_ai/
```

**Tasks:**

- Load and warm the HF Whisper ASR model.
- Produce transcript from audio; preserve a manually verified transcript alongside it for evaluation.
- Load and validate the acoustic arousal/tone model on real F1-style clips.
- Implement the mandatory coarse tone output with confidence/uncertainty.
- Implement FEEL2PHYSICS classification into the frozen 4–5 category taxonomy.
- Implement transcript concern intensity for The Mask.
- Implement Text–Tone Disagreement as an optional, non-blocking output.
- Expose a stable `/v1/radio/analyze` endpoint.
- Benchmark model cold-start and per-clip latency; support model warm-up on server start.

**Input contract:** audio bytes/path + incident identifiers.  
**Output contract:** transcript, acoustic state, complaint category, category confidence, optional disagreement signal.  
**Independent test:** run the service against fixture audio and return valid JSON while Workstreams A/C/D are absent.  
**Cut rule:** if The Mask is unstable, remove `text_tone_disagreement`; ASR + tone + complaint classification still ship.

### Workstream C — Incident Memory, Telemetry Evidence & Core API

**Mission:** own the project’s engineering intelligence: ECHO LAP memory, telemetry evidence, recurrence monitoring and lead-time calculation. This is the backend brain, but it must be testable with fixtures rather than waiting on Workstream B.

**Own these files only:**

```text
/services/core_api/
/services/evidence_memory/
/storage/
/tests/core_api/
```

**Tasks:**

- Define the incident database schema and SQLite metadata store.
- Generate/store sentence embeddings for incident memory and build FAISS retrieval.
- Implement semantic retrieval and top-k historical candidates.
- Build telemetry fingerprint generation for normalized speed/throttle/brake windows.
- Implement own-baseline comparison and historical-window similarity.
- Implement the transparent lead-time calculation.
- Implement background recurrence scanning against stored incident fingerprints.
- Fuse all evidence into one `IncidentAssessment` object; do not generate an opaque risk score.
- Expose `/v1/incidents/evaluate`, `/v1/incidents/{id}`, `/v1/replay/frame`, and a WebSocket/SSE stream as needed.
- Treat optional Field Context as a late feature flag only.

**Input contract:** fixture or real `RadioAnalysisOutput` + pre-cached telemetry window.  
**Output contract:** historical match, similarity components, baseline evidence, lead time, recurrence state, interpretation-safe wording.  
**Independent test:** with synthetic transcript/category/telemetry fixtures, the service can store an incident, retrieve it, compare a later window, and produce an assessment without the radio-AI service or UI.

### Workstream D — Pit-Wall Product, Visualization & Deployment

**Mission:** turn the project into a single coherent judge experience and own integration at the contract boundary, not by editing other members’ code.

**Own these files only:**

```text
/apps/web/
/deployment/
/mock_server/
```

**Tasks:**

- Build the single-screen Pit-Wall Incident Inspector in Next.js/React.
- Use mock JSON fixtures from `/contracts/fixtures` from Day 1; never wait for real backend endpoints to start UI work.
- Build radio player, transcript panel, complaint category, tone indicator, telemetry overlay, historical match panel, lead-time timeline and recurrence alert.
- Build a deterministic 90–120 second replay mode and controls.
- Implement graceful degraded states when The Mask or optional Field Context are disabled.
- Add loading/error states; no blank panels or spinner during the judged path.
- Package Docker Compose and, if useful, a Hugging Face Space for deployment.
- Own the final demo script and verify every number shown can be traced to the core API response.

**Input contract:** `IncidentAssessment` JSON/WebSocket stream.  
**Output:** working web app + deployment package.  
**Independent test:** the full UI runs against the mock server even if Workstreams A/B/C are offline.

## 12. Shared Contracts: Freeze These on Day 1

No member should directly import another member’s internal Python/TypeScript code. Integration happens through frozen JSON/Pydantic contracts.

### `RadioAnalysisOutput`

```json
{
  "incident_id": "INC-017",
  "transcript": "Rear is moving again on throttle.",
  "tone_label": "ELEVATED_AROUSAL",
  "tone_score": 0.73,
  "tone_confidence": 0.61,
  "complaint_category": "EXIT_TRACTION_REAR",
  "category_confidence": 0.86,
  "text_tone_disagreement": "MODERATE"
}
```

### `IncidentAssessment`

```json
{
  "incident_id": "INC-031",
  "lap": 31,
  "segment": "T7_EXIT",
  "reported_phenomenon": "EXIT_TRACTION_REAR",
  "baseline_evidence": {
    "throttle_pickup_delta_pct": -11.0,
    "sector_delta_s": 0.18,
    "status": "BEHAVIOR_CONSISTENT"
  },
  "echo_match": {
    "incident_id": "INC-017",
    "semantic_similarity": 0.88,
    "telemetry_similarity": 0.81,
    "same_segment": true,
    "label": "STRONG_PROTOTYPE_MATCH"
  },
  "driver_warning_lead_time_s": 42,
  "recurrence_state": "POSSIBLE_RECURRENCE",
  "human_message": "Behavior is consistent with a previously reported concern; review recommended."
}
```

**Important:** similarity values are model/prototype scores, not probabilities of the same mechanical cause.

## 13. Repository and Branching Strategy

```text
apexsignal/
├─ contracts/
│  ├─ schemas/
│  ├─ fixtures/
│  └─ api_contract.md
├─ data_pipeline/        # Workstream A only
├─ data/                 # Workstream A only
├─ hf_dataset/           # Workstream A only
├─ services/
│  ├─ radio_ai/          # Workstream B only
│  ├─ core_api/          # Workstream C only
│  └─ evidence_memory/   # Workstream C only
├─ storage/              # Workstream C only
├─ apps/web/             # Workstream D only
├─ mock_server/          # Workstream D only
├─ deployment/           # Workstream D only
└─ tests/
```

Recommended branches:

- `ws-a-data-replay`
- `ws-b-radio-ai`
- `ws-c-evidence-memory`
- `ws-d-product-ui`
- `integration/main`

**Rule:** changes to `/contracts` require team agreement. Nobody edits another workstream’s owned folder to “quickly fix” integration; change the contract or file an issue.

## 14. Integration Roadmap

### Integration principle

**Integrate on Day 1 with mocks, not on Day 4 with finished modules.**

1. Freeze contracts and create fixture JSON first.
2. Workstream D builds the UI against fixtures.
3. Workstream C builds the core API against fake `RadioAnalysisOutput` and fake telemetry.
4. Workstream B builds `/radio/analyze` against fixture audio.
5. Workstream A produces real replay assets that match the same schema.
6. Swap mock providers with real providers one interface at a time.
7. Put every optional feature behind a feature flag.
8. Run the final demo from local cached assets with models preloaded.

### End-to-end sequence

```text
A replay event arrives
  → C loads the pre-cached telemetry window
  → B analyzes the attached radio clip
  → C stores/retrieves incident memory and computes evidence
  → C emits IncidentAssessment
  → D renders one incident card and updates the replay timeline
  → C continues telemetry-only recurrence scanning in the background
```

## 15. Validation & Evaluation Plan

The project should be evaluated on evidence you can actually defend.

| Area | Evaluation |
|---|---|
| Data alignment | 100% manual verification for the 4–6 demo-critical incidents |
| ASR | Compare model transcript with verified transcript on the curated sample; report errors honestly |
| Tone/arousal | Bench-test on several real F1-quality clips before relying on The Mask; show uncertainty |
| FEEL2PHYSICS | Manually label curated clips and report a small confusion matrix or per-category accuracy; do not imply general F1 benchmark performance |
| ECHO LAP | Create known related/unrelated incident pairs; measure top-1/top-k retrieval success |
| Telemetry similarity | Visual overlay + component similarity on known same-segment windows |
| Lead time | Manually verify radio timestamp and threshold-crossing timestamp for each claimed demo example |
| Recurrence | Demonstrate at least one replay where a telemetry pattern is flagged before a later related radio message; label it “possible recurrence” |
| UI | A judge should understand the incident in under 10 seconds without opening another tab |

## 16. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Wrong radio-to-lap alignment | Critical | Manual verification; curated subset; never auto-align the entire corpus for the MVP |
| Model cold start / demo latency | High | Load models at startup; cache data/embeddings; no live FastF1 calls |
| Acoustic model fails on helmet-radio audio | High | Day-1 benchmark; The Mask is optional; raw tone/arousal remains mandatory baseline |
| FEEL2PHYSICS overclaims physics | High | Output “reported phenomenon” and observable evidence only |
| Echo match is semantically similar but mechanically unrelated | High | Show separate semantic/telemetry/context evidence; never call it same fault |
| Arbitrary risk score | High | Do not build one; expose evidence components and transparent priority rules |
| UI becomes four disconnected modules | High | One incident card; no module tabs |
| Scope creep | Critical | Full GripSwarm, strategy, crowd and chatbot are explicitly out of scope |
| One member blocks the rest | High | Frozen contracts + mock fixtures + folder ownership from Day 1 |
| Network outage during judging | Critical | Pre-cache race data/models; local replay and local inference fallback |

## 17. Sprint Plan

Treat the sprint as **four build days plus one freeze/submission day**.

### Day 1 — Contract and feasibility lock

- Freeze schemas and folder ownership.
- Choose `[PRIMARY_SESSION]` and `[PRIMARY_DRIVER]`.
- Workstream A creates the first 4–6 verified incident fixtures.
- Workstream B proves ASR + tone on 3–5 real clips.
- Workstream C runs memory/evidence logic on synthetic fixtures.
- Workstream D renders the full UI using mock JSON.
- End of day: the entire system works end-to-end with stubs.

### Day 2 — Real data replaces mocks

- Telemetry windows and replay assets are real and verified.
- FEEL2PHYSICS taxonomy is frozen.
- Core API stores incidents and returns baseline evidence.
- UI consumes at least one real backend response.

### Day 3 — Memory and lead time

- ECHO LAP retrieval works on the curated corpus.
- Telemetry fingerprint comparison works.
- Lead-time calculations are manually verified.
- First complete historical replay succeeds.

### Day 4 — Product polish and optional The Mask

- Add Text–Tone Disagreement only if Day-1 testing justified it.
- Tune UI hierarchy, labels and timeline.
- Add Field Context only if every mandatory feature is stable.
- Freeze new feature development by end of day.

### Day 5 — Cut, verify, rehearse, submit

- Remove anything unstable.
- Run offline cold-start and warm-start tests.
- Verify every visible number against source data/model output.
- Rehearse a 90–120 second chronological demo.
- Package repository, README, architecture diagram and deployment.

## 18. Definition of Done

ApexSignal is ready to submit only when all of the following are true:

- The app accepts/plays a radio clip and produces a transcript through the backend.
- The mandatory tone/arousal output is visible with uncertainty.
- The transcript is mapped to one of the frozen complaint categories.
- The event is aligned to a manually verified lap/segment and cached telemetry window.
- At least one prior incident can be retrieved with semantic and telemetry evidence.
- At least one lead-time example is computed from verified timestamps, or the UI correctly states that no measurable lead time exists.
- The final demo contains no unverified “fault confirmed,” “lie detected,” “stress caused lap loss,” “exact grip,” or similar claims.
- The judge sees one coherent incident view, not four feature tabs.
- The judged path works without live FastF1/OpenF1/network access.
- The system can degrade gracefully if The Mask or Field Context is switched off.

## 19. Recommended Demo Narrative

Use one verified story from `[PRIMARY_SESSION]`:

1. **Incident A:** the driver reports a handling/grip concern. ApexSignal transcribes it, normalizes the complaint and stores the telemetry context.
2. **Later replay:** telemetry at the same segment starts resembling Incident A. The recurrence monitor raises **Possible Recurrence** with component evidence.
3. **Incident B:** the driver later says a related phrase such as “same issue again.” ECHO LAP retrieves Incident A.
4. The incident card shows semantic similarity, telemetry similarity, lap/segment context, mandatory tone/arousal, and measured lead time where valid.
5. Close with: **“We did not diagnose the car. We gave the pit wall structured memory and evidence that the driver’s concern may be returning.”**

The narrative has a beginning, memory, early signal and later confirmation without inventing causal certainty.

## 20. Final Pitch

### 10-second version

> **ApexSignal turns subjective F1 driver radio into structured incident memory and telemetry evidence, helping the pit wall recognize recurring performance concerns earlier.**

### 30-second version

> **F1 cars have hundreds of telemetry signals, but the driver is also a sensor — and that sensor speaks in subjective language. ApexSignal transcribes the radio, interprets what the driver is reporting, links it to telemetry, remembers similar past incidents, and measures whether the driver provided warning before an observable performance change. When a later telemetry pattern resembles an earlier driver-reported issue, ApexSignal surfaces the prior incident and the evidence. It supports the engineer; it does not pretend to diagnose the car.**

---

## Scope Lock

**Build deeply inside PS1.** The final project is **ApexSignal**, combining ECHO LAP + RacePulse + FEEL2PHYSICS + The Mask into one evidence-driven radio intelligence product. Full GripSwarm is excluded. The only optional multi-car idea is a small Field Context evidence point after the core is finished.
