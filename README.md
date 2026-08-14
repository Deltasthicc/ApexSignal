---
title: ApexSignal
emoji: 🏁
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# ApexSignal

**The Silent Co-Driver — evidence-driven incident memory for the F1 pit wall.**

> The car has telemetry. The driver has feel. ApexSignal connects the two, with memory and evidence.

Built for **AI Race Month — GrandPrix Hackathon @ Paytm**, anchored on **Problem Statement 1: The Silent Co-Driver**. Theme: Artificial Intelligence in Racing Strategy & Decision-Making, powered by Hugging Face.

## Public build

- **Presentation site:** https://apex-signal-sigma.vercel.app
- **Replay API:** https://apexsignal-mock-server.onrender.com/health
- **Source:** https://github.com/Deltasthicc/ApexSignal

The public site calls the deployed replay API and automatically falls back to
the same contract-validated records in the browser if the free Render service
is waking up. See [`docs/PRESENTATION_RUNBOOK.md`](docs/PRESENTATION_RUNBOOK.md)
for the 90-second judge flow and [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)
for the exact shipped/roadmap boundary.

## What it does

Formula 1 teams have dense telemetry, but a driver can perceive a change in handling, grip, or braking before it shows up in a lap-time graph. That feedback arrives as short, subjective radio language ("rear's moving," "no front," "same thing again"), while telemetry arrives as numbers. Nobody connects the two.

ApexSignal transcribes team radio, scores acoustic tone/arousal, normalizes the driver's language into a fixed complaint taxonomy, aligns the report with telemetry and lap context, and retrieves similar historical incidents. When a driver reports something again, ApexSignal checks whether the new report's telemetry resembles an earlier incident's and surfaces that match as evidence.

It reports **measured lead time**, **behavior consistent with a complaint**, and **probable recurrence**. It does not claim lie detection, psychological diagnosis, confirmed mechanical faults, or autonomous strategy decisions. Every number on screen traces back to source data or a documented model output.

Full ambition and design rationale live in [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md). This README describes what actually ships for the hackathon submission.

## How it works

```text
Curated race replay (radio + timestamp + cached telemetry)
        |
        +--> HF Whisper ASR ----------> transcript --+
        |                                             |
        +--> Acoustic tone/arousal model ---> tone ---+
                                                       v
                                    Radio Perception Record
                                    (transcript + tone + ids)
                                                       |
                                    Driver Feedback Normalizer
                                    (complaint category, fixed taxonomy)
                                                       |
                                    Incident Memory (semantic + telemetry)
                                                       |
                                    Evidence & Lead-Time Engine
                                    (baseline deviation + historical match)
                                                       |
                                    Unified Incident Card
                                    (evidence + uncertainty, one screen)
```

Recurrence is flagged when a *new* radio event's telemetry resembles a
stored incident's — not by a standing background process that watches
telemetry independent of radio events. ApexSignal cannot catch a
recurrence before the driver reports it again; it can only recognize
one faster once they do. A telemetry-only background monitor was in
the original concept (see `docs/PROJECT_CHARTER.md`) but is out of
scope for this build.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full request flow and design decisions.

## Repository layout

```text
apexsignal/
├── contracts/            Frozen JSON schemas + fixtures every workstream builds against
├── data_pipeline/        Workstream A — dataset curation, FastF1 caching, replay assets
├── data/                 Workstream A — audio clips, telemetry windows, incident manifest
├── hf_dataset/           Workstream A — Hugging Face dataset artifact (optional)
├── services/
│   ├── radio_ai/         Workstream B — ASR + tone/arousal + complaint classification
│   ├── core_api/         Workstream C — incident memory, evidence engine, recurrence monitor
│   └── evidence_memory/  Workstream C — embeddings, FAISS retrieval, telemetry fingerprints
├── storage/              Workstream C — SQLite schema for incident metadata
├── apps/web/             Workstream D — Pit-Wall Incident Inspector (Next.js)
├── mock_server/          Workstream D — serves contract fixtures so UI never blocks on backend
├── deployment/           Workstream D — Docker Compose, Hugging Face Space config
├── tests/                Cross-cutting integration tests
└── docs/                 Charter, problem statement, submission notes
```

