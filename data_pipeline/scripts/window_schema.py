"""Canonical schema for Workstream A telemetry windows.

Single source of truth shared by the window builder, the validator, the
offline tests and `contracts/telemetry_window.md`. Renaming anything here
is a cross-workstream contract change -- read that document first.
"""

from __future__ import annotations

# --- clock ---------------------------------------------------------------

CLOCK_ORIGIN = "FASTF1_SESSION_TIME"
"""The one legal time origin in this project.

`session_time_s` in every telemetry window and `event_time_ms` in every
incident manifest entry are both measured in seconds from FastF1's session
t0 (`fastf1.core.Session.t0_date`). They are the same clock with the same
zero. Lead-time arithmetic is only meaningful because of that; a window
built on any other origin produces a lead time that looks plausible and is
silently wrong, which is exactly the failure this constant exists to stop.

The absolute UTC instant of t0 is written to `session_meta.json` so the
origin stays reconstructible after the fact.
"""

SESSION_META_FILENAME = "session_meta.json"

# --- window shape --------------------------------------------------------

MIN_CLEAN_LAPS_BEFORE = 3
"""Minimum *clean* laps preceding the incident lap that a window must carry.

Baseline features compare the incident lap against the driver's own normal.
Fewer than this and `baseline_evidence.status` can only ever be
INSUFFICIENT_DATA. Clean laps are counted, not raw laps: a window may span
more than three preceding laps if pit or safety-car laps sit in between.
"""

# --- columns -------------------------------------------------------------

REQUIRED_COLUMNS: tuple[str, ...] = (
    "session_time_s",
    "lap",
    "distance_m",
    "speed_kph",
    "throttle_pct",
    "brake",
)

OPTIONAL_COLUMNS: tuple[str, ...] = (
    "driver",
    "session_id",
    "segment",
    "rpm",
    "gear",
)

LAP_ROLE_COLUMN = "lap_role"
LAP_ROLES: tuple[str, ...] = ("BASELINE", "INCIDENT", "CONTEXT", "POST")
"""Why each lap is in the window.

BASELINE  clean pre-incident lap, safe to average into a reference
INCIDENT  the lap the radio call belongs to
CONTEXT   pre-incident lap inside the span that failed the clean test;
          carried so the window stays contiguous, never averaged
POST      everything after the incident lap, for the recurrence monitor

Consumers must filter to BASELINE before computing a reference. Without
this column a consumer would have to re-derive cleanliness from data the
window does not carry.
"""

WINDOW_COLUMNS: tuple[str, ...] = REQUIRED_COLUMNS + (LAP_ROLE_COLUMN,)

# --- FastF1 mapping ------------------------------------------------------

FASTF1_COLUMN_MAP: dict[str, str] = {
    "SessionTime": "session_time_s",
    "Distance": "distance_m",
    "Speed": "speed_kph",
    "Throttle": "throttle_pct",
    "Brake": "brake",
    "RPM": "rpm",
    "nGear": "gear",
}
"""Every required column is a direct FastF1 rename plus a unit cast.

`SessionTime` is a timedelta and becomes float seconds; `Distance` comes
from `add_distance()` applied per lap, so it is lap-relative (see
`telemetry_frame.normalize_lap_frame`). Nothing here is computed from a
model or an assumption.
"""
