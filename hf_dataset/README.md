# hf_dataset — Workstream A (optional)

Optional Hugging Face `datasets` artifact wrapping the curated incident
corpus, so the team has a reproducible, citable data artifact and a
Hugging Face Hub presence for this component of the submission.

Only build this after `data/incident_manifest.json` is frozen and
verified. Do not publish partial or unverified incidents.

Planned contents:

- `dataset_card.md` — Hugging Face dataset card (source, license,
  limitations, PII/consent notes for any real radio audio used).
- `loading_script.py` or a `datasets.load_dataset`-compatible folder
  layout, pointing at `../data/incident_manifest.json` and the
  associated audio/telemetry files.

Skip entirely if time is short; it is P1, not required for the judged
demo per the charter.
