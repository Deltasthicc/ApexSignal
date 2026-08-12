"""Pull the session's team radio index and put it on the session clock.

The F1 livetiming archive publishes `TeamRadio.json` for every session: one
entry per radio capture, with an absolute UTC instant, the driver's racing
number, and a path to the mp3.

That absolute instant is what makes curation safe. Hand-timing a clip off
broadcast footage is how `event_time_ms` ends up on the wrong origin --
a well-formed number, on a clock nobody wrote down, that silently offsets
every lead time in the product. Here the conversion is arithmetic:

    session_time_s = (Utc - t0_date).total_seconds()
    event_time_ms  = session_time_s * 1000

with `t0_date` read from the session_meta.json that `fetch_fastf1_session`
already pinned.

This script does NOT decide which captures are complaints. It produces the
candidate list a human listens through. Output columns include whether each
candidate can even support a baseline, so obviously-unusable moments can be
dropped before anyone spends time on the audio.

  python data_pipeline/scripts/fetch_team_radio.py \
      --session-id 2023_ITALIAN_GRAND_PRIX_R --driver SAI

Needs network. No FastF1 -- it reads session_meta.json and the lap index.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import requests

from lap_window import InsufficientBaselineError, LapRecord, select_window_laps
from window_schema import MIN_CLEAN_LAPS_BEFORE, SESSION_META_FILENAME

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_DIR = REPO_ROOT / "data" / "telemetry"
AUDIO_DIR = REPO_ROOT / "data" / "audio"
LIVETIMING = "https://livetiming.formula1.com"
HEADERS = {"User-Agent": "ApexSignal-datapipeline/0.1 (hackathon, contact: team)"}


def _get_json(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    text = response.content.decode("utf-8-sig", errors="replace")
    if "\x00" in text[:50]:  # some livetiming files are utf-16
        text = response.content.decode("utf-16", errors="replace")
    return json.loads(text)


def resolve_racing_number(base: str, driver: str) -> str:
    """Three-letter code -> racing number, from the session's own driver list."""
    drivers = _get_json(base + "DriverList.json")
    for number, info in drivers.items():
        if not isinstance(info, dict):
            continue
        if str(info.get("Tla", "")).upper() == driver.upper():
            return str(number)
    raise SystemExit(
        f"Driver {driver!r} not in this session's driver list: "
        + ", ".join(sorted(str(i.get("Tla")) for i in drivers.values() if isinstance(i, dict)))
    )


def lap_records_from_index(index: pd.DataFrame) -> list[LapRecord]:
    return [
        LapRecord(
            lap=int(row["lap"]),
            start_s=None if pd.isna(row["start_s"]) else float(row["start_s"]),
            end_s=None if pd.isna(row["end_s"]) else float(row["end_s"]),
            is_accurate=bool(row["is_accurate"]),
            pitted_in=bool(row["pitted_in"]),
            pitted_out=bool(row["pitted_out"]),
            track_status=str(row["track_status"]),
            deleted=bool(row["deleted"]),
            has_telemetry=True,
        )
        for _, row in index.iterrows()
    ]


def lap_at(index: pd.DataFrame, session_time_s: float) -> int | None:
    hit = index[(index["start_s"] <= session_time_s) & (session_time_s <= index["end_s"])]
    return None if hit.empty else int(hit.iloc[0]["lap"])


def baseline_status(records: list[LapRecord], lap: int | None, min_clean: int) -> str:
    """Can an incident on this lap support a baseline at all?"""
    if lap is None:
        return "NO_LAP"
    try:
        spec = select_window_laps(records, lap, min_clean_before=min_clean)
    except InsufficientBaselineError as exc:
        return f"UNUSABLE ({len(exc.found)}/{min_clean} clean)"
    except KeyError:
        return "NO_LAP"
    return f"OK (baseline {list(spec.baseline_laps)})"


def fetch_radio(
    session_id: str, driver: str, *, min_clean: int = MIN_CLEAN_LAPS_BEFORE, download: bool = False
) -> Path:
    session_dir = TELEMETRY_DIR / session_id
    meta_path = session_dir / SESSION_META_FILENAME
    if not meta_path.exists():
        raise SystemExit(f"No {SESSION_META_FILENAME} at {meta_path}. Run fetch_fastf1_session.py first.")
    meta = json.loads(meta_path.read_text())

    api_path = meta.get("api_path")
    if not api_path:
        raise SystemExit(
            "session_meta.json has no api_path. Re-run fetch_fastf1_session.py "
            "with the current version to record it."
        )
    base = LIVETIMING + api_path

    t0 = pd.Timestamp(meta["t0_date_utc"])
    if t0.tzinfo is not None:
        t0 = t0.tz_convert(None)

    index_path = session_dir / meta["lap_index_file"]
    if not index_path.exists():
        raise SystemExit(f"No lap index at {index_path}.")
    index = pd.read_csv(index_path)
    records = lap_records_from_index(index)

    number = resolve_racing_number(base, driver)
    captures = _get_json(base + "TeamRadio.json").get("Captures", [])
    print(f"{len(captures)} captures in session; driver {driver} is #{number}")

    rows = []
    for capture in captures:
        if str(capture.get("RacingNumber")) != number:
            continue
        utc = pd.Timestamp(capture["Utc"])
        if utc.tzinfo is not None:
            utc = utc.tz_convert(None)
        session_time_s = (utc - t0).total_seconds()
        lap = lap_at(index, session_time_s)
        rows.append(
            {
                "utc": capture["Utc"],
                "session_time_s": round(session_time_s, 3),
                "event_time_ms": round(session_time_s * 1000.0, 1),
                "lap": lap,
                "baseline": baseline_status(records, lap, min_clean),
                "audio_url": base + capture["Path"],
                "audio_file": capture["Path"].split("/")[-1],
            }
        )

    if not rows:
        raise SystemExit(f"No radio captures for {driver} (#{number}) in this session.")

    candidates = pd.DataFrame(rows).sort_values("session_time_s").reset_index(drop=True)
    out_path = session_dir / f"radio_candidates_{driver.upper()}.csv"
    candidates.to_csv(out_path, index=False)

    usable = candidates["baseline"].str.startswith("OK").sum()
    in_session = candidates["lap"].notna().sum()
    print(f"{len(candidates)} captures for {driver}; {in_session} land on a lap; {usable} can support a baseline")
    print(f"candidates -> {out_path}")

    if download:
        target = AUDIO_DIR / session_id
        target.mkdir(parents=True, exist_ok=True)
        for _, row in candidates.iterrows():
            destination = target / row["audio_file"]
            if destination.exists():
                continue
            response = requests.get(row["audio_url"], headers=HEADERS, timeout=60)
            response.raise_for_status()
            destination.write_bytes(response.content)
        print(f"audio -> {target}")
    else:
        print("Audio not downloaded. Re-run with --download to fetch the mp3s.")

    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--driver", required=True, help="Three-letter driver code")
    parser.add_argument("--min-clean-before", type=int, default=MIN_CLEAN_LAPS_BEFORE)
    parser.add_argument("--download", action="store_true", help="Also fetch the mp3 files")
    args = parser.parse_args()

    fetch_radio(
        args.session_id,
        args.driver,
        min_clean=args.min_clean_before,
        download=args.download,
    )
