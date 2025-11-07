from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Path
from pydantic import BaseModel, Field
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.errors import DomainError
from app.services.room_manager import room_manager

router = APIRouter()


class CreateRoomIn(BaseModel):
    seats: int = Field(ge=6, le=10)
    fill_ai: bool = False
    name: str | None = None


class RoomOut(BaseModel):
    id: str
    seats: int
    name: str | None
    owner_id: str | None
    fill_ai: bool
    member_count: int
    game_id: str | None


class JoinRoomIn(BaseModel):
    seat: int | None = Field(default=None, ge=1, le=10)


def _room_to_out(room) -> RoomOut:
    return RoomOut(
        id=room.id,
        seats=room.seats,
        name=room.name,
        owner_id=room.owner_id,
        fill_ai=room.fill_ai,
        member_count=len(room.members),
        game_id=room.game_id,
    )


@router.get("")
async def list_rooms():
    rooms = [_room_to_out(r) for r in room_manager.rooms.values()]
    return {"ok": True, "data": rooms}


@router.post("")
async def create_room(
    payload: Annotated[CreateRoomIn, Body(...)],
    # TODO: get user from JWT, for now stub
):
    if payload.seats not in (6, 9, 10):
        raise DomainError(
            code="VALIDATION_ERROR", http_status=400, message="seats must be 6, 9, or 10"
        )
    user_id = "stub_user"  # TODO: from JWT
    room = room_manager.create_room(
        seats=payload.seats, fill_ai=payload.fill_ai, name=payload.name, owner_id=user_id
    )
    return {"ok": True, "data": _room_to_out(room)}


@router.get("/{room_id}")
async def get_room(room_id: Annotated[str, Path(min_length=1)]):
    room = room_manager.get(room_id)
    if not room:
        raise DomainError(
            code="ROOM_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="room not found"
        )
    return {"ok": True, "data": _room_to_out(room)}


@router.post("/{room_id}/join")
async def join_room(
    room_id: Annotated[str, Path(min_length=1)],
    payload: Annotated[JoinRoomIn, Body(...)],
):
    room = room_manager.get(room_id)
    if not room:
        raise DomainError(
            code="ROOM_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="room not found"
        )
    user_id = "stub_user"  # TODO: from JWT
    if len(room.members) >= room.seats:
        raise DomainError(code="ROOM_FULL", http_status=409, message="room is full")
    room = room_manager.join(room_id, user_id, payload.seat)
    return {"ok": True, "data": _room_to_out(room)}


@router.post("/{room_id}/leave")
async def leave_room(room_id: Annotated[str, Path(min_length=1)]):
    room = room_manager.get(room_id)
    if not room:
        raise DomainError(
            code="ROOM_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="room not found"
        )
    user_id = "stub_user"  # TODO: from JWT
    room = room_manager.leave(room_id, user_id)
    return {"ok": True, "data": _room_to_out(room)}


@router.post("/{room_id}/start")
async def start_room(room_id: Annotated[str, Path(min_length=1)]):
    room = room_manager.get(room_id)
    if not room:
        raise DomainError(
            code="ROOM_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="room not found"
        )
    user_id = "stub_user"  # TODO: from JWT
    if room.owner_id != user_id:
        raise DomainError(
            code="ROOM_FORBIDDEN", http_status=HTTP_403_FORBIDDEN, message="only owner can start"
        )
    if len(room.members) < room.seats and not room.fill_ai:
        raise DomainError(code="VALIDATION_ERROR", http_status=400, message="not enough players")
    game_id = room_manager.start_game(room_id)
    return {"ok": True, "data": {"game_id": game_id}}
