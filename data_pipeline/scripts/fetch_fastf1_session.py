"""Download and cache FastF1 telemetry for the primary demo session.

Run once, before any other workstream needs telemetry. Never call this
during the judged demo; the cache written here is what the demo reads.

Writes three things under `data/telemetry/<session_id>/`:

  session_meta.json  the clock origin, pinned. Records t0 as an absolute
                     UTC instant so `session_time_s` and `event_time_ms`
                     stay reconstructible long after this run.
  laps_<DRV>.csv     human-readable lap index with session-time bounds.
                     This is the artifact you use for the manual
                     lap/timestamp verification the README demands.
  _fastf1_cache/     FastF1's own cache, so every later script is offline.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from window_schema import CLOCK_ORIGIN, SESSION_META_FILENAME

TELEMETRY_DIR = Path(__file__).resolve().parents[2] / "data" / "telemetry"
CACHE_DIR = TELEMETRY_DIR / "_fastf1_cache"


def make_session_id(year: int, event_name: str, session: str) -> str:
    slug = re.sub(r"[^A-Z0-9]+", "_", event_name.upper()).strip("_")
    return f"{year}_{slug}_{session.upper()}"


def _pick_driver(laps, driver: str):
    """FastF1 renamed pick_driver -> pick_drivers in v3.1."""
    if hasattr(laps, "pick_drivers"):
        return laps.pick_drivers(driver)
    return laps.pick_driver(driver)


def _seconds(value) -> float | None:
    """Session-time timedelta -> float seconds, or None if not recorded."""
    import pandas as pd

    if value is None or pd.isna(value):
        return None
    return float(value.total_seconds())


def fetch_session(year: int, grand_prix: str, session: str, driver: str) -> Path:
    """Cache one session's telemetry for one driver via FastF1.

    Returns the session directory. Requires network on first run only;
    afterwards FastF1 serves everything from CACHE_DIR.
    """
    import fastf1
    import pandas as pd

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))

    race = fastf1.get_session(year, grand_prix, session)
    # telemetry=True is not optional: t0_date -- the clock origin this whole
    # project hangs on -- is only populated by the telemetry load.
    race.load(laps=True, telemetry=True, weather=False, messages=False)

    event_name = str(race.event["EventName"])
    session_id = make_session_id(year, event_name, session)
    session_dir = TELEMETRY_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    laps = _pick_driver(race.laps, driver)
    if laps.empty:
        raise SystemExit(f"No laps for driver {driver!r} in {session_id}.")

    rows = []
    for _, lap in laps.iterrows():
        start_s = _seconds(lap.get("LapStartTime"))
        end_s = _seconds(lap.get("Time"))
        rows.append(
            {
                "lap": int(lap["LapNumber"]),
                "start_s": start_s,
                "end_s": end_s,
                "lap_time_s": _seconds(lap.get("LapTime")),
                "is_accurate": bool(lap.get("IsAccurate", False)),
                "pitted_in": bool(pd.notna(lap.get("PitInTime"))),
                "pitted_out": bool(pd.notna(lap.get("PitOutTime"))),
                "track_status": str(lap.get("TrackStatus") or ""),
                "deleted": bool(lap.get("Deleted", False)),
                "compound": lap.get("Compound"),
                "tyre_life": lap.get("TyreLife"),
            }
        )

    index = pd.DataFrame(rows).sort_values("lap")
    index_path = session_dir / f"laps_{driver.upper()}.csv"
    index.to_csv(index_path, index=False)

    t0 = race.t0_date
    meta = {
        "session_id": session_id,
        "year": year,
        "event_name": event_name,
        "session": session.upper(),
        "driver": driver.upper(),
        "clock_origin": CLOCK_ORIGIN,
        "t0_date_utc": None if t0 is None else pd.Timestamp(t0).isoformat(),
        "clock_note": (
            "session_time_s in every telemetry window and event_time_ms in "
            "the incident manifest are both seconds from this t0. Same clock, "
            "same zero. Do not mix in broadcast or clip-relative times."
        ),
        "first_lap": int(index["lap"].min()),
        "last_lap": int(index["lap"].max()),
        "lap_index_file": index_path.name,
        # Needed by fetch_team_radio.py to locate TeamRadio.json for this
        # session in the livetiming archive.
        "api_path": race.api_path,
        "fastf1_version": getattr(fastf1, "__version__", "unknown"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (session_dir / SESSION_META_FILENAME).write_text(json.dumps(meta, indent=2))

    print(f"session_id      {session_id}")
    print(f"laps            {meta['first_lap']}-{meta['last_lap']} ({len(index)} rows)")
    print(f"t0 (UTC)        {meta['t0_date_utc']}")
    print(f"lap index       {index_path}")
    print(f"session meta    {session_dir / SESSION_META_FILENAME}")
    print("\nVerify a few lap boundaries against timing data before curating incidents.")
    return session_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--grand-prix", required=True)
    parser.add_argument("--session", required=True, help="e.g. R, Q, FP1")
    parser.add_argument("--driver", required=True, help="Three-letter driver code")
    args = parser.parse_args()

    fetch_session(args.year, args.grand_prix, args.session, args.driver)
