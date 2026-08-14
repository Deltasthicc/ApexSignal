# Telemetry window contract

**Status: implemented and in use.** `api_contract.md` names
`telemetry_window_path` but never said what is inside the file; this
document fills that gap. Workstream A's `data_pipeline/scripts/
build_telemetry_windows.py` and `validate_telemetry_windows.py` both
build and enforce this exact shape, and `services/evidence_memory`
consumes it — see that service's README for the consumer-side view of
the same contract. Nothing here changes an existing frozen shape.

Produced by `data_pipeline/scripts/build_telemetry_windows.py`. Consumed by
`services/core_api` (baseline evidence, lead time) and
`services/evidence_memory` (telemetry fingerprints).

---

## The clock

There is exactly one time origin in this project:

> **`session_time_s` and `event_time_ms` are both measured in seconds from
> FastF1's session t0 (`Session.t0_date`).**

`session_time_s` in the window and `event_time_ms` in
`data/incident_manifest.json` are the same clock with the same zero.
`driver_warning_lead_time_s` is a subtraction across those two, so it is
only meaningful because of this.

This is the rule most likely to be broken quietly. A time measured from
lights-out, from the start of the broadcast, or from the start of an audio
clip is a well-formed number that lands inside the session and passes every
type check — and it makes every lead time in the product wrong by a
constant offset that nothing in the pipeline would reveal.

Two things guard it:

- `data/telemetry/<session_id>/session_meta.json` records the declared
  `clock_origin` and t0 as an absolute UTC instant, so the origin is
  reconstructible later.
- The builder and validator both assert that `event_time_ms / 1000` falls
  inside the incident lap's own session-time span. An event time on the
  wrong origin will not land on the right lap.

Neither the builder nor the validator will write or pass a window that
fails this. `--skip-alignment-check` exists for mid-curation work only and
must never be used for a demo build.

---

## Coverage

One Parquet file per incident, at the manifest's `telemetry_window_path`.
Each file covers:

| Part | Rule |
|---|---|
| Baseline | **at least 3 clean laps** before the incident lap |
| Context | any unclean laps between the earliest baseline lap and the incident lap, so the window is contiguous in time |
| Incident | the lap the radio call belongs to |
| Post | every lap after the incident that the replay covers |

**A one-lap-per-file window is not a valid smaller version of this.**
Baseline evidence is a comparison against the driver's own normal, so with
no preceding laps in the file `baseline_evidence.status` can only ever be
`INSUFFICIENT_DATA` and `driver_warning_lead_time_s` can only ever be
`null`. The validator rejects single-lap windows explicitly.

Baseline laps are counted **clean**, not raw. A window may therefore span
more than three preceding laps when pit or safety-car laps intervene. A lap
is clean only if it has telemetry and valid bounds, is not deleted, is not a
pit in- or out-lap, is `IsAccurate`, and ran under an all-clear track status
for its whole length. Anything else is carried as `CONTEXT` with the
exclusion reason recorded in `windows_index.json`.

If three clean laps cannot be found, the build **fails for that incident**
rather than emitting a weaker window. A window quietly built on two
baseline laps produces numbers that look like every other incident's and
are not comparable to them.

---

## Columns

Required — every one is a direct FastF1 rename plus a unit cast. Nothing is
modelled, interpolated, or inferred.

| Column | Type | FastF1 source | Notes |
|---|---|---|---|
| `session_time_s` | float64 | `SessionTime` | seconds from session t0; see above |
| `lap` | int64 | `LapNumber` | the lap the sample belongs to |
| `distance_m` | float64 | `Distance` | **lap-relative**, see below |
| `speed_kph` | float64 | `Speed` | km/h as reported |
| `throttle_pct` | float64 | `Throttle` | 0–100 as reported |
| `brake` | bool | `Brake` | numeric feeds cast as `> 0` |

Also always present:

| Column | Type | Values |
|---|---|---|
| `lap_role` | string | `BASELINE` / `CONTEXT` / `INCIDENT` / `POST` |

Optional, present when known: `driver`, `session_id`, `segment`, `rpm`
(`RPM`), `gear` (`nGear`). `segment` is populated only when a segment map is
supplied to the builder; it is absent rather than guessed.

### `distance_m` is lap-relative

Zero at the start/finish line, rising to lap length. FastF1's
`add_distance()` integrates from the start of whatever slice it is given,
so on a multi-lap slice distance keeps climbing across laps. The builder
rebases per lap.

This is what makes the window usable: the same `distance_m` is the same
piece of tarmac on every lap in the file, so comparing throttle pickup at
T7 exit against the baseline laps is an interpolation on one axis. With
cumulative distance every consumer would have to re-derive this, and they
would each derive it slightly differently.

### `lap_role` is not decoration

Consumers **must** filter to `lap_role == "BASELINE"` before computing a
reference. `CONTEXT` laps are in the file for time continuity only —
averaging a safety-car lap into a baseline is exactly the mistake the role
column exists to prevent. Cleanliness cannot be re-derived downstream,
because the fields it depends on (`IsAccurate`, `TrackStatus`, pit times)
are not carried in the window.

---

## Side files

`data/telemetry/<session_id>/`:

| File | Contents |
|---|---|
| `session_meta.json` | clock origin, t0 as absolute UTC, lap range, FastF1 version |
| `laps_<DRV>.csv` | lap index with session-time bounds — the artifact for manual lap/timestamp verification |
| `windows_index.json` | per incident: lap roles, excluded laps **with reasons**, row counts, time span |
| `_fastf1_cache/` | FastF1's cache, so every later run is offline |

---

## Validating

```bash
python data_pipeline/scripts/validate_telemetry_windows.py
```

Reads the manifest and the written Parquet only — no FastF1, no session
cache, no network. Run it on the demo machine before judging. Exit code 0
means every window can support the features that depend on it.
