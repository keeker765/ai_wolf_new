from __future__ import annotations

import logging
import random
import string
from typing import Annotated

from fastapi import APIRouter, Body

from app.core.errors import DomainError

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory stores for test period
_email_codes: dict[str, str] = {}


def _gen_code() -> str:
    return "".join(random.choices(string.digits, k=6))


@router.post("/guest")
async def auth_guest():
    # Test period: issue stub tokens
    return {"ok": True, "data": {"token": "guest-token", "refresh": "guest-refresh"}}


@router.post("/email/request")
async def auth_email_request(payload: Annotated[dict, Body(...)]):
    email = payload.get("email")
    if not email or "@" not in email:
        raise DomainError(code="VALIDATION_ERROR", http_status=400, message="invalid email")
    code = _gen_code()
    _email_codes[email] = code
    logger.info("[AUTH][EMAIL] send code %s to %s (test mode)", code, email)
    return {"ok": True}


@router.post("/email/verify")
async def auth_email_verify(payload: Annotated[dict, Body(...)]):
    email = payload.get("email")
    code = payload.get("code")
    if not email or not code:
        raise DomainError(code="VALIDATION_ERROR", http_status=400, message="email and code required")
    saved = _email_codes.get(email)
    if not saved or saved != str(code):
        raise DomainError(code="AUTH_INVALID_CODE", http_status=401, message="invalid code")
    return {"ok": True, "data": {"token": "email-token", "refresh": "email-refresh"}}

