# ApexSignal — Full Project Audit and Completion Checklist

**Audit date:** 14 August 2026  
**Repository:** [Deltasthicc/ApexSignal](https://github.com/Deltasthicc/ApexSignal)  
**Frontend:** [apex-signal-sigma.vercel.app](https://apex-signal-sigma.vercel.app/)  
**Replay API:** [apexsignal-mock-server.onrender.com](https://apexsignal-mock-server.onrender.com/health)

## Executive verdict

ApexSignal is currently a strong, working presentation demo, but it is not yet a complete live AI product.

| Area | Current state |
|---|---|
| Public frontend | ✅ Live and interactive on Vercel |
| Public backend | ⚠️ Live, but fixture/replay-only on Render |
| Race-map background | ⚠️ Animated and data-backed, but contains one wrong-track bug and mobile readability issues |
| Real radio AI | ❌ Implemented in code but not deployed or runnable in the current environment |
| Real telemetry pipeline | ❌ Code exists, but the actual telemetry/audio corpus is absent |
| ECHO LAP/evidence engine | ⚠️ Tested extensively with synthetic data; not running publicly against real incidents |
| Hugging Face | ❌ No publicly accessible Space or dataset could be verified |
| Automated tests | ✅ 204 passed, 5 skipped |
| Frontend build | ✅ Passes |
| Frontend lint | ❌ Not configured |
| CI on `main` | ❌ Does not run |
| Security dependency audit | ❌ Five high-severity dependency findings |
| Presentation readiness | ⚠️ Usable, but several visible/data-integrity issues should be fixed first |
| Full production readiness | ❌ Significant data, ML, deployment, validation, and operational work remains |

No files, commits, branches, deployments, or settings were changed during this audit.

---

## 1. What is working now

### Public deployment

- The Vercel site returns HTTP 200 and loads successfully.
- The Render service returns:

```json
{
  "status": "ok",
  "evaluate_mode": "replay",
  "service": "apexsignal_replay_api"
}
```

- Render successfully serves the replay manifest, individual replay frames, radio-analysis fixtures, and incident-assessment fixtures.
- The three public incidents load consistently:
  - `INC-114` — Lap 14, insufficient baseline
  - `INC-117` — Lap 17, recurrence and telemetry deviation
  - `INC-145` — Lap 45, negative/no-deviation example
- Invalid replay routes return 404 correctly.
- CORS permits the Vercel frontend to call Render.
- The frontend has an embedded fallback, so it remains interactive if Render is unavailable.

### Live frontend checks completed

Desktop and mobile were tested directly on the deployed website.

Working features:

- All major sections load.
- Navigation anchors resolve.
- Replay Play and Stop work.
- Selecting Lap 14, Lap 17, and Lap 45 updates the inspector.
- Pit-wall/raw-view toggle changes the interface.
- The actual MP3 loads and plays; it is approximately 12.7 seconds.
- No browser console errors or warnings appeared.
- Mobile at 390×844 has no horizontal overflow.
- The selected incident data and recurrence badges render correctly.
- The negative Lap 45 example correctly shows no historical match and no lead time.
- Static embedded fixtures exactly match the contract fixture files.

### Backend and pipeline tests

| Suite | Result |
|---|---:|
| `core_api` | 157 passed, 5 skipped |
| `radio_ai` | 3 passed |
| `data_pipeline` | 44 passed |
| **Total** | **204 passed, 5 skipped** |
| Python compilation | Pass |
| TypeScript `tsc --noEmit` | Pass |
| Next.js production build | Pass |

The five skipped tests require the real `sentence-transformers` model dependency.

---

## 2. Critical issues to fix before presenting

### P0 — Hungarian race uses the wrong map

The replay dataset uses the key `Hungaroring`, but the circuit atlas uses `Budapest`.

The rendering code cannot find `Hungaroring`, so it silently falls back to the first circuit—Albert Park, Melbourne. This means the 2021 Hungarian Grand Prix can currently appear on the Australian circuit.

Required action:

- Make the replay and circuit keys identical.
- Add a data-validation test that rejects any replay whose `circuitKey` is absent from the circuit atlas.

### P0 — The 189.4-second lead-time story is inconsistent

The live algorithm defines lead time as:

> First observable performance change after the current radio call, minus the current radio-event time.

However, the public fixture/UI appears to use the time between two radio incidents:

- `INC-114`: 840,000 ms
- `INC-117`: 1,029,400 ms
- Difference: exactly 189.4 seconds

The UI presents:

- Radio warning: Lap 14
- Measurable deterioration: Lap 17
- Lead time: 189.4 seconds

But the `INC-117` assessment says the performance change followed the `INC-117` radio call by 189.4 seconds. Those are different definitions.

The team must choose one definition:

1. First driver warning → later measurable deterioration, or
2. Current radio event → subsequent deterioration.

Then align the contract, algorithm, fixture data, human message, tests, and UI. The contract should also expose `first_change_lap` if the UI claims a particular deterioration lap.

### P0 — The website makes claims stronger than the backend allows

The frontend says:

> “same complaint, confirmed by telemetry”

The backend documentation explicitly says `BEHAVIOR_CONSISTENT` is not proof of a fault or confirmation that the complaint is correct.

Suggested replacement:

> “Same reported concern; telemetry behavior is consistent with the report.”

The timeline also says:

> “No incidents flagged outside the marked laps”

Only three curated fixture incidents are displayed. There is no complete session inference output proving every other lap was examined.

Suggested replacement:

> “No additional incidents are included in this reference replay.”

### P0 — Race background still overwrites content on mobile

The background is rendered as a fixed `z-40` element above the main page and uses `mix-blend-screen`. During mobile testing, the standings tower crossed the incident-inspector heading and body text.

Required action:

- Put the race replay behind the foreground content.
- Give the actual site content a higher stacking layer.
- Hide or heavily condense the standings panel on small screens.
- Add a dark readability scrim between the background and content.
- Keep the track apparent while lowering its effective opacity.

### P0 — Upgrade the vulnerable frontend dependency chain

`npm audit` reports five high-severity dependency findings affecting:

- `next@14.2.35`
- Next’s bundled `postcss`
- `glob@10.3.10`
- `eslint-config-next`
- `@next/eslint-plugin-next`

Some advisories relate to features ApexSignal may not use, but the deployed app still directly depends on an affected Next.js version. Upgrade Next.js and its matching ESLint package, then rerun the build, browser checks, and `npm audit`.

---

## 3. Race maps and animation audit

### What is working

- 25 circuit centerlines are included.
- Geometry is sourced from `TUMFTM/racetrack-database`, not randomly drawn.
- 21 historical race replays are bundled.
- The combined replay dataset contains 1,284 laps.
- Every replay contains race metadata, driver entries, grid and finishing positions, per-lap order, and source URLs.
- Each race is compressed into 104 seconds.
- A 3.2-second opacity transition occurs before changing circuits.
- Selection is randomized.
- The immediately previous replay is remembered and avoided during the next selection.
- Driver dots move around the circuit.
- The standings order changes with recorded lap data.
- Retired cars stop being rendered after their completed-lap count.
- All 21 linked race articles returned HTTP 200.
- The replay does not depend on historical-data APIs at runtime because the data is bundled.

### What remains incomplete

- Fix the `Hungaroring`/`Budapest` key mismatch.
- Only the first eight positions have driver codes beside their map dots. The standings tower labels all entries, but the map does not label every point.
- Historic grids do not always contain exactly 20 cars. The site should say “all race entries” rather than promise exactly 20 racers for every era.
- The moving positions are per-lap order plus interpolated spacing—not GPS coordinates or exact on-track gaps. The site currently discloses this correctly.
- “Most famous race” is subjective. The project has short race rationales but no documented selection methodology.
- There is no automated validation for circuit keys, lap counts, duplicate drivers, invalid lap-order IDs, URLs, or circuit/replay pairing.
- Reduced-motion CSS stops visual animations, but the JavaScript race timer continues updating. The replay should pause or reduce work when reduced motion is requested.

---

## 4. Frontend work still remaining

### Testing and code quality

- No frontend unit tests.
- No automated interaction or E2E tests.
- No Playwright, Cypress, Jest, or Vitest configuration.
- `npm run lint` is not operational because ESLint was never configured.
- Thirty-seven buttons do not explicitly declare `type="button"`. This is not currently breaking anything because the page has no forms, but it should be cleaned up.
- No route-level `error.tsx` or global error boundary.
- Remote API failures are silently replaced with embedded fixtures. This is resilient but can hide backend failures.
- The page can display “API REPLAY” even when an individual request has fallen back to local embedded data.

### Accessibility and presentation polish

- Manual navigation and mobile layout mostly work.
- A formal automated accessibility audit has not been run.
- The moving background needs stronger reduced-motion handling.
- The standings overlap foreground content on mobile.
- Some background text remains visually competitive with the main content.
- The Google font is externally loaded; offline styling may differ.
- Missing or unverified polish items:
  - Dedicated favicon
  - Open Graph preview image
  - `robots.txt`
  - Sitemap
  - Social-share verification
  - Lighthouse/performance audit

### Audio presentation

The deployed MP3 is a real file and plays correctly. The UI honestly says it is a reference input rather than the recording associated with the selected replay incident.

Remaining issues:

- Every incident plays the same audio clip.
- Fixture paths reference files such as `data/audio/INC-114.wav`, but those files do not exist.
- The MP3 is not connected to the incident’s displayed transcript, lap, driver, or telemetry.
- Redistribution rights and source attribution for the clip are not documented.
- “Team-provided original recording” should remain only if the team owns it or has distribution permission.

Vapi and Omnidimension are not currently used. Neither is necessary merely to play authentic clips. They would help with conversational voice-agent orchestration, not replace licensed race audio and a validated ASR pipeline.

---

## 5. Backend and AI status

### Public Render backend

The deployed backend is intentionally the lightweight fixture server, not the real ApexSignal AI backend.

Therefore, the public site does not currently perform:

- Audio transcription
- Acoustic tone inference
- Complaint classification
- Telemetry-baseline calculation
- Similar-incident embedding retrieval
- Live recurrence detection
- Real lead-time calculation
- Persistent incident storage

It serves three prebuilt reference records. This is acceptable for a deterministic hackathon presentation if clearly labeled, but it must not be described as the deployed real-time AI system.

### Real `core_api`

The real backend is significantly more developed than the deployment suggests:

- Contract validation exists.
- SQLite storage exists.
- Baseline comparison exists.
- Lead-time calculation exists.
- Incident retrieval exists.
- Recurrence logic exists.
- Synthetic integration tests are extensive.

Remaining limitations:

- It is not publicly deployed.
- It has no real incident corpus to process.
- Retrieval uses in-memory cosine similarity rather than a production FAISS index.
- Recurrence is evaluated only when a new radio report arrives; there is no independent continuous telemetry monitor.
- “Field Context” is not implemented.
- No authentication, rate limiting, durable public database, or persistence deployment exists.
- Observability is limited to service logs with no alerting integration.

### Real `radio_ai`

The live radio path exists in code, but the current machine lacks its main dependencies:

- `faster_whisper`
- `torch`
- `torchaudio`
- `torchcodec`
- `transformers`
- `sentence_transformers`
- `faiss`
- `scipy`

Other issues:

- A missing audio file in live mode likely produces an internal-server error instead of a clean 400/422 response.
- The service has no CORS middleware, so a browser calling it directly would be blocked unless proxied.
- `/health` does not expose model readiness or fixture/live mode.
- The text-tone disagreement flag must stay disabled; enabling it raises `NotImplementedError`.

---

## 6. Actual data is missing

The following required project artifacts are absent:

- `data/incident_manifest.json`
- Curated incident audio in `data/audio/`
- Aligned telemetry Parquet files in `data/telemetry/`
- FastF1 cache
- Runtime `storage/incidents.db`
- Final embeddings/index
- A usable Hugging Face dataset artifact

The actual input directories currently contain only placeholder `.gitkeep` files.

The 20 files in `data/radio_analysis/` are intermediate placeholder analyses based on source filename stems. They are not connected to a completed `INC-xxx` manifest and cannot form a full live pipeline by themselves.

To run the real product, the team still needs to:

1. Choose and license the demo incidents.
2. Manually verify each transcript.
3. Align each clip to session, driver, lap, segment, and FastF1 session time.
4. Build `incident_manifest.json`.
5. Download and cache the matching FastF1 session.
6. Generate multi-lap telemetry windows.
7. Run the radio model on each clip.
8. Store the outputs under the real incident IDs.
9. Validate every generated artifact.
10. Ingest incidents into the database.
11. Build the retrieval memory/index.
12. Run end-to-end live evaluations.
13. Deploy the real backend on suitable compute.

---

## 7. Model validation status

### ASR gate failed

| Metric | Required | Result |
|---|---:|---:|
| Normalized WER | ≤20% | **20.28% — fail** |
| Meaning-critical word accuracy | ≥90% | **84.21% — fail** |

The remaining misses include important words such as “front” and “tyres”.

### Complaint classifier gate failed

| Metric | Required | Result |
|---|---:|---:|
| Macro-F1 | ≥0.80 | **0.356 — fail** |
| `NO_COMPLAINT` F1 | ≥0.85 | **0.818 — fail** |

The labeling sample contains 58 usable clips, one below the target of at least 60. It is also heavily imbalanced:

- 44/58 are `NO_COMPLAINT`.
- There are zero valid `TYRE_GRIP_DEGRADATION` examples.
- The current classifier threshold is 0.15.

### Other incomplete model gates

- Human single-speaker verification is pending.
- Ten of twenty clips were flagged by a rough VAD-gap heuristic; this is not diarization.
- Fatigue detection has zero true-positive validation examples.
- Text-tone disagreement passed prerequisite numerical gates, but the feature itself is not implemented.
- Holdout documentation conflicts: one document says no untouched set remains, while another contains an unverified and stale report.
- The holdout report uses threshold 0.5, while the current classifier uses 0.15.

The holdout must be regenerated from a genuinely untouched, manually verified sample using the final model configuration.

---

## 8. Hugging Face status

A public Hugging Face deployment is not currently verifiable.

Checks performed:

- `huggingface-cli` is not installed or available locally.
- There is no Hugging Face Git remote.
- The repository contains a Dockerfile and Hugging Face-compatible README metadata.
- `hf_dataset/` contains only a README, not a published dataset.
- Requests to the expected Space and dataset API paths did not expose a public project.
- No searchable public ApexSignal Space or dataset was found.

If Hugging Face is mandatory, the team still needs to:

- Install/authenticate the Hugging Face CLI or use the website.
- Create a Docker Space.
- Push or connect the repository.
- Make the Space public if required.
- Wait for and verify a clean build.
- Test the Space while signed out.
- Save the final public URL.
- Confirm whether the submission requires a Space, dataset, model, or all three.
- Publish an appropriate dataset/model card with licensing and limitations.

---

## 9. Deployment and CI/CD gaps

### CI targets the wrong branch

The repository’s default branch is now `main`, but the GitHub Actions test workflow only runs on `integration/main`.

As a result, recent `main` commits have no automated test workflow runs.

Required workflow change:

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

CI should also use `npm ci` and run lint, TypeScript, build, frontend tests, backend tests, and an agreed security-audit policy.

### Docker Compose is not runnable out of the box

`docker compose config` failed because expected local environment files do not exist, including `services/core_api/.env`.

Additional issues:

- The Compose `version` field is obsolete.
- Documentation says `radio_ai` starts by default, but it is actually behind the optional `live` profile.
- The documentation and commands must be brought back into alignment.

### Reproducibility

- Python requirements use broad `>=` version ranges.
- No Python lockfile or hash-pinned dependency set exists.
- Model revisions are pinned, which is good.
- Python dependency/security auditing has not been run.
- Vercel CLI is not installed locally, so dashboard environment variables and deployment logs were not independently inspected through the CLI.

---

## 10. Security and legal readiness

### Security

The Vercel frontend has HSTS, but no explicit application-level headers were observed for:

- Content Security Policy
- `X-Content-Type-Options`
- Frame restrictions
- Referrer Policy
- Permissions Policy

The Render fixture API currently has:

- Wildcard CORS
- No authentication
- No application rate limiting
- No application-level abuse protection

This is acceptable for a short-term public demo but not a durable production API.

No tracked secrets were found. `.env` files, audio data, telemetry, and the SQLite database are ignored appropriately.

### Licensing and attribution

Already present:

- Repository MIT license
- LGPL attribution for circuit geometry

Still required:

- Audio source and redistribution-rights documentation
- Jolpica/Ergast data attribution and terms
- FastF1 data/library attribution
- Hugging Face source-dataset license
- Model licenses and model-card links
- Confirmation that every shipped audio file may legally be redistributed
- Formula 1 trademark/non-affiliation notice if appropriate

The current third-party notice covers the map geometry but not the complete audio, data, and model stack.

---

## 11. Documentation inconsistencies

The following records are stale or contradictory:

- README says 162 core tests pass; the current result is 157 passed and 5 skipped.
- The project-wide result is 204 passed and 5 skipped.
- `PROGRESS_REPORT.md` says `/v1/replay/frame` is not implemented, but it is implemented.
- Deployment README says `radio_ai` starts by default, but it is behind a Compose profile.
- Gate 7 says both “not run/no untouched set” and provides a stale holdout report.
- Root `.env.example` still mentions a radio API URL even though `core_api` reads radio results from disk.
- Core `.env.example` describes the radio-output location as unsettled, while later contracts treat it as settled.
- Evidence-memory documentation still describes telemetry contract sign-off as pending.
- `PROJECT_STATUS.md` says the presentation build is complete despite the wrong Hungarian map, mobile overlay, claim-language errors, failed lint, absent CI, and dependency advisories.

---

## 12. Recommended completion order

### Phase 1 — Fix before the next presentation

- [ ] Fix the `Hungaroring`/`Budapest` circuit-key mismatch.
- [ ] Resolve the 189.4-second lead-time definition.
- [ ] Remove “confirmed by telemetry”.
- [ ] Remove the unsupported “no incidents outside marked laps” claim.
- [ ] Move the race replay behind foreground content.
- [ ] Hide or condense standings on mobile.
- [ ] Add race-data validation tests.
- [ ] Configure ESLint.
- [ ] Make GitHub Actions run on `main`.
- [ ] Upgrade Next.js and resolve/review the dependency audit.
- [ ] Verify the public audio clip’s rights and attribution.
- [ ] Run a full signed-out presentation rehearsal.

### Phase 2 — Produce a defensible real AI demo

- [ ] Curate licensed incident audio.
- [ ] Build and validate the incident manifest.
- [ ] Generate aligned multi-lap telemetry windows.
- [ ] Install and run the real model stack.
- [ ] Improve the classifier beyond macro-F1 0.356.
- [ ] Improve ASR critical-word accuracy beyond 90%.
- [ ] Perform human speaker verification.
- [ ] Create a genuinely untouched holdout.
- [ ] Regenerate the holdout report with the final threshold.
- [ ] Connect real radio outputs to `core_api`.
- [ ] Validate lead-time results against actual telemetry.
- [ ] Add clean 4xx handling and CORS/proxying.
- [ ] Add automated live-pipeline E2E tests.

### Phase 3 — Deploy the real product

- [ ] Choose compute capable of running the radio models.
- [ ] Add persistent incident storage.
- [ ] Deploy `core_api` in live mode.
- [ ] Deploy or separately host `radio_ai`.
- [ ] Point Vercel at the real backend.
- [ ] Add authentication and rate limiting where necessary.
- [ ] Add model-readiness health checks.
- [ ] Add logs, monitoring, and alerts.
- [ ] Test backend cold starts.
- [ ] Test failure and fallback behavior.
- [ ] Publish and verify the Hugging Face Space/dataset if mandatory.

### Phase 4 — Final submission package

- [ ] Public Vercel URL
- [ ] Public Render/live-backend URL
- [ ] Public Hugging Face URL if required
- [ ] GitHub `main` commit SHA used for deployment
- [ ] Updated README with truthful architecture
- [ ] Final model metrics
- [ ] Dataset and model cards
- [ ] License and attribution bundle
- [ ] Architecture diagram
- [ ] Two-minute and five-minute demo scripts
- [ ] Offline fallback plan
- [ ] Screenshots/video backup
- [ ] Signed-out link verification on another device

---

## Bottom line for the team

The website is online and the fixture-backed presentation works. The source code contains a substantial synthetic-tested backend and an experimental radio-AI pipeline. However, the deployed site is not currently running that AI pipeline, the real incident dataset is missing, the key model gates have not passed, Hugging Face is not publicly verified, CI does not protect `main`, and several visible/data-integrity issues remain.

The fastest defensible path is:

1. Fix the P0 presentation bugs.
2. Clearly describe the public build as a **contract-validated historical replay demo**.
3. Do not claim that the public backend is processing live audio or real telemetry.
4. Build and validate one genuinely end-to-end real incident before expanding the corpus.

