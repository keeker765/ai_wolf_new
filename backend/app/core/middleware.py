from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class TraceIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request, call_next):
        trace_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["x-request-id"] = trace_id
        return response

