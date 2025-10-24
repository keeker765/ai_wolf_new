from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rooms_create_and_list_and_delete():
    # initially empty
    r0 = client.get("/rooms/")
    assert r0.status_code == 200
    assert r0.json()["data"] == []

    # create
    r1 = client.post("/rooms/", json={"seats": 6, "name": "A", "fill_ai": True, "owner_id": "u1"})
    assert r1.status_code == 200
    body = r1.json()
    assert body["ok"] is True
    room_id = body["data"]["id"]

    # list contains the room
    r2 = client.get("/rooms/")
    assert r2.status_code == 200
    ids = [x["id"] for x in r2.json()["data"]]
    assert room_id in ids

    # delete
    r3 = client.delete(f"/rooms/{room_id}")
    assert r3.status_code == 200
    assert r3.json() == {"ok": True}

    # delete again -> 404
    r4 = client.delete(f"/rooms/{room_id}")
    assert r4.status_code == 404
    err = r4.json()["error"]
    assert err["code"] == "ROOM_NOT_FOUND"


def test_rooms_create_validation():
    # invalid seats
    r = client.post("/rooms/", json={"seats": 1})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
