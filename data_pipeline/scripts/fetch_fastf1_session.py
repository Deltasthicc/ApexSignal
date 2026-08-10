"""Download and cache FastF1 telemetry for the primary demo session.

Run once, before any other workstream needs telemetry. Never call this
during the judged demo; the cache written here is what the demo reads.
"""

from __future__ import annotations

import argparse
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "telemetry" / "_fastf1_cache"


def fetch_session(year: int, grand_prix: str, session: str, driver: str) -> None:
    """Cache one session's telemetry for one driver via FastF1.

    TODO(Workstream A): implement once the primary session is chosen.
    Enable FastF1's cache at CACHE_DIR before calling fastf1.get_session,
    then persist the driver's lap/telemetry frames needed for
    contracts/fixtures/incident_manifest.sample.json entries.
    """
    raise NotImplementedError("Implement after the primary session is validated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--grand-prix", required=True)
    parser.add_argument("--session", required=True, help="e.g. R, Q, FP1")
    parser.add_argument("--driver", required=True, help="Three-letter driver code")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fetch_session(args.year, args.grand_prix, args.session, args.driver)
