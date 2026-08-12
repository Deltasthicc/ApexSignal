"""Contract tests for Workstream A telemetry windows.

Three properties are load-bearing and each has a failure mode that produces
plausible output rather than an error:

  coverage  a one-lap window makes every baseline feature return
            INSUFFICIENT_DATA forever
  columns   a renamed or computed column silently changes what a consumer
            thinks it is reading
  clock     a manifest time on a different origin than the telemetry gives
            a lead time that is wrong by a constant, with nothing to show it

All offline. No FastF1, no network, no cached session.
"""

from __future__ import annotations

import pandas as pd
import pytest

from lap_window import (
    InsufficientBaselineError,
    LapRecord,
    clean_lap_exclusions,
    is_clean_lap,
    select_window_laps,
)
from telemetry_frame import (
    build_window_frame,
    check_event_alignment,
    check_window_frame,
    normalize_lap_frame,
)
from window_schema import (
    FASTF1_COLUMN_MAP,
    LAP_ROLE_COLUMN,
    MIN_CLEAN_LAPS_BEFORE,
    REQUIRED_COLUMNS,
)

LAP_DURATION_S = 90.0


def lap_records(specs: dict[int, dict]) -> list[LapRecord]:
    """Build a lap table; each lap starts where the previous one ended."""
    records = []
    for index, number in enumerate(sorted(specs)):
        start = index * LAP_DURATION_S
        records.append(
            LapRecord(lap=number, start_s=start, end_s=start + LAP_DURATION_S, **specs[number])
        )
    return records


def clean(count: int, first: int = 1) -> dict[int, dict]:
    return {first + offset: {} for offset in range(count)}


# --- clean-lap rules -----------------------------------------------------


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"pitted_in": True}, "PIT_IN_LAP"),
        ({"pitted_out": True}, "PIT_OUT_LAP"),
        ({"deleted": True}, "DELETED"),
        ({"is_accurate": False}, "NOT_ACCURATE"),
        ({"track_status": "14"}, "TRACK_STATUS_14"),
        ({"track_status": ""}, "NO_TRACK_STATUS"),
        ({"has_telemetry": False}, "NO_TELEMETRY"),
    ],
)
def test_dirty_laps_are_excluded_with_a_stated_reason(overrides, expected):
    lap = LapRecord(lap=10, start_s=0.0, end_s=90.0, **overrides)
    assert not is_clean_lap(lap)
    assert expected in clean_lap_exclusions(lap)


def test_a_green_flag_lap_with_telemetry_is_clean():
    assert is_clean_lap(LapRecord(lap=10, start_s=0.0, end_s=90.0))


def test_every_exclusion_reason_is_reported_not_just_the_first():
    lap = LapRecord(lap=10, start_s=0.0, end_s=90.0, pitted_in=True, track_status="4")
    reasons = clean_lap_exclusions(lap)
    assert "PIT_IN_LAP" in reasons and "TRACK_STATUS_4" in reasons


# --- coverage ------------------------------------------------------------


def test_window_covers_incident_lap_plus_three_clean_laps_before():
    spec = select_window_laps(lap_records(clean(10)), incident_lap=5)

    assert spec.incident_lap == 5
    assert spec.baseline_laps == (2, 3, 4)
    assert len(spec.baseline_laps) >= MIN_CLEAN_LAPS_BEFORE
    assert len(spec.all_laps) > 1, "a single-lap window cannot support baseline features"


def test_window_reaches_further_back_when_pit_and_safety_car_laps_intervene():
    specs = clean(10)
    specs[5] = {"pitted_in": True}
    specs[4] = {"track_status": "4"}

    spec = select_window_laps(lap_records(specs), incident_lap=6)

    # Three *clean* laps, not three raw laps. Laps 5 and 4 are unusable as a
    # reference but stay in the span so the window is contiguous in time.
    assert spec.baseline_laps == (1, 2, 3)
    assert set(spec.context_laps) == {4, 5}
    assert spec.all_laps[: len(spec.baseline_laps) + 3] == (1, 2, 3, 4, 5, 6)


def test_dirty_laps_do_not_count_toward_the_baseline_requirement():
    specs = clean(10)
    specs[5] = {"pitted_in": True}
    specs[4] = {"track_status": "4"}

    spec = select_window_laps(lap_records(specs), incident_lap=6)

    assert len(spec.baseline_laps) == MIN_CLEAN_LAPS_BEFORE
    assert not set(spec.baseline_laps) & {4, 5}
    assert spec.span_start_lap == min(spec.baseline_laps)


