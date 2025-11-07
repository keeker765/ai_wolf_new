from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel

from app.services.ai_service import decide_action_with_openai, generate_speech_with_openai

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateSpeechIn(BaseModel):
    role: str
    phase: str
    visible_state: dict
    history_summary: str | None = None
    persona: dict | None = None


class DecideActionIn(BaseModel):
    options: list
    role: str
    phase: str
    visible_state: dict
    history_summary: str | None = None


@router.post("/generate_speech")
async def generate_speech(payload: Annotated[GenerateSpeechIn, Body(...)]):
    """Generate AI speech using OpenAI."""
    result = await generate_speech_with_openai(
        role=payload.role,
        phase=payload.phase,
        visible_state=payload.visible_state,
        history_summary=payload.history_summary,
        persona=payload.persona,
    )
    return {"ok": True, "data": result}


@router.post("/decide_action")
async def decide_action(payload: Annotated[DecideActionIn, Body(...)]):
    """AI decides on an action."""
    result = await decide_action_with_openai(
        options=payload.options,
        role=payload.role,
        phase=payload.phase,
        visible_state=payload.visible_state,
        history_summary=payload.history_summary,
    )
    return {"ok": True, "data": result}
