# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

- Backend dev server (run in `backend/`):
  - `uvicorn app.main:app --reload`
- Backend tests (pytest):
  - All: `pytest -q`
  - Single test by node id: `pytest -q backend/tests/test_file.py::TestClass::test_case`
  - Single test by keyword: `pytest -q -k "keyword"`
- Lint/format/type (run in `backend/`):
  - Lint: `ruff check .`
  - Format: `black .` (check only: `black --check .`)
  - Types: `mypy backend/app backend/tests`
- Dependencies (no lockfile present):
  - Create venv; install: `pip install fastapi uvicorn[standard] starlette pytest ruff black mypy`
- Frontend (planned; once `frontend/` exists):
  - Run: `flutter run`
  - Tests: `flutter test`
  - Lint/format: `flutter analyze && dart format .`

## Architecture Overview

- Backend: FastAPI app with Starlette middleware and a unified response contract.
  - Entry: `backend/app/main.py:1` defines the app, registers middleware, and includes routers (e.g., `auth`).
    - `backend/app/main.py:12` sets `title`/`version`, adds `TraceIdMiddleware`, and includes `auth` router with prefix `/auth` and tag `auth`.
  - Errors: `backend/app/core/errors.py:1` defines `DomainError` (with `code`, `http_status`) and helpers so handlers can convert exceptions into `{ ok:false, error:{...} }`.
  - Middleware: `backend/app/core/middleware.py:1` `TraceIdMiddleware` attaches `x-request-id` (uses existing header or generates `uuid4().hex[:12]`).
  - Routers: `backend/app/routers/auth.py:1` implements guest sign-in and email code request/verify endpoints backed by an in‑memory code store for the test phase.
  - Intended modules (documented but may not exist yet): `rooms`, `games`, `ai`, `replay`, `stt`, `billing`, `stats` (see comments in `backend/app/main.py`).
- Frontend: Flutter Web planned; architecture and CI gates are described in `docs/frontend-guidelines-and-plan.md:14` and later sections.
- Docs as source of truth:
  - Repo blueprint and conventions: `AGENTS.md:1`
  - Dev workflow and env tips: `docs/dev-plan.md:1`
  - API contract and response shape: `docs/api-spec.md:1`
  - Game logic notes: `docs/game-logic.md:1`

## Development Workflow Notes

- Run backend from `backend/`; default commands assume a local venv.
- Unified response envelope expected across endpoints and errors:
  - Success: `{ ok: true, data: ... }`
  - Error: `{ ok: false, error: { code, message, details? } }`
- Tracing: Each request gets/echoes `x-request-id` via `TraceIdMiddleware`.
- CI not yet configured; docs outline intended PR gates for backend (ruff/black check/pytest) and, once present, frontend gates (`flutter analyze`, `dart format --set-exit-if-changed`, `flutter test`).

## File Pointers

- App entry and router wiring: `backend/app/main.py:12`
- Error domain and helpers: `backend/app/core/errors.py:6`
- Request ID middleware: `backend/app/core/middleware.py:11`
- Auth endpoints and temporary code store: `backend/app/routers/auth.py:22`
- Conventions and commands: `AGENTS.md:16`, `AGENTS.md:324`
- Dev plan and commands: `docs/dev-plan.md:35`, `docs/dev-plan.md:38`
- Frontend guidelines and CI gates: `docs/frontend-guidelines-and-plan.md:14`, `docs/frontend-guidelines-and-plan.md:156`, `docs/frontend-guidelines-and-plan.md:163`

## Missing/Assumed

- No `pyproject.toml`, `requirements.txt`, Docker, or CI manifests present at time of writing. Install minimal deps manually as above.
- No `frontend/` yet; follow `docs/frontend-guidelines-and-plan.md` when scaffolding.
