from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def get_openai_api_key() -> str | None:
    """Get OpenAI API key from environment."""
    return os.getenv("OPENAI_API_KEY")


def is_openai_available() -> bool:
    """Check if OpenAI is available."""
    key = get_openai_api_key()
    return key is not None and len(key) > 0


async def generate_speech_with_openai(
    role: str, phase: str, visible_state: dict, history_summary: str | None, persona: dict | None
) -> dict[str, Any]:
    """Generate speech using OpenAI API."""
    if not is_openai_available():
        logger.warning("[AI] OpenAI API key not configured, using fallback")
        return _fallback_generate_speech(role, phase)

    try:
        import openai

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

        # Build prompt
        system_prompt = f"""你是一名狼人杀游戏玩家。你的身份是{role}。
当前阶段是{phase}。请根据局势生成一段自然、合理的发言，长度控制在50字以内。"""

        user_prompt = f"可见信息：{visible_state}\n历史摘要：{history_summary or '无'}"

        client = openai.AsyncOpenAI(api_key=get_openai_api_key())
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        text = (response.choices[0].message.content or "").strip()
        if not text:
            return _fallback_generate_speech(role, phase)
        return {"text": text, "confidence": 0.85}

    except Exception as e:
        logger.error("[AI] OpenAI API error: %s", e)
        return _fallback_generate_speech(role, phase)


async def decide_action_with_openai(
    options: list, role: str, phase: str, visible_state: dict, history_summary: str | None
) -> dict[str, Any]:
    """Decide on an action using OpenAI API."""
    if not is_openai_available():
        logger.warning("[AI] OpenAI API key not configured, using fallback")
        return _fallback_decide_action(options)

    try:
        import openai

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "200"))
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

        # Build prompt
        system_prompt = f"""你是一名狼人杀游戏玩家。你的身份是{role}。
当前阶段是{phase}。从以下选项中选择一个最佳行动目标，只需返回目标编号。"""

        user_prompt = (
            f"可用目标：{options}\n可见信息：{visible_state}\n历史摘要：{history_summary or '无'}"
        )

        client = openai.AsyncOpenAI(api_key=get_openai_api_key())
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Try to parse the response to get a valid option
        text = (response.choices[0].message.content or "").strip()
        if text:
            try:
                pick = int(text)
                if pick in options:
                    return {"pick": pick, "confidence": 0.8}
            except ValueError:
                pass

        # Fallback to first option
        logger.warning("[AI] Could not parse OpenAI response, using fallback")
        return _fallback_decide_action(options)

    except Exception as e:
        logger.error("[AI] OpenAI API error: %s", e)
        return _fallback_decide_action(options)


def _fallback_generate_speech(role: str, phase: str) -> dict[str, Any]:
    """Fallback speech generation when OpenAI is unavailable."""
    stub_speeches = {
        "狼人": "我觉得这局情况很复杂，大家要理性分析。",
        "W": "我觉得这局情况很复杂，大家要理性分析。",
        "预言家": "昨晚我验了一个人，结果显示是好人。",
        "S": "昨晚我验了一个人，结果显示是好人。",
        "女巫": "我选择保留我的药，等更关键的时刻使用。",
        "Witch": "我选择保留我的药，等更关键的时刻使用。",
        "猎人": "我会默默观察，在合适的时候出手。",
        "H": "我会默默观察，在合适的时候出手。",
        "平民": "我是平民，希望大家能找到真正的狼人。",
        "V": "我是平民，希望大家能找到真正的狼人。",
    }

    text = stub_speeches.get(role, "我会仔细观察局势。")
    return {"text": text, "confidence": 0.5}


def _fallback_decide_action(options: list) -> dict[str, Any]:
    """Fallback action decision when OpenAI is unavailable."""
    import random

    pick = random.choice(options) if options else None
    return {"pick": pick, "confidence": 0.5}
