from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class TranscribeIn(BaseModel):
    audio_base64: str | None = None
    mime: str | None = None


@router.post("/transcribe")
async def transcribe(payload: Annotated[TranscribeIn, Body(...)]):
    """STT placeholder - returns stub transcription."""
    logger.info("[STT] transcribe request received (test mode stub)")
    return {"ok": True, "data": {"text": "", "note": "stub - test period"}}
