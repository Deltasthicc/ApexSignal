"""Offline fixtures for the Workstream A window tests.

Nothing here touches FastF1, the network, or a cached session. The frames
are shaped the way FastF1 hands them over -- `SessionTime` as a timedelta,
`Distance` cumulative across the slice -- so the tests exercise the real
mapping rather than a convenient one.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def fastf1_lap_frame():
    """Factory for one lap of FastF1-shaped car data.

    `distance_offset` simulates `add_distance()` having been run over a
    multi-lap slice, where distance keeps climbing instead of restarting at
    the line. Normalisation must rebase that to zero.
    """

    def _make(
        start_s: float,
        *,
        duration_s: float = 90.0,
        samples: int = 120,
        distance_offset: float = 0.0,
        lap_length_m: float = 5000.0,
        brake_as_int: bool = False,
    ) -> pd.DataFrame:
        session_time = np.linspace(start_s, start_s + duration_s, samples)
        progress = np.linspace(0.0, 1.0, samples)
        brake = progress > 0.85
        return pd.DataFrame(
            {
                "SessionTime": pd.to_timedelta(session_time, unit="s"),
                "Distance": distance_offset + progress * lap_length_m,
                "Speed": 120.0 + 180.0 * np.sin(progress * np.pi),
                "Throttle": np.clip(100.0 * np.sin(progress * np.pi), 0.0, 100.0),
                "Brake": brake.astype(int) if brake_as_int else brake,
                "RPM": 9000.0 + 2500.0 * progress,
                "nGear": np.clip((progress * 8).astype(int) + 1, 1, 8),
            }
        )

    return _make


@pytest.fixture
def lap_series(fastf1_lap_frame):
    """Consecutive laps starting at t=0, each following the previous."""

    def _make(lap_numbers, *, duration_s: float = 90.0, cumulative_distance: bool = False):
        frames = {}
        for index, number in enumerate(sorted(lap_numbers)):
            frames[number] = fastf1_lap_frame(
                start_s=index * duration_s,
                duration_s=duration_s,
                distance_offset=index * 5000.0 if cumulative_distance else 0.0,
            )
        return frames

    return _make