Ownership is enforced by folder, not by convention. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full map and the branching model.

## Tech stack

| Layer | Choice |
|---|---|
| Backend services | Python 3.11, FastAPI, Pydantic, Uvicorn |
| Telemetry | FastF1, pandas, NumPy |
| ASR | Hugging Face `openai/whisper-small` (or validated alternative) |
| Acoustic tone/arousal | Hugging Face `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim` |
| Semantic embeddings | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` |
| Retrieval | FAISS (or cosine search over the small corpus) |
| Metadata store | SQLite |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Deployment | Docker Compose, optional Hugging Face Space |

## Getting started

Each service is independently runnable against the deterministic reference replay. No service should require another service to be running.

### Fastest path — one screen, zero backend setup

```bash
cd mock_server && pip install -r requirements.txt && uvicorn server:app --reload --port 8000
# new terminal
cd apps/web && npm install && cp .env.local.example .env.local && npm run dev
```

Open `http://localhost:3000`. This runs the full ApexSignal UI — replay
timeline, radio pins, tone/complaint classification, baseline evidence,
the gold-incident lead-time card, and the Pit-Wall toggle — against
the replay API's contract records (`contracts/fixtures/`). No GPU, no model
downloads, no other service required.

### Full stack, real `core_api`

```bash
cd services/core_api && pip install -r requirements.txt && cp .env.example .env && uvicorn app.main:app --reload --port 8001
# new terminal
cd mock_server && pip install -r requirements.txt && uvicorn server:app --reload --port 8000
# new terminal
cd apps/web && npm install && npm run dev
# then set NEXT_PUBLIC_CORE_API_BASE_URL=http://localhost:8001 in apps/web/.env.local
# (mock_server still serves /v1/radio/analyze via NEXT_PUBLIC_RADIO_AI_BASE_URL=http://localhost:8000)
```

`services/core_api` runs `EVALUATE_MODE=fixture` by default (162 tests
pass against it with every dependency in `requirements.txt` installed;
5 of those require `sentence-transformers` specifically and show as
skipped, not failed, without it), so this exercises the real
evidence-pipeline service without needing Workstream A's real
telemetry/manifest data.

### Docker Compose

```bash
docker compose -f deployment/docker-compose.yml up --build
```

Brings up `mock_server` (8000), `core_api` (8001, fixture mode), and
`web` (3000) — the same deterministic reference replay, containerized. The real
`services/radio_ai` pipeline (Whisper + tone + classifier models) is
opt-in and GPU-oriented; add `--profile live` to also build and start
it.

Copy `.env.example` to `.env` in each service directory and fill in real values before running against live models. Never commit `.env`.

### Verification

```bash
python scripts/run_test_suites.py
cd apps/web && npm run build
```

The Python runner isolates each service's top-level `app` package, avoiding the
module-name collision caused by collecting every service from the repository
root.

## Data policy for the presentation replay

The judged path runs from pre-cached, contract-validated records: no live FastF1 call is required during a presentation. See [`data_pipeline/README.md`](data_pipeline/README.md) for how an expanded incident corpus is curated and verified.

## What ApexSignal does not claim

- No lie detection, no psychological diagnosis, no fatigue scoring.
- No confirmed mechanical fault diagnosis ("differential failure confirmed").
- No autonomous pit-stop or race-strategy decisions.
- No grip-coefficient estimation.
- Similarity scores are prototype/model scores, not probabilities of a shared mechanical cause.

## Team

| Workstream | Focus | Owner |
|---|---|---|
| A | Data, telemetry, deterministic replay | Jagrav |
| B | Radio & language intelligence (ASR, tone, complaint classification) | Shashwat |
| C | Incident memory, evidence engine, core API | Tanish |
| D | Product UI, visualization, deployment | Mohit |

## License

MIT. See [`LICENSE`](LICENSE).
