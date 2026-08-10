from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_evaluate_fixture_mode_returns_valid_shape():
    response = client.post("/v1/incidents/evaluate", params={"incident_id": "INC-999"})
    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == "INC-999"
    assert body["recurrence_state"] in {"NONE", "POSSIBLE_RECURRENCE", "CONFIRMED_BY_RADIO"}
