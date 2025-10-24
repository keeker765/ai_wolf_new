from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

router = APIRouter()


@router.post("/crash")
async def crash(payload: dict[str, Any] | None = Body(None)):
    # Force an unhandled exception to verify internal error guard
    raise RuntimeError("boom")
