"""Build data/incident_manifest.json from curated incident entries.

Each entry must match contracts/schemas produced downstream (see
contracts/fixtures/incident_manifest.sample.json for the frozen shape).
This script should never invent a field that isn't in that fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data" / "incident_manifest.json"


def build_manifest(entries: list[dict]) -> None:
    """Write validated incident entries to the manifest file.

    TODO(Workstream A): replace the empty list below with the curated,
    manually verified incident set (15-25 entries, 4-6 demo-critical).
    """
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(entries, indent=2))


if __name__ == "__main__":
    build_manifest([])
