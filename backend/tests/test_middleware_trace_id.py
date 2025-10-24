from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_trace_id_middleware_echo_and_generate():
    # echo header
    r1 = client.get("/healthz", headers={"x-request-id": "abc123xyz789"})
    assert r1.headers["x-request-id"] == "abc123xyz789"

    # generate when absent (length 12 hex)
    r2 = client.get("/healthz")
    tid = r2.headers.get("x-request-id")
    assert isinstance(tid, str) and len(tid) == 12
