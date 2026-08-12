"""Gate every telemetry window against the three rules that matter.

  1. Coverage   incident lap + >= MIN_CLEAN_LAPS_BEFORE clean laps before
                it + the post-incident laps. Never a single-lap file.
  2. Columns    every required column present, typed, not all-null.
  3. Clock      event_time_ms lands inside the incident lap's own
                session-time span, proving both sides share a zero.

Reads written Parquet plus the manifest. No FastF1, no session cache, no
network -- so this runs in CI and on the demo machine minutes before
judging.

  python data_pipeline/scripts/validate_telemetry_windows.py

Exit code 0 means every window is usable. Anything else means at least one
downstream feature will silently degrade.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from telemetry_frame import check_event_alignment, check_window_frame
from window_schema import CLOCK_ORIGIN, MIN_CLEAN_LAPS_BEFORE, SESSION_META_FILENAME

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "data" / "incident_manifest.json"
TELEMETRY_DIR = REPO_ROOT / "data" / "telemetry"


def validate_entry(entry: dict, *, min_clean_before: int) -> list[str]:
    """Every contract violation for one manifest entry."""
    problems: list[str] = []

    for field in ("incident_id", "session_id", "lap", "event_time_ms", "telemetry_window_path"):
        if entry.get(field) is None:
            problems.append(f"manifest entry is missing '{field}'")
    if problems:
        return problems

    path = REPO_ROOT / entry["telemetry_window_path"]
    if not path.exists():
        return [f"telemetry window not found at {entry['telemetry_window_path']}"]

    try:
        window = pd.read_parquet(path)
    except Exception as exc:  # noqa: BLE001
        return [f"could not read {path.name}: {type(exc).__name__}: {exc}"]

    problems += check_window_frame(window, min_clean_before=min_clean_before)
    if problems:
        return problems

    problems += check_event_alignment(window, entry["event_time_ms"], int(entry["lap"]))

    # The clock origin has to be declared, not assumed. A session whose meta
    # says something other than FASTF1_SESSION_TIME makes every lead time in
    # that session meaningless even if the alignment check happens to pass.
    meta_path = TELEMETRY_DIR / entry["session_id"] / SESSION_META_FILENAME
    if not meta_path.exists():
        problems.append(f"no {SESSION_META_FILENAME} for session {entry['session_id']}")
    else:
        declared = json.loads(meta_path.read_text()).get("clock_origin")
        if declared != CLOCK_ORIGIN:
            problems.append(
                f"session declares clock_origin={declared!r}, contract requires {CLOCK_ORIGIN!r}"
            )

    return problems


def summarize(entry: dict) -> str:
    path = REPO_ROOT / entry["telemetry_window_path"]
    window = pd.read_parquet(path)
    roles = window[["lap", "lap_role"]].drop_duplicates()
    counts = roles["lap_role"].value_counts().to_dict()
    span = float(window["session_time_s"].max()) - float(window["session_time_s"].min())
    return (
        f"{window['lap'].nunique()} laps "
        f"(baseline={counts.get('BASELINE', 0)} context={counts.get('CONTEXT', 0)} "
        f"post={counts.get('POST', 0)}), {len(window)} rows, {span:.1f}s"
    )


def main(manifest_path: Path, *, min_clean_before: int) -> int:
    if not manifest_path.exists():
        print(f"No manifest at {manifest_path}.")
        return 2

    manifest = json.loads(manifest_path.read_text())
    if not manifest:
        print(f"{manifest_path} is empty -- nothing to validate. This is not a pass.")
        return 2

    failed = 0
    for entry in manifest:
        incident_id = entry.get("incident_id", "<no incident_id>")
        problems = validate_entry(entry, min_clean_before=min_clean_before)
        if problems:
            failed += 1
            print(f"FAIL  {incident_id}")
            for problem in problems:
                print(f"        {problem}")
        else:
            print(f"ok    {incident_id}  {summarize(entry)}")

    print(f"\n{len(manifest) - failed}/{len(manifest)} windows valid.")
    if failed:
        print(
            "Windows that fail coverage produce baseline_evidence="
            "INSUFFICIENT_DATA; windows that fail the clock check produce a "
            "lead time that looks valid and is not."
        )
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--min-clean-before", type=int, default=MIN_CLEAN_LAPS_BEFORE)
    args = parser.parse_args()

    raise SystemExit(main(args.manifest, min_clean_before=args.min_clean_before))
