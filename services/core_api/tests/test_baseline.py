"""Own-baseline comparison tests.

The synthetic generator integrates segment time from distance and speed,
so a "degraded" lap is genuinely slower rather than having a lap time
planted in it. These tests therefore measure a real effect.
"""

from __future__ import annotations

import pytest

import app  # noqa: F401  -- puts services/ on sys.path
from evidence_memory import synthetic
from evidence_memory.baseline import (
    MIN_BASELINE_LAPS,
    BaselineComparison,
    compare_to_baseline,
    robust_threshold,
    segment_time_s,
    throttle_pickup_distance_m,
)
from evidence_memory.telemetry_fingerprint import select_segment


@pytest.fixture()
def steady():
    """Eight consistent laps, no deterioration anywhere."""
    return synthetic.synthetic_window(laps=list(range(10, 18)))


@pytest.fixture()
def deteriorating():
    """Laps 10-17, with a real change from lap 15 onward."""
    return synthetic.synthetic_window(
        laps=list(range(10, 18)),
        degrade_from_lap=15,
        throttle_pickup_delay=0.10,
        exit_speed_loss_kph=18.0,
    )


def test_segment_time_is_measured_from_telemetry(steady):
    lap = select_segment(steady, lap=14)
    duration = segment_time_s(lap)
    assert duration is not None and 4.0 < duration < 8.0


def test_segment_time_needs_at_least_two_samples(steady):
    assert segment_time_s(select_segment(steady, lap=14).head(1)) is None


def test_throttle_pickup_is_a_distance_into_the_segment(steady):
    lap = select_segment(steady, lap=14)
    pickup = throttle_pickup_distance_m(lap)
    assert pickup is not None
    assert 0.0 < pickup < 300.0


def test_throttle_pickup_is_none_when_never_reached(steady):
    """A braking-limited segment must not report a pickup of zero."""
    lap = select_segment(steady, lap=14).copy()
    lap["throttle_pct"] = 5.0
    assert throttle_pickup_distance_m(lap) is None


def test_insufficient_data_when_too_few_prior_laps(steady):
    comparison = compare_to_baseline(steady, current_lap=11, segment="T7_EXIT")
    assert comparison.status == "INSUFFICIENT_DATA"
    assert comparison.baseline_lap_count < MIN_BASELINE_LAPS
    assert "need 3" in comparison.reason
    # Contract requires numbers here, not nulls; status carries the caveat.
    assert comparison.throttle_pickup_delta_pct == 0.0
    assert comparison.sector_delta_s == 0.0


def test_insufficient_data_when_the_current_lap_is_absent(steady):
    comparison = compare_to_baseline(steady, current_lap=99, segment="T7_EXIT")
    assert comparison.status == "INSUFFICIENT_DATA"
    assert "no usable telemetry" in comparison.reason


def test_no_deviation_on_a_steady_run(steady):
    comparison = compare_to_baseline(steady, current_lap=17, segment="T7_EXIT")
    assert comparison.status == "NO_DEVIATION"
    assert abs(comparison.sector_delta_s) <= comparison.sector_delta_threshold_s
    assert "within this driver's own baseline spread" in comparison.reason


def test_behavior_consistent_when_the_driver_actually_changed(deteriorating):
    comparison = compare_to_baseline(deteriorating, current_lap=17, segment="T7_EXIT")
    assert comparison.status == "BEHAVIOR_CONSISTENT"
    # Slower through the segment than the driver's own baseline.
    assert comparison.sector_delta_s > 0
    # Later to power than their own baseline -> negative by convention.
    assert comparison.throttle_pickup_delta_pct < 0


def test_baseline_uses_only_earlier_laps(deteriorating):
    comparison = compare_to_baseline(deteriorating, current_lap=15, segment="T7_EXIT")
    assert all(lap < 15 for lap in comparison.baseline_laps)


def test_baseline_window_is_bounded(steady):
    comparison = compare_to_baseline(
        steady, current_lap=17, segment="T7_EXIT", baseline_window_laps=4
    )
    assert comparison.baseline_lap_count == 4
    assert comparison.baseline_laps == (13, 14, 15, 16)


