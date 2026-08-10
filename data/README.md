# data — Workstream A

Curated, manually verified demo assets. Not for direct editing by other
workstreams; produced by `../data_pipeline/scripts/`.

- `incident_manifest.json` — ground truth for every curated incident.
  Populated by `data_pipeline/scripts/build_incident_manifest.py`.
  Shape matches `contracts/fixtures/incident_manifest.sample.json`.
- `audio/` — cut radio clips referenced by the manifest. Git-ignored
  except for `.gitkeep`; audio ships via a release asset or is
  regenerated locally, not committed to source control.
- `telemetry/` — per-incident Parquet telemetry windows. Same policy
  as `audio/`.

No UI number should exist unless it traces back to a manifest entry or
a documented model output. See the charter, section 7.4.
