import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthz_ok():
    r = client.get("/healthz", headers={"x-request-id": "t123"})
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_auth_guest_ok():
    r = client.post("/auth/guest")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert set(body["data"].keys()) == {"token", "refresh"}


def test_auth_email_flow_ok(monkeypatch):
    # valid request sets a code in memory; we don't know the code,
    # but we can swap the internal store for deterministic behavior
    from app.routers import auth as auth_router

    store = {}
    monkeypatch.setattr(auth_router, "_email_codes", store, raising=True)

    email = "a@b.com"
    r1 = client.post("/auth/email/request", json={"email": email})
    assert r1.status_code == 200
    assert r1.json() == {"ok": True}

    code = next(iter(store.values()))
    r2 = client.post("/auth/email/verify", json={"email": email, "code": code})
    assert r2.status_code == 200
    body = r2.json()
    assert body["ok"] is True
    assert set(body["data"].keys()) == {"token", "refresh"}
