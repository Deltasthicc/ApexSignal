from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_fixture_mode_returns_valid_shape():
    response = client.post("/v1/radio/analyze", params={"incident_id": "INC-999"})
    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == "INC-999"
    assert body["tone_label"] in {"CALM", "ELEVATED_AROUSAL", "FATIGUED"}
