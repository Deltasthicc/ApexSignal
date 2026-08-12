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
