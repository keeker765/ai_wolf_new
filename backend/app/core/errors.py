from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DomainError(Exception):
    code: str
    http_status: int = 400
    message: str = ""
    details: dict[str, Any] | None = None


def to_error_payload(
    code: str,
    message: str,
    trace_id: str | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    if trace_id:
        err["trace_id"] = trace_id
    return {"ok": False, "error": err}

