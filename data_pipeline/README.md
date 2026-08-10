# data_pipeline — Workstream A

Mission: produce the authoritative, verified race dataset every other
workstream consumes without making live network calls.

## Owns

This directory, plus `../data/` and `../hf_dataset/`. Nothing else.

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
  skipped.

## Session-selection gate

A session is acceptable only if all of the following hold:

1. FastF1 telemetry for the selected driver is complete enough for
   speed/throttle/brake and lap/sector comparison.
2. At least two radio moments relate to a recurring or comparable
   concern.
3. The lap/time context can be verified manually from trustworthy
   commentary, timing data, or dataset timestamps.
4. The selected moments produce a coherent 90-120 second demo story.

Do not default to Spa 2021: it lacks normal green-flag race evolution,
which this project needs to show a baseline deviation.

## Independent test

A script can replay the primary session and print the correct
lap/event/telemetry record without any AI service running. See
`scripts/replay_driver.py`.

## Definition of done

The demo can run completely offline from these assets, and every
demo-critical timestamp is manually verified.

## Outputs consumed downstream

- `../data/incident_manifest.json` — ground truth. See
  `contracts/fixtures/incident_manifest.sample.json` for the shape.
- `../data/audio/*.wav` — cut radio clips.
- `../data/telemetry/*.parquet` — per-incident telemetry windows.
