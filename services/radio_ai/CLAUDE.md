# CLAUDE.md — Workstream B (radio_ai) session handoff

This file exists so a fresh Claude Code session on the GPU box can pick
up exactly where the previous session left off, without re-deriving
context from scratch. Read this whole file before doing anything.

---

## Read this first: this is not your machine

This session runs on a remote Arch Linux GPU box (`ssh.ddesai.dev`,
accessed via a Cloudflare Access tunnel) that Shashwat has SSH access
to but does not own. Act like a guest, not a root user.

- **Scope everything to `~/ApexSignal/`.** Do not read, write, or
  explore `~/authorized_keys`, `~/F1_Simulator_OpenENV`, or
  `~/opstwin-work` — those belong to other work on this box, not this
  project. Never read or modify `~/authorized_keys` under any
  circumstance; it's an SSH security file.
- **No `sudo`, no system package changes, without explicitly asking
  the user first and getting a yes in that exact session.** A prior
  session already triggered a `pacman` conflict (`ffmpeg` vs.
  `ffmpeg-obs`) and the user resolved it themselves by removing
  `ffmpeg-obs` — that changed system state on a machine that isn't
  ours to change. Don't repeat that pattern proactively.
- **Never print, log, or commit the contents of `.env`.** It has a
  real Hugging Face read token in it. It's gitignored — keep it that
  way. If you ever see a real token value in a file that isn't `.env`
  (e.g. `.env.example`), that's a leak — flag it immediately and fix
  it, don't just proceed.
- **`git push` to `github.com/Deltasthicc/ApexSignal` is fine** — that's
  Shashwat's own repo, unrelated to who owns this physical machine.
  Destructive git operations (force-push, hard reset) still need
  explicit sign-off same as anywhere else.
- This workstream (`services/radio_ai/`) is the only part of the repo
  you should be editing. See `../../CONTRIBUTING.md` for the full
  ownership map before touching anything under `services/core_api/`,
  `apps/web/`, `data_pipeline/`, etc.

---

## What ApexSignal is

A hackathon submission (AI Race Month — GrandPrix Hackathon @ Paytm,
Problem Statement 1: "The Silent Co-Driver") that turns F1 driver radio
into structured incident memory connected to telemetry evidence. Full
design context: `../../docs/PROJECT_CHARTER.md` and
`../../docs/problem_statement.md`. Short version: transcribe radio,
score acoustic tone/arousal, classify the complaint into a fixed
5-category taxonomy, connect it to telemetry, retrieve similar past
incidents, measure driver-warning lead time. Never claims lie
detection, diagnosis, or confirmed mechanical faults — only evidence
and labeled model scores.

## What this workstream (B) builds

One stateless FastAPI service: audio in, `RadioAnalysisOutput` JSON
out. Full contract: `../../contracts/api_contract.md` and
`../../contracts/schemas/radio_analysis_output.schema.json`. Three
other workstreams (data/telemetry, incident memory/core API,
frontend/UI) are separate people's territory — don't cross into them.

---

## Current state of this machine, as of this handoff

- GPU: NVIDIA RTX 5090, 32GB VRAM, driver reports CUDA 13.3.
  `torch.cuda.is_available()` returns `True`. Plenty of headroom for
  this pipeline.
