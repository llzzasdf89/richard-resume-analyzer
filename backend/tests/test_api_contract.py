from fastapi.testclient import TestClient

from main import server


def test_health_returns_ok():
    client = TestClient(server)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
