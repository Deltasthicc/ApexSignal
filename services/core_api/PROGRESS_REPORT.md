# Workstream C — Progress Report

**Incident Memory, Telemetry Evidence & Core API**
Branch: `ws-c-evidence-memory` · Status as of this report: MVP scope
(charter §5.1 "must ship") complete and tested.

**162 tests passing** (`pytest` inside `services/core_api/`). Every
number below is produced by code in this repository and covered by a
test; nothing here is aspirational.

---

## 1. What is implemented and working

| Module | Purpose |
|---|---|
| `app/db.py` | SQLite incident store, `storage/schema.sql` applied verbatim |
| `app/config.py` | Every filesystem input the live pipeline reads, in one place |
| `app/pipeline.py` | Evidence fusion → `IncidentAssessment` |
| `app/ingest.py` | `python -m app.ingest` loads the manifest into SQLite |
| `app/main.py` | `/health`, `/v1/incidents/evaluate`, `/v1/incidents/{id}` |
| `evidence_memory/telemetry_fingerprint.py` | Distance-normalized fingerprints + channel similarity |
| `evidence_memory/embeddings.py` | MiniLM sentence embeddings (lazy-loaded) |
| `evidence_memory/retrieval.py` | ECHO LAP retrieval (cosine over in-memory list) |
| `evidence_memory/baseline.py` | Own-baseline deviation |
| `evidence_memory/lead_time.py` | Lead-time measurement |
| `evidence_memory/recurrence.py` | Recurrence state (synchronous) |
| `evidence_memory/synthetic.py` | Deterministic synthetic telemetry — **test scaffolding only** |

Test coverage by area: retrieval 23, recurrence 28, telemetry 19,
contract conformance 19, live end-to-end 18, baseline 18, lead time 13,
storage 13, real-model embeddings 9, scaffold 2.

### Charter §18 Definition of Done — Workstream C's portion only

| # | DoD item | C's status |
|---|---|---|
| 1 | Radio clip → transcript through the backend | **N/A to C** — Workstream B. C consumes the result. |
| 2 | Tone/arousal visible with uncertainty | **N/A to C** — B produces, D displays. C parses and passes through `tone_label`/`tone_score`/`tone_confidence` without consuming them. |
| 3 | Transcript mapped to a frozen complaint category | **N/A to C** (B classifies). C *enforces* it: the taxonomy is an enum, a junk category is rejected at the storage and contract boundary. |
| 4 | Event aligned to verified lap/segment + cached telemetry window | **DONE for C's half** — schema, store, manifest mapping, telemetry loading. **Blocked on A** for the "manually verified" half: no real manifest or telemetry exists yet. |
| 5 | At least one prior incident retrievable with semantic **and** telemetry evidence | **DONE.** `echo_match` returns `semantic_similarity` and `telemetry_similarity` as separate numbers. Proven end-to-end in `test_evaluate_live.py`. |
| 6 | At least one lead-time example computed, **or** correctly stated as unavailable | **DONE, with a caveat.** Both paths work and are tested. But the worked example runs on *synthetic* timestamps — no verified real timestamps exist yet. See §6. |
| 7 | No unverified "fault confirmed" / "lie detected" / "exact grip" claims | **DONE for C's outputs.** `human_message` and all match labels are checked against a banned-phrase list by test. D still owns its own copy. |
| 8 | One coherent incident view | **N/A to C** — Workstream D. |
| 9 | Judged path works without live FastF1/OpenF1/network | **DONE, conditionally.** Verified with `HF_HUB_OFFLINE=1`. **The MiniLM weights must be cached before the demo** — see §6, this is a live risk. |
| 10 | Degrades gracefully if The Mask / Field Context is off | **DONE.** `text_tone_disagreement` is optional and deliberately unused; a payload without it parses and evaluates identically. Tested. |

---

## 2. Input contract needed from **Workstream A**

`data_pipeline/README.md` promises "per-incident Parquet telemetry
windows" but specifies no columns, units, or lap coverage. Workstream C
defined a minimal shape to build against. **This is a proposal, not an
agreement — A must match it or tell C what to change.** Full detail in
`services/evidence_memory/README.md`.

### Required columns

| Column | Type | Units | Notes |
|---|---|---|---|
| `session_time_s` | float | seconds | Since session start |
| `lap` | int | — | Lap the sample belongs to |
| `distance_m` | float | metres | Distance along the lap; increasing within a lap |
| `speed_kph` | float | km/h | FastF1 `Speed` as-is |
| `throttle_pct` | float | 0–100 | FastF1 `Throttle` as-is |
| `brake` | bool / 0-1 | — | FastF1 `Brake` as-is |

