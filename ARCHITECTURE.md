# Architecture

## Request flow

```text
1. Replay driver (Workstream A asset) emits the next timestamped event:
   a radio clip reference + the pre-cached telemetry window around it.
2. core_api loads the cached telemetry window for that event.
3. radio_ai analyzes the attached audio clip -> RadioAnalysisOutput
   (transcript, tone/arousal, complaint category, confidences).
4. core_api stores the incident in evidence_memory, retrieves the top
   historical match, computes baseline + historical evidence, and
   computes lead time where the data supports it.
5. core_api emits one IncidentAssessment object.
6. apps/web renders one incident card and advances the replay timeline.
7. core_api continues telemetry-only recurrence scanning in the
   background, independent of new radio events.
```

Two flows share this pipeline:

- **Flow A, incident capture:** radio event -> transcript/tone -> complaint
  category -> telemetry context -> historical retrieval -> incident stored.
- **Flow B, recurrence monitoring:** new telemetry window -> compare against
  stored incident fingerprints -> flag possible recurrence -> surface prior
  radio context -> wait for later radio/telemetry to strengthen or weaken
  the hypothesis.

Flow B is why the product can claim early warning rather than just
after-the-fact tagging.

## Service boundaries

| Service | Owns | Talks to |
|---|---|---|
| `services/radio_ai` | ASR, tone/arousal, complaint classification | Nothing else. Stateless. Takes audio, returns `RadioAnalysisOutput`. |
| `services/core_api` + `services/evidence_memory` | Incident storage, retrieval, evidence fusion, recurrence monitor | Calls `radio_ai` over HTTP. Reads `data/` telemetry windows. Owns `storage/`. |
| `apps/web` | Pit-Wall Incident Inspector UI | Calls `core_api` (or `mock_server` during independent development). |
| `mock_server` | Fixture-backed stand-in for `core_api` + `radio_ai` | Serves `contracts/fixtures/*` verbatim. |
| `data_pipeline` | Offline dataset curation, FastF1 caching, replay asset generation | Not called at runtime. Produces files consumed by `core_api` and the replay driver. |

No service imports another service's Python/TypeScript modules directly.
Integration happens only through the JSON contracts frozen in `contracts/`.

## Design decisions and why

- **Deterministic replay, no live FastF1 during the demo.** Network calls
  are the single biggest risk to a live demo. All telemetry and audio for
  the demo path is cached before judging starts.
- **Evidence components, not a composite risk score.** A single opaque
  "risk score" cannot be defended when a judge asks "why." `IncidentAssessment`
  exposes `baseline_evidence` and `echo_match` as separate, inspectable
  fields instead.
- **Similarity is a prototype score, not a probability.** `echo_match.semantic_similarity`
  and `echo_match.telemetry_similarity` describe how alike two incidents
  look under the model, not the probability they share a mechanical cause.
  The UI and the report language must preserve that distinction.
- **The Mask (text-tone disagreement) is optional and feature-flagged.**
  Acoustic emotion models are frequently out-of-domain on compressed
  helmet-radio audio. If Day-1 validation on real clips is unstable, the
  field is omitted rather than shipped unreliable. `tone_label`,
  `tone_score`, and `tone_confidence` remain mandatory (this is the
  official PS1 requirement); `text_tone_disagreement` is the only optional
  field in `RadioAnalysisOutput`.
- **Fixed 4-5 category complaint taxonomy.** An open-ended label space is
  neither testable nor explainable in a two-minute demo. See
  `contracts/api_contract.md` for the frozen list.
- **Mock-first integration.** `apps/web` and `mock_server` exist so the
  frontend never blocks on a backend service being finished. Any service
  can be developed and tested in isolation against `contracts/fixtures/`.

## Deployment

Local development runs each service with `uvicorn --reload` and the
frontend with `next dev`. `deployment/docker-compose.yml` wires all
services together for an end-to-end local run. `deployment/` also holds
notes for an optional Hugging Face Space deployment of the demo.

## Observability

Each FastAPI service exposes `/health`. Structured logs go to stdout;
no external logging service is required for the hackathon build.

## Security posture

No user authentication for the hackathon build; this is a local/demo
tool, not a production multi-tenant system. Do not commit `.env` files
or API keys. `.env.example` in each service directory documents the
required variables with placeholder values only.
