from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Path, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from app.core.errors import DomainError
from app.routers.replay import _game_events, _game_summaries
from app.services.game_actions import (
    handle_seer_check,
    handle_vote,
    handle_witch_heal,
    handle_witch_poison,
    handle_wolf_kill,
    resolve_night,
    resolve_vote,
)
from app.services.game_state import GameState, Phase, create_game
from app.services.room_manager import room_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for test period
_games: dict[str, GameState] = {}  # game_id -> game state
_ws_connections: dict[str, list[WebSocket]] = {}  # room_id -> list of websockets


class ActionIn(BaseModel):
    kind: Literal["chat", "vote", "skill"]
    text: str | None = None
    target_seat: int | None = None
    skill_name: str | None = None


async def broadcast_to_room(room_id: str, message: dict):
    """Broadcast a message to all connections in a room."""
    for conn in _ws_connections.get(room_id, []):
        try:
            await conn.send_json(message)
        except Exception as e:
            logger.warning("[WS] failed to send to connection: %s", e)


@router.get("/{game_id}")
async def get_game(game_id: Annotated[str, Path(min_length=1)]):
    """Get game state."""
    game = _games.get(game_id)
    if not game:
        raise DomainError(
            code="GAME_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="game not found"
        )

    # Return visible state (simplified for test period)
    return {
        "ok": True,
        "data": {
            "game_id": game.game_id,
            "phase": game.phase.value,
            "round": game.round,
            "alive_players": game.alive_players(),
        },
    }


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

    user_id = "stub_user"  # TODO: from JWT
    # Find player seat
    actor_seat = None
    for seat, player in game.players.items():
        if player.user_id == user_id:
            actor_seat = seat
            break

    if actor_seat is None:
        raise DomainError(code="NOT_MEMBER", http_status=403, message="not a game member")

    # Handle action based on kind
    if payload.kind == "chat":
        game.add_event("chat_message", actor_seat=actor_seat, payload={"text": payload.text})
        await broadcast_to_room(
            game.room_id,
            {"type": "chat_message", "from": f"player_{actor_seat}", "text": payload.text},
        )

    elif payload.kind == "vote":
        handle_vote(game, actor_seat, payload.target_seat)
        await broadcast_to_room(
            game.room_id, {"type": "vote_event", "seat": actor_seat, "target": payload.target_seat}
        )

    elif payload.kind == "skill":
        if payload.skill_name == "wolf_kill":
            handle_wolf_kill(game, actor_seat, payload.target_seat)
        elif payload.skill_name == "witch_heal":
            handle_witch_heal(game, actor_seat, payload.target_seat)
        elif payload.skill_name == "witch_poison":
            handle_witch_poison(game, actor_seat, payload.target_seat)
        elif payload.skill_name == "seer_check":
            handle_seer_check(game, actor_seat, payload.target_seat)
        else:
            raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="unknown skill")

        await broadcast_to_room(
            game.room_id,
            {
                "type": "skill_event",
                "seat": actor_seat,
                "skill": payload.skill_name,
                "target": payload.target_seat,
            },
        )

    return {"ok": True}


@router.post("/{game_id}/advance")
async def advance_phase(game_id: Annotated[str, Path(min_length=1)]):
    """Advance game to next phase (for testing/admin)."""
    game = _games.get(game_id)
    if not game:
        raise DomainError(
            code="GAME_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="game not found"
        )

    # Resolve current phase
    if game.phase == Phase.NIGHT:
        deaths = resolve_night(game)
        game.add_event("day_deaths_announced", payload={"deaths": deaths})
        await broadcast_to_room(game.room_id, {"type": "day_deaths_announced", "deaths": deaths})

    elif game.phase == Phase.VOTE:
        result = resolve_vote(game)
        if result["action"] == "revote":
            # Stay in vote phase for revote
            game.phase = Phase.VOTE
            await broadcast_to_room(
                game.room_id,
                {"type": "vote_result", "action": "revote", "leaders": result["leaders"]},
            )
        else:
            # Advance normally
            game.advance_phase()
            await broadcast_to_room(
                game.room_id,
                {
                    "type": "lynch_result",
                    "action": result["action"],
                    "executed": result.get("executed"),
                },
            )
    else:
        game.advance_phase()

    # Send phase update
    game.add_event("phase_changed", payload={"phase": game.phase.value, "round": game.round})
    await broadcast_to_room(
        game.room_id,
        {"type": "state_update", "phase": game.phase.value, "round": game.round},
    )

    # Check for game end
    if game.phase == Phase.END:
        game.add_event("game_ended", payload={"winner": game.winner})
        await broadcast_to_room(game.room_id, {"type": "game_ended", "winner": game.winner})

        # Save to replay
        _game_events[game_id] = game.events
        _game_summaries[game_id] = {
            "game_id": game_id,
            "winner": game.winner,
            "rounds": game.round,
        }

    return {"ok": True, "data": {"phase": game.phase.value, "round": game.round}}


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

        # If there's an active game, send the current state
        room = room_manager.get(room_id)
        if room and room.game_id:
            game = _games.get(room.game_id)
            if game:
                await websocket.send_json(
                    {
                        "type": "state_update",
                        "phase": game.phase.value,
                        "round": game.round,
                        "alive_players": game.alive_players(),
                    }
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
                # Broadcast to all other connections in room
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


# Helper to create a game when room starts
def start_game_for_room(room_id: str, game_id: str) -> GameState:
    """Create and initialize a game for a room."""
    room = room_manager.get(room_id)
    if not room:
        raise DomainError(code="ROOM_NOT_FOUND", http_status=404, message="room not found")

    game = create_game(game_id, room_id, room.seats, room.members)
    _games[game_id] = game

    # Advance to first night
    game.advance_phase()
    game.add_event("phase_changed", payload={"phase": game.phase.value, "round": game.round})

    return game
