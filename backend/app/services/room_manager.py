from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


def now_ts() -> float:
    return time.time()


def short_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time()*1000)%1000000:06d}"


@dataclass
class Member:
    user_id: str
    seat: int | None = None


@dataclass
class Room:
    id: str
    name: str | None
    seats: int
    fill_ai: bool = False
    owner_id: str | None = None
    members: dict[str, Member] = field(default_factory=dict)  # user_id -> Member
    created_at: float = field(default_factory=now_ts)
    game_id: str | None = None


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def create_room(self, *, seats: int, fill_ai: bool, name: str | None, owner_id: str | None) -> Room:
        room_id = short_id("r")
        room = Room(id=room_id, name=name, seats=seats, fill_ai=fill_ai, owner_id=owner_id)
        self.rooms[room_id] = room
        return room

    def get(self, room_id: str) -> Room | None:
        return self.rooms.get(room_id)

    def join(self, room_id: str, user_id: str, seat: int | None = None) -> Room:
        room = self.rooms[room_id]
        if user_id in room.members:
            return room
        room.members[user_id] = Member(user_id=user_id, seat=seat)
        return room

    def leave(self, room_id: str, user_id: str) -> Room:
        room = self.rooms[room_id]
        room.members.pop(user_id, None)
        return room

    def start_game(self, room_id: str) -> str:
        room = self.rooms[room_id]
        gid = short_id("g")
        room.game_id = gid
        return gid


# Singleton for test period
room_manager = RoomManager()