Optional, used when present and never fabricated: `driver`,
`session_id`, `segment`, `rpm`, `gear`. `segment` is strongly
recommended — without it, per-segment slicing falls back to the whole
window.

All six map 1:1 onto FastF1's native columns; A should not have to
compute anything new.

### ⚠️ Two requests that change A's export

**(a) A window must span several laps at the same segment, not one lap.**
The incident lap, ≥3 clean laps before it, and as many after as the
replay covers.

With a single lap per file, `baseline_evidence.status` can only ever be
`INSUFFICIENT_DATA` and `driver_warning_lead_time_s` can only ever be
`null` — own-baseline needs prior laps, lead time needs subsequent ones.
The charter §19 demo narrative does not work. This is the single highest
-impact item on this list.

**(b) `session_time_s` and the manifest's `event_time_ms` must share a
clock origin.** Lead time subtracts across those two sources. Different
origins produce a plausible-looking number that is silently wrong and
undetectable from the data. Any origin is fine; it must be one origin,
and written down.

### Also useful, not blocking

Lap-validity / track-status flags would let C exclude traffic and
yellow-flag laps properly instead of relying on the persistence
heuristic in §4.

### Manifest field-name mismatch (handled, no action needed)

The manifest fixture uses `sector_or_corner` / `verified_transcript` /
`complaint_label`; `storage/schema.sql` uses `segment` / `transcript` /
`complaint_category`. Both are frozen, so C did not touch either — the
mapping lives in `IncidentRecord.from_manifest_entry` and is tested.
Manifest-only fields (`tyre_compound`, `tyre_age_laps`, `lap_delta_s`,
`verification_notes`) are **not stored**: `schema.sql` has no column for
them. If retrieval should use tyre context later, that is a schema
change and a contract conversation.

---

## 3. Input contract from **Workstream B** — confirmed, one gap

**`RadioAnalysisOutput` is consumed exactly as frozen** in
`contracts/api_contract.md`. `app/models.py` mirrors
`contracts/schemas/radio_analysis_output.schema.json` field for field,
and `test_contract_conformance.py` fails if the two ever drift.

- All five required fields parsed and validated.
- `complaint_category` accepts `null` per contract.
- `text_tone_disagreement` accepted and **deliberately not consumed** —
  The Mask is post-core (§5) and its cut rule must break nothing.
- `tone_label` / `tone_score` / `tone_confidence` are parsed but not used
  by the evidence pipeline. Tone is a display concern (D) in the MVP; C
  does not let acoustic arousal influence any evidence number, which
  would edge toward the psychological inference the charter forbids.

### ⚠️ Gap: where B's output lands is not defined anywhere

The contract specifies the *shape* of `RadioAnalysisOutput` but not
where a consumer reads it from. C's independent test forbids depending
on a running `radio_ai`, so C reads **`{incident_id}.json` files from
`CORE_API_RADIO_ANALYSIS_DIR`** (default `data/radio_analysis/`).

**B needs to either write there, or tell C where they write.** This is
the only unresolved integration point between B and C.

### Ambiguity worth a decision

`complaint_category` may be `null` (radio that is not a complaint), but
`IncidentAssessment.reported_phenomenon` has **no** null option. So a
non-complaint radio message cannot produce an `IncidentAssessment` at
all. C currently returns **HTTP 422** with an explanatory message rather
than inventing a phenomenon or defaulting to `MECHANICAL_OTHER`.
Defaulting would be dishonest; if D needs a renderable response for
non-complaint radio, that needs a contract change.

---

## 4. Assumptions the team should sanity-check

Everything here is a judgement call C made where the charter or contract
was underspecified. **All are single named constants in one place.**

### A1 — Retrieval gate: same category **plus** cosine ≥ 0.40

The suggested 0.6 threshold was implemented, tested against the real
model, and **failed**. Measured over 23 realistic F1 phrasings, 247
pairs:

| | median | p95 | max |
|---|---|---|---|
| Same complaint category | 0.382 | 0.594 | 0.618 |
| Different categories | 0.213 | 0.438 | 0.683 |

At 0.6, only **5.4%** of genuine repeats are retrieved. Worse, the
distributions overlap structurally:

```
0.429  "Rear is moving on throttle." vs "The front is washing out under braking."    <- DIFFERENT complaint
0.422  "Rear is moving on throttle." vs "The rear stepped out again on corner exit." <- SAME complaint
```

