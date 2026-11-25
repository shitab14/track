from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_context_resolution():
    # 1. Default user when no header is provided -> u1 (Admin)
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    assert res.json()["data"]["id"] == "u1"
    assert res.json()["data"]["role"] == "admin"

    # 2. Explicit user via X-User-Id header -> u5 (Observer)
    res_obs = client.get("/api/v1/auth/me", headers={"X-User-Id": "u5"})
    assert res_obs.status_code == 200
    assert res_obs.json()["data"]["id"] == "u5"
    assert res_obs.json()["data"]["role"] == "observer"

    # 3. Invalid user ID -> 401 Unauthorized with standard error envelope
    res_invalid = client.get("/api/v1/auth/me", headers={"X-User-Id": "unknown_user"})
    assert res_invalid.status_code == 401
    assert res_invalid.json()["code"] == 401
    assert res_invalid.json()["data"] is None

def test_team_member_cross_team_access_refusal():
    # u6 is Team Member of 'team_sales' ONLY.
    # Reading own team 'team_sales' -> 200 OK
    res_own = client.get("/api/v1/auth/teams/team_sales/verify-read", headers={"X-User-Id": "u6"})
    assert res_own.status_code == 200

    # Reading another team 'team_ops' -> 403 Forbidden
    res_other = client.get("/api/v1/auth/teams/team_ops/verify-read", headers={"X-User-Id": "u6"})
    assert res_other.status_code == 403
    assert res_other.json()["code"] == 403
    assert "denied" in res_other.json()["message"].lower()

    # Reading non-existent / guessed team ID -> 404
    res_guessed = client.get("/api/v1/auth/teams/non_existent_team/verify-read", headers={"X-User-Id": "u6"})
    assert res_guessed.status_code == 404

def test_observer_read_allowed_write_refused():
    # u5 is Observer of 'team_lead'
    # 1. Reading team_lead -> 200 OK
    res_read = client.get("/api/v1/auth/teams/team_lead/verify-read", headers={"X-User-Id": "u5"})
    assert res_read.status_code == 200

    # 2. Writing to team_lead -> 403 Forbidden
    res_write = client.post("/api/v1/auth/teams/team_lead/verify-write", headers={"X-User-Id": "u5"})
    assert res_write.status_code == 403
    assert res_write.json()["code"] == 403
    assert "observers have read-only access" in res_write.json()["message"].lower()

def test_admin_universal_access():
    # u1 is Admin (only in team_lead membership in seed)
    # 1. Read own team -> 200 OK
    assert client.get("/api/v1/auth/teams/team_lead/verify-read", headers={"X-User-Id": "u1"}).status_code == 200

    # 2. Read team_sales (where u1 is NOT an explicit member) -> 200 OK
    assert client.get("/api/v1/auth/teams/team_sales/verify-read", headers={"X-User-Id": "u1"}).status_code == 200

    # 3. Write to team_ops -> 200 OK
    assert client.post("/api/v1/auth/teams/team_ops/verify-write", headers={"X-User-Id": "u1"}).status_code == 200
