# API contract

Frozen on Day 1. Changes require agreement from every workstream that
reads or writes the affected shape. Nobody imports another workstream's
internal code; integration happens only through these JSON contracts.

## `RadioAnalysisOutput`

Produced by `services/radio_ai`, `POST /v1/radio/analyze`. Consumed by
`services/core_api`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `incident_id` | string | yes | Matches the incident manifest entry. |
| `transcript` | string | yes | ASR output. |
| `tone_label` | string | yes | Mandatory PS1 output. One of `CALM`, `ELEVATED_AROUSAL`, `FATIGUED`. |
| `tone_score` | float, 0-1 | yes | Acoustic arousal/deviation magnitude. |
| `tone_confidence` | float, 0-1 | yes | Model confidence in `tone_label`. |
| `complaint_category` | string | yes | One of the fixed taxonomy below, or `null` if the message is not a complaint. |
| `category_confidence` | float, 0-1 | yes if `complaint_category` set | |
| `text_tone_disagreement` | string, optional | no | `LOW` / `MODERATE` / `HIGH`. Omit entirely if The Mask is disabled. Never call this deception. |

See `contracts/schemas/radio_analysis_output.schema.json` and
`contracts/fixtures/radio_analysis_output.sample.json`.

### Complaint taxonomy (frozen, max 5 categories)

1. `EXIT_TRACTION_REAR` — rear instability / traction complaint on corner exit.
2. `FRONT_TURNIN_BRAKE` — front-end, turn-in, or braking complaint.
3. `TYRE_GRIP_DEGRADATION` — loss of tyre performance / grip degradation.
4. `VISIBILITY_TRACK_CONDITION` — visibility or track-condition complaint.
5. `MECHANICAL_OTHER` — fallback bucket, used sparingly.

Output language is always "reported phenomenon," never "diagnosed fault."

## `IncidentAssessment`

Produced by `services/core_api`, `POST /v1/incidents/evaluate` and
`GET /v1/incidents/{id}`. Consumed by `apps/web`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `incident_id` | string | yes | |
| `lap` | int | yes | |
| `segment` | string | yes | e.g. `T7_EXIT`. |
| `reported_phenomenon` | string | yes | One of the taxonomy values above. |
| `baseline_evidence` | object | yes | `throttle_pickup_delta_pct`, `sector_delta_s`, `status` (`BEHAVIOR_CONSISTENT` / `NO_DEVIATION` / `INSUFFICIENT_DATA`). |
| `echo_match` | object or null | yes | `incident_id`, `semantic_similarity` (0-1), `telemetry_similarity` (0-1), `same_segment` (bool), `label`. `null` if no historical match clears the retrieval threshold. |
| `driver_warning_lead_time_s` | float or null | yes | `null` means no measurable lead time was established; the UI must say so, never omit the field. |
| `recurrence_state` | string | yes | `NONE` / `POSSIBLE_RECURRENCE` / `CONFIRMED_BY_RADIO`. |
| `human_message` | string | yes | Interpretation-safe wording. Never "fault confirmed," never a diagnosis. |

See `contracts/schemas/incident_assessment.schema.json` and
`contracts/fixtures/incident_assessment.sample.json`.

**Important:** `semantic_similarity` and `telemetry_similarity` are
model/prototype scores, not probabilities of a shared mechanical cause.
No copy anywhere in the product may imply otherwise.

## Incident manifest (Workstream A -> everyone)

The ground-truth source of truth Workstream A curates. Not an HTTP
contract, but every downstream field depends on it matching this shape.
See `contracts/fixtures/incident_manifest.sample.json`.

## Endpoints at a glance

| Service | Endpoint | Method | Request | Response |
|---|---|---|---|---|
| `radio_ai` | `/health` | GET | - | `{"status": "ok"}` |
| `radio_ai` | `/v1/radio/analyze` | POST | audio bytes/path + `incident_id` | `RadioAnalysisOutput` |
| `core_api` | `/health` | GET | - | `{"status": "ok"}` |
| `core_api` | `/v1/incidents/evaluate` | POST | `RadioAnalysisOutput` + telemetry window ref | `IncidentAssessment` |
| `core_api` | `/v1/incidents/{id}` | GET | - | `IncidentAssessment` |
| `core_api` | `/v1/replay/frame` | GET | `?index=N` | next replay frame (radio + telemetry) |
| `mock_server` | same paths as above | - | - | fixture data verbatim |

## Cut rules

- If The Mask is unstable on Day 1 real-clip validation, drop
  `text_tone_disagreement` entirely. Every other field still ships.
- If historical retrieval finds nothing above threshold, `echo_match` is
  `null`, not a low-confidence guess.
- If no observable performance change follows a radio event,
  `driver_warning_lead_time_s` is `null` and `human_message` says so
  explicitly ("No measurable lead-time established").
