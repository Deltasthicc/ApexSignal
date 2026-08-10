# storage — Workstream C

SQLite metadata store for incident memory. `incidents.db` is created
at runtime by `services/core_api` and is git-ignored; `schema.sql` is
the source of truth for its structure.

Embeddings and FAISS indices are cached alongside this store but are
also git-ignored (see root `.gitignore`); they are regenerated from
`data/incident_manifest.json`, not committed.
