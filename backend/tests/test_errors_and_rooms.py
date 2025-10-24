from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_validation_error_shape():
    # Missing email should trigger validation error shape (DomainError handled to 400)
    r = client.post("/auth/email/request", json={})
    assert r.status_code == 400
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_auth_invalid_code_error():
    r = client.post("/auth/email/verify", json={"email": "a@b.com", "code": "000000"})
    assert r.status_code == 401
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "AUTH_INVALID_CODE"


def test_internal_error_guard_shape():
    # unhandled error gets wrapped as INTERNAL_ERROR (500)
    r = client.post("/games/crash", json={"x": 1}, headers={"x-request-id": "t456"})
    assert r.status_code == 500
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INTERNAL_ERROR"
    # ensure trace id is echoed
    assert body["error"]["trace_id"] == "t456"


def test_rooms_list_ok():
    r = client.get("/rooms/")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"] == []
