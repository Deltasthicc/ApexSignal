# Third-party notices

## Circuit geometry

The circuit centerline coordinates compiled into
`apps/web/src/data/circuits.ts` are derived from the
[TUMFTM racetrack-database](https://github.com/TUMFTM/racetrack-database),
licensed under the GNU Lesser General Public License v3.0.

ApexSignal stores only uniformly scaled, downsampled centerlines for browser
visualization. The source circuit proportions are preserved; the coordinates
are not stretched or redrawn by hand. Run `scripts/build_circuit_atlas.py`
against a checkout of the upstream repository to regenerate the file.

The circuit descriptions and location labels are original ApexSignal copy.

## Historical race results (background replay)

The lap-by-lap driver order, grid, and finishing positions compiled into
`apps/web/src/data/raceReplays.json` are sourced from the
[Jolpica-F1](https://github.com/jolpica/jolpica-f1) API (an Ergast-compatible
successor), which redistributes historical Formula 1 results data. This is
results/timing data, not broadcast footage or audio. The 21 bundled races and
their source article links are listed in `raceReplays.json` itself.

## FastF1

Telemetry curation in `data_pipeline/` uses the
[FastF1](https://github.com/theOehrly/Fast-F1) Python library (MIT licensed),
which itself fetches session data from timing feeds. See FastF1's own terms
for restrictions on redistributing raw timing data at scale; ApexSignal only
ever ships small, per-incident telemetry windows, not bulk session exports.

## Reference race-radio audio clip (Incident Inspector fixture cards only)

The team-radio audio clip played from the incident inspector's three fixture
cards (`INC-114`/`117`/`145`) (`apps/web/public/audio/reference-radio-clip.mp3`)
is a synthesized voice (Microsoft Edge TTS, `en-GB-RyanNeural`) reading the
INC-114 fixture's own transcript ("Rear is moving on throttle, exiting Turn
7."). Fully original audio -- no third-party broadcast rights apply. Kept
synthesized here specifically because these three cards are tied to an
*authored, fictional* lap/telemetry narrative (`REFERENCE_REPLAY_2026`,
`CAR44`) with no real broadcast counterpart -- playing real audio that says
different words than the displayed transcript would be a real inconsistency,
not an improvement. Labeled as synthesized in the UI (`AudioPlayer.tsx`).

## Real broadcast clips used elsewhere on the public site (Hero, Live Pipeline Walkthrough, Tone Comparison, Human-in-the-Loop)

**Status changed 2026-08-15, by explicit team direction, superseding the
research below.** Real `MikCil/f1-team-radio` broadcast clips (2018-2025,
multiple real drivers) are now used publicly in `LivePipelineDemo.tsx`,
`ToneComparison.tsx`, `HumanLoopSection.tsx`, and the `Hero.tsx` ambient
clip -- audio files live in `apps/web/public/audio/live_demo/`.

**The legal research below was not wrong and is kept for the record, not
deleted.** Two independent passes concluded no real F1 team radio clip
clears a defensible bar for public redistribution:

- Formula 1's own published content guidelines state audio/audiovisual
  content "should not be used" beyond platform-native sharing/embedding;
  the educational-use carve-out they describe explicitly excludes "public
  postings such as YouTube, websites and social media."
- No F1 team publishes team radio audio under an open reuse license.
- `MikCil/f1-team-radio`'s CC-BY-4.0 tag cannot legally cover the underlying
  broadcast audio -- the dataset card credits Formula 1 as the source
  without documenting permission to redistribute.
- Indian fair dealing (Copyright Act 1957, ss. 52/39) has no seconds-based
  safe harbor and does not survive public web deployment ("communication to
  the public").

**The decision to proceed anyway was made knowingly, not by working around
this section.** Team judgment (2026-08-15): for a hackathon demo, real audio
communicates the product better than TTS, and the practical enforcement risk
against a small non-commercial student project is judged low enough to
accept. This is a real, live legal exposure if Formula One Management (or a
team/driver whose broadcast is used) ever objects -- not a hypothetical
closed out by this paragraph. If this project is taken further than the
hackathon (continued public deployment, fundraising, wider distribution),
revisit this decision for real before that happens; don't let "we decided
this once under demo deadline pressure" quietly become permanent policy.

## Hugging Face dataset

`MikCil/f1-team-radio` (tagged CC-BY-4.0 by its uploader, though the dataset
card also credits Formula 1 for the underlying broadcasts) is used both for
Workstream B's own development/benchmarking (`services/radio_ai/`) and,
as of 2026-08-15, for real clips served on the public site -- see above.

## Trademark notice

"Formula 1", team names, and driver names referenced throughout this project
are used descriptively, for an educational hackathon submission analyzing
publicly available race data and radio communications. ApexSignal is not
affiliated with, endorsed by, or sponsored by Formula 1, FIA, or any
constructor or team named in this repository.
