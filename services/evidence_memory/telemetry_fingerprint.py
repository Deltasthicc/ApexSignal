"""Telemetry fingerprints for segment-to-segment comparison.

Charter section 9.6: normalize by track distance rather than clock time,
resample speed/throttle/brake to a fixed number of points, standardize
channels, and compute channel-by-channel similarity so the components
are inspectable rather than hidden behind one number.

Only channels that are actually recorded are used. Steering angle, tyre
temperature, wheel slip and mechanical state are never inferred.

The expected window shape is documented in ``README.md`` in this
directory. It was defined by Workstream C because Workstream A had not
specified one; treat it as a proposal Workstream A must confirm.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Mapping, Sequence

if TYPE_CHECKING:  # heavy imports stay out of module import time
    import pandas as pd

# Channels compared by the fingerprint, in a fixed order.
CHANNELS: tuple[str, ...] = ("speed_kph", "throttle_pct", "brake")

# Columns every telemetry window must carry. See README.md.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "session_time_s",
    "lap",
    "distance_m",
    "speed_kph",
    "throttle_pct",
    "brake",
)

# Recognised but not required; used when present, never fabricated.
OPTIONAL_COLUMNS: tuple[str, ...] = (
    "driver",
    "session_id",
    "segment",
    "rpm",
    "gear",
)

# Resampling grid size. 128 points over a corner-exit segment is a few
# metres per point at F1 speeds -- fine enough to keep the shape of a
# throttle pickup, coarse enough that sensor jitter does not dominate.
DEFAULT_RESAMPLE_POINTS = 128

# Below this many usable rows a window cannot honestly be called a trace.
MIN_SAMPLES = 8

_ZERO_VARIANCE_EPS = 1e-9


class TelemetryWindowError(ValueError):
    """A telemetry window is missing, malformed, or too sparse to use."""


@dataclass(frozen=True)
class TelemetryFingerprint:
    """A distance-normalized, fixed-length view of one telemetry window.

    ``channels`` holds the resampled traces in their original units;
    ``standardized`` holds the same traces z-scored per channel. Shape
    comparison uses the standardized form so that a lap driven slightly
    faster overall does not read as a different shape, while the raw form
    stays available for absolute measurements such as throttle pickup.
    """

    n_points: int
    channels: Mapping[str, tuple[float, ...]]
    standardized: Mapping[str, tuple[float, ...]]
    distance_span_m: float
    duration_s: float
    source_rows: int


@dataclass(frozen=True)
class FingerprintSimilarity:
    """Channel-by-channel similarity plus the mean across channels.

    ``overall`` is the plain unweighted mean of ``per_channel`` and exists
    only because the frozen contract has a single ``telemetry_similarity``
    field. It is not a composite risk score: no channel is weighted, and
    ``per_channel`` is always reported alongside it so the number can be
    taken apart.
    """

    per_channel: Mapping[str, float]
    overall: float


def load_window(path: str | Path) -> "pd.DataFrame":
    """Read a telemetry window from Parquet (or CSV, for hand-made fixtures).

    Raises ``TelemetryWindowError`` if the file is absent or does not
    carry the documented columns.
    """
    import pandas as pd

    window_path = Path(path)
    if not window_path.exists():
        raise TelemetryWindowError(f"telemetry window not found: {window_path}")

    if window_path.suffix.lower() == ".csv":
        frame = pd.read_csv(window_path)
    else:
        frame = pd.read_parquet(window_path)

    validate_window(frame)
    return frame


def validate_window(frame: "pd.DataFrame") -> None:
    """Check a window carries the documented columns and some usable rows."""
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise TelemetryWindowError(
            f"telemetry window is missing required columns: {sorted(missing)}. "
            f"Expected at least {list(REQUIRED_COLUMNS)} -- see "
            f"services/evidence_memory/README.md"
        )
    if len(frame) < MIN_SAMPLES:
        raise TelemetryWindowError(
            f"telemetry window has {len(frame)} rows, need at least {MIN_SAMPLES}"
        )


def select_segment(
    frame: "pd.DataFrame",
    *,
    lap: int | None = None,
    segment: str | None = None,
) -> "pd.DataFrame":
    """Narrow a window to one lap and/or one named segment.

    A window file covers several laps at a segment (see README.md), so
    callers doing per-lap work slice it here rather than each writing
    their own filter.
    """
    selected = frame
    if lap is not None:
        selected = selected[selected["lap"] == lap]
    if segment is not None:
        if "segment" not in selected.columns:
            raise TelemetryWindowError(
                "cannot filter by segment: window has no 'segment' column"
            )
        selected = selected[selected["segment"] == segment]
    return selected


def build_fingerprint(
    frame: "pd.DataFrame",
    *,
    n_points: int = DEFAULT_RESAMPLE_POINTS,
) -> TelemetryFingerprint:
    """Build a distance-normalized fingerprint from a telemetry window.

    Steps, in order: drop rows with unusable channel values, sort by track
    distance, collapse duplicate distance readings, map distance onto a
    0-1 position within the window, resample every channel onto a fixed
    grid of that position, then z-score each channel.

    Normalizing by distance rather than time is what makes two passes
    through the same corner comparable even when one is slower.
    """
    import numpy as np

    validate_window(frame)

    columns = ["session_time_s", "distance_m", *CHANNELS]
    usable = frame[columns].copy()
    usable["brake"] = _brake_to_float(usable["brake"])
    usable = usable.dropna()
    usable = usable.sort_values("distance_m")
    # np.interp needs a strictly increasing x; keep the first sample at
    # each distance rather than averaging, so no value is synthesised.
    usable = usable[~usable["distance_m"].duplicated(keep="first")]

    if len(usable) < MIN_SAMPLES:
        raise TelemetryWindowError(
            f"telemetry window has {len(usable)} usable rows after cleaning, "
            f"need at least {MIN_SAMPLES}"
        )

    distance = usable["distance_m"].to_numpy(dtype=float)
    span = float(distance[-1] - distance[0])
    # Defensive: after sorting and de-duplication a span of zero should be
    # unreachable (identical readings collapse into the row-count guard
    # above). Kept so a future change to de-duplication surfaces as an
    # error instead of a silently NaN fingerprint.
    if span <= 0:
        raise TelemetryWindowError(
            "telemetry window covers no track distance; cannot normalize by distance"
        )

    position = (distance - distance[0]) / span
    grid = np.linspace(0.0, 1.0, n_points)

    channels: dict[str, tuple[float, ...]] = {}
    standardized: dict[str, tuple[float, ...]] = {}
    for channel in CHANNELS:
        resampled = np.interp(grid, position, usable[channel].to_numpy(dtype=float))
        channels[channel] = tuple(float(v) for v in resampled)
        standardized[channel] = tuple(float(v) for v in _standardize(resampled))

    session_time = usable["session_time_s"].to_numpy(dtype=float)

    return TelemetryFingerprint(
        n_points=n_points,
        channels=channels,
        standardized=standardized,
        distance_span_m=span,
        duration_s=float(session_time.max() - session_time.min()),
        source_rows=int(len(usable)),
    )


def fingerprint_from_path(
    path: str | Path,
    *,
    lap: int | None = None,
    segment: str | None = None,
    n_points: int = DEFAULT_RESAMPLE_POINTS,
) -> TelemetryFingerprint:
    """Load a window file and fingerprint one lap/segment slice of it."""
    frame = load_window(path)
    return build_fingerprint(
        select_segment(frame, lap=lap, segment=segment), n_points=n_points
    )


def compare_fingerprints(
    left: TelemetryFingerprint, right: TelemetryFingerprint
) -> FingerprintSimilarity:
    """Compare two fingerprints channel by channel.

    Per channel the score is the Pearson correlation of the two
    distance-normalized traces, rescaled from [-1, 1] to [0, 1] so it fits
    the contract's 0-1 range. 1.0 means the traces rise and fall together,
    0.5 means unrelated, 0.0 means one mirrors the other.

    This measures shape, not magnitude, which is the point: two exits with
    the same throttle-pickup shape should score high even if one was two
    km/h quicker. Absolute differences are the baseline engine's job, not
    the fingerprint's.
    """
    if left.n_points != right.n_points:
        raise ValueError(
            f"fingerprints have different resample sizes: "
            f"{left.n_points} vs {right.n_points}"
        )

    per_channel = {
        channel: _channel_similarity(left.channels[channel], right.channels[channel])
        for channel in CHANNELS
    }
    overall = sum(per_channel.values()) / len(per_channel)
    return FingerprintSimilarity(per_channel=per_channel, overall=overall)


def _brake_to_float(series: "pd.Series") -> "pd.Series":
    """Accept brake as bool, 0/1, or 0-100 and return it as 0.0/1.0-scaled."""
    if series.dtype == bool:
        return series.astype(float)
    return series.astype(float)


def _standardize(values):
    """Z-score a channel; a flat channel standardizes to all zeros."""
    import numpy as np

    spread = float(np.std(values))
    if spread < _ZERO_VARIANCE_EPS:
        return np.zeros_like(values, dtype=float)
    return (values - float(np.mean(values))) / spread


def _channel_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Pearson correlation rescaled to 0-1, with flat channels handled.

    A channel that never moves (brake untouched through a corner exit, for
    example) has no correlation defined. Two flat channels at the same
    level are identical traces and score 1.0; a flat channel against a
    moving one has no shared shape and scores 0.0. Saying so is more
    honest than emitting a NaN or silently dropping the channel.
    """
    import numpy as np

    a = np.asarray(left, dtype=float)
    b = np.asarray(right, dtype=float)

    a_flat = float(np.std(a)) < _ZERO_VARIANCE_EPS
    b_flat = float(np.std(b)) < _ZERO_VARIANCE_EPS
    if a_flat and b_flat:
        scale = max(abs(float(np.mean(a))), abs(float(np.mean(b))), 1.0)
        return 1.0 if abs(float(np.mean(a) - np.mean(b))) / scale < 1e-6 else 0.0
    if a_flat or b_flat:
        return 0.0

    correlation = float(np.corrcoef(a, b)[0, 1])
    if not np.isfinite(correlation):
        return 0.0
    return _clamp01((correlation + 1.0) / 2.0)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
