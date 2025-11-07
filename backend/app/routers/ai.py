from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel

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
    # For test period, return a stub response
    # TODO: Implement actual OpenAI integration
    logger.info("[AI] generate_speech: role=%s phase=%s (stub mode)", payload.role, payload.phase)

    stub_speeches = {
        "狼人": "我觉得这局情况很复杂，大家要理性分析。",
        "预言家": "昨晚我验了一个人，结果显示是好人。",
        "女巫": "我选择保留我的药，等更关键的时刻使用。",
        "猎人": "我会默默观察，在合适的时候出手。",
        "平民": "我是平民，希望大家能找到真正的狼人。",
    }

    text = stub_speeches.get(payload.role, "我会仔细观察局势。")
    return {"ok": True, "data": {"text": text, "confidence": 0.8}}


@router.post("/decide_action")
async def decide_action(payload: Annotated[DecideActionIn, Body(...)]):
    """AI decides on an action."""
    # For test period, return a stub decision
    # TODO: Implement actual OpenAI integration
    logger.info(
        "[AI] decide_action: role=%s phase=%s options=%s (stub mode)",
        payload.role,
        payload.phase,
        len(payload.options),
    )

    # Simple stub logic: pick first available option
    pick = payload.options[0] if payload.options else None
    return {"ok": True, "data": {"pick": pick, "confidence": 0.7}}
