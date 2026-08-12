"""Deterministic synthetic telemetry windows for tests and local demos.

This exists because Workstream C's independent test has to pass with no
real data present: `data/telemetry/` is Workstream A's folder and is
empty. Nothing here is a substitute for verified FastF1 data, and no
number produced by this module may reach a judge-facing screen.

The generator produces windows in exactly the shape documented in
`README.md`, so the same code path that will read Workstream A's Parquet
files reads these too.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    import pandas as pd

SAMPLES_PER_LAP = 120
SEGMENT_LENGTH_M = 300.0
LAP_DURATION_S = 90.0


@dataclass(frozen=True)
class SegmentProfile:
    """Shape of one pass through a corner-exit segment.

    Speeds are km/h, ``throttle_pickup_at`` is a fraction of segment
    distance, ``brake_until`` likewise.
    """

    entry_speed_kph: float = 250.0
    apex_speed_kph: float = 120.0
    exit_speed_kph: float = 265.0
    apex_at: float = 0.20
    brake_until: float = 0.15
    throttle_pickup_at: float = 0.25
    throttle_ramp: float = 0.35


def synthetic_window(
    *,
    laps: Sequence[int],
    driver: str = "TEST_DRIVER",
    session_id: str = "TEST_SESSION",
    segment: str = "T7_EXIT",
    profile: SegmentProfile | None = None,
    degrade_from_lap: int | None = None,
    throttle_pickup_delay: float = 0.06,
    exit_speed_loss_kph: float = 9.0,
    noise_kph: float = 0.4,
    seed: int = 17,
) -> "pd.DataFrame":
    """Build a multi-lap telemetry window for one segment.

    From ``degrade_from_lap`` onward the driver picks up throttle later
    and carries less exit speed. Lap times are not written in by hand:
    session time is integrated from distance and speed, so a slower exit
    produces a genuinely slower segment traversal. That keeps the baseline
    and lead-time engines honest -- they measure a real effect in the
    signal rather than a number planted for them to find.
    """
    import numpy as np
    import pandas as pd

    profile = profile or SegmentProfile()
    rng = np.random.default_rng(seed)

    frames = []
    for lap in laps:
        degraded = degrade_from_lap is not None and lap >= degrade_from_lap
        lap_profile = profile
        if degraded:
            lap_profile = SegmentProfile(
                entry_speed_kph=profile.entry_speed_kph,
                apex_speed_kph=profile.apex_speed_kph,
                exit_speed_kph=profile.exit_speed_kph - exit_speed_loss_kph,
                apex_at=profile.apex_at,
                brake_until=profile.brake_until,
                throttle_pickup_at=profile.throttle_pickup_at + throttle_pickup_delay,
                throttle_ramp=profile.throttle_ramp,
            )

        frames.append(
            _one_lap(
                lap=lap,
                driver=driver,
                session_id=session_id,
                segment=segment,
                profile=lap_profile,
                noise_kph=noise_kph,
                rng=rng,
            )
        )

    return pd.concat(frames, ignore_index=True)


def write_window(frame: "pd.DataFrame", path: str | Path) -> Path:
    """Write a window to Parquet, creating parent directories."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() == ".csv":
        frame.to_csv(target, index=False)
    else:
        frame.to_parquet(target, index=False)
    return target


def _one_lap(
    *,
    lap: int,
    driver: str,
    session_id: str,
    segment: str,
    profile: SegmentProfile,
    noise_kph: float,
    rng,
) -> "pd.DataFrame":
    import numpy as np
    import pandas as pd

    position = np.linspace(0.0, 1.0, SAMPLES_PER_LAP)
    distance = position * SEGMENT_LENGTH_M

    speed = np.where(
        position <= profile.apex_at,
        _lerp(
            profile.entry_speed_kph,
            profile.apex_speed_kph,
            _safe_ratio(position, profile.apex_at),
        ),
        profile.apex_speed_kph
        + (profile.exit_speed_kph - profile.apex_speed_kph)
        * _safe_ratio(position - profile.apex_at, 1.0 - profile.apex_at) ** 0.7,
    )
    speed = speed + rng.normal(0.0, noise_kph, size=speed.shape)
    speed = np.clip(speed, 1.0, None)

    throttle = np.clip(
        (position - profile.throttle_pickup_at) / profile.throttle_ramp * 100.0,
        0.0,
        100.0,
    )
    brake = (position <= profile.brake_until).astype(bool)

    # Integrate travel time from distance and speed so segment duration is
    # a consequence of the trace, not an independent invention.
    speed_ms = speed / 3.6
    step = np.diff(distance, prepend=distance[0])
    elapsed = np.cumsum(step / speed_ms)
    session_time = lap * LAP_DURATION_S + elapsed

    return pd.DataFrame(
        {
            "session_time_s": session_time,
            "lap": lap,
            "distance_m": distance,
            "speed_kph": speed,
            "throttle_pct": throttle,
            "brake": brake,
            "driver": driver,
            "session_id": session_id,
            "segment": segment,
        }
    )


def _lerp(start: float, end: float, ratio):
    return start + (end - start) * ratio


def _safe_ratio(numerator, denominator: float):
    import numpy as np

    if denominator <= 0:
        return np.zeros_like(np.asarray(numerator, dtype=float))
    return np.clip(np.asarray(numerator, dtype=float) / denominator, 0.0, 1.0)
