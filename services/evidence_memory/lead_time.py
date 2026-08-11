"""Driver-warning lead time.

    driver_warning_lead_time_s
        = first_observable_performance_change_time - radio_event_time

This is the number most likely to be challenged by a judge, so every
input to it is measured, thresholded against the driver's own data, and
reported alongside the result.

`None` is a first-class, expected answer. Charter section 9.5 and the
contract's cut rules both require that no measurable lead time is
reported as exactly that -- "No measurable lead-time established" --
rather than being forced into a positive number.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from evidence_memory.baseline import (
    MIN_BASELINE_LAPS,
    ROBUST_K,
    SECTOR_TIME_FLOOR_S,
    robust_threshold,
    segment_time_s,
)

if TYPE_CHECKING:
    import pandas as pd

# A single slow lap is not evidence of deterioration -- traffic, a lift
# for yellow flags, or a scrappy lap all produce one. Requiring the
# deviation to persist across consecutive laps is the cheapest defence
# available without lap-validity flags, which Workstream A does not
# currently provide. Documented as an assumption in PROGRESS_REPORT.md.
MIN_CONSECUTIVE_DETERIORATING_LAPS = 2


@dataclass(frozen=True)
class LeadTimeResult:
    """A lead-time measurement, or a stated reason there isn't one."""

    lead_time_s: float | None
    first_change_lap: int | None
    first_change_time_s: float | None
    radio_event_time_s: float
    baseline_laps: tuple[int, ...]
    baseline_sector_time_s: float | None
    deterioration_threshold_s: float | None
    laps_examined: tuple[int, ...]
    reason: str


def measure_lead_time(
    window: "pd.DataFrame",
    *,
    radio_event_time_s: float,
    segment: str | None = None,
    min_baseline_laps: int = MIN_BASELINE_LAPS,
    min_consecutive_laps: int = MIN_CONSECUTIVE_DETERIORATING_LAPS,
) -> LeadTimeResult:
    """Measure how far ahead of an observable change the driver spoke.

    Method, in full, so it can be defended:

    1. **Baseline.** Take every lap at this segment whose traversal ended
       before the radio call. Their median segment time is the baseline.
       Fewer than `min_baseline_laps` of them and the answer is None --
       with no baseline there is no defensible notion of "change".
    2. **Threshold.** A lap counts as an observable performance change
       when its segment time exceeds the baseline median by more than
       `ROBUST_K` MAD-based sigmas of the baseline's own spread, floored
       at `SECTOR_TIME_FLOOR_S`. The threshold comes from the driver's own
       consistency, not from a constant picked to make the demo work.
    3. **Persistence.** The deviation must hold for
       `min_consecutive_laps` consecutive laps. One slow lap is traffic.
    4. **Lead time.** Take the session time at which the *first* lap of
       that run entered the segment, and subtract the radio event time.

    Only laps beginning at or after the radio call are examined, so the
    result is never negative: this measures warning lead, and a change
    that predates the call is not one. If no qualifying run exists, the
    answer is None -- never a fallback, never the largest deviation found.
    """
    import numpy as np

    from evidence_memory.telemetry_fingerprint import select_segment

    scoped = select_segment(window, segment=segment) if segment else window
    if scoped.empty:
        return _empty(radio_event_time_s, "no telemetry at this segment")

    per_lap = _per_lap_traversals(scoped)
    if not per_lap:
        return _empty(radio_event_time_s, "no usable lap traversals at this segment")

    baseline = [lap for lap in per_lap if lap["end_s"] < radio_event_time_s]
    after = [lap for lap in per_lap if lap["start_s"] >= radio_event_time_s]

    baseline_laps = tuple(int(lap["lap"]) for lap in baseline)
    if len(baseline) < min_baseline_laps:
        return _empty(
            radio_event_time_s,
            f"{len(baseline)} lap(s) at this segment before the radio call, "
            f"need {min_baseline_laps} to establish what 'normal' is",
            baseline_laps=baseline_laps,
        )

    baseline_times = [lap["time_s"] for lap in baseline]
    baseline_median = float(np.median(baseline_times))
    threshold = robust_threshold(
        baseline_times, k=ROBUST_K, floor=SECTOR_TIME_FLOOR_S
    )
    laps_examined = tuple(int(lap["lap"]) for lap in after)

    if not after:
        return _empty(
            radio_event_time_s,
            "no laps at this segment after the radio call",
            baseline_laps=baseline_laps,
            baseline_sector_time_s=baseline_median,
            deterioration_threshold_s=threshold,
        )

    run_start: dict | None = None
    run_length = 0
    for lap in after:
        if lap["time_s"] - baseline_median > threshold:
            run_length += 1
            if run_start is None:
                run_start = lap
            if run_length >= min_consecutive_laps:
                lead = float(run_start["start_s"] - radio_event_time_s)
                return LeadTimeResult(
                    lead_time_s=round(lead, 3),
                    first_change_lap=int(run_start["lap"]),
                    first_change_time_s=float(run_start["start_s"]),
                    radio_event_time_s=radio_event_time_s,
                    baseline_laps=baseline_laps,
                    baseline_sector_time_s=baseline_median,
                    deterioration_threshold_s=threshold,
                    laps_examined=laps_examined,
                    reason=(
                        f"lap {int(run_start['lap'])} and the "
                        f"{min_consecutive_laps - 1} lap(s) following it exceeded "
                        f"the driver's own baseline of {baseline_median:.3f}s by "
                        f"more than {threshold:.3f}s"
                    ),
                )
        else:
            run_start = None
            run_length = 0

    return _empty(
        radio_event_time_s,
        (
            f"no run of {min_consecutive_laps} consecutive laps after the radio "
            f"call exceeded the baseline of {baseline_median:.3f}s by more than "
            f"{threshold:.3f}s"
        ),
        baseline_laps=baseline_laps,
        baseline_sector_time_s=baseline_median,
        deterioration_threshold_s=threshold,
        laps_examined=laps_examined,
    )


def _per_lap_traversals(frame: "pd.DataFrame") -> list[dict]:
    """One entry per lap: when the segment was entered, left, and how long."""
    traversals: list[dict] = []
    for lap in sorted({int(value) for value in frame["lap"]}):
        rows = frame[frame["lap"] == lap]
        duration = segment_time_s(rows)
        if duration is None:
            continue
        times = rows["session_time_s"].to_numpy(dtype=float)
        traversals.append(
            {
                "lap": lap,
                "start_s": float(times.min()),
                "end_s": float(times.max()),
                "time_s": duration,
            }
        )
    return traversals


def _empty(
    radio_event_time_s: float,
    reason: str,
    *,
    baseline_laps: tuple[int, ...] = (),
    baseline_sector_time_s: float | None = None,
    deterioration_threshold_s: float | None = None,
    laps_examined: tuple[int, ...] = (),
) -> LeadTimeResult:
    return LeadTimeResult(
        lead_time_s=None,
        first_change_lap=None,
        first_change_time_s=None,
        radio_event_time_s=radio_event_time_s,
        baseline_laps=baseline_laps,
        baseline_sector_time_s=baseline_sector_time_s,
        deterioration_threshold_s=deterioration_threshold_s,
        laps_examined=laps_examined,
        reason=reason,
    )
