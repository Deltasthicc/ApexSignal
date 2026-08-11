"""Lead-time engine tests.

The most important assertions here are the negative ones: that a null
lead time is produced honestly and often, and that nothing in the code
path can force a positive number when the data does not support one.
"""

from __future__ import annotations

import pytest

import app  # noqa: F401  -- puts services/ on sys.path
from evidence_memory import synthetic
from evidence_memory.lead_time import measure_lead_time
from evidence_memory.synthetic import LAP_DURATION_S


def radio_time_for(lap: int) -> float:
    """Session time roughly when the driver enters the segment on `lap`."""
    return lap * LAP_DURATION_S


@pytest.fixture()
def deteriorating():
    """Clean to lap 14, real deterioration from lap 15."""
    return synthetic.synthetic_window(
        laps=list(range(10, 21)),
        degrade_from_lap=15,
        throttle_pickup_delay=0.10,
        exit_speed_loss_kph=18.0,
    )


@pytest.fixture()
def steady():
    return synthetic.synthetic_window(laps=list(range(10, 21)))


def test_lead_time_measured_when_deterioration_follows(deteriorating):
    """The headline case: driver speaks on lap 14, car changes on lap 15."""
    result = measure_lead_time(
        deteriorating, radio_event_time_s=radio_time_for(14), segment="T7_EXIT"
    )
    assert result.lead_time_s is not None
    assert result.lead_time_s > 0
    assert result.first_change_lap == 15
    assert result.deterioration_threshold_s is not None
    assert result.baseline_sector_time_s is not None


def test_lead_time_equals_change_time_minus_radio_time(deteriorating):
    """The formula, asserted literally."""
    radio_at = radio_time_for(14)
    result = measure_lead_time(
        deteriorating, radio_event_time_s=radio_at, segment="T7_EXIT"
    )
    assert result.first_change_time_s is not None
    assert result.lead_time_s == pytest.approx(
        result.first_change_time_s - radio_at, abs=1e-3
    )


def test_null_when_nothing_deteriorates(steady):
    """Contract: no later deterioration means null, not a small number."""
    result = measure_lead_time(
        steady, radio_event_time_s=radio_time_for(14), segment="T7_EXIT"
    )
    assert result.lead_time_s is None
    assert result.first_change_lap is None
    assert "no run of 2 consecutive laps" in result.reason


def test_null_when_there_is_no_baseline(deteriorating):
    """Speaking on lap 11 leaves too little history to define 'normal'."""
    result = measure_lead_time(
        deteriorating, radio_event_time_s=radio_time_for(11), segment="T7_EXIT"
    )
    assert result.lead_time_s is None
    assert "need 3" in result.reason


def test_null_when_no_laps_follow_the_call(deteriorating):
    result = measure_lead_time(
        deteriorating, radio_event_time_s=radio_time_for(99), segment="T7_EXIT"
    )
    assert result.lead_time_s is None
    assert result.reason in {
        "no laps at this segment after the radio call",
        "no usable lap traversals at this segment",
    }


def test_null_on_an_empty_segment(deteriorating):
    result = measure_lead_time(
        deteriorating, radio_event_time_s=radio_time_for(14), segment="T1_ENTRY"
    )
    assert result.lead_time_s is None
    assert result.reason == "no telemetry at this segment"


def test_a_single_slow_lap_is_not_deterioration(steady):
    """One slow lap is traffic. Persistence is required."""
    import numpy as np

    frame = steady.copy()
    # Make exactly one post-call lap slow, by slowing the car through it.
    mask = frame["lap"] == 16
    frame.loc[mask, "speed_kph"] = frame.loc[mask, "speed_kph"] * 0.75
    frame.loc[mask, "session_time_s"] = frame.loc[mask, "session_time_s"] + np.linspace(
        0, 1.5, int(mask.sum())
    )

    result = measure_lead_time(
        frame, radio_event_time_s=radio_time_for(14), segment="T7_EXIT"
    )
    assert result.lead_time_s is None
    assert "consecutive" in result.reason


def test_persistence_requirement_can_be_relaxed_explicitly(steady):
    import numpy as np

    frame = steady.copy()
    mask = frame["lap"] == 16
    frame.loc[mask, "session_time_s"] = frame.loc[mask, "session_time_s"] + np.linspace(
        0, 1.5, int(mask.sum())
    )

    strict = measure_lead_time(
        frame, radio_event_time_s=radio_time_for(14), segment="T7_EXIT"
    )
    relaxed = measure_lead_time(
        frame,
        radio_event_time_s=radio_time_for(14),
        segment="T7_EXIT",
        min_consecutive_laps=1,
    )
    assert strict.lead_time_s is None
    assert relaxed.lead_time_s is not None
    assert relaxed.first_change_lap == 16


def test_lead_time_is_never_negative(deteriorating):
    """Only laps starting at or after the call are examined."""
    for lap in range(13, 19):
        result = measure_lead_time(
            deteriorating, radio_event_time_s=radio_time_for(lap), segment="T7_EXIT"
        )
        if result.lead_time_s is not None:
            assert result.lead_time_s >= 0


def test_baseline_excludes_laps_after_the_call(deteriorating):
    result = measure_lead_time(
        deteriorating, radio_event_time_s=radio_time_for(14), segment="T7_EXIT"
    )
    assert all(lap < 14 for lap in result.baseline_laps)


def test_examined_laps_are_reported_for_audit(deteriorating):
    result = measure_lead_time(
        deteriorating, radio_event_time_s=radio_time_for(14), segment="T7_EXIT"
    )
    assert result.laps_examined
    assert all(lap >= 14 for lap in result.laps_examined)


def test_threshold_scales_with_the_drivers_own_consistency():
    """An erratic driver needs a bigger change before it counts."""
    consistent = synthetic.synthetic_window(laps=list(range(10, 21)), noise_kph=0.1)
    erratic = synthetic.synthetic_window(laps=list(range(10, 21)), noise_kph=6.0)

    tight = measure_lead_time(
        consistent, radio_event_time_s=radio_time_for(15), segment="T7_EXIT"
    )
    loose = measure_lead_time(
        erratic, radio_event_time_s=radio_time_for(15), segment="T7_EXIT"
    )
    assert tight.deterioration_threshold_s is not None
    assert loose.deterioration_threshold_s is not None
    assert loose.deterioration_threshold_s > tight.deterioration_threshold_s


def test_every_null_states_a_reason(steady, deteriorating):
    for frame in (steady, deteriorating):
        for lap in (11, 14, 19, 99):
            result = measure_lead_time(
                frame, radio_event_time_s=radio_time_for(lap), segment="T7_EXIT"
            )
            if result.lead_time_s is None:
                assert result.reason
                assert len(result.reason) > 20
