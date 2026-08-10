-- Incident metadata store for ECHO LAP retrieval and recurrence monitoring.
-- Created at runtime by services/core_api. Embeddings themselves live in
-- a separate FAISS index file, not in this table.

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    driver TEXT NOT NULL,
    event_time_ms INTEGER NOT NULL,
    lap INTEGER NOT NULL,
    segment TEXT NOT NULL,
    transcript TEXT NOT NULL,
    complaint_category TEXT NOT NULL,
    telemetry_window_path TEXT NOT NULL,
    embedding_index INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_incidents_segment ON incidents (segment);
CREATE INDEX IF NOT EXISTS idx_incidents_driver ON incidents (driver);

CREATE TABLE IF NOT EXISTS recurrence_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggering_incident_id TEXT NOT NULL,
    matched_incident_id TEXT NOT NULL,
    telemetry_similarity REAL NOT NULL,
    flagged_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_state TEXT NOT NULL DEFAULT 'PENDING',
    FOREIGN KEY (matched_incident_id) REFERENCES incidents (incident_id)
);
