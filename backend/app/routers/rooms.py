from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body

from app.core.errors import DomainError
from app.services.room_manager import room_manager

router = APIRouter()


@router.get("/")
async def list_rooms():
    data = [
        {
            "id": r.id,
            "name": r.name,
            "seats": r.seats,
            "fill_ai": r.fill_ai,
            "owner_id": r.owner_id,
            "members": list(r.members.keys()),
            "game_id": r.game_id,
        }
        for r in room_manager.rooms.values()
    ]
    return {"ok": True, "data": data}


@router.post("/")
async def create_room(payload: Annotated[dict, Body(...)]):
    seats = payload.get("seats")
    if not isinstance(seats, int) or seats < 2 or seats > 12:
        raise DomainError(code="VALIDATION_ERROR", http_status=400, message="invalid seats")
    name = payload.get("name")
    fill_ai = bool(payload.get("fill_ai", False))
    owner_id = payload.get("owner_id")
    r = room_manager.create_room(seats=seats, fill_ai=fill_ai, name=name, owner_id=owner_id)
    return {
        "ok": True,
        "data": {
            "id": r.id,
            "name": r.name,
            "seats": r.seats,
            "fill_ai": r.fill_ai,
            "owner_id": r.owner_id,
            "members": list(r.members.keys()),
            "game_id": r.game_id,
        },
    }


@router.delete("/{room_id}")
async def delete_room(room_id: str):
    r = room_manager.get(room_id)
    if not r:
        raise DomainError(code="ROOM_NOT_FOUND", http_status=404, message="room not found")
    room_manager.rooms.pop(room_id, None)
    return {"ok": True}
