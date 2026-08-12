# services/evidence_memory — Workstream C

Supporting library imported by `services/core_api`. Not a standalone
HTTP service.

## Responsibilities

- `embeddings.py` — generate sentence embeddings for incident
  transcripts (ECHO LAP memory). Model: `sentence-transformers/all-MiniLM-L6-v2`
  or equivalent.
- `retrieval.py` — FAISS (or cosine, given the small corpus size) top-k
  search over stored incident embeddings.
- `telemetry_fingerprint.py` — normalize a telemetry window by track
  distance, resample speed/throttle/brake to a fixed number of points,
  standardize channels, compute channel-by-channel similarity. Never
  infer a channel that was not actually recorded (no steering angle, no
  tyre temperature, no wheel slip unless the source data has it).
- `baseline.py` — own-baseline deviation: is the driver behaving
  differently at this segment relative to a recent personal baseline.
- `lead_time.py` — the transparent lead-time calculation and the
  observable-performance-change threshold definition.
- `synthetic.py` — deterministic synthetic windows for tests and local
  demos. Test scaffolding only; never a source of judge-facing numbers.

Each module should be independently unit-testable against synthetic
fixtures; none of them should require a running FastAPI server.

---

## Telemetry window shape — PROPOSED, needs Workstream A sign-off

> **Status: proposed by Workstream C, not yet agreed.**
> `data_pipeline/README.md` promises "per-incident Parquet telemetry
> windows" but never specifies columns, units, or how many laps a window
> covers. Workstream C needed a concrete shape to build against, so this
> is it. **Workstream A must either match this or tell Workstream C what
> to change.** It is not in `contracts/` because it is not agreed yet;
> once it is, it belongs there.

One Parquet file per incident, at the `telemetry_window_path` given in
`data/incident_manifest.json` (e.g. `data/telemetry/INC-017.parquet`).

### Required columns

| Column | Type | Units | Notes |
|---|---|---|---|
| `session_time_s` | float | seconds | Since session start. **Must share its clock origin with the manifest's `event_time_ms`.** |
| `lap` | int | — | Lap the sample belongs to. |
| `distance_m` | float | metres | Distance along the lap. Must increase within a lap. |
| `speed_kph` | float | km/h | FastF1 `Speed` as-is. |
| `throttle_pct` | float | 0–100 | FastF1 `Throttle` as-is. |
| `brake` | bool or 0/1 | — | FastF1 `Brake`. |

### Optional columns

`driver`, `session_id`, `segment`, `rpm`, `gear`. Used when present,
never fabricated when absent. `segment` is strongly recommended: without
it, per-segment slicing falls back to the whole window.

### The part that changes Workstream A's export

**A window must contain several laps at the same segment, not just the
incident lap.** Concretely: the incident lap, at least 3 clean laps
before it, and as many laps after as the replay covers.

Two of Workstream C's required outputs are undefined with a single lap:

- `baseline_evidence` compares the driver against *their own recent
  baseline at the same segment* — that needs prior laps.
- `driver_warning_lead_time_s` looks for a performance change in the laps
  *after* the radio call — that needs subsequent laps.

With one lap per file, both fields can only ever be `INSUFFICIENT_DATA`
and `null`. The demo narrative in charter section 19 does not work.

### Clock alignment

`session_time_s` and the manifest's `event_time_ms` must be on the same
clock. Lead time is `first_observable_performance_change_time −
radio_event_time`; if the two are measured from different origins the
number is meaningless in a way that is not detectable from the data.
Whatever origin Workstream A picks is fine, as long as it is the same one
and it is written down.

### Minimum viable window

8 usable rows after cleaning, and a non-zero distance span. Below that
`telemetry_fingerprint` raises `TelemetryWindowError` rather than
returning a fingerprint built from too little signal.

---

## How the fingerprint works

`build_fingerprint()`:

1. Drop rows with missing channel values; sort by `distance_m`; keep the
   first sample at each distance (duplicates break interpolation).
2. Map distance onto 0–1 position within the window.
3. Resample each channel onto a fixed 128-point grid of that position.
4. Z-score each channel.

Normalizing by **distance rather than time** is what makes two passes
through the same corner comparable when one is slower — the whole point.
A flat channel (brake untouched) z-scores to zeros rather than dividing
by zero.

`compare_fingerprints()` scores each channel by Pearson correlation of
the two distance-normalized traces, rescaled from [-1, 1] to [0, 1] for
the contract's range. **1.0 = traces move together, 0.5 = unrelated,
0.0 = mirrored.** Two flat channels at the same level score 1.0; a flat
channel against a moving one scores 0.0.

This measures **shape, not magnitude** — by design. Two exits with the
same throttle-pickup shape score high even if one was 2 km/h quicker.
Absolute differences are `baseline.py`'s job.

`FingerprintSimilarity.overall` is the unweighted mean of the per-channel
scores. It exists only because the frozen contract has one
`telemetry_similarity` field. It is **not** a composite risk score: no
channel is weighted, and `per_channel` always travels with it so the
number can be taken apart in front of a judge.

---

## Retrieval gate — measured, not assumed

`all-MiniLM-L6-v2` was run over 23 realistic F1 radio phrasings across
the five taxonomy categories plus non-complaint chatter (247 pairs).

| | median | p95 | max |
|---|---|---|---|
| Same complaint category | 0.382 | 0.594 | 0.618 |
| Different categories | 0.213 | 0.438 | 0.683 |

**The distributions overlap, and not incidentally.** A cross-category
pair scores *above* a genuine same-category repeat:

```
0.429   "Rear is moving on throttle."  vs  "The front is washing out under braking."   <- DIFFERENT complaint
0.422   "Rear is moving on throttle."  vs  "The rear stepped out again on corner exit."  <- SAME complaint
```

No cosine cut separates these. Short idiomatic radio gives MiniLM too
little to work with, and the original 0.6 guess would have rejected
almost every genuine repeat (5.4% retained).

So the gate is **two independent conditions**, neither derived from the
other:

1. **Same complaint category**, from Workstream B's classifier — a model
   trained for exactly this decision, rather than cosine over a six-word
   sentence. This does the precision work.
2. **Semantic cosine ≥ 0.40** — catches the case where the category label
   is right but the wording describes something unrelated. Set for
   recall, since (1) handles precision: 0.40 sits above the
   cross-category median (0.213) and p75 (0.301) while retaining roughly
   three-quarters of genuine same-category repeats.

Telemetry similarity is **not** part of the gate. A driver reporting the
same thing again while the car looks different is a real and interesting
case; gating on telemetry would hide it.

`test_embeddings_real_model.py` guards both numbers against the live
model, including a test that fails if cosine ever *does* separate the
categories — at which point the category gate can be revisited.

> **ASSUMPTION to re-check:** calibrated on clean hand-written phrasings,
> not real ASR output, which will be noisier and may score lower. Re-run
> the calibration once Workstream B has real transcripts.
