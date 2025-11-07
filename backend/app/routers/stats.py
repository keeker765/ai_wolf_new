from __future__ import annotations

from fastapi import APIRouter

from app.services.room_manager import room_manager

router = APIRouter()


@router.get("/rooms")
async def get_room_stats():
    """Get current room statistics."""
    total_rooms = len(room_manager.rooms)
    active_games = sum(1 for r in room_manager.rooms.values() if r.game_id is not None)
    total_players = sum(len(r.members) for r in room_manager.rooms.values())
    return {
        "ok": True,
        "data": {
            "total_rooms": total_rooms,
            "active_games": active_games,
            "total_players": total_players,
        },
    }
