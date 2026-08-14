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

## Reference race-radio audio clip

The team-radio audio clip played from the hero section and incident inspector
(`apps/web/public/audio/reference-radio-clip.mp3`) is a synthesized voice
(Microsoft Edge TTS, `en-GB-RyanNeural`) reading the INC-114 fixture's own
transcript ("Rear is moving on throttle, exiting Turn 7."). It replaced an
earlier real broadcast excerpt whose redistribution rights were never
confirmed. Fully original audio generated for this repository -- no
third-party broadcast rights apply. Labeled as synthesized in the UI
(`AudioPlayer.tsx`), not presented as an authentic recording.

## Hugging Face dataset (Workstream B development only)

`MikCil/f1-team-radio` (tagged CC-BY-4.0 by its uploader, though the dataset
card also credits Formula 1 for the underlying broadcasts) is used for
Workstream B's own development and benchmarking, never served to the public
site. See `services/radio_ai/CLAUDE.md` for the same caveat in context.

## Trademark notice

"Formula 1", team names, and driver names referenced throughout this project
are used descriptively, for an educational hackathon submission analyzing
publicly available race data and radio communications. ApexSignal is not
affiliated with, endorsed by, or sponsored by Formula 1, FIA, or any
constructor or team named in this repository.
