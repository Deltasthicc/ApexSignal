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

Each module should be independently unit-testable against synthetic
fixtures; none of them should require a running FastAPI server.
