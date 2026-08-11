"""Own-baseline comparison: is this driver different from their own recent self?

Answers one question and only that question: at this circuit segment, is
the driver's current behaviour different from their own recent baseline
at the same segment? It compares a driver to themselves, never to another
driver and never to a model of how the car "should" behave.

`BEHAVIOR_CONSISTENT` means the telemetry moved in a way consistent with
something having been reported. It is not a claim that the complaint is
correct, that a fault exists, or that a cause has been identified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    import pandas as pd

# --- Tunables, all documented in services/core_api/README.md ------------

# Fewer clean prior laps than this and there is no baseline worth the
# name; status becomes INSUFFICIENT_DATA rather than a number nobody can
# defend.
MIN_BASELINE_LAPS = 3

# How many prior laps form the baseline. "Recent personal baseline"
# (charter 9.5): recent enough to reflect the current tyre/fuel state,
# long enough to be robust to one scrappy lap.
BASELINE_WINDOW_LAPS = 5

# Throttle is "picked up" at the first distance where the driver commits
# past this. 50% is well clear of the trailing-throttle noise around a
# brake release and well below full power, so it lands on the ramp rather
# than at either end of it.
THROTTLE_PICKUP_PCT = 50.0

# A deviation counts when it exceeds the baseline's own spread by this
# many robust standard deviations (MAD-based, so one bad lap in the
# baseline does not inflate it).
ROBUST_K = 3.0

# Absolute floors. A very consistent driver has a tiny MAD, and without a
# floor any rounding wobble would clear ROBUST_K. These are the smallest
# deviations worth showing a race engineer.
SECTOR_TIME_FLOOR_S = 0.05
THROTTLE_PICKUP_FLOOR_PCT = 2.0

# Scale factor turning MAD into a standard-deviation equivalent for
# normally distributed data.
_MAD_TO_SIGMA = 1.4826


@dataclass(frozen=True)
class BaselineComparison:
    """Own-baseline evidence, with the raw measurements kept alongside.

    The two contract fields are `throttle_pickup_delta_pct` and
    `sector_delta_s`; everything else is here so the numbers can be
    audited rather than taken on trust.
    """

    throttle_pickup_delta_pct: float
    sector_delta_s: float
    status: str

    current_lap: int
    baseline_laps: tuple[int, ...]
    current_sector_time_s: float | None
    baseline_sector_time_s: float | None
    current_throttle_pickup_m: float | None
    baseline_throttle_pickup_m: float | None
    sector_delta_threshold_s: float | None
    throttle_delta_threshold_pct: float | None
    reason: str

    @property
    def baseline_lap_count(self) -> int:
        return len(self.baseline_laps)


def segment_time_s(frame: "pd.DataFrame") -> float | None:
    """Time taken to traverse the rows given, in seconds.

    Measured from the telemetry itself (last sample time minus first),
    never read from a lap-time column, so it always refers to exactly the
    stretch of track being compared.
    """
    if len(frame) < 2:
        return None
    times = frame["session_time_s"].to_numpy(dtype=float)
    return float(times.max() - times.min())


def throttle_pickup_distance_m(
    frame: "pd.DataFrame", *, pickup_pct: float = THROTTLE_PICKUP_PCT
) -> float | None:
    """Distance into the segment at which the driver commits to throttle.

    The first sample at or above `pickup_pct`, as a distance from the
    start of the segment. Returns None when the driver never reaches that
    throttle level in the window -- which is a real possibility on a
    braking-limited segment and must not be silently reported as zero.
    """
    import numpy as np

    if frame.empty:
        return None

    ordered = frame.sort_values("distance_m")
    throttle = ordered["throttle_pct"].to_numpy(dtype=float)
    distance = ordered["distance_m"].to_numpy(dtype=float)

    above = np.flatnonzero(throttle >= pickup_pct)
    if above.size == 0:
        return None
    return float(distance[above[0]] - distance[0])


def robust_threshold(values: Sequence[float], *, k: float, floor: float) -> float:
    """`k` MAD-based sigmas of spread, never below `floor`."""
    import numpy as np

    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        return floor
    median = float(np.median(array))
    mad = float(np.median(np.abs(array - median)))
    return max(floor, k * _MAD_TO_SIGMA * mad)


def compare_to_baseline(
    window: "pd.DataFrame",
    *,
    current_lap: int,
    segment: str | None = None,
    baseline_window_laps: int = BASELINE_WINDOW_LAPS,
    min_baseline_laps: int = MIN_BASELINE_LAPS,
) -> BaselineComparison:
    """Compare one lap at a segment against the driver's own recent baseline.

    Baseline laps are the most recent `baseline_window_laps` laps at the
    same segment strictly *before* `current_lap`. Laps after it are never
    used: a baseline that includes the future would let a later
    deterioration hide the very deviation being looked for.

    `sector_delta_s` is the current segment traversal time minus the
    baseline median. Positive means slower.

    `throttle_pickup_delta_pct` is the shift in throttle-pickup point,
    expressed as a percentage of segment length and sign-flipped so that
    **negative means the driver got to power later** than their baseline
    -- the direction a traction complaint would predict. Segment length is
    the denominator rather than the baseline pickup distance because it is
    stable: a baseline pickup close to the segment start would otherwise
    make the percentage explode.
    """
    import numpy as np

    from evidence_memory.telemetry_fingerprint import select_segment

    scoped = select_segment(window, segment=segment) if segment else window

    current = scoped[scoped["lap"] == current_lap]
    prior_laps = sorted({int(lap) for lap in scoped["lap"] if lap < current_lap})
    baseline_laps = tuple(prior_laps[-baseline_window_laps:])

    current_time = segment_time_s(current)
    current_pickup = throttle_pickup_distance_m(current)

    if len(baseline_laps) < min_baseline_laps:
        return BaselineComparison(
            throttle_pickup_delta_pct=0.0,
            sector_delta_s=0.0,
            status="INSUFFICIENT_DATA",
            current_lap=current_lap,
            baseline_laps=baseline_laps,
            current_sector_time_s=current_time,
            baseline_sector_time_s=None,
            current_throttle_pickup_m=current_pickup,
            baseline_throttle_pickup_m=None,
            sector_delta_threshold_s=None,
            throttle_delta_threshold_pct=None,
            reason=(
                f"{len(baseline_laps)} prior lap(s) at this segment, "
                f"need {min_baseline_laps} to establish a baseline"
            ),
        )

    if current.empty or current_time is None:
        return BaselineComparison(
            throttle_pickup_delta_pct=0.0,
            sector_delta_s=0.0,
            status="INSUFFICIENT_DATA",
            current_lap=current_lap,
            baseline_laps=baseline_laps,
            current_sector_time_s=None,
            baseline_sector_time_s=None,
            current_throttle_pickup_m=current_pickup,
            baseline_throttle_pickup_m=None,
            sector_delta_threshold_s=None,
            throttle_delta_threshold_pct=None,
            reason=f"no usable telemetry for lap {current_lap} at this segment",
        )

    baseline_times: list[float] = []
    baseline_pickups: list[float] = []
    for lap in baseline_laps:
        lap_rows = scoped[scoped["lap"] == lap]
        lap_time = segment_time_s(lap_rows)
        if lap_time is not None:
            baseline_times.append(lap_time)
        lap_pickup = throttle_pickup_distance_m(lap_rows)
        if lap_pickup is not None:
            baseline_pickups.append(lap_pickup)

    if len(baseline_times) < min_baseline_laps:
        return BaselineComparison(
            throttle_pickup_delta_pct=0.0,
            sector_delta_s=0.0,
            status="INSUFFICIENT_DATA",
            current_lap=current_lap,
            baseline_laps=baseline_laps,
            current_sector_time_s=current_time,
            baseline_sector_time_s=None,
            current_throttle_pickup_m=current_pickup,
            baseline_throttle_pickup_m=None,
            sector_delta_threshold_s=None,
            throttle_delta_threshold_pct=None,
            reason=(
                f"only {len(baseline_times)} baseline lap(s) had usable telemetry, "
                f"need {min_baseline_laps}"
            ),
        )

    baseline_time = float(np.median(baseline_times))
    sector_delta = current_time - baseline_time
    sector_threshold = robust_threshold(
        baseline_times, k=ROBUST_K, floor=SECTOR_TIME_FLOOR_S
    )

    segment_length = _segment_length_m(scoped)
    baseline_pickup: float | None = None
    throttle_delta_pct = 0.0
    throttle_threshold: float | None = None

    if baseline_pickups and current_pickup is not None and segment_length > 0:
        baseline_pickup = float(np.median(baseline_pickups))
        # Negative == later to power than baseline.
        throttle_delta_pct = -100.0 * (current_pickup - baseline_pickup) / segment_length
        pickup_pcts = [100.0 * p / segment_length for p in baseline_pickups]
        throttle_threshold = robust_threshold(
            pickup_pcts, k=ROBUST_K, floor=THROTTLE_PICKUP_FLOOR_PCT
        )

    sector_deviated = abs(sector_delta) > sector_threshold
    throttle_deviated = (
        throttle_threshold is not None and abs(throttle_delta_pct) > throttle_threshold
    )

    if sector_deviated or throttle_deviated:
        status = "BEHAVIOR_CONSISTENT"
        moved = []
        if sector_deviated:
            moved.append(
                f"segment time {sector_delta:+.3f}s vs own baseline "
                f"(threshold {sector_threshold:.3f}s)"
            )
        if throttle_deviated:
            moved.append(
                f"throttle pickup {throttle_delta_pct:+.1f}% vs own baseline "
                f"(threshold {throttle_threshold:.1f}%)"
            )
        reason = "; ".join(moved)
    else:
        status = "NO_DEVIATION"
        reason = (
            f"segment time {sector_delta:+.3f}s and throttle pickup "
            f"{throttle_delta_pct:+.1f}% both within this driver's own "
            f"baseline spread at this segment"
        )

    return BaselineComparison(
        # `+ 0.0` normalises negative zero, which renders as "-0.0".
        throttle_pickup_delta_pct=round(throttle_delta_pct, 3) + 0.0,
        sector_delta_s=round(sector_delta, 3) + 0.0,
        status=status,
        current_lap=current_lap,
        baseline_laps=baseline_laps,
        current_sector_time_s=current_time,
        baseline_sector_time_s=baseline_time,
        current_throttle_pickup_m=current_pickup,
        baseline_throttle_pickup_m=baseline_pickup,
        sector_delta_threshold_s=sector_threshold,
        throttle_delta_threshold_pct=throttle_threshold,
        reason=reason,
    )


def _segment_length_m(frame: "pd.DataFrame") -> float:
    distance = frame["distance_m"].to_numpy(dtype=float)
    if distance.size == 0:
        return 0.0
    return float(distance.max() - distance.min())