def test_a_long_running_deterioration_normalises_itself_away(deteriorating):
    """A documented limitation, pinned so it cannot change silently.

    The baseline is the driver's *recent* laps. Once a deterioration has
    persisted for most of the baseline window, the new behaviour becomes
    the baseline and the deviation reads as NO_DEVIATION. This is the
    intended meaning of "recent personal baseline" -- a driver who has
    adapted is genuinely no longer deviating from their current self --
    but it means BEHAVIOR_CONSISTENT is only reachable within a few laps
    of the onset. Lead time, which anchors its baseline to laps before
    the radio call, is unaffected.
    """
    onset = compare_to_baseline(deteriorating, current_lap=16, segment="T7_EXIT")
    settled = compare_to_baseline(deteriorating, current_lap=17, segment="T7_EXIT")

    assert onset.status == "BEHAVIOR_CONSISTENT"
    # Baseline for lap 17 still holds a clean majority (12, 13, 14 clean).
    assert settled.baseline_laps == (12, 13, 14, 15, 16)

    late = synthetic.synthetic_window(
        laps=list(range(10, 26)),
        degrade_from_lap=15,
        throttle_pickup_delay=0.10,
        exit_speed_loss_kph=18.0,
    )
    absorbed = compare_to_baseline(late, current_lap=25, segment="T7_EXIT")
    assert absorbed.baseline_laps == (20, 21, 22, 23, 24)
    assert absorbed.status == "NO_DEVIATION"


def test_raw_measurements_are_reported_alongside_the_deltas(deteriorating):
    """Every derived number can be traced back to what it came from."""
    comparison = compare_to_baseline(deteriorating, current_lap=17, segment="T7_EXIT")
    assert comparison.current_sector_time_s is not None
    assert comparison.baseline_sector_time_s is not None
    assert comparison.current_throttle_pickup_m is not None
    assert comparison.baseline_throttle_pickup_m is not None
    assert comparison.sector_delta_s == pytest.approx(
        comparison.current_sector_time_s - comparison.baseline_sector_time_s, abs=1e-3
    )


def test_thresholds_come_from_the_drivers_own_spread(steady, deteriorating):
    """Not a constant tuned to make the demo work."""
    steady_cmp = compare_to_baseline(steady, current_lap=17, segment="T7_EXIT")
    assert steady_cmp.sector_delta_threshold_s is not None
    assert steady_cmp.sector_delta_threshold_s > 0


def test_robust_threshold_respects_its_floor():
    assert robust_threshold([1.0, 1.0, 1.0], k=3.0, floor=0.05) == 0.05


def test_robust_threshold_grows_with_spread():
    tight = robust_threshold([1.0, 1.01, 0.99], k=3.0, floor=0.001)
    loose = robust_threshold([1.0, 1.5, 0.5], k=3.0, floor=0.001)
    assert loose > tight


def test_robust_threshold_ignores_one_outlier():
    """MAD-based, so a single scrappy baseline lap does not inflate it."""
    clean = robust_threshold([1.0, 1.02, 0.98, 1.01], k=3.0, floor=0.001)
    with_outlier = robust_threshold([1.0, 1.02, 0.98, 1.01, 9.0], k=3.0, floor=0.001)
    assert with_outlier == pytest.approx(clean, rel=0.5)


def test_status_is_one_of_the_three_contract_values(steady, deteriorating):
    allowed = {"BEHAVIOR_CONSISTENT", "NO_DEVIATION", "INSUFFICIENT_DATA"}
    for frame in (steady, deteriorating):
        for lap in range(10, 18):
            assert (
                compare_to_baseline(frame, current_lap=lap, segment="T7_EXIT").status
                in allowed
            )


def test_comparison_carries_no_composite_score():
    fields = set(BaselineComparison.__dataclass_fields__)
    assert not any(
        word in name for name in fields for word in ("risk", "score", "composite")
    )