- Repo cloned at `~/ApexSignal`, branch `ws-b-radio-ai` checked out,
  at commit `b5c4b5a` ("fix(radio_ai): add missing sys.path insert to
  shortlist/extract scripts"). Run `git pull origin ws-b-radio-ai`
  first thing to make sure nothing newer landed after this handoff.
- Python virtualenv at `services/radio_ai/.venv`. **It does not
  auto-activate across SSH reconnects** — this has already caused one
  `ModuleNotFoundError` this session. Check for `(.venv)` at the start
  of the shell prompt before running anything that imports a package;
  if it's missing, `source .venv/bin/activate` from
  `~/ApexSignal/services/radio_ai/`.
- `torch==2.13.0` / `torchaudio==2.11.0+cu130` are installed — these
  are a minor-version mismatch (torchaudio normally ships in lockstep
  with torch), but `import torchaudio; torchaudio.functional` was
  manually verified working on this box. Don't assume every torchaudio
  code path is safe just because that smoke test passed; keep an eye
  out if something audio-decode-related misbehaves later.
- `services/radio_ai/.env` exists with `ANALYZE_MODE=live` and a real
  `HF_TOKEN` already set. Don't touch it beyond what the task needs.
- `services/radio_ai/candidates.csv` exists: 4,297 rows from
  `scripts/shortlist_candidate_clips.py`'s keyword matching against
  `MikCil/f1-team-radio`. This is deliberately loose/noisy — keyword
  hits include real false positives (e.g. strategy chatter that
  happens to contain the word "engine," or a driver commenting on a
  *different* car's damage). A CSV row matching a category is a
  candidate to go listen to, not a verified label.
- `data/audio/` (repo root, i.e. `~/ApexSignal/data/audio/`) has 20 real
  extracted clips from `scripts/extract_audio_clips.py`, all from the
  2018 Australian and Bahrain Grands Prix. **Nobody has listened to any
  of them yet.** Their printed transcripts are Cohere-generated (from
  the dataset itself), not verified by a human.

## What actually happened this session (chronological)

1. Repo skeleton + all four workstream branches were scaffolded and
   pushed from a separate local session (not this machine).
2. A separate research pass (GPT, reviewed and verified against the
   live Hugging Face Hub API) picked a concrete model stack for this
   workstream, replacing the charter's placeholder models. Every model
   ID was checked for existence/gating/license and pinned to a commit
   SHA — see `app/config.py` and `README.md`'s stack table for the
   full list and reasoning (short version: VoiceCLAP over audEERING's
   model because it's commercially licensed and has a fatigue head;
   zero-shot NLI over embedding prototypes for the classifier because
   the taxonomy definitions become the classifier input directly).
3. The four pipeline modules (`app/audio_preprocessing.py`, `app/asr.py`,
   `app/tone.py`, `app/complaint_classifier.py`) were implemented and
   wired into `app/main.py` behind `ANALYZE_MODE=live`. Fixture mode
   (the default) was untouched and its tests still pass.
4. Two real bugs were found and fixed: `python-multipart` was missing
   for FastAPI form handling (now in `requirements.txt`), and
   `scripts/shortlist_candidate_clips.py` +
   `scripts/extract_audio_clips.py` were both missing a `sys.path`
   insert that `scripts/benchmark_day1.py` already had — this was only
   caught by actually running them on this GPU box, not in the
   sandbox that wrote them.
5. On this machine: dependencies installed, GPU confirmed working,
   `.env` configured, the shortlist script run (4,297 candidates), and
   20 real clips extracted. **`scripts/benchmark_day1.py` — the script
   that actually runs the live ASR/tone/classifier pipeline — has not
   been run yet.** That's the next concrete step.

## What is NOT verified yet — be honest about this

Only *existence*, *gating*, *license*, and *config metadata* for every
model/dataset were checked against the live HF API. Nobody has
measured actual accuracy, latency, or tone-model reliability on real
F1 audio on any machine, including this one. Do not represent anything
in `VALIDATION_GATES.md` as passed until real numbers are in that file.

## The plan, in order

See `VALIDATION_GATES.md` for the full numeric criteria — this is the
short version:

1. **Human listens to the 20 clips in `data/audio/`** (or a subset),
   labels each blind as CALM / ELEVATED_AROUSAL / FATIGUED / AMBIGUOUS
   plus a 1-5 arousal rating, and manually corrects the transcript by
   ear. This step cannot be automated or done by an AI session — if
   asked to do it, say so and wait for the human labels.
2. **Run `python scripts/benchmark_day1.py <chosen clips>`** — first
   real live-mode run, will download several GB of model weights on
   first call. Compare its output against the human labels from step 1.
3. **Fill in `VALIDATION_GATES.md`** with real numbers from step 2.
4. **Mask decision**: `ENABLE_TEXT_TONE_DISAGREEMENT` in `.env` stays
   `false` unless gates 2, 3, and 4 in `VALIDATION_GATES.md` all pass.
   Don't flip it on a hunch.
5. **Day 2**: benchmark the complaint classifier on 60-90 manually
   labeled transcripts (not yet done), decide base vs. xsmall DeBERTa.
6. **Day 3+**: once Workstreams C/D start consuming real (non-fixture)
   output, freeze model revisions — don't let `ANALYZE_MODE=live`
   silently pick up a new model version underneath a working demo.

## One more data caveat

`MikCil/f1-team-radio` is tagged CC-BY-4.0 by its uploader, but the
same dataset card credits Formula 1 for the original broadcasts —
those are two different claims. Fine to use for development and Day-1
benchmarking. Do NOT treat it as cleared for the actual public demo
clip without an explicit provenance decision from Shashwat — that's a
human sign-off, not something to default into.

## Where to look before asking again

- Full stack + reasoning: `README.md`
- Every model ID, pinned revision, threshold: `app/config.py`
- The exact contract this service must produce: `../../contracts/api_contract.md`
- Numeric pass/fail criteria: `VALIDATION_GATES.md`
- Ownership boundaries across the whole repo: `../../CONTRIBUTING.md`
