# ApexSignal project status

## Presentation build: complete

| Capability | Status | Evidence |
|---|---|---|
| Public responsive UI | Shipped | Vercel production deployment |
| Public API-backed replay | Shipped | Render health + replay endpoints |
| Offline/resilient fallback | Shipped | Embedded copy of identical contract records |
| Incident timeline and inspector | Shipped | Three reference cases, including a negative control |
| Pit-wall before/after comparison | Shipped | Interactive toggle |
| Baseline, recurrence, and lead-time views | Shipped | Contract-backed incident assessments |
| Circuit atlas | Shipped | 25 source-derived centerlines |
| Service contracts and tests | Shipped | JSON Schema, FastAPI and pipeline test suites |
| Presentation narrative | Shipped | `docs/PRESENTATION_RUNBOOK.md` |

## Production-research expansion: not represented as shipped

These are not blockers for presenting the deterministic MVP, but they are
required before describing ApexSignal as a live, production race-operations
system:

1. License and curate incident-specific radio plus aligned FastF1 telemetry.
2. Re-run the Gate 7 holdout (`services/radio_ai/HOLDOUT_REPORT.md`) on the
   final calibrated classifier threshold -- the untouched 20-clip holdout
   itself is done, but that report predates the Gate 6 recalibration.
3. Improve complaint classification beyond the recorded Gate 6 macro-F1.
4. Deploy `radio_ai` on GPU-capable infrastructure and the live `core_api` with
   persistent storage/FAISS.
5. Run a larger multi-session evaluation and document false positives,
   false negatives, latency, and calibration.

The public site intentionally does not expose a pretend upload/transcription
control. It presents the part of the system that is reproducible and verified.
