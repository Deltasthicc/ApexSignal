# ApexSignal

**The Silent Co-Driver — evidence-driven incident memory for the F1 pit wall.**

> The car has telemetry. The driver has feel. ApexSignal connects the two, with memory and evidence.

Built for **AI Race Month — GrandPrix Hackathon @ Paytm**, anchored on **Problem Statement 1: The Silent Co-Driver**. Theme: Artificial Intelligence in Racing Strategy & Decision-Making, powered by Hugging Face.

## What it does

Formula 1 teams have dense telemetry, but a driver can perceive a change in handling, grip, or braking before it shows up in a lap-time graph. That feedback arrives as short, subjective radio language ("rear's moving," "no front," "same thing again"), while telemetry arrives as numbers. Nobody connects the two.

ApexSignal transcribes team radio, scores acoustic tone/arousal, normalizes the driver's language into a fixed complaint taxonomy, aligns the report with telemetry and lap context, retrieves similar historical incidents, and watches later telemetry for patterns that resemble earlier driver-reported concerns.

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

Background path: cached telemetry stream --> Recurrence Monitor --> possible-recurrence alert
```

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

Each service is independently runnable against fixture data from Day 1. No service should require another service to be running.

```bash
# Backend services
cd services/core_api && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8001
cd services/radio_ai && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8002

# Mock server (fixture-backed, unblocks frontend work)
cd mock_server && pip install -r requirements.txt && uvicorn server:app --reload --port 8000

# Frontend
cd apps/web && npm install && npm run dev
```

Copy `.env.example` to `.env` in each service directory and fill in real values before running against live models. Never commit `.env`.

## Data policy for the demo

The judged path runs entirely from pre-cached local assets: no live FastF1 or network calls during the demo. See [`data_pipeline/README.md`](data_pipeline/README.md) for how the incident corpus is curated and verified.

## What ApexSignal does not claim

- No lie detection, no psychological diagnosis, no fatigue scoring.
- No confirmed mechanical fault diagnosis ("differential failure confirmed").
- No autonomous pit-stop or race-strategy decisions.
- No grip-coefficient estimation.
- Similarity scores are prototype/model scores, not probabilities of a shared mechanical cause.

## Team

| Workstream | Focus | Owner |
|---|---|---|
| A | Data, telemetry, deterministic replay | TBD |
| B | Radio & language intelligence (ASR, tone, complaint classification) | TBD |
| C | Incident memory, evidence engine, core API | TBD |
| D | Product UI, visualization, deployment | TBD |

## License

MIT. See [`LICENSE`](LICENSE).
