from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Path, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from app.core.errors import DomainError

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for test period
_games: dict[str, dict] = {}  # game_id -> game state
_ws_connections: dict[str, list[WebSocket]] = {}  # room_id -> list of websockets


class ActionIn(BaseModel):
    kind: Literal["chat", "vote", "skill"]
    text: str | None = None
    target_seat: int | None = None
    skill_name: str | None = None


@router.get("/{game_id}")
async def get_game(game_id: Annotated[str, Path(min_length=1)]):
    """Get game state."""
    game = _games.get(game_id)
    if not game:
        raise DomainError(
            code="GAME_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="game not found"
        )
    return {"ok": True, "data": game}


@router.post("/{game_id}/action")
async def post_action(
    game_id: Annotated[str, Path(min_length=1)],
    payload: Annotated[ActionIn, Body(...)],
):
    """Submit a game action (chat, vote, skill)."""
    game = _games.get(game_id)
    if not game:
        raise DomainError(
            code="GAME_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="game not found"
        )

    # TODO: Implement actual game logic
    logger.info("[GAME] action: game_id=%s kind=%s (stub)", game_id, payload.kind)

    # For now, just accept the action
    return {"ok": True}


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(room_id: str, websocket: WebSocket):
    """WebSocket endpoint for real-time game updates."""
    await websocket.accept()
    logger.info("[WS] client connected to room %s", room_id)

    # Register connection
    if room_id not in _ws_connections:
        _ws_connections[room_id] = []
    _ws_connections[room_id].append(websocket)

    try:
        # Send initial state
        await websocket.send_json(
            {"type": "system_log", "level": "info", "message": f"Connected to room {room_id}"}
        )

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "ack":
                pass  # Acknowledge received
            else:
                # Broadcast to all connections in room
                for conn in _ws_connections.get(room_id, []):
                    if conn != websocket:
                        try:
                            await conn.send_json(data)
                        except Exception as e:
                            logger.warning("[WS] failed to send to connection: %s", e)

    except WebSocketDisconnect:
        logger.info("[WS] client disconnected from room %s", room_id)
    except Exception as e:
        logger.error("[WS] error in room %s: %s", room_id, e)
    finally:
        # Unregister connection
        if room_id in _ws_connections:
            try:
                _ws_connections[room_id].remove(websocket)
            except ValueError:
                pass
            if not _ws_connections[room_id]:
                del _ws_connections[room_id]
