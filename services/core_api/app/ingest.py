"""Load Workstream A's incident manifest into the SQLite store.

    python -m app.ingest [--replace]

Run from `services/core_api/`. Reads `CORE_API_MANIFEST_PATH` (default
`data/incident_manifest.json`) and writes to `CORE_API_DB_PATH`.
"""

from __future__ import annotations

import argparse
import sys

from app import db
from app.config import load_settings
from app.pipeline import EvaluationError, load_manifest_entries


def ingest(*, replace: bool = False) -> int:
    """Load every manifest entry into the store; returns the count written."""
    settings = load_settings()
    records = load_manifest_entries(settings)

    connection = db.connect(settings.db_path)
    try:
        written = db.insert_incidents(connection, records, replace=replace)
    finally:
        connection.close()
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="overwrite incidents already in the store",
    )
    args = parser.parse_args(argv)

    try:
        written = ingest(replace=args.replace)
    except EvaluationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    settings = load_settings()
    print(f"loaded {written} incident(s) from {settings.manifest_path}")
    print(f"into {db.resolve_db_path(settings.db_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
