from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data
    assert json_data["message"] == "Welcome to Track Backend API"

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data["data"]["status"] == "healthy"
    assert json_data["data"]["timezone"] == "America/Chicago"

def test_404_error_envelope():
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["code"] == 404
    assert json_data["data"] is None
    assert "Not Found" in json_data["message"]

def test_mock_team_summary():
    response = client.get("/api/v1/mock/team-summary")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data["data"]["team"]["id"] == "team_lead"
    assert len(json_data["data"]["sampleMeasurables"]) == 2

