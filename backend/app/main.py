from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from app.core.errors import DomainError, to_error_payload
from app.core.middleware import TraceIdMiddleware
from app.routers import auth, rooms, games, ai, replay, stt, billing, stats


app = FastAPI(title="AI Werewolf API", version="0.1.0-test")
app.add_middleware(TraceIdMiddleware)


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError):
    trace_id = getattr(request.state, "trace_id", None)
    payload = to_error_payload(exc.code, exc.message or exc.code, trace_id, exc.details)
    return JSONResponse(status_code=exc.http_status, content=payload)


@app.exception_handler(RequestValidationError)
async def handle_validation(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", None)
    payload = to_error_payload(
        "VALIDATION_ERROR", "invalid request", trace_id, {"errors": exc.errors()}
    )
    return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content=payload)


@app.middleware("http")
async def internal_error_guard(request: Request, call_next):
    try:
        return await call_next(request)
    except DomainError:
        raise
    except Exception:
        trace_id = getattr(request.state, "trace_id", None)
        payload = to_error_payload("INTERNAL_ERROR", "unexpected server error", trace_id)
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=payload)


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(games.router, prefix="/games", tags=["games"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(replay.router, prefix="/replay", tags=["replay"])
app.include_router(stt.router, prefix="/stt", tags=["stt"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

