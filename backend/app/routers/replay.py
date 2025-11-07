from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query
from starlette.status import HTTP_404_NOT_FOUND

from app.core.errors import DomainError

router = APIRouter()

# In-memory storage for test period
# game_id -> list of events
_game_events: dict[str, list[dict]] = {}
_game_summaries: dict[str, dict] = {}


@router.get("/{game_id}/timeline")
async def get_timeline(
    game_id: Annotated[str, Path(min_length=1)],
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Get replay timeline for a game."""
    events = _game_events.get(game_id, [])
    if not events:
        raise DomainError(
            code="GAME_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="game not found"
        )

    # Simple pagination by cursor (sequence number)
    start_idx = 0
    if cursor:
        try:
            start_idx = int(cursor)
        except ValueError:
            pass

    items = events[start_idx : start_idx + limit]
    next_cursor = str(start_idx + limit) if start_idx + limit < len(events) else None

    return {"ok": True, "data": {"items": items, "next_cursor": next_cursor}}


@router.get("/{game_id}/summary")
async def get_summary(game_id: Annotated[str, Path(min_length=1)]):
    """Get replay summary for a game."""
    summary = _game_summaries.get(game_id)
    if not summary:
        raise DomainError(
            code="GAME_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="game not found"
        )
    return {"ok": True, "data": summary}
