# ApexSignal — submission checklist

Actionable, in priority order. Checked items are verified true as of
this session (backend tests, live deployments, CI) — re-verify anything
checked here if meaningful time passes before you actually submit,
deployments and free-tier services can drift.

## Required artifacts

- [x] Public, working demo URL — https://apex-signal-sigma.vercel.app
      (verified live, correct build, zero console errors)
- [x] Source code, public repository — https://github.com/Deltasthicc/ApexSignal
- [x] README with setup instructions, tech stack, and an honest
      shipped-vs-roadmap boundary (`README.md`, `docs/PROJECT_STATUS.md`)
- [x] License — MIT, `LICENSE`
- [ ] Deck — outline drafted (`docs/pitch/deck_outline.md`), still
      needs to actually be built in Slides/PowerPoint/Keynote with real
      screenshots dropped in (see "Screenshots to capture" below)
- [ ] Demo video — script drafted (`docs/pitch/demo_script.md`), still
      needs recording, editing, and uploading unlisted
- [ ] Confirm the hackathon's actual required format for the above two
      (slide count limit? video length limit? specific upload
      platform?) — this session assumed no hard limit; if the real
      rules differ, adjust the outline/script to match before building
      final versions

## Screenshots to capture (for the deck, all from the live site)

- [ ] Hero section, full width, race replay background visible
- [ ] Circuit atlas, one card focused/hovered
- [ ] Incident inspector, Lap 17 selected, Gold Incident card visible
- [ ] Pit Wall View toggled on (before-state)
- [ ] Lap 45 negative-control result (NO_DEVIATION, no match)
- [ ] Mobile viewport, no horizontal overflow, standings hidden

Every screenshot must come from an actual run of the live/local app —
never mock or hand-edit a screenshot to show a number the app didn't
really produce.

## Technical readiness (already verified this session)

- [x] 209/209 backend tests passing (`python scripts/run_test_suites.py`)
- [x] Frontend build, lint, and TypeScript check all clean
- [x] CI green end-to-end on GitHub Actions (manually verified; note
      push-triggered runs have an unresolved intermittent issue — see
      "Known gaps" below)
- [x] `npm audit` and `pip-audit` both report zero vulnerabilities
- [x] Render replay API live and serving current data
- [x] Hugging Face Space live (static, embedded fixture data) as an
      offline-safe backup independent of Render

## Known gaps — say these out loud, don't let a judge find them first

- [ ] Complaint classifier macro-F1 is 0.393 against an 0.80 target
      (honest, documented in `VALIDATION_GATES.md` gate 6 — this is a
      talking point about rigor, not something to hide)
- [ ] No real curated incident has been processed through the live
      (non-fixture) pipeline yet — `data/incident_manifest.json` does
      not exist; the 3 demo incidents are hand-authored, contract-
      validated reference fixtures
- [ ] The public Render/Vercel/HF deployments all serve the fixture
      replay, not the real Whisper/VoiceCLAP/DeBERTa pipeline — this is
      a deliberate, honestly-labeled scoping choice (see
      `docs/PRESENTATION_RUNBOOK.md` "claims not to use"), not an
      oversight, but it needs to be said plainly if asked
- [ ] GitHub Actions push-triggered runs don't reliably fire even
      though the workflow itself is fixed and passes on manual trigger
      (`workflow_dispatch`) — use manual triggering to get a green run
      before judges look at the Actions tab, and don't claim automatic
      CI-on-push is fully working until this is actually root-caused
- [ ] Reference audio clip is synthesized (TTS), not a real broadcast
      recording — labeled honestly in the UI and `THIRD_PARTY_NOTICES.md`,
      not something to walk back to an "authentic" framing without an
      actually-cleared source (see the audio-rights research prompt if
      one was run)

## Final pass before submitting

- [ ] Fill in team member names/contact info wherever the submission
      form asks for it
- [ ] Re-run the "five-minute preflight" in `docs/PRESENTATION_RUNBOOK.md`
      from a private/incognito browser window, on a different device
      than the one used for development if possible
- [ ] Re-check both public URLs (Vercel, Render health) and the HF
      Space one more time within an hour of the actual submission
      deadline — free-tier services can sleep/wake unpredictably
- [ ] Confirm the demo video plays without a login prompt (upload
      unlisted, not private)
- [ ] Have all four team members read `docs/PRESENTATION_RUNBOOK.md`'s
      "claims to use" / "claims not to use" section before Q&A — a
      single team member overclaiming in the room undoes the whole
      "honestly scoped" pitch
