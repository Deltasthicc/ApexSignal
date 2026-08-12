"""Build one multi-lap telemetry window per curated incident.

Each window covers the incident lap, at least MIN_CLEAN_LAPS_BEFORE clean
laps preceding it, and every lap after it that the replay covers. A
single-lap window is not a smaller version of this -- it is a window on
which baseline and lead-time features cannot produce anything except
INSUFFICIENT_DATA.

Reads the FastF1 cache written by `fetch_fastf1_session.py`; no network.

  python data_pipeline/scripts/build_telemetry_windows.py \
      --session-id 2023_ITALIAN_GRAND_PRIX_R --driver VER
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from lap_window import InsufficientBaselineError, LapRecord, select_window_laps
from telemetry_frame import (
    build_window_frame,
    check_event_alignment,
    check_window_frame,
    normalize_lap_frame,
)
from window_schema import MIN_CLEAN_LAPS_BEFORE, SESSION_META_FILENAME

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_DIR = REPO_ROOT / "data" / "telemetry"
CACHE_DIR = TELEMETRY_DIR / "_fastf1_cache"
MANIFEST_PATH = REPO_ROOT / "data" / "incident_manifest.json"

MIN_SAMPLES_PER_LAP = 20
"""A lap with a handful of samples is a gap in the feed, not a lap."""


def _load_session(session_meta: dict, driver: str):
    import fastf1

    fastf1.Cache.enable_cache(str(CACHE_DIR))
    race = fastf1.get_session(
        session_meta["year"], session_meta["event_name"], session_meta["session"]
    )
    race.load(laps=True, telemetry=True, weather=False, messages=False)
    laps = (
        race.laps.pick_drivers(driver)
        if hasattr(race.laps, "pick_drivers")
        else race.laps.pick_driver(driver)
    )
    return race, laps


def extract_lap_frames(laps, driver: str, session_id: str) -> tuple[dict, dict]:
    """Per-lap normalized telemetry, plus why any lap produced none."""
    import pandas as pd

    frames: dict[int, pd.DataFrame] = {}
    failures: dict[int, str] = {}

    for _, lap in laps.iterrows():
        number = int(lap["LapNumber"])
        try:
            car = lap.get_car_data()
            if car is None or car.empty:
                failures[number] = "no car data"
                continue
            # Distance from the start of *this lap*, which is what makes the
            # same value mean the same tarmac on every lap in the window.
            car = car.add_distance()
            frame = normalize_lap_frame(car, number, driver=driver, session_id=session_id)
        except Exception as exc:  # noqa: BLE001 - one bad lap must not kill the run
            failures[number] = f"{type(exc).__name__}: {exc}"
            continue

        if len(frame) < MIN_SAMPLES_PER_LAP:
            failures[number] = f"only {len(frame)} samples"
            continue
        frames[number] = frame

    return frames, failures


def build_lap_records(laps, frames: dict) -> list[LapRecord]:
    import pandas as pd

    records = []
    for _, lap in laps.iterrows():
        number = int(lap["LapNumber"])
        start = lap.get("LapStartTime")
        end = lap.get("Time")
        records.append(
            LapRecord(
                lap=number,
                start_s=None if pd.isna(start) else float(start.total_seconds()),
                end_s=None if pd.isna(end) else float(end.total_seconds()),
                is_accurate=bool(lap.get("IsAccurate", False)),
                pitted_in=bool(pd.notna(lap.get("PitInTime"))),
                pitted_out=bool(pd.notna(lap.get("PitOutTime"))),
                track_status=str(lap.get("TrackStatus") or ""),
                deleted=bool(lap.get("Deleted", False)),
                has_telemetry=number in frames,
            )
        )
    return records


def build_windows(
    session_id: str,
    driver: str,
    *,
    min_clean_before: int = MIN_CLEAN_LAPS_BEFORE,
    replay_end_lap: int | None = None,
    max_post_laps: int | None = None,
    segment_map: dict | None = None,
    skip_alignment_check: bool = False,
) -> int:
    """Build every window for one session/driver. Returns an exit code."""
    session_dir = TELEMETRY_DIR / session_id
    meta_path = session_dir / SESSION_META_FILENAME
    if not meta_path.exists():
        raise SystemExit(f"No {SESSION_META_FILENAME} at {meta_path}. Run fetch_fastf1_session.py first.")
    session_meta = json.loads(meta_path.read_text())

    if not MANIFEST_PATH.exists():
        raise SystemExit(f"No incident manifest at {MANIFEST_PATH}. Run build_incident_manifest.py first.")
    manifest = json.loads(MANIFEST_PATH.read_text())

    incidents = [
        entry
        for entry in manifest
        if entry.get("session_id") == session_id and entry.get("driver", "").upper() == driver.upper()
    ]
    if not incidents:
        raise SystemExit(f"No manifest entries for session_id={session_id} driver={driver}.")

    _, laps = _load_session(session_meta, driver)
    frames, failures = extract_lap_frames(laps, driver, session_id)
    records = build_lap_records(laps, frames)

    print(f"{session_id} / {driver}: {len(frames)} laps with telemetry, {len(failures)} without")
    for number, reason in sorted(failures.items()):
        print(f"  lap {number:>3}  no telemetry: {reason}")

    index_entries = []
    errors: list[str] = []

    for entry in sorted(incidents, key=lambda e: e.get("event_time_ms", 0)):
        incident_id = entry["incident_id"]
        incident_lap = int(entry["lap"])

        try:
            spec = select_window_laps(
                records,
                incident_lap,
                min_clean_before=min_clean_before,
                replay_end_lap=replay_end_lap,
                max_post_laps=max_post_laps,
            )
        except (InsufficientBaselineError, KeyError) as exc:
            errors.append(f"{incident_id}: {exc}")
            print(f"  {incident_id}  FAILED  {exc}")
            continue

        window = build_window_frame(
            {lap: frames[lap] for lap in spec.all_laps}, spec, segment_map=segment_map
        )

        problems = check_window_frame(window, min_clean_before=min_clean_before)
        if not skip_alignment_check:
            problems += check_event_alignment(window, entry["event_time_ms"], incident_lap)

        if problems:
            for problem in problems:
                errors.append(f"{incident_id}: {problem}")
                print(f"  {incident_id}  FAILED  {problem}")
            continue

        out_path = REPO_ROOT / entry["telemetry_window_path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        window.to_parquet(out_path, index=False)

        span = (float(window["session_time_s"].min()), float(window["session_time_s"].max()))
        index_entries.append(
            {
                "incident_id": incident_id,
                "incident_lap": incident_lap,
                "baseline_laps": list(spec.baseline_laps),
                "context_laps": list(spec.context_laps),
                "post_laps": list(spec.post_laps),
                "excluded_laps": {str(k): list(v) for k, v in spec.excluded.items()},
                "laps_total": int(window["lap"].nunique()),
                "rows": int(len(window)),
                "session_time_span_s": [round(span[0], 3), round(span[1], 3)],
                "event_time_ms": entry["event_time_ms"],
                "path": entry["telemetry_window_path"],
            }
        )
        print(
            f"  {incident_id}  lap {incident_lap}  "
            f"baseline={list(spec.baseline_laps)} post={len(spec.post_laps)} laps  "
            f"{len(window)} rows -> {entry['telemetry_window_path']}"
        )

    index_path = session_dir / "windows_index.json"
    index_path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "driver": driver.upper(),
                "clock_origin": session_meta["clock_origin"],
                "min_clean_laps_before": min_clean_before,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "windows": index_entries,
            },
            indent=2,
        )
    )
    print(f"\n{len(index_entries)}/{len(incidents)} windows written. Index: {index_path}")

    if errors:
        print(f"\n{len(errors)} problem(s); those windows were NOT written:")
        for error in errors:
            print(f"  - {error}")
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", required=True, help="As written in session_meta.json")
    parser.add_argument("--driver", required=True, help="Three-letter driver code")
    parser.add_argument("--min-clean-before", type=int, default=MIN_CLEAN_LAPS_BEFORE)
    parser.add_argument(
        "--replay-end-lap",
        type=int,
        default=None,
        help="Last lap the replay covers. Default: every lap after the incident.",
    )
    parser.add_argument("--max-post-laps", type=int, default=None)
    parser.add_argument("--segment-map", type=Path, default=None, help="JSON: {name: [start_m, end_m]}")
    parser.add_argument(
        "--skip-alignment-check",
        action="store_true",
        help="Build even if event_time_ms does not land on the incident lap. "
        "For curation only -- never for a demo build.",
    )
    args = parser.parse_args()

    raise SystemExit(
        build_windows(
            args.session_id,
            args.driver,
            min_clean_before=args.min_clean_before,
            replay_end_lap=args.replay_end_lap,
            max_post_laps=args.max_post_laps,
            segment_map=json.loads(args.segment_map.read_text()) if args.segment_map else None,
            skip_alignment_check=args.skip_alignment_check,
        )
    )
