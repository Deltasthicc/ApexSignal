"""SQLite incident metadata store for ECHO LAP memory.

The table structure is owned by ``storage/schema.sql`` and is applied
verbatim; this module never redefines or migrates it. Embeddings are not
stored here -- ``incidents.embedding_index`` is a pointer into whatever
vector store ``services/evidence_memory`` is currently backed by.

Nothing in this module imports a model runtime, so it stays importable
and testable without sentence-transformers or torch installed.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

from app.models import ReportedPhenomenon

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "storage" / "schema.sql"
DEFAULT_DB_PATH = REPO_ROOT / "storage" / "incidents.db"

_INCIDENT_COLUMNS = (
    "incident_id",
    "session_id",
    "driver",
    "event_time_ms",
    "lap",
    "segment",
    "transcript",
    "complaint_category",
    "telemetry_window_path",
    "embedding_index",
    "created_at",
)


class IncidentRecord(BaseModel):
    """One row of the ``incidents`` table.

    Mirrors ``storage/schema.sql``. ``created_at`` is left unset on insert
    so SQLite applies its own ``datetime('now')`` default; it is populated
    on read.
    """

    incident_id: str
    session_id: str
    driver: str
    event_time_ms: int
    lap: int = Field(ge=0)
    segment: str
    transcript: str
    complaint_category: ReportedPhenomenon
    telemetry_window_path: str
    embedding_index: int | None = None
    created_at: str | None = None

    @classmethod
    def from_manifest_entry(cls, entry: dict) -> "IncidentRecord":
        """Build a record from a Workstream A incident-manifest entry.

        The manifest (``contracts/fixtures/incident_manifest.sample.json``)
        uses different field names than the storage schema, so the mapping
        lives here rather than being duplicated at each call site:

        ``sector_or_corner`` -> ``segment``
        ``verified_transcript`` -> ``transcript``
        ``complaint_label`` -> ``complaint_category``

        Manifest-only fields (tyre context, verification notes) are not
        stored: the schema has no column for them and inventing one would
        put this store out of sync with ``storage/schema.sql``.
        """
        return cls(
            incident_id=entry["incident_id"],
            session_id=entry["session_id"],
            driver=entry["driver"],
            event_time_ms=entry["event_time_ms"],
            lap=entry["lap"],
            segment=entry["sector_or_corner"],
            transcript=entry["verified_transcript"],
            complaint_category=entry["complaint_label"],
            telemetry_window_path=entry["telemetry_window_path"],
        )


def resolve_db_path(db_path: str | Path | None = None) -> Path:
    """Resolve a configured database path to an absolute path.

    Relative paths (such as the ``../../storage/incidents.db`` default in
    ``.env.example``) are resolved against the ``services/core_api``
    service root, which is the directory the service is documented to be
    started from. ``:memory:`` is passed through untouched.
    """
    if db_path is None:
        import os

        db_path = os.environ.get("CORE_API_DB_PATH") or DEFAULT_DB_PATH
    if str(db_path) == ":memory:":
        return Path(":memory:")
    candidate = Path(db_path)
    if not candidate.is_absolute():
        candidate = (SERVICE_ROOT / candidate).resolve()
    return candidate


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with the schema applied.

    Safe to call repeatedly: ``storage/schema.sql`` is written with
    ``CREATE TABLE IF NOT EXISTS``, so this both creates a fresh store and
    opens an existing one.
    """
    resolved = resolve_db_path(db_path)
    if str(resolved) != ":memory:":
        resolved.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Apply ``storage/schema.sql`` exactly as written."""
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def insert_incident(
    conn: sqlite3.Connection,
    record: IncidentRecord,
    *,
    replace: bool = False,
) -> None:
    """Insert one incident.

    Raises ``sqlite3.IntegrityError`` on a duplicate ``incident_id``
    unless ``replace`` is set. ``created_at`` is omitted from the
    statement when unset so the schema default applies.
    """
    columns = [c for c in _INCIDENT_COLUMNS if c != "created_at"]
    values: list[object] = [
        record.incident_id,
        record.session_id,
        record.driver,
        record.event_time_ms,
        record.lap,
        record.segment,
        record.transcript,
        record.complaint_category.value,
        record.telemetry_window_path,
        record.embedding_index,
    ]
    if record.created_at is not None:
        columns.append("created_at")
        values.append(record.created_at)

    verb = "INSERT OR REPLACE" if replace else "INSERT"
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(
        f"{verb} INTO incidents ({', '.join(columns)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()


def insert_incidents(
    conn: sqlite3.Connection,
    records: Iterable[IncidentRecord],
    *,
    replace: bool = False,
) -> int:
    """Insert many incidents; returns the number written."""
    count = 0
    for record in records:
        insert_incident(conn, record, replace=replace)
        count += 1
    return count


def get_incident(conn: sqlite3.Connection, incident_id: str) -> IncidentRecord | None:
    """Fetch one incident by id, or ``None`` if it is not stored."""
    row = conn.execute(
        "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)
    ).fetchone()
    return _row_to_record(row) if row is not None else None


def query_incidents(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
    driver: str | None = None,
    complaint_category: ReportedPhenomenon | str | None = None,
    exclude_incident_id: str | None = None,
    before_event_time_ms: int | None = None,
) -> list[IncidentRecord]:
    """Query stored incidents, ordered oldest first by event time.

    ``before_event_time_ms`` restricts results to incidents that happened
    strictly earlier than the given event time. Historical retrieval must
    use it: matching an incident against something that happened after it
    would make any lead-time claim meaningless.
    """
    clauses: list[str] = []
    params: list[object] = []
    if segment is not None:
        clauses.append("segment = ?")
        params.append(segment)
    if driver is not None:
        clauses.append("driver = ?")
        params.append(driver)
    if complaint_category is not None:
        clauses.append("complaint_category = ?")
        params.append(
            complaint_category.value
            if isinstance(complaint_category, ReportedPhenomenon)
            else complaint_category
        )
    if exclude_incident_id is not None:
        clauses.append("incident_id != ?")
        params.append(exclude_incident_id)
    if before_event_time_ms is not None:
        clauses.append("event_time_ms < ?")
        params.append(before_event_time_ms)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM incidents{where} ORDER BY event_time_ms ASC, incident_id ASC",
        params,
    ).fetchall()
    return [_row_to_record(row) for row in rows]


def set_embedding_index(
    conn: sqlite3.Connection, incident_id: str, embedding_index: int | None
) -> None:
    """Point a stored incident at its slot in the vector store."""
    conn.execute(
        "UPDATE incidents SET embedding_index = ? WHERE incident_id = ?",
        (embedding_index, incident_id),
    )
    conn.commit()


def insert_recurrence_flag(
    conn: sqlite3.Connection,
    *,
    triggering_incident_id: str,
    matched_incident_id: str,
    telemetry_similarity: float,
    resolved_state: str = "PENDING",
) -> int:
    """Record that a window resembled a stored incident fingerprint.

    Written synchronously by ``evaluate()`` for the MVP. The charter's
    Flow B background monitor -- which would write these rows on its own
    schedule -- is cut from the MVP; the table is populated the same way
    either path would populate it.
    """
    cursor = conn.execute(
        """
        INSERT INTO recurrence_flags (
            triggering_incident_id, matched_incident_id,
            telemetry_similarity, resolved_state
        ) VALUES (?, ?, ?, ?)
        """,
        (
            triggering_incident_id,
            matched_incident_id,
            telemetry_similarity,
            resolved_state,
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def list_recurrence_flags(
    conn: sqlite3.Connection, *, triggering_incident_id: str | None = None
) -> list[dict]:
    """List recorded recurrence flags, newest first."""
    where = ""
    params: list[object] = []
    if triggering_incident_id is not None:
        where = " WHERE triggering_incident_id = ?"
        params.append(triggering_incident_id)
    rows = conn.execute(
        f"SELECT * FROM recurrence_flags{where} ORDER BY id DESC", params
    ).fetchall()
    return [dict(row) for row in rows]


def load_manifest(manifest_path: str | Path) -> list[IncidentRecord]:
    """Read a Workstream A incident manifest into storage records."""
    entries = json.loads(Path(manifest_path).read_text())
    return [IncidentRecord.from_manifest_entry(entry) for entry in entries]


def _row_to_record(row: sqlite3.Row) -> IncidentRecord:
    return IncidentRecord.model_validate({key: row[key] for key in row.keys()})
