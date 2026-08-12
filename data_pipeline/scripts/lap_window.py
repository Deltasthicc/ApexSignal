"""Which laps belong in an incident's telemetry window, and why.

Pure logic: no FastF1, no pandas, no network. The rules that decide whether
a lap can serve as a baseline are the part most likely to be wrong in a way
nobody notices, so they live here where they can be tested offline against
hand-written laps.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from window_schema import MIN_CLEAN_LAPS_BEFORE


@dataclass(frozen=True)
class LapRecord:
    """One lap reduced to the fields that decide baseline eligibility.

    Populated from FastF1's lap table by `build_telemetry_windows`, or by
    hand in tests. `start_s` / `end_s` are session-time seconds on
    `window_schema.CLOCK_ORIGIN`.
    """

    lap: int
    start_s: float | None = None
    end_s: float | None = None
    is_accurate: bool = True
    pitted_in: bool = False
    pitted_out: bool = False
    track_status: str = "1"
    deleted: bool = False
    has_telemetry: bool = True


def clean_lap_exclusions(lap: LapRecord) -> tuple[str, ...]:
    """Every reason `lap` cannot be used as a baseline. Empty means clean.

    Returns all reasons rather than the first, because a lap excluded for
    three reasons and a lap excluded for one are different problems when a
    session turns out to have too few clean laps and someone has to decide
    whether to move the incident or move the session.
    """
    reasons: list[str] = []

    if not lap.has_telemetry:
        reasons.append("NO_TELEMETRY")
    if lap.start_s is None or lap.end_s is None:
        reasons.append("NO_LAP_BOUNDS")
    elif lap.end_s <= lap.start_s:
        reasons.append("NON_POSITIVE_DURATION")
    if lap.deleted:
        reasons.append("DELETED")
    if lap.pitted_in:
        reasons.append("PIT_IN_LAP")
    if lap.pitted_out:
        reasons.append("PIT_OUT_LAP")
    if not lap.is_accurate:
        reasons.append("NOT_ACCURATE")

    status = (lap.track_status or "").strip()
    if not status:
        reasons.append("NO_TRACK_STATUS")
    elif set(status) != {"1"}:
        # FastF1 concatenates every status flag seen during the lap, so "1"
        # is the only all-clear value; "14" means the lap went green then
        # safety car and is not representative of anything.
        reasons.append(f"TRACK_STATUS_{status}")

    return tuple(reasons)


def is_clean_lap(lap: LapRecord) -> bool:
    return not clean_lap_exclusions(lap)


class InsufficientBaselineError(RuntimeError):
    """Raised when a window cannot reach `min_clean_before` clean laps.

    This is deliberately fatal. A window built with two baseline laps
    instead of three still produces numbers downstream, and those numbers
    would be quietly weaker than every other incident's.
    """

    def __init__(
        self,
        incident_lap: int,
        found: tuple[int, ...],
        required: int,
        excluded: dict[int, tuple[str, ...]],
    ) -> None:
        self.incident_lap = incident_lap
        self.found = found
        self.required = required
        self.excluded = excluded
        rejected = ", ".join(
            f"lap {lap}: {'/'.join(reasons)}" for lap, reasons in sorted(excluded.items())
        )
        super().__init__(
            f"incident lap {incident_lap} has {len(found)} clean preceding "
            f"lap(s) {list(found)}, needs {required}. "
            f"Rejected: {rejected or 'nothing -- ran out of laps'}"
        )


@dataclass(frozen=True)
class WindowSpec:
    """The laps one telemetry window covers, with each lap's role."""

    incident_lap: int
    baseline_laps: tuple[int, ...]
    context_laps: tuple[int, ...]
    post_laps: tuple[int, ...]
    excluded: dict[int, tuple[str, ...]] = field(default_factory=dict)

    @property
    def span_start_lap(self) -> int:
        pre = self.baseline_laps + self.context_laps
        return min(pre) if pre else self.incident_lap

    @property
    def span_end_lap(self) -> int:
        return max(self.post_laps) if self.post_laps else self.incident_lap

    @property
    def all_laps(self) -> tuple[int, ...]:
        laps = set(self.baseline_laps) | set(self.context_laps) | {self.incident_lap}
        laps |= set(self.post_laps)
        return tuple(sorted(laps))

    def role_of(self, lap: int) -> str:
        if lap == self.incident_lap:
            return "INCIDENT"
        if lap in self.baseline_laps:
            return "BASELINE"
        if lap in self.post_laps:
            return "POST"
        if lap in self.context_laps:
            return "CONTEXT"
        raise KeyError(f"lap {lap} is not part of this window")


def select_window_laps(
    laps: list[LapRecord],
    incident_lap: int,
    *,
    min_clean_before: int = MIN_CLEAN_LAPS_BEFORE,
    replay_end_lap: int | None = None,
    max_post_laps: int | None = None,
) -> WindowSpec:
    """Pick the laps for one incident window.

    Walks backwards from the incident lap until `min_clean_before` clean
    laps are found -- so the span grows past three laps when pit or
    safety-car laps intervene, rather than silently accepting a dirty
    baseline. Every lap inside the resulting span is kept so the window
    stays contiguous in time; the dirty ones are tagged CONTEXT.

    Forward, it takes everything up to `replay_end_lap` (default: the last
    lap present), because the recurrence monitor scans post-incident
    telemetry with no radio event to anchor it.
    """
    if min_clean_before < 0:
        raise ValueError("min_clean_before must be >= 0")

    by_number = {record.lap: record for record in laps}
    if incident_lap not in by_number:
        raise KeyError(f"incident lap {incident_lap} is not in the lap table")

    incident_record = by_number[incident_lap]
    if not incident_record.has_telemetry:
        raise InsufficientBaselineError(incident_lap, (), min_clean_before, {})

    # --- backwards: collect clean laps, remember why others were skipped ---
    baseline: list[int] = []
    context: list[int] = []
    excluded: dict[int, tuple[str, ...]] = {}

    for number in sorted((n for n in by_number if n < incident_lap), reverse=True):
        if len(baseline) >= min_clean_before:
            break
        reasons = clean_lap_exclusions(by_number[number])
        if reasons:
            excluded[number] = reasons
            context.append(number)
        else:
            baseline.append(number)

    if len(baseline) < min_clean_before:
        raise InsufficientBaselineError(
            incident_lap, tuple(sorted(baseline)), min_clean_before, excluded
        )

    # Trailing context laps below the earliest baseline lap are outside the
    # span -- they were inspected, not included.
    earliest_baseline = min(baseline)
    context = [n for n in context if n > earliest_baseline]

    # --- forwards -------------------------------------------------------
    after = sorted(n for n in by_number if n > incident_lap)
    if replay_end_lap is not None:
        after = [n for n in after if n <= replay_end_lap]
    if max_post_laps is not None:
        after = after[:max_post_laps]

    return WindowSpec(
        incident_lap=incident_lap,
        baseline_laps=tuple(sorted(baseline)),
        context_laps=tuple(sorted(context)),
        post_laps=tuple(after),
        excluded=excluded,
    )
