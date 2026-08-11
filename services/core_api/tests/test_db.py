"""Storage-layer tests: insert a fixture incident, read it back.

Runs against a temporary database file, never the developer's real
storage/incidents.db.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app import db
from app.db import IncidentRecord
from app.models import ReportedPhenomenon

MANIFEST_FIXTURE = (
    db.REPO_ROOT / "contracts" / "fixtures" / "incident_manifest.sample.json"
)


@pytest.fixture()
def conn(tmp_path: Path):
    connection = db.connect(tmp_path / "incidents.db")
    yield connection
    connection.close()


def _record(incident_id: str = "INC-017", **overrides) -> IncidentRecord:
    base = dict(
        incident_id=incident_id,
        session_id="TEST_SESSION",
        driver="TEST_DRIVER",
        event_time_ms=1_200_000,
        lap=17,
        segment="T7_EXIT",
        transcript="Rear is moving on throttle.",
        complaint_category=ReportedPhenomenon.EXIT_TRACTION_REAR,
        telemetry_window_path="data/telemetry/INC-017.parquet",
    )
    base.update(overrides)
    return IncidentRecord(**base)


def test_schema_applied_matches_storage_schema_sql(conn: sqlite3.Connection):
    """The store is built from storage/schema.sql, not a local redefinition."""
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"incidents", "recurrence_flags"} <= tables

    columns = {row["name"] for row in conn.execute("PRAGMA table_info(incidents)")}
    assert columns == {
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
    }


def test_connect_is_idempotent(tmp_path: Path):
    path = tmp_path / "incidents.db"
    first = db.connect(path)
    db.insert_incident(first, _record())
    first.close()

    second = db.connect(path)
    assert second.execute("SELECT COUNT(*) AS n FROM incidents").fetchone()["n"] == 1
    second.close()


def test_insert_fixture_incident_and_read_it_back(conn: sqlite3.Connection):
    """The independent-test criterion, first half: store then retrieve."""
    records = db.load_manifest(MANIFEST_FIXTURE)
    assert records, "incident manifest fixture is empty"

    db.insert_incidents(conn, records)

    manifest = json.loads(MANIFEST_FIXTURE.read_text())
    for entry in manifest:
        stored = db.get_incident(conn, entry["incident_id"])
        assert stored is not None
        # Manifest field names differ from the storage schema; check the mapping.
        assert stored.segment == entry["sector_or_corner"]
        assert stored.transcript == entry["verified_transcript"]
        assert stored.complaint_category.value == entry["complaint_label"]
        assert stored.telemetry_window_path == entry["telemetry_window_path"]
        assert stored.lap == entry["lap"]
        assert stored.event_time_ms == entry["event_time_ms"]
        assert stored.created_at is not None  # schema default applied


def test_get_incident_returns_none_when_absent(conn: sqlite3.Connection):
    assert db.get_incident(conn, "INC-DOES-NOT-EXIST") is None


def test_duplicate_incident_id_rejected_unless_replacing(conn: sqlite3.Connection):
    db.insert_incident(conn, _record())
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_incident(conn, _record())

    db.insert_incident(conn, _record(transcript="Rear stepped out again."), replace=True)
    stored = db.get_incident(conn, "INC-017")
    assert stored is not None
    assert stored.transcript == "Rear stepped out again."


def test_query_by_segment_and_driver(conn: sqlite3.Connection):
    db.insert_incidents(
        conn,
        [
            _record("INC-017", segment="T7_EXIT", driver="DRV_A", event_time_ms=1_000),
            _record("INC-031", segment="T7_EXIT", driver="DRV_A", event_time_ms=3_000),
            _record("INC-042", segment="T4_ENTRY", driver="DRV_A", event_time_ms=2_000),
            _record("INC-055", segment="T7_EXIT", driver="DRV_B", event_time_ms=4_000),
        ],
    )

    by_segment = db.query_incidents(conn, segment="T7_EXIT")
    assert [r.incident_id for r in by_segment] == ["INC-017", "INC-031", "INC-055"]

    by_driver = db.query_incidents(conn, driver="DRV_A")
    assert [r.incident_id for r in by_driver] == ["INC-017", "INC-042", "INC-031"]

    both = db.query_incidents(conn, segment="T7_EXIT", driver="DRV_A")
    assert [r.incident_id for r in both] == ["INC-017", "INC-031"]

    assert db.query_incidents(conn, segment="NO_SUCH_SEGMENT") == []


def test_query_excludes_self_and_future_incidents(conn: sqlite3.Connection):
    """Retrieval must never match against an incident from the future."""
    db.insert_incidents(
        conn,
        [
            _record("INC-017", event_time_ms=1_000),
            _record("INC-031", event_time_ms=3_000),
            _record("INC-099", event_time_ms=9_000),
        ],
    )

    prior = db.query_incidents(
        conn,
        segment="T7_EXIT",
        exclude_incident_id="INC-031",
        before_event_time_ms=3_000,
    )
    assert [r.incident_id for r in prior] == ["INC-017"]


def test_query_by_complaint_category(conn: sqlite3.Connection):
    db.insert_incidents(
        conn,
        [
            _record("INC-017", complaint_category=ReportedPhenomenon.EXIT_TRACTION_REAR),
            _record("INC-031", complaint_category=ReportedPhenomenon.FRONT_TURNIN_BRAKE),
        ],
    )
    matches = db.query_incidents(
        conn, complaint_category=ReportedPhenomenon.EXIT_TRACTION_REAR
    )
    assert [r.incident_id for r in matches] == ["INC-017"]


def test_embedding_index_round_trip(conn: sqlite3.Connection):
    db.insert_incident(conn, _record())
    stored = db.get_incident(conn, "INC-017")
    assert stored is not None and stored.embedding_index is None

    db.set_embedding_index(conn, "INC-017", 3)
    stored = db.get_incident(conn, "INC-017")
    assert stored is not None and stored.embedding_index == 3


def test_recurrence_flag_round_trip(conn: sqlite3.Connection):
    db.insert_incidents(conn, [_record("INC-017"), _record("INC-031")])
    flag_id = db.insert_recurrence_flag(
        conn,
        triggering_incident_id="INC-031",
        matched_incident_id="INC-017",
        telemetry_similarity=0.81,
    )
    assert flag_id > 0

    flags = db.list_recurrence_flags(conn, triggering_incident_id="INC-031")
    assert len(flags) == 1
    assert flags[0]["matched_incident_id"] == "INC-017"
    assert flags[0]["telemetry_similarity"] == pytest.approx(0.81)
    assert flags[0]["resolved_state"] == "PENDING"


def test_recurrence_flag_requires_known_matched_incident(conn: sqlite3.Connection):
    """The schema's foreign key is enforced, so flags can't dangle."""
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_recurrence_flag(
            conn,
            triggering_incident_id="INC-031",
            matched_incident_id="INC-NOT-STORED",
            telemetry_similarity=0.5,
        )


def test_invalid_complaint_category_rejected():
    """The complaint taxonomy is frozen at five values."""
    with pytest.raises(ValueError):
        _record(complaint_category="TYRES_ARE_SAD")


def test_resolve_db_path_handles_relative_env_default():
    """The .env.example default resolves against the service root."""
    resolved = db.resolve_db_path("../../storage/incidents.db")
    assert resolved.is_absolute()
    assert resolved == db.REPO_ROOT / "storage" / "incidents.db"
