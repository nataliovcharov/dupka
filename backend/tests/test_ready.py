from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ready_reports_postgis():
    # needs the database running (docker compose locally, service container in CI)
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["postgis"].startswith("3.5")
