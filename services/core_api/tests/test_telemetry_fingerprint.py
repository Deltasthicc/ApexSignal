"""Telemetry fingerprint tests.

Covers the documented window shape, distance normalization, resampling,
standardization, and channel-by-channel similarity.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import app  # noqa: F401  -- puts services/ on sys.path
from evidence_memory import synthetic
from evidence_memory.telemetry_fingerprint import (
    CHANNELS,
    DEFAULT_RESAMPLE_POINTS,
    MIN_SAMPLES,
    REQUIRED_COLUMNS,
    TelemetryWindowError,
    build_fingerprint,
    compare_fingerprints,
    fingerprint_from_path,
    load_window,
    select_segment,
)


@pytest.fixture()
def window():
    return synthetic.synthetic_window(laps=[14, 15, 16, 17])


def test_synthetic_window_matches_documented_shape(window):
    """The generator emits exactly the shape README.md asks Workstream A for."""
    for column in REQUIRED_COLUMNS:
        assert column in window.columns
    assert set(window["lap"]) == {14, 15, 16, 17}
    assert window["throttle_pct"].between(0, 100).all()
    assert window["distance_m"].min() >= 0


def test_window_round_trips_through_parquet(tmp_path: Path, window):
    path = synthetic.write_window(window, tmp_path / "INC-017.parquet")
    reloaded = load_window(path)
    assert list(reloaded.columns) == list(window.columns)
    assert len(reloaded) == len(window)


def test_load_window_rejects_missing_file(tmp_path: Path):
    with pytest.raises(TelemetryWindowError, match="not found"):
        load_window(tmp_path / "nope.parquet")


def test_load_window_rejects_missing_columns(tmp_path: Path, window):
    path = synthetic.write_window(
        window.drop(columns=["throttle_pct"]), tmp_path / "bad.parquet"
    )
    with pytest.raises(TelemetryWindowError, match="missing required columns"):
        load_window(path)


def test_fingerprint_resamples_to_fixed_length(window):
    lap = select_segment(window, lap=17)
    fingerprint = build_fingerprint(lap)

    assert fingerprint.n_points == DEFAULT_RESAMPLE_POINTS
    for channel in CHANNELS:
        assert len(fingerprint.channels[channel]) == DEFAULT_RESAMPLE_POINTS
        assert len(fingerprint.standardized[channel]) == DEFAULT_RESAMPLE_POINTS
    assert fingerprint.distance_span_m > 0
    assert fingerprint.duration_s > 0


def test_fingerprint_length_is_independent_of_sample_count(window):
    """Distance normalization: fewer raw samples, same fingerprint length."""
    lap = select_segment(window, lap=17)
    sparse = lap.iloc[::3]

    dense_fp = build_fingerprint(lap)
    sparse_fp = build_fingerprint(sparse)

    assert dense_fp.n_points == sparse_fp.n_points
    similarity = compare_fingerprints(dense_fp, sparse_fp)
    assert similarity.overall > 0.95


def test_standardized_channels_are_zero_mean_unit_variance(window):
    import numpy as np

    fingerprint = build_fingerprint(select_segment(window, lap=17))
    for channel in CHANNELS:
        values = np.asarray(fingerprint.standardized[channel])
        if np.std(fingerprint.channels[channel]) < 1e-9:
            assert np.allclose(values, 0.0)
        else:
            assert abs(float(np.mean(values))) < 1e-9
            assert abs(float(np.std(values)) - 1.0) < 1e-9


def test_fingerprint_rejects_too_few_rows(window):
    with pytest.raises(TelemetryWindowError, match="need at least"):
        build_fingerprint(window.iloc[: MIN_SAMPLES - 1])


def test_fingerprint_rejects_a_window_that_covers_no_distance(window):
    """A stalled window is refused rather than yielding a NaN fingerprint.

    Identical distance readings collapse to a single row in de-duplication,
    so this is caught by the usable-row guard; the explicit zero-span check
    in build_fingerprint is defensive and sits behind it.
    """
    stalled = select_segment(window, lap=17).copy()
    stalled["distance_m"] = 0.0
    with pytest.raises(TelemetryWindowError):
        build_fingerprint(stalled)


def test_identical_laps_score_near_one(window):
    lap = select_segment(window, lap=17)
    similarity = compare_fingerprints(build_fingerprint(lap), build_fingerprint(lap))
    assert similarity.overall == pytest.approx(1.0, abs=1e-6)
    for channel in CHANNELS:
        assert similarity.per_channel[channel] == pytest.approx(1.0, abs=1e-6)


def test_similarity_reports_every_channel_separately(window):
    """Components are always exposed, never collapsed into one opaque score."""
    similarity = compare_fingerprints(
        build_fingerprint(select_segment(window, lap=16)),
        build_fingerprint(select_segment(window, lap=17)),
    )
    assert set(similarity.per_channel) == set(CHANNELS)
    assert all(0.0 <= v <= 1.0 for v in similarity.per_channel.values())
    assert 0.0 <= similarity.overall <= 1.0
    assert similarity.overall == pytest.approx(
        sum(similarity.per_channel.values()) / len(CHANNELS)
    )


def test_degraded_lap_scores_lower_than_a_clean_lap():
    """A delayed throttle pickup shows up as reduced throttle similarity."""
    degraded_window = synthetic.synthetic_window(
        laps=[14, 15, 16, 17, 18, 19],
        degrade_from_lap=18,
        throttle_pickup_delay=0.18,
        exit_speed_loss_kph=20.0,
    )

    clean = build_fingerprint(select_segment(degraded_window, lap=15))
    another_clean = build_fingerprint(select_segment(degraded_window, lap=16))
    degraded = build_fingerprint(select_segment(degraded_window, lap=19))

    clean_pair = compare_fingerprints(clean, another_clean)
    degraded_pair = compare_fingerprints(clean, degraded)

    assert degraded_pair.per_channel["throttle_pct"] < clean_pair.per_channel[
        "throttle_pct"
    ]
    assert degraded_pair.overall < clean_pair.overall


def test_shape_similarity_ignores_a_uniform_speed_offset(window):
    """Shape, not magnitude: a slower-everywhere lap keeps its shape."""
    lap = select_segment(window, lap=17)
    slower = lap.copy()
    slower["speed_kph"] = slower["speed_kph"] - 5.0

    similarity = compare_fingerprints(build_fingerprint(lap), build_fingerprint(slower))
    assert similarity.per_channel["speed_kph"] > 0.99


def test_flat_channels_are_handled_without_nan(window):
    lap = select_segment(window, lap=17).copy()
    lap["brake"] = False
    other = lap.copy()

    similarity = compare_fingerprints(build_fingerprint(lap), build_fingerprint(other))
    assert similarity.per_channel["brake"] == 1.0

    moving = select_segment(window, lap=17)
    mixed = compare_fingerprints(build_fingerprint(lap), build_fingerprint(moving))
    assert mixed.per_channel["brake"] == 0.0


def test_mismatched_resample_sizes_are_rejected(window):
    lap = select_segment(window, lap=17)
    with pytest.raises(ValueError, match="different resample sizes"):
        compare_fingerprints(
            build_fingerprint(lap, n_points=64), build_fingerprint(lap, n_points=128)
        )


def test_select_segment_filters_lap_and_segment(window):
    lap_only = select_segment(window, lap=15)
    assert set(lap_only["lap"]) == {15}

    both = select_segment(window, lap=15, segment="T7_EXIT")
    assert len(both) == len(lap_only)

    assert len(select_segment(window, segment="T1_ENTRY")) == 0


def test_fingerprint_from_path_slices_one_lap(tmp_path: Path, window):
    path = synthetic.write_window(window, tmp_path / "INC-017.parquet")
    fingerprint = fingerprint_from_path(path, lap=17, segment="T7_EXIT")
    assert fingerprint.n_points == DEFAULT_RESAMPLE_POINTS
    assert fingerprint.source_rows <= len(window)


def test_synthetic_degradation_actually_costs_time():
    """Segment time is integrated from the trace, not planted."""
    frame = synthetic.synthetic_window(
        laps=[15, 19], degrade_from_lap=19, exit_speed_loss_kph=20.0
    )
    clean = build_fingerprint(select_segment(frame, lap=15))
    degraded = build_fingerprint(select_segment(frame, lap=19))
    assert degraded.duration_s > clean.duration_s


def test_generator_is_deterministic():
    first = synthetic.synthetic_window(laps=[17], seed=17)
    second = synthetic.synthetic_window(laps=[17], seed=17)
    assert first.equals(second)
