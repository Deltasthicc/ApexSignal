from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["evaluate_mode"] in {"fixture", "live"}
