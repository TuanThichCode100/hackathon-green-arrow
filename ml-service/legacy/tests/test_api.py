from fastapi.testclient import TestClient

from app import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_forecast_with_invalid_location_returns_404():
    client = TestClient(app)
    response = client.post(
        "/forecast",
        json={"location_name": "some location", "horizon_name": "day3"},
    )
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]