A different complaint outranks a genuine repeat. **No cosine cut fixes
this**, so the gate is two independent conditions: same complaint
category (B's classifier does the precision work) **and** cosine ≥ 0.40
(set for recall, above the cross-category median 0.213 and p75 0.301).

Calibrated on clean hand-written phrasings, **not real ASR output**,
which will be noisier. **Re-run the calibration once B has real
transcripts.** `test_embeddings_real_model.py` guards both numbers, and
one test fails if cosine ever *does* separate the categories — at which
point the category gate can be revisited.

### A2 — "Observable performance change" = 3 robust sigmas, 2 consecutive laps

A lap qualifies when its segment time exceeds the driver's own pre-call
median by more than 3 MAD-based sigmas of their own spread (floored at
0.05 s), **and** the deviation holds for 2 consecutive laps.

MAD rather than standard deviation so one outlier lap cannot inflate the
threshold. The persistence rule is the cheapest available defence
against traffic and yellow-flag laps; with lap-validity flags from A it
could be relaxed. Full method in `README.md`.

### A3 — Throttle pickup = first point at 50% throttle

50% is clear of trailing-throttle noise around brake release and below
full power, so it lands on the ramp. `throttle_pickup_delta_pct` is the
shift in that point as a percentage of **segment length**, sign-flipped
so **negative = later to power**. Segment length as denominator (not
baseline pickup distance) so a pickup near the segment start cannot make
the percentage explode.

### A4 — `telemetry_similarity` is a comparability check, not severity

Measured on synthetic traces:

```
clean vs clean, same corner         1.0000
clean vs DETERIORATED, same corner  0.9920   <- 0.008 apart
same corner vs a DIFFERENT corner   0.7265
```

Fingerprint similarity separates **corners** with a wide margin and
barely separates a deteriorated lap from a clean one. That is by design
— the fingerprint normalizes by distance and standardizes channels so
shape comparison ignores magnitude; magnitude is `baseline.py`'s job.

**So `telemetry_similarity` answers "are these comparable?", not "how
badly is the car behaving?"** The recurrence threshold (0.90) sits in
the wide gap between 0.73 and 0.99 and is deliberately not tuned to the
narrow clean/deteriorated gap, which this metric cannot resolve.

> **Workstream D: do not render `telemetry_similarity` as severity or
> as a progress bar implying "how bad".** It is a comparability score.

### A5 — `CONFIRMED_BY_RADIO` requires wording **and** a prior report

Since retrieval gates on category (A1), *every* `echo_match` already
shares a category — so category alone would fire `CONFIRMED_BY_RADIO` on
every match and badly over-claim. C requires both the driver's own
repeat wording **and** a stored prior incident of that phenomenon.
Without the wording it is C's inference dressed up as the driver's
statement; without a prior there is nothing to point at when a judge
asks "a recurrence of what?"

Repeat detection is a plain keyword list, not a model — readable in ten
seconds. `"say again"` / `"come again"` are stripped first: ubiquitous
in real team radio, and they mean the opposite.

### A6 — The baseline is *recent*, so a long deterioration normalises away

Once a deterioration has persisted for most of the 5-lap baseline
window, it becomes the baseline and reads as `NO_DEVIATION`. This is the
intended meaning of "recent personal baseline" — a driver who has
adapted is genuinely no longer deviating from their current self — but
it means `BEHAVIOR_CONSISTENT` is only reachable within a few laps of
onset. Lead time is unaffected (it anchors to pre-call laps). Pinned by
test so it cannot change silently.

### A7 — `INSUFFICIENT_DATA` forces `0.0` into the two delta fields

The schema requires numbers with no null option. `status` sits alongside
carrying the caveat. **D should render on `status`, not on the numbers.**

### A8 — A match with no comparable telemetry is not reported

`telemetry_similarity` is required, `number`, 0–1 — no null option. When
telemetry is unavailable there is no honest value: `0.0` renders as "no
resemblance", a claim about the car rather than an admission of missing
data. C returns `echo_match: null` with a distinct reason. This is
contract-legal but discards real semantic evidence. It does not bite
with current data (telemetry always present) and would bite if A ships
incidents without windows.

---

## 5. Deliberately simplified vs. the full charter

These are intentional MVP scope decisions, not unfinished work.

### FAISS → cosine over an in-memory list

The corpus is 15–25 incidents. A brute-force scan is microseconds and
has no index to build, persist, or keep in sync with SQLite. FAISS earns
its complexity around 10⁵ vectors — four orders of magnitude away.
`faiss-cpu` remains in `requirements.txt` for a later swap; the
retrieval interface would not change.

### Background recurrence monitor (Flow B) → synchronous check

Charter §6.1 describes a background process that scans new telemetry
against stored fingerprints independent of any radio event. **It is
cut.** `recurrence.py` evaluates the same evidence once, inside
`evaluate()`.

> **Honest consequence:** the system **cannot currently claim to surface
> a recurrence *before* the driver reports it again.** It characterises a
> recurrence at the moment a report arrives. Charter §6.1 calls the
> background flow "essential"; the MVP does not have it. **Demo
> narration must respect this.**

The `recurrence_flags` table from `schema.sql` is populated the same way
a background monitor would populate it, so adding one later is additive.

### The Mask (text–tone disagreement) → parsed, not consumed

Post-core feature (§5). Accepted in input, never influences an evidence
number. Removing it entirely breaks nothing — tested.

### Field Context → not built

Post-core feature (§5). No stub, no dead code.

### ECHO LAP stored fields → subset

Charter §9.4 lists tyre context and "subsequent performance outcome" as
stored fields. `storage/schema.sql` has no columns for them and C did
not redesign the frozen schema. Retrieval uses transcript embedding,
category, segment, telemetry fingerprint, and lap context.

### `/v1/replay/frame` → implemented

Listed in `api_contract.md` and charter §11, not in the §5.1 must-ship
list, and not required by C's independent test, but Workstream D needed
it: both `services/core_api/app/main.py` and `mock_server/server.py`
now serve it. This note previously said "not implemented"; it was
stale as of the presentation-readiness pass.

---

## 6. Risks

1. **The MiniLM weights must be cached before the demo.** First use
   downloads ~90 MB from Hugging Face. Verified working with
   `HF_HUB_OFFLINE=1` *after* caching. On a cold machine with no network,
   the live path fails. **Pre-warm on the demo machine** (see §7) — this
   directly threatens DoD item 9.
2. **No real data exists.** Everything is proven on synthetic telemetry.
   `data/telemetry/` and `data/incident_manifest.json` are empty/absent.
   The lead-time worked example uses synthetic timestamps — the demo
   number `90.0 s` is an artifact of the generator placing laps exactly
   90 s apart and **must not be quoted**.
3. **Threshold recalibration is pending real ASR text** (A1).
4. **The Dockerfile build context changed.** It previously built from
   `services/core_api/` and could never have contained
   `evidence_memory/`, `storage/schema.sql`, or `contracts/` — fixture
   mode would have 500'd in the image. It now builds from the repo root.
   **Workstream D: `deployment/` compose needs `context: .` with
   `dockerfile: services/core_api/Dockerfile`.**

---

## 7. Running this service locally

### Setup

```bash
cd services/core_api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Two dependencies were added to `requirements.txt`: `pyarrow` (Parquet
cannot be read without it) and `jsonschema` (tests validate output
against the frozen schema).

### Pre-warm the model cache — do this before any offline demo

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Run the tests

```bash
cd services/core_api && python -m pytest tests/ -v
```

Expect **162 passed**. The 9 real-model tests skip cleanly if the
weights are unavailable.

### Fixture mode (unchanged — Workstream D's path)

```bash
cd services/core_api && EVALUATE_MODE=fixture uvicorn app.main:app --reload --port 8001
```

```bash
curl -s -X POST "http://127.0.0.1:8001/v1/incidents/evaluate?incident_id=INC-031" | python -m json.tool
```

### Live mode against a real fixture incident

Requires: incidents in SQLite, a telemetry Parquet window per incident,
and a `RadioAnalysisOutput` JSON per incident. Until A and B produce
real assets, build a self-contained world with the synthetic generator:

```bash
cd services/core_api && python - <<'PY'
import json, pathlib, sys
sys.path.insert(0, '.')
import app
from app import db
from app.db import IncidentRecord
from evidence_memory import synthetic

root = pathlib.Path('/tmp/apexsignal_demo')
(root / 'data/telemetry').mkdir(parents=True, exist_ok=True)
(root / 'data/radio_analysis').mkdir(parents=True, exist_ok=True)

synthetic.write_window(synthetic.synthetic_window(laps=list(range(10, 21))),
                       root / 'data/telemetry/INC-017.parquet')
synthetic.write_window(synthetic.synthetic_window(laps=list(range(22, 33)),
                       degrade_from_lap=27, throttle_pickup_delay=0.10,
                       exit_speed_loss_kph=18.0),
                       root / 'data/telemetry/INC-031.parquet')

for iid, text in [('INC-017', 'Rear is moving on throttle.'),
                  ('INC-031', 'Same thing again, rear is loose out of seven.')]:
    (root / f'data/radio_analysis/{iid}.json').write_text(json.dumps({
        'incident_id': iid, 'transcript': text, 'tone_label': 'ELEVATED_AROUSAL',
        'tone_score': 0.73, 'tone_confidence': 0.61,
        'complaint_category': 'EXIT_TRACTION_REAR', 'category_confidence': 0.86}))

conn = db.connect(root / 'incidents.db')
db.insert_incidents(conn, [
    IncidentRecord(incident_id='INC-017', session_id='DEMO', driver='DEMO_DRIVER',
                   event_time_ms=14 * 90 * 1000, lap=14, segment='T7_EXIT',
                   transcript='Rear is moving on throttle.',
                   complaint_category='EXIT_TRACTION_REAR',
                   telemetry_window_path='data/telemetry/INC-017.parquet'),
    IncidentRecord(incident_id='INC-031', session_id='DEMO', driver='DEMO_DRIVER',
                   event_time_ms=26 * 90 * 1000, lap=26, segment='T7_EXIT',
                   transcript='Same thing again, rear is loose out of seven.',
                   complaint_category='EXIT_TRACTION_REAR',
                   telemetry_window_path='data/telemetry/INC-031.parquet'),
], replace=True)
conn.close()
print('demo world ready at', root)
PY
```

Then start the service in live mode:

```bash
cd services/core_api && EVALUATE_MODE=live CORE_API_DB_PATH=/tmp/apexsignal_demo/incidents.db CORE_API_RADIO_ANALYSIS_DIR=/tmp/apexsignal_demo/data/radio_analysis CORE_API_TELEMETRY_ROOT=/tmp/apexsignal_demo uvicorn app.main:app --port 8001
```

```bash
curl -s -X POST "http://127.0.0.1:8001/v1/incidents/evaluate?incident_id=INC-031" | python -m json.tool
```

Actual output:

```json
{
    "incident_id": "INC-031",
    "lap": 26,
    "segment": "T7_EXIT",
    "reported_phenomenon": "EXIT_TRACTION_REAR",
    "baseline_evidence": {
        "throttle_pickup_delta_pct": 0.0,
        "sector_delta_s": 0.001,
        "status": "NO_DEVIATION"
    },
    "echo_match": {
        "incident_id": "INC-017",
        "semantic_similarity": 0.4967,
        "telemetry_similarity": 1.0,
        "same_segment": true,
        "label": "MODERATE_PROTOTYPE_MATCH"
    },
    "driver_warning_lead_time_s": 90.0,
    "recurrence_state": "CONFIRMED_BY_RADIO",
    "human_message": "Telemetry at this segment is within the driver's own recent baseline; no deviation measured. Resembles an earlier reported concern (INC-017) by prototype similarity. An observable performance change followed the radio call by 90.0s. The driver's message refers to a repeat."
}
```

`INC-017` (the first report, nothing before it) returns
`echo_match: null`, `driver_warning_lead_time_s: null`, and
`"No measurable lead-time established"` — the honest empty case.

> **Read this output carefully:** `NO_DEVIATION` **with** a positive lead
> time is not a miss. INC-031 is reported on lap 26; the deterioration
> begins on lap 27. At the moment of the call the car still looks normal
> — *which is exactly why there is a lead time*. The driver was ahead of
> the data. That is the product's thesis, and the strongest output it can
> produce.
>
> Note the frozen fixture pairs `BEHAVIOR_CONSISTENT` with a 42 s lead
> time — a different, also-valid situation where the driver reports after
> the change is already visible. **The demo should be clear about which
> of the two stories it is telling.**

### Once A and B ship real assets

```bash
cd services/core_api && python -m app.ingest      # manifest -> SQLite
EVALUATE_MODE=live uvicorn app.main:app --port 8001
```

Defaults in `.env.example` point at `data/incident_manifest.json`,
`data/radio_analysis/`, and manifest-relative telemetry paths — no
overrides needed once those exist.

---

## 8. Files owned and touched

Inside Workstream C's folders only (`services/core_api/`,
`services/evidence_memory/`, `storage/`). **No file under `contracts/`,
`data/`, `data_pipeline/`, `services/radio_ai/`, `apps/`, `mock_server/`
or `deployment/` was modified.** A test walks C's source tree and fails
on any import of another workstream's code.

`storage/schema.sql` was used exactly as written — not modified, not
redesigned. A test asserts the live table structure still matches it.
