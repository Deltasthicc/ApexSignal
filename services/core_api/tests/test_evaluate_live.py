"""The Workstream C independent test, end to end.

    "With synthetic transcript/category/telemetry fixtures, this service
     can store an incident, retrieve it, compare a later window, and
     produce an assessment without radio_ai or apps/web running."
                                    -- charter section 11, Workstream C

Nothing here starts another service. The only inputs are a SQLite store,
Parquet telemetry, and RadioAnalysisOutput JSON files on disk.

Every assessment produced is validated against the frozen JSON schema at
contracts/schemas/incident_assessment.schema.json, not just against the
Pydantic model, so a drift between the two would fail here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app  # noqa: F401  -- puts services/ on sys.path
from app import db
from app.config import REPO_ROOT
from app.db import IncidentRecord
from app.models import ReportedPhenomenon
from evidence_memory import synthetic

SCHEMA_PATH = REPO_ROOT / "contracts" / "schemas" / "incident_assessment.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def assert_matches_contract(payload: dict, schema: dict) -> None:
    """Validate against the frozen schema, not just the Pydantic model."""
    import jsonschema

    jsonschema.validate(instance=payload, schema=schema)


# --- world building ------------------------------------------------------


def _write_radio(
    directory: Path,
    incident_id: str,
    transcript: str,
    category: str | None = "EXIT_TRACTION_REAR",
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "incident_id": incident_id,
        "transcript": transcript,
        "tone_label": "ELEVATED_AROUSAL",
        "tone_score": 0.73,
        "tone_confidence": 0.61,
        "complaint_category": category,
        "category_confidence": 0.86 if category else None,
    }
    (directory / f"{incident_id}.json").write_text(json.dumps(payload))


def _record(
    incident_id: str,
    *,
    lap: int,
    event_time_ms: int,
    telemetry_path: str,
    transcript: str,
    segment: str = "T7_EXIT",
    category: ReportedPhenomenon = ReportedPhenomenon.EXIT_TRACTION_REAR,
) -> IncidentRecord:
    return IncidentRecord(
        incident_id=incident_id,
        session_id="TEST_SESSION",
        driver="TEST_DRIVER",
        event_time_ms=event_time_ms,
        lap=lap,
        segment=segment,
        transcript=transcript,
        complaint_category=category,
        telemetry_window_path=telemetry_path,
    )


@pytest.fixture()
def world(tmp_path: Path, monkeypatch):
    """A self-contained ApexSignal world on disk.

    INC-017 -- an earlier rear-traction report on lap 14, steady car.
    INC-031 -- a report on lap 26, one lap BEFORE a real deterioration
               begins on lap 27. The driver is ahead of the data, so the
               car still looks normal at the moment of the call and a
               lead time exists. This is the product's core case.
    INC-045 -- a report on lap 28, one lap AFTER the same deterioration
               began, so the deviation is already measurable against a
               baseline that is still mostly clean.
    """
    telemetry_dir = tmp_path / "data" / "telemetry"
    radio_dir = tmp_path / "data" / "radio_analysis"

    early = synthetic.synthetic_window(laps=list(range(10, 21)))
    synthetic.write_window(early, telemetry_dir / "INC-017.parquet")

    later = synthetic.synthetic_window(
        laps=list(range(22, 33)),
        degrade_from_lap=27,
        throttle_pickup_delay=0.10,
        exit_speed_loss_kph=18.0,
    )
    synthetic.write_window(later, telemetry_dir / "INC-031.parquet")

    _write_radio(radio_dir, "INC-017", "Rear is moving on throttle.")
    _write_radio(radio_dir, "INC-031", "Same thing again, rear is loose out of seven.")
    _write_radio(radio_dir, "INC-045", "Rear is snapping on power out of seven.")

    db_path = tmp_path / "incidents.db"
    connection = db.connect(db_path)
    db.insert_incidents(
        connection,
        [
            _record(
                "INC-017",
                lap=14,
                event_time_ms=14 * 90 * 1000,
                telemetry_path=str(telemetry_dir / "INC-017.parquet"),
                transcript="Rear is moving on throttle.",
            ),
            _record(
                "INC-031",
                lap=26,
                event_time_ms=26 * 90 * 1000,
                telemetry_path=str(telemetry_dir / "INC-031.parquet"),
                transcript="Same thing again, rear is loose out of seven.",
            ),
            _record(
                "INC-045",
                lap=28,
                event_time_ms=28 * 90 * 1000,
                telemetry_path=str(telemetry_dir / "INC-031.parquet"),
                transcript="Rear is snapping on power out of seven.",
            ),
        ],
    )
    connection.close()

    monkeypatch.setenv("EVALUATE_MODE", "live")
    monkeypatch.setenv("CORE_API_DB_PATH", str(db_path))
    monkeypatch.setenv("CORE_API_RADIO_ANALYSIS_DIR", str(radio_dir))
    monkeypatch.setenv("CORE_API_TELEMETRY_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture()
def client():
    from app.main import app as fastapi_app

    return TestClient(fastapi_app)


# --- fixture mode must not regress --------------------------------------


def test_fixture_mode_still_returns_the_frozen_fixture(client, schema, monkeypatch):
    """Workstream D depends on this. It must not change."""
    monkeypatch.setenv("EVALUATE_MODE", "fixture")
    fixture = json.loads(
        (REPO_ROOT / "contracts" / "fixtures" / "incident_assessment.sample.json").read_text()
    )

    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-999"})
    assert response.status_code == 200

    body = response.json()
    assert_matches_contract(body, schema)
    assert body["incident_id"] == "INC-999"
    for field in (
        "lap",
        "segment",
        "reported_phenomenon",
        "baseline_evidence",
        "echo_match",
        "driver_warning_lead_time_s",
        "recurrence_state",
        "human_message",
    ):
        assert body[field] == fixture[field]


def test_fixture_mode_is_the_default(client, schema, monkeypatch):
    monkeypatch.delenv("EVALUATE_MODE", raising=False)
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-1"})
    assert response.status_code == 200
    assert_matches_contract(response.json(), schema)


# --- the independent test ------------------------------------------------


def test_store_retrieve_compare_assess_with_no_other_service(client, schema, world):
    """Store an incident, retrieve it, compare a later window, assess."""
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-031"})
    assert response.status_code == 200, response.text

    body = response.json()
    assert_matches_contract(body, schema)

    assert body["incident_id"] == "INC-031"
    assert body["lap"] == 26
    assert body["segment"] == "T7_EXIT"
    assert body["reported_phenomenon"] == "EXIT_TRACTION_REAR"

    # The earlier incident was retrieved from memory.
    assert body["echo_match"] is not None
    assert body["echo_match"]["incident_id"] == "INC-017"
    assert body["echo_match"]["same_segment"] is True

    # Both similarity components present and separate.
    assert 0.0 <= body["echo_match"]["semantic_similarity"] <= 1.0
    assert 0.0 <= body["echo_match"]["telemetry_similarity"] <= 1.0

    # The driver said "again", and a prior report of the same phenomenon
    # is on record for it to refer to.
    assert body["recurrence_state"] == "CONFIRMED_BY_RADIO"

    # The product's core case: the driver spoke one lap BEFORE the car
    # measurably changed. At the moment of the call the telemetry is
    # still within their own baseline -- and a lead time exists precisely
    # because of that ordering. Reporting NO_DEVIATION here is correct,
    # not a miss.
    assert body["baseline_evidence"]["status"] == "NO_DEVIATION"
    assert body["driver_warning_lead_time_s"] is not None
    assert body["driver_warning_lead_time_s"] > 0


def test_deviation_is_measured_when_the_report_follows_the_change(
    client, schema, world
):
    """INC-045 reports on lap 28, one lap into the deterioration."""
    body = client.post(
        "/v1/incidents/evaluate", params={"incident_id": "INC-045"}
    ).json()
    assert_matches_contract(body, schema)

    assert body["lap"] == 28
    assert body["baseline_evidence"]["status"] == "BEHAVIOR_CONSISTENT"
    # Slower through the segment, and later to power, than their own baseline.
    assert body["baseline_evidence"]["sector_delta_s"] > 0
    assert body["baseline_evidence"]["throttle_pickup_delta_pct"] < 0


def test_get_endpoint_returns_the_same_assessment(client, schema, world):
    posted = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-031"})
    fetched = client.get("/v1/incidents/INC-031")
    assert fetched.status_code == 200
    assert_matches_contract(fetched.json(), schema)
    assert fetched.json() == posted.json()


def test_first_incident_has_no_history_to_match(client, schema, world):
    """INC-017 is the earliest incident: echo_match must be null."""
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-017"})
    assert response.status_code == 200

    body = response.json()
    assert_matches_contract(body, schema)
    assert body["echo_match"] is None
    assert body["recurrence_state"] == "NONE"


def test_null_lead_time_is_reported_honestly(client, schema, world, tmp_path):
    """A steady car after the call means null, and the message says so."""
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-017"})
    body = response.json()

    assert_matches_contract(body, schema)
    assert body["driver_warning_lead_time_s"] is None
    assert "No measurable lead-time established" in body["human_message"]


def test_lead_time_is_present_when_deterioration_follows(client, world):
    body = client.post(
        "/v1/incidents/evaluate", params={"incident_id": "INC-031"}
    ).json()
    assert body["driver_warning_lead_time_s"] > 0
    assert "No measurable lead-time established" not in body["human_message"]


# --- honest failure modes ------------------------------------------------


def test_unknown_incident_is_404_not_a_fabricated_assessment(client, world):
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-NOPE"})
    assert response.status_code == 404
    assert "not in the store" in response.json()["detail"]


def test_missing_radio_analysis_is_422_with_the_expected_path(
    client, world, tmp_path
):
    (tmp_path / "data" / "radio_analysis" / "INC-031.json").unlink()
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-031"})
    assert response.status_code == 422
    assert "no RadioAnalysisOutput" in response.json()["detail"]


def test_missing_telemetry_is_422_with_the_expected_path(client, world, tmp_path):
    (tmp_path / "data" / "telemetry" / "INC-031.parquet").unlink()
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-031"})
    assert response.status_code == 422
    assert "telemetry window" in response.json()["detail"]


def test_malformed_radio_analysis_is_rejected_against_the_contract(
    client, world, tmp_path
):
    path = tmp_path / "data" / "radio_analysis" / "INC-031.json"
    path.write_text(json.dumps({"incident_id": "INC-031", "tone_label": "SLEEPY"}))
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-031"})
    assert response.status_code == 422
    assert "does not match the frozen contract" in response.json()["detail"]


def test_non_complaint_radio_cannot_produce_an_assessment(client, world, tmp_path):
    """complaint_category may be null; reported_phenomenon may not."""
    _write_radio(
        tmp_path / "data" / "radio_analysis",
        "INC-031",
        "Box this lap, box box.",
        category=None,
    )
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-031"})
    assert response.status_code == 422
    assert "no complaint_category" in response.json()["detail"]


# --- contract guarantees -------------------------------------------------


def test_no_composite_risk_score_anywhere_in_the_output(client, world):
    body = client.post(
        "/v1/incidents/evaluate", params={"incident_id": "INC-031"}
    ).json()
    flattened = json.dumps(body).lower()
    for banned in ("risk_score", "confidence_score", "composite", "overall_score"):
        assert banned not in flattened


def test_human_message_stays_in_the_interpretation_safe_register(client, world):
    """Charter: reported phenomenon, never diagnosed fault."""
    banned = (
        "fault confirmed",
        "confirmed fault",
        "diagnos",
        "lie detect",
        "lying",
        "deception",
        "failure confirmed",
        "stress caused",
        "fatigue",
        "grip coefficient",
    )
    for incident_id in ("INC-017", "INC-031"):
        body = client.post(
            "/v1/incidents/evaluate", params={"incident_id": incident_id}
        ).json()
        message = body["human_message"].lower()
        for phrase in banned:
            assert phrase not in message, f"{incident_id}: {phrase!r} in human_message"


def test_similarity_is_described_as_prototype_not_probability(client, world):
    body = client.post(
        "/v1/incidents/evaluate", params={"incident_id": "INC-031"}
    ).json()
    assert "probability" not in body["human_message"].lower()
    assert "PROTOTYPE" in body["echo_match"]["label"] or body["echo_match"] is None


def test_health_needs_no_heavy_dependencies(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"


# --- ingest --------------------------------------------------------------


def test_ingest_loads_the_manifest_into_the_store(tmp_path, monkeypatch):
    from app.ingest import ingest

    manifest = REPO_ROOT / "contracts" / "fixtures" / "incident_manifest.sample.json"
    db_path = tmp_path / "ingested.db"
    monkeypatch.setenv("CORE_API_MANIFEST_PATH", str(manifest))
    monkeypatch.setenv("CORE_API_DB_PATH", str(db_path))

    assert ingest() == 3

    connection = db.connect(db_path)
    stored = db.get_incident(connection, "INC-114")
    connection.close()
    assert stored is not None
    assert stored.segment == "T7_EXIT"
