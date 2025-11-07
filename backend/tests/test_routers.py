from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_room_ok():
    r = client.post("/rooms", json={"seats": 9, "fill_ai": False, "name": "Test Room"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["seats"] == 9
    assert body["data"]["name"] == "Test Room"
    assert "id" in body["data"]


def test_create_room_invalid_seats():
    r = client.post("/rooms", json={"seats": 5, "fill_ai": False})
    assert r.status_code == 400
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_list_rooms_ok():
    r = client.get("/rooms")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert isinstance(body["data"], list)


def test_get_room_not_found():
    r = client.get("/rooms/nonexistent")
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ROOM_NOT_FOUND"


def test_join_room_ok():
    # Create room first
    r1 = client.post("/rooms", json={"seats": 6, "fill_ai": False})
    room_id = r1.json()["data"]["id"]

    # Join room
    r2 = client.post(f"/rooms/{room_id}/join", json={"seat": 1})
    assert r2.status_code == 200
    body = r2.json()
    assert body["ok"] is True


def test_stats_rooms_ok():
    r = client.get("/stats/rooms")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "total_rooms" in body["data"]


def test_billing_products_ok():
    r = client.get("/billing/products")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert isinstance(body["data"], list)


def test_billing_purchase_ok():
    r = client.post("/billing/purchase")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "order_id" in body["data"]


def test_stt_transcribe_ok():
    r = client.post("/stt/transcribe", json={"audio_base64": "test", "mime": "audio/wav"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True


def test_ai_generate_speech_ok():
    r = client.post(
        "/ai/generate_speech",
        json={"role": "狼人", "phase": "Day", "visible_state": {}, "history_summary": None},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "text" in body["data"]


def test_ai_decide_action_ok():
    r = client.post(
        "/ai/decide_action",
        json={"options": [1, 2, 3], "role": "狼人", "phase": "Night", "visible_state": {}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "pick" in body["data"]


def test_replay_timeline_not_found():
    r = client.get("/replay/nonexistent/timeline")
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "GAME_NOT_FOUND"