def test_insufficient_clean_history_fails_loudly_and_names_the_laps():
    specs = {1: {"pitted_out": True}, 2: {"track_status": "4"}, 3: {}, 4: {}}

    with pytest.raises(InsufficientBaselineError) as excinfo:
        select_window_laps(lap_records(specs), incident_lap=4)

    message = str(excinfo.value)
    assert "needs 3" in message
    assert "PIT_OUT_LAP" in message and "TRACK_STATUS_4" in message


def test_window_carries_every_lap_after_the_incident_by_default():
    spec = select_window_laps(lap_records(clean(12)), incident_lap=5)

    assert spec.post_laps == (6, 7, 8, 9, 10, 11, 12)
    assert spec.span_end_lap == 12


def test_post_laps_respect_the_replay_end_and_an_explicit_cap():
    records = lap_records(clean(20))

    assert select_window_laps(records, incident_lap=5, replay_end_lap=9).post_laps == (6, 7, 8, 9)
    assert select_window_laps(records, incident_lap=5, max_post_laps=2).post_laps == (6, 7)


def test_roles_cover_every_lap_in_the_window():
    spec = select_window_laps(lap_records(clean(12)), incident_lap=5)

    roles = {lap: spec.role_of(lap) for lap in spec.all_laps}
    assert roles[5] == "INCIDENT"
    assert all(roles[lap] == "BASELINE" for lap in spec.baseline_laps)
    assert all(roles[lap] == "POST" for lap in spec.post_laps)


# --- columns -------------------------------------------------------------


def test_required_columns_are_direct_fastf1_renames_not_computations():
    """Every required column maps straight off a FastF1 column.

    `lap` is the exception: it is the lap number the frame was sliced by.
    If anything else ever needs deriving, that is a design change, not an
    implementation detail.
    """
    derived_from_fastf1 = set(FASTF1_COLUMN_MAP.values())
    assert set(REQUIRED_COLUMNS) - derived_from_fastf1 == {"lap"}


def test_normalisation_produces_exactly_the_contract_columns(fastf1_lap_frame):
    frame = normalize_lap_frame(fastf1_lap_frame(start_s=0.0), 7, driver="VER", session_id="S")

    for column in REQUIRED_COLUMNS:
        assert column in frame.columns, column
        assert frame[column].notna().any(), f"{column} is entirely null"
    assert (frame["lap"] == 7).all()
    assert frame["driver"].eq("VER").all()


def test_session_time_becomes_float_seconds(fastf1_lap_frame):
    frame = normalize_lap_frame(fastf1_lap_frame(start_s=1234.5, duration_s=90.0), 7)

    assert frame["session_time_s"].dtype == "float64"
    assert frame["session_time_s"].min() == pytest.approx(1234.5)
    assert frame["session_time_s"].max() == pytest.approx(1324.5)


def test_distance_is_rebased_to_zero_at_the_start_of_each_lap(fastf1_lap_frame):
    """The property that makes cross-lap comparison possible at all.

    FastF1's add_distance() integrates from the start of the slice, so on a
    multi-lap window distance keeps climbing. Rebasing per lap means the
    same distance_m is the same piece of track on every lap, which is what
    a baseline comparison at T7 exit depends on.
    """
    raw = fastf1_lap_frame(start_s=900.0, distance_offset=45_000.0)

    frame = normalize_lap_frame(raw, 10)

    assert frame["distance_m"].min() == pytest.approx(0.0)
    assert frame["distance_m"].max() == pytest.approx(5000.0)


def test_every_lap_in_a_window_shares_one_distance_origin(lap_series):
    """Cumulative distance in, lap-relative distance out, for every lap."""
    spec = select_window_laps(lap_records(clean(6)), incident_lap=5)
    raw = lap_series(spec.all_laps, cumulative_distance=True)
    normalized = {lap: normalize_lap_frame(raw[lap], lap) for lap in spec.all_laps}

    window = build_window_frame(normalized, spec)

    per_lap_start = window.groupby("lap")["distance_m"].min()
    assert per_lap_start.eq(0.0).all()
    assert window.groupby("lap")["distance_m"].max().eq(5000.0).all()


def test_brake_normalises_to_bool_when_fastf1_hands_over_ints(fastf1_lap_frame):
    frame = normalize_lap_frame(fastf1_lap_frame(start_s=0.0, brake_as_int=True), 7)

    assert frame["brake"].dtype == "bool"
    assert frame["brake"].any() and not frame["brake"].all()


def test_missing_distance_is_an_error_not_a_guess(fastf1_lap_frame):
    raw = fastf1_lap_frame(start_s=0.0).drop(columns=["Distance"])

    with pytest.raises(KeyError, match="add_distance"):
        normalize_lap_frame(raw, 7)


