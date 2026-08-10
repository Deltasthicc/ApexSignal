"""Deterministic replay driver: print the incident manifest in
timestamp order with attached telemetry window paths.

Independent test for Workstream A: this script must run correctly with
no AI service, no core_api, and no network access. If this fails, the
demo has no offline fallback.
"""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data" / "incident_manifest.json"


def replay() -> None:
    entries = json.loads(MANIFEST_PATH.read_text())
    for entry in sorted(entries, key=lambda e: e["event_time_ms"]):
        print(
            f"t={entry['event_time_ms']}ms lap={entry['lap']} "
            f"segment={entry['sector_or_corner']} "
            f"telemetry={entry['telemetry_window_path']}"
        )


if __name__ == "__main__":
    replay()
