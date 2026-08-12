"""Build data/incident_manifest.json from curated incident entries.

Each entry must match contracts/schemas produced downstream (see
contracts/fixtures/incident_manifest.sample.json for the frozen shape).
This script should never invent a field that isn't in that fixture.

Entries are validated before they are written. The manifest is ground
truth for every other workstream, so a placeholder that reaches disk is a
placeholder that reaches the UI.
"""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data" / "incident_manifest.json"

REQUIRED_FIELDS = (
    "incident_id",
    "session_id",
    "driver",
    "event_time_ms",
    "lap",
    "sector_or_corner",
    "audio_path",
    "verified_transcript",
    "complaint_label",
    "telemetry_window_path",
)

PLACEHOLDER_VALUES = {"PLACEHOLDER_SESSION", "PLACEHOLDER_DRIVER", "OPTIONAL", "TBD", ""}


def validate_entries(entries: list[dict]) -> list[str]:
    """Every problem across every entry. Empty list means writable."""
    problems: list[str] = []
    seen: set[str] = set()

    for index, entry in enumerate(entries):
        label = entry.get("incident_id") or f"entry[{index}]"

        for field in REQUIRED_FIELDS:
            if entry.get(field) is None:
                problems.append(f"{label}: missing '{field}'")

        for field, value in entry.items():
            if isinstance(value, str) and value.strip() in PLACEHOLDER_VALUES:
                problems.append(f"{label}: '{field}' is still a placeholder ({value!r})")

        incident_id = entry.get("incident_id")
        if incident_id in seen:
            problems.append(f"{label}: duplicate incident_id")
        elif incident_id:
            seen.add(incident_id)

        event_time = entry.get("event_time_ms")
        if isinstance(event_time, (int, float)) and event_time <= 0:
            # 0 is the fixture's placeholder. A real session t0 precedes
            # every radio call, so a genuine event time is always positive.
            problems.append(
                f"{label}: event_time_ms={event_time} is not a real session time. "
                "It must be milliseconds from FastF1 session t0 -- see "
                "contracts/telemetry_window.md."
            )

    return problems


def build_manifest(entries: list[dict], *, allow_empty: bool = False) -> None:
    """Write validated incident entries to the manifest file.

    TODO(Workstream A): replace the empty list below with the curated,
    manually verified incident set (15-25 entries, 4-6 demo-critical).
    """
    if not entries and not allow_empty:
        raise SystemExit(
            "Refusing to write an empty manifest. Curate entries first, or pass "
            "allow_empty=True to scaffold deliberately."
        )

    problems = validate_entries(entries)
    if problems:
        raise SystemExit(
            "Manifest not written; fix these first:\n  " + "\n  ".join(problems)
        )

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(entries, indent=2))
    print(f"Wrote {len(entries)} entries to {MANIFEST_PATH}")


if __name__ == "__main__":
    build_manifest([], allow_empty=True)