# --- assembled windows ---------------------------------------------------


@pytest.fixture
def built_window(lap_series):
    """A valid window: incident lap 5, baseline 2-4, post 6-8."""
    records = lap_records(clean(8))
    spec = select_window_laps(records, incident_lap=5)
    raw = lap_series(spec.all_laps)
    normalized = {lap: normalize_lap_frame(raw[lap], lap, driver="VER") for lap in spec.all_laps}
    return spec, build_window_frame(normalized, spec)


def test_a_built_window_satisfies_the_contract(built_window):
    _, window = built_window

    assert check_window_frame(window) == []
    assert window["lap"].nunique() == 7
    assert set(window[LAP_ROLE_COLUMN].unique()) == {"BASELINE", "INCIDENT", "POST"}


def test_a_built_window_is_ordered_by_session_time(built_window):
    _, window = built_window

    assert window["session_time_s"].is_monotonic_increasing


def test_a_single_lap_window_is_rejected(lap_series):
    """The exact failure this work exists to prevent."""
    raw = lap_series([5])
    only_incident = normalize_lap_frame(raw[5], 5)
    only_incident[LAP_ROLE_COLUMN] = "INCIDENT"

    problems = check_window_frame(only_incident)

    assert any("single-lap" in problem for problem in problems)
    assert any("BASELINE" in problem for problem in problems)


def test_a_window_with_too_few_baseline_laps_is_rejected(built_window):
    spec, window = built_window
    thinned = window[window["lap"] != spec.baseline_laps[0]]

    problems = check_window_frame(thinned)

    assert any("BASELINE" in problem and "requires 3" in problem for problem in problems)


def test_a_missing_required_column_is_rejected(built_window):
    _, window = built_window

    problems = check_window_frame(window.drop(columns=["throttle_pct"]))

    assert any("throttle_pct" in problem for problem in problems)


def test_an_all_null_required_column_is_rejected(built_window):
    _, window = built_window
    blanked = window.copy()
    blanked["speed_kph"] = pd.NA

    problems = check_window_frame(blanked)

    assert any("speed_kph" in problem and "null" in problem for problem in problems)


# --- clock origin --------------------------------------------------------


def test_an_event_time_on_the_incident_lap_passes(built_window):
    spec, window = built_window
    incident = window.loc[window["lap"] == spec.incident_lap, "session_time_s"]
    mid_lap_ms = float(incident.mean()) * 1000.0

    assert check_event_alignment(window, mid_lap_ms, spec.incident_lap) == []


def test_an_event_time_on_a_different_clock_origin_is_caught(built_window):
    """A manifest time measured from lights-out instead of session t0.

    The number is well-formed and lands inside the session, so nothing
    downstream would reject it -- lead time would just come out wrong by a
    constant offset on every incident.
    """
    spec, window = built_window
    incident = window.loc[window["lap"] == spec.incident_lap, "session_time_s"]
    lights_out_offset_s = 3600.0
    misaligned_ms = (float(incident.mean()) - lights_out_offset_s) * 1000.0

    problems = check_event_alignment(window, misaligned_ms, spec.incident_lap)

    assert problems
    assert "clock origin" in problems[0]


def test_an_event_time_one_lap_late_is_caught(built_window):
    """Off-by-one-lap is the alignment error a human is most likely to make."""
    spec, window = built_window
    next_lap = window.loc[window["lap"] == spec.incident_lap + 1, "session_time_s"]

    problems = check_event_alignment(window, float(next_lap.mean()) * 1000.0, spec.incident_lap)

    assert problems


def test_alignment_check_reports_rather_than_raises_when_the_lap_is_absent(built_window):
    _, window = built_window

    problems = check_event_alignment(window, 0.0, incident_lap=999)

    assert problems and "no telemetry" in problems[0]


# --- round trip ----------------------------------------------------------


def test_a_window_survives_parquet_round_trip(built_window, tmp_path):
    """Parquet is what downstream actually reads, so the contract has to
    hold after a write/read cycle, not only in memory."""
    spec, window = built_window
    path = tmp_path / "INC-TEST.parquet"
    window.to_parquet(path, index=False)

    reloaded = pd.read_parquet(path)

    assert check_window_frame(reloaded) == []
    assert reloaded["brake"].dtype == "bool"
    assert reloaded["session_time_s"].dtype == "float64"
    incident = reloaded.loc[reloaded["lap"] == spec.incident_lap, "session_time_s"]
    assert check_event_alignment(reloaded, float(incident.mean()) * 1000.0, spec.incident_lap) == []
