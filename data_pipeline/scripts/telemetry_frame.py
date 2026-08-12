"""Turn FastF1 lap telemetry into a contract-shaped window frame.

Separated from `build_telemetry_windows.py` so the column mapping, the
lap-relative distance rule and the window contract checks can be tested
with synthetic frames -- no FastF1, no network, no cached session.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from lap_window import WindowSpec
from window_schema import (
    FASTF1_COLUMN_MAP,
    LAP_ROLE_COLUMN,
    MIN_CLEAN_LAPS_BEFORE,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
)


def _to_seconds(values: pd.Series) -> pd.Series:
    """Timedelta (or already-numeric) -> float seconds."""
    if pd.api.types.is_timedelta64_dtype(values):
        return values.dt.total_seconds().astype("float64")
    return pd.to_numeric(values, errors="coerce").astype("float64")


def normalize_lap_frame(
    raw: pd.DataFrame,
    lap_number: int,
    *,
    driver: str | None = None,
    session_id: str | None = None,
) -> pd.DataFrame:
    """One lap of FastF1 telemetry -> canonical columns.

    Renames per `FASTF1_COLUMN_MAP`, casts `SessionTime` to float seconds,
    and **rebases `distance_m` to zero at the start of the lap**.

    That rebase is the point of this function. FastF1's `add_distance()`
    integrates from the start of whatever slice it is handed, so distance
    on a multi-lap slice is cumulative across the window. Lap-relative
    distance instead makes the same value mean the same piece of tarmac on
    every lap, which is what lets a consumer compare throttle pickup at
    T7 exit on the incident lap against the same metres on the baseline
    laps. Cumulative distance would force every consumer to re-derive this,
    and they would each derive it slightly differently.
    """
    frame = raw.rename(columns=FASTF1_COLUMN_MAP).copy()

    missing = [
        source
        for source, target in FASTF1_COLUMN_MAP.items()
        if target in ("session_time_s", "distance_m", "speed_kph", "throttle_pct", "brake")
        and target not in frame.columns
    ]
    if missing:
        raise KeyError(
            f"lap {lap_number}: telemetry is missing {missing}. "
            "Distance requires .add_distance() on the lap slice."
        )

    frame["session_time_s"] = _to_seconds(frame["session_time_s"])

    distance = pd.to_numeric(frame["distance_m"], errors="coerce").astype("float64")
    if distance.notna().any():
        distance = distance - distance.min()
    frame["distance_m"] = distance

    frame["lap"] = int(lap_number)
    frame["speed_kph"] = pd.to_numeric(frame["speed_kph"], errors="coerce").astype("float64")
    frame["throttle_pct"] = pd.to_numeric(frame["throttle_pct"], errors="coerce").astype("float64")

    brake = frame["brake"]
    if not pd.api.types.is_bool_dtype(brake):
        brake = pd.to_numeric(brake, errors="coerce").fillna(0) > 0
    frame["brake"] = brake.astype(bool)

    for name, value in (("driver", driver), ("session_id", session_id)):
        if value is not None:
            frame[name] = value

    for name in ("rpm", "gear"):
        if name in frame.columns:
            frame[name] = pd.to_numeric(frame[name], errors="coerce")

    keep = [c for c in REQUIRED_COLUMNS + OPTIONAL_COLUMNS if c in frame.columns]
    return frame.loc[:, keep].sort_values("session_time_s").reset_index(drop=True)


def apply_segment_map(
    frame: pd.DataFrame, segment_map: Mapping[str, Sequence[float]] | None
) -> pd.DataFrame:
    """Label each sample with a track segment from lap-relative distance.

    `segment_map` is `{"T7_EXIT": [1820.0, 2050.0], ...}` in metres from the
    start/finish line. Optional: with no map, `segment` is simply absent
    rather than guessed.
    """
    if not segment_map:
        return frame

    frame = frame.copy()
    frame["segment"] = pd.Series([None] * len(frame), dtype="object")
    for name, bounds in segment_map.items():
        start, end = float(bounds[0]), float(bounds[1])
        inside = frame["distance_m"].between(start, end, inclusive="left")
        frame.loc[inside, "segment"] = name
    return frame


def build_window_frame(
    lap_frames: Mapping[int, pd.DataFrame],
    spec: WindowSpec,
    *,
    segment_map: Mapping[str, Sequence[float]] | None = None,
) -> pd.DataFrame:
    """Concatenate normalized per-lap frames into one window, tagged by role."""
    missing = [lap for lap in spec.all_laps if lap not in lap_frames]
    if missing:
        raise KeyError(f"no telemetry supplied for lap(s) {missing}")

    parts = []
    for lap in spec.all_laps:
        part = lap_frames[lap].copy()
        part["lap"] = int(lap)
        part[LAP_ROLE_COLUMN] = spec.role_of(lap)
        parts.append(part)

    window = pd.concat(parts, ignore_index=True)
    window = window.sort_values(["lap", "session_time_s"]).reset_index(drop=True)
    window["lap"] = window["lap"].astype("int64")
    window = apply_segment_map(window, segment_map)

    ordered = [c for c in REQUIRED_COLUMNS if c in window.columns]
    ordered += [LAP_ROLE_COLUMN]
    ordered += [c for c in OPTIONAL_COLUMNS if c in window.columns]
    return window.loc[:, ordered]


# --- contract checks -----------------------------------------------------


def check_window_frame(
    window: pd.DataFrame, *, min_clean_before: int = MIN_CLEAN_LAPS_BEFORE
) -> list[str]:
    """Every way this window violates the contract. Empty list means valid."""
    problems: list[str] = []

    for column in REQUIRED_COLUMNS:
        if column not in window.columns:
            problems.append(f"missing required column '{column}'")
        elif window[column].isna().all():
            problems.append(f"required column '{column}' is entirely null")

    if LAP_ROLE_COLUMN not in window.columns:
        problems.append(f"missing '{LAP_ROLE_COLUMN}' column")

    # Everything below reads those columns, so a structural failure has to
    # stop here rather than raise a KeyError over the top of a clear report.
    if problems:
        return problems

    roles = window[["lap", LAP_ROLE_COLUMN]].drop_duplicates()

    laps_total = roles["lap"].nunique()
    if laps_total < 2:
        problems.append(
            f"window covers {laps_total} lap; a single-lap window cannot support "
            "baseline or lead-time features"
        )

    baseline_laps = roles.loc[roles[LAP_ROLE_COLUMN] == "BASELINE", "lap"].nunique()
    if baseline_laps < min_clean_before:
        problems.append(
            f"{baseline_laps} BASELINE lap(s), contract requires {min_clean_before}"
        )

    incident_laps = roles.loc[roles[LAP_ROLE_COLUMN] == "INCIDENT", "lap"].unique()
    if len(incident_laps) != 1:
        problems.append(f"expected exactly 1 INCIDENT lap, found {len(incident_laps)}")

    if len(incident_laps) == 1:
        incident_lap = int(incident_laps[0])
        if baseline_laps and roles.loc[
            roles[LAP_ROLE_COLUMN] == "BASELINE", "lap"
        ].max() >= incident_lap:
            problems.append("a BASELINE lap is at or after the INCIDENT lap")

    session_time = window["session_time_s"]
    if session_time.notna().any() and not session_time.dropna().is_monotonic_increasing:
        problems.append(
            "session_time_s is not non-decreasing across the window; laps are "
            "out of order or the clock origin is inconsistent"
        )

    return problems


def check_event_alignment(
    window: pd.DataFrame, event_time_ms: float, incident_lap: int
) -> list[str]:
    """Check the manifest event time really lands on the incident lap.

    This is the clock-origin test. If `event_time_ms` were measured from
    broadcast start, clip start, or lights-out instead of FastF1 session t0,
    it would still be a plausible-looking number -- and lead time computed
    against it would be wrong by a fixed offset with nothing to reveal it.
    Landing inside the incident lap's own session-time span is the cheapest
    evidence that both sides share a zero.
    """
    problems: list[str] = []
    event_s = float(event_time_ms) / 1000.0

    incident = window.loc[window["lap"] == incident_lap, "session_time_s"].dropna()
    if incident.empty:
        return [f"incident lap {incident_lap} has no telemetry in the window"]

    lap_start, lap_end = float(incident.min()), float(incident.max())
    if not (lap_start <= event_s <= lap_end):
        window_start = float(window["session_time_s"].min())
        window_end = float(window["session_time_s"].max())
        problems.append(
            f"event_time_ms={event_time_ms} (={event_s:.3f}s) falls outside "
            f"incident lap {incident_lap} [{lap_start:.3f}s, {lap_end:.3f}s]. "
            f"Window spans [{window_start:.3f}s, {window_end:.3f}s]. "
            "Most likely the manifest time is on a different clock origin than "
            "the telemetry -- see window_schema.CLOCK_ORIGIN."
        )

    return problems
