# data_pipeline — Workstream A

Mission: produce the authoritative, verified race dataset every other
workstream consumes without making live network calls.

## Owns

This directory, plus `../data/` and `../hf_dataset/`. Nothing else.

## Pipeline

```bash
pip install -r data_pipeline/requirements.txt

# 1. Warm the FastF1 cache and pin the clock origin. Needs network, once.
python data_pipeline/scripts/fetch_fastf1_session.py \
    --year 2023 --grand-prix "Italian Grand Prix" --session R --driver VER

# 2. Verify lap boundaries by hand against timing data.
#    data/telemetry/<session_id>/laps_VER.csv

# 3. Pull the driver's team radio onto the session clock. Needs network.
#    Produces radio_candidates_<DRV>.csv: every capture with a real
#    event_time_ms, its lap, and whether that lap can support a baseline.
python data_pipeline/scripts/fetch_team_radio.py \
    --session-id 2023_ITALIAN_GRAND_PRIX_R --driver SAI [--download]

# 4. Listen to the candidates, pick the complaints, curate them.
python data_pipeline/scripts/build_incident_manifest.py

# 5. Build one multi-lap telemetry window per incident. Offline.
python data_pipeline/scripts/build_telemetry_windows.py \
    --session-id 2023_ITALIAN_GRAND_PRIX_R --driver SAI

# 6. Gate. Run before every demo. Offline.
python data_pipeline/scripts/validate_telemetry_windows.py
```

## Where event_time_ms comes from

Not from a stopwatch against broadcast footage. The F1 livetiming archive
publishes `TeamRadio.json` per session — one entry per capture with an
absolute UTC instant, the driver's racing number, and an mp3 path. So:

```
session_time_s = (capture Utc - t0_date).total_seconds()
event_time_ms  = session_time_s * 1000
```

`t0_date` is verified to be the true anchor: across every telemetry sample,
`Date - SessionTime` is a single constant equal to it. Radio and telemetry
are therefore on the same clock by construction, not by careful manual work
that has to be repeated correctly for every incident.

FastF1 itself has no team radio API — `fetch_team_radio.py` reads the
livetiming archive directly.

## The clock rule

`session_time_s` in every telemetry window and `event_time_ms` in every
manifest entry are both **seconds from FastF1's session t0**. Same clock,
same zero. `driver_warning_lead_time_s` is a subtraction across the two.

A time taken from lights-out, from the broadcast, or from the start of an
audio clip is a well-formed number that lands inside the session and passes
every type check — and it makes every lead time wrong by a constant offset
with nothing in the pipeline to reveal it. Steps 4 and 5 both assert that
`event_time_ms` lands inside the incident lap's own session-time span,
which a wrong origin cannot do.

Full spec: [`../contracts/telemetry_window.md`](../contracts/telemetry_window.md).

## Window shape

Each incident gets **one Parquet file covering many laps**: at least three
*clean* laps before the incident lap, the unclean laps in between as
`CONTEXT`, the incident lap, and every lap after that the replay covers.

One lap per file is not a smaller version of this. With no preceding laps
there is nothing to compare against, so `baseline_evidence.status` is
permanently `INSUFFICIENT_DATA` and `driver_warning_lead_time_s` is
permanently `null`. The validator rejects single-lap windows.

Clean means: has telemetry and valid bounds, not deleted, not a pit in- or
out-lap, `IsAccurate`, all-clear track status for the whole lap. When pit or
safety-car laps intervene the window reaches further back rather than
accepting a dirty baseline. If three clean laps cannot be found, that
incident **fails the build** instead of shipping a weaker window.

## Tasks

- Choose and verify the primary session and driver using the
  session-selection gate below.
- Curate 15-25 incidents total; mark 4-6 as demo-critical.
- Download and cache FastF1 telemetry before any integration work starts.
- Cut and normalize audio clips; build `data/incident_manifest.json`.
- Pre-compute telemetry windows around each incident as Parquet files.
- Build the deterministic replay stream: radio events + telemetry
  frames in timestamp order.
- Manually verify lap/timestamp alignment for every demo-critical
  incident. This is the step most likely to embarrass the team if
  skipped. `laps_<DRV>.csv` exists for exactly this.

## Session-selection gate

A session is acceptable only if all of the following hold:

1. FastF1 telemetry for the selected driver is complete enough for
   speed/throttle/brake and lap/sector comparison.
2. At least two radio moments relate to a recurring or comparable
   concern.
3. The lap/time context can be verified manually from trustworthy
   commentary, timing data, or dataset timestamps.
4. The selected moments produce a coherent 90-120 second demo story.
5. Every demo-critical incident has **at least three clean laps before
   it**. An incident on lap 2, or straight after a safety-car restart,
   cannot produce baseline evidence no matter how good the radio is.

Do not default to Spa 2021: it lacks normal green-flag race evolution,
which this project needs to show a baseline deviation.

## Tests

```bash
pip install -r data_pipeline/requirements-test.txt
pytest data_pipeline/tests
```

No FastF1, no network, no cached session — the window rules, the column
mapping and the clock check all run against synthetic frames. A test that
needs a real session is reaching too far.

## Independent test

A script can replay the primary session and print the correct
lap/event/telemetry record without any AI service running. See
`scripts/replay_driver.py`.

## Definition of done

The demo can run completely offline from these assets, every
demo-critical timestamp is manually verified, and
`validate_telemetry_windows.py` exits 0.

## Outputs consumed downstream

- `../data/incident_manifest.json` — ground truth. See
  `contracts/fixtures/incident_manifest.sample.json` for the shape.
- `../data/audio/*.wav` — cut radio clips.
- `../data/telemetry/*.parquet` — per-incident telemetry windows. Shape:
  `contracts/telemetry_window.md`.
- `../data/telemetry/<session_id>/` — `session_meta.json` (clock origin),
  `laps_<DRV>.csv` (lap index), `windows_index.json` (lap roles and
  exclusion reasons per incident).
