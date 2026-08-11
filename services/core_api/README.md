# services/core_api — Workstream C

Mission: the backend brain. Owns incident memory (ECHO LAP), telemetry
evidence, recurrence monitoring, and the lead-time calculation. Must be
testable with fixtures without waiting on `services/radio_ai`.

## Owns

This directory, `../evidence_memory/`, `../../storage/`, and
`../../tests/core_api/`.

## Tasks

- Define the incident schema and SQLite metadata store (`../../storage/`).
- Generate/store sentence embeddings for incident memory; build FAISS
  (or cosine) retrieval in `../evidence_memory/`.
- Implement semantic retrieval returning top-k historical candidates
  with separate evidence components, never a single opaque probability.
- Build telemetry fingerprint generation: normalize by track distance,
  resample speed/throttle/brake to a fixed number of points, standardize
  channels.
- Implement own-baseline comparison (is the driver behaving differently
  at this segment vs. a recent personal baseline) and historical-window
  similarity.
- Implement the lead-time calculation:
  `driver_warning_lead_time = first_observable_performance_change_time - radio_event_time`.
  If there is no clear later deterioration, return `null` and let the
  UI say "No measurable lead-time established." Never force a positive
  result.
- Implement background recurrence scanning against stored incident
  fingerprints, independent of new radio events.
- Fuse all evidence into one `IncidentAssessment`. Do not add a
  composite risk score; expose the components.
- Expose `POST /v1/incidents/evaluate`, `GET /v1/incidents/{id}`,
  `GET /v1/replay/frame`.

## Contract

Input: fixture or real `RadioAnalysisOutput` + a pre-cached telemetry
window. Output: `IncidentAssessment`. See `contracts/api_contract.md`.

## Independent test

With synthetic transcript/category/telemetry fixtures, this service can
store an incident, retrieve it, compare a later window, and produce an
assessment without `radio_ai` or `apps/web` running.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

---

## Methods: how each number is produced

Every threshold below is one named constant in one place. None was
picked to make the demo work; each is either derived from the driver's
own data or documented here with its rationale. Where a method rests on
an assumption the team should challenge, it says so.

### Segment time

Measured from telemetry directly: last sample time minus first sample
time within the lap's rows at that segment. Never read from a lap-time
column, so it always refers to exactly the stretch of track being
compared.

### `baseline_evidence.sector_delta_s`

Current lap's segment time minus the **median** of the driver's own
recent laps at the same segment. Positive means slower. Median rather
than mean so one scrappy baseline lap does not move it.

Baseline = the most recent `BASELINE_WINDOW_LAPS` (5) laps at that
segment strictly *before* the current lap. Never later laps: a baseline
containing the future could hide the very deviation being looked for.

### `baseline_evidence.throttle_pickup_delta_pct`

**Throttle pickup point** = the first distance into the segment where
throttle reaches `THROTTLE_PICKUP_PCT` (50%). 50% is clear of the
trailing-throttle noise around brake release and below full power, so it
lands on the ramp rather than at either end of it. If the driver never
reaches 50% in the window the pickup is `None`, not zero — a
braking-limited segment must not be reported as an instant pickup.

The delta is the shift in that point relative to the baseline median,
as a percentage of segment length, **sign-flipped so negative means the
driver got to power later** than their own baseline — the direction a
traction complaint would predict. Segment length is the denominator
rather than the baseline pickup distance because it is stable: a
baseline pickup near the segment start would make the percentage
explode.

### `baseline_evidence.status`

| Status | Meaning |
|---|---|
| `INSUFFICIENT_DATA` | Fewer than `MIN_BASELINE_LAPS` (3) usable prior laps at this segment. |
| `BEHAVIOR_CONSISTENT` | Segment time **or** throttle pickup deviated beyond the driver's own spread. |
| `NO_DEVIATION` | Both within the driver's own spread. |

"Deviated beyond the driver's own spread" means: exceeds `ROBUST_K` (3)
MAD-based sigmas of the baseline's own variability, with an absolute
floor (`SECTOR_TIME_FLOOR_S` = 0.05 s, `THROTTLE_PICKUP_FLOOR_PCT` = 2%)
so a very consistent driver does not trip on rounding noise. MAD rather
than standard deviation so one outlier lap cannot inflate the threshold
and mask a real change.

An erratic driver therefore needs a larger change before it counts than a
metronomic one. That is deliberate.

> `BEHAVIOR_CONSISTENT` means the telemetry moved in a way consistent
> with something having been reported. It is **not** a claim that the
> complaint is correct, that a fault exists, or that a cause is known.

### `driver_warning_lead_time_s`

```
driver_warning_lead_time_s
    = first_observable_performance_change_time - radio_event_time
```

"First observable performance change" is defined as follows, and this is
the definition to quote if a judge challenges the number:

1. **Baseline.** Every lap at this segment whose traversal *ended* before
   the radio call. Their median segment time is the baseline. Fewer than
   `MIN_BASELINE_LAPS` (3) and the answer is `null` — with no baseline
   there is no defensible notion of "change".
2. **Threshold.** A lap qualifies when its segment time exceeds that
   baseline median by more than `ROBUST_K` (3) MAD-based sigmas of the
   baseline's own spread, floored at `SECTOR_TIME_FLOOR_S` (0.05 s). The
   threshold comes from the driver's own consistency, not a constant.
3. **Persistence.** The deviation must hold for
   `MIN_CONSECUTIVE_DETERIORATING_LAPS` (2) consecutive laps. One slow
   lap is traffic, a yellow-flag lift, or a scrappy lap.
4. **Result.** The session time at which the *first* lap of that run
   entered the segment, minus the radio event time.

Only laps beginning at or after the radio call are examined, so the
result is never negative — this measures *warning lead*, and a change
that predates the call is not one.

If no qualifying run exists, the result is `null` and `human_message`
says **"No measurable lead-time established."** There is no fallback
path, and the code never reports the largest deviation it found as a
consolation result. `null` is a correct, expected answer.

### Assumptions to sanity-check

- **The 2-consecutive-lap persistence rule** is the cheapest defence
  against traffic laps available today. Workstream A does not currently
  provide lap-validity or track-status flags; with them, invalid laps
  could be excluded properly and the rule relaxed.
- **`session_time_s` and `event_time_ms` must share a clock origin.**
  Lead time subtracts across those two sources. Different origins produce
  a plausible-looking number that is silently wrong. See
  `services/evidence_memory/README.md`.
- **The baseline window is "recent laps before the current lap"**, which
  for a lap well after a complaint may include already-deteriorated laps.
  The median keeps this robust up to roughly half the window, but a
  long-running deterioration will gradually normalise itself away. This
  is the intended meaning of "recent personal baseline" and is a real
  limitation worth stating rather than hiding.
- **Retrieval thresholds** are documented separately in
  `services/evidence_memory/README.md`, including the measured evidence
  that a cosine threshold alone cannot separate complaint categories.
