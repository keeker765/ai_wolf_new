# Flutter Frontend Guidelines & Development Plan

## Goals
- Deliver a responsive, Web-first Flutter client for AI Werewolf.
- Align with shared contracts: REST `{ok,data|error}` and WS message schema.
- Keep code modular: routers/I-O on backend; providers/services on frontend.

## Principles
- Simplicity first: small widgets, pure services, testable providers.
- Contract-driven: implement exactly what `docs/api-spec.md` defines.
- Fail gracefully: map `error.code` to user-friendly messages; surface `trace_id` for support.
- Performance-aware: avoid unnecessary rebuilds, debounce inputs, batch WS updates.
- Privacy & safety: never log tokens or prompts; only log `code + trace_id`.

## Directory Structure (target)
```
frontend/
  pubspec.yaml
  analysis_options.yaml
  assets/ (images, i18n)
  lib/
    main.dart
    routes.dart
    theme/ (tokens.dart, theme.dart)
    models/ (room.dart, game.dart, message.dart)
    services/ (api_client.dart, websocket_service.dart, auth_service.dart, stt_service.dart)
    providers/ (auth_provider.dart, room_provider.dart, game_provider.dart, ws_provider.dart, replay_provider.dart)
    screens/ (lobby_screen.dart, room_screen.dart, game_screen.dart, spectator_screen.dart, voice_chat_screen.dart, settings_screen.dart)
    widgets/ (player_avatar.dart, timer_bar.dart, vote_panel.dart, skill_panel.dart, chat_list.dart)
    utils/ (debounce.dart, formatters.dart)
  test/ (mirrors lib/)
```

## Coding Standards
- Dart style: `flutter analyze` clean; `dart format` enforced.
- Naming: PascalCase for classes, lower_snake_case for files under `lib/`.
- Null-safety everywhere; sealed classes for results/events when useful.
- Widgets: prefer `const` constructors; split UI and logic; keep build methods light.
- State: Providers expose immutable state objects; side effects inside services.
 - Module boundaries (align with AGENTS.md):
   - screens: compose UI only, no I/O.
   - providers: state + orchestration, no direct HTTP/WS; call services only.
   - services: I/O, retries, backoff, mapping to domain events.
   - models: pure data; no business logic.

## Networking & Config
- All REST responses parsed via unified result:
  - Success: `{ ok:true, data }` -> `Ok<T>`.
  - Failure: `{ ok:false, error:{ code, message, details?, trace_id?, status? } }` -> `Err<ApiError>`.
- Error mapping uses the `ErrorCode` enum in `api_client.dart` per AGENTS.md.
- Auth: inject `Authorization: Bearer <jwt>` using `getToken()` callback; guest/login flows stored securely (local storage only for non-sensitive; do not persist raw prompts or tokens in logs).
- Config by `--dart-define` for base URLs and feature flags:
  - `API_BASE_URL` (e.g., `http://localhost:8000`)
  - `WS_BASE_URL` (e.g., `ws://localhost:8000`)
  - `FEATURE_VOICE=false` initially

## WebSocket Rules
- Connect: `/ws/{room_id}?token=<jwt>` with `lastSeq` for replay.
- Heartbeat: ping every 15s; consider disconnected if >30s no frames.
- Reconnect: 0.5s → 1s → 2s → 5s capped; resend `lastSeq`.
- Errors: emit `ErrorEvent(code,message)`; only close on fatal (4000–4099).

## State Management
- Use Riverpod (preferred) or Provider; expose:
  - `AuthProvider`: session state, token, guest/email flows.
  - `RoomProvider`: lobby/room list, join/leave/start room.
  - `GameProvider`: visible state, phase machine, timers; actions API (`chat`, `vote`, `skill`).
  - `WsProvider`: connection status, seq/ack, events stream.
  - `ReplayProvider`: timeline, summary pagination.
- Keep providers thin; business rules live in `services/`.

## UI & Theming
- Global theme with tokens (colors/typography/spacing); dark mode ready.
- Responsive layout: min 1024px Web, adaptive columns for spectators.
- Accessibility: text scale friendly; contrast AA+; semantic labels for buttons (vote/skill/chat).

## Error Handling & Telemetry
- Show friendly toasts/dialogs mapped from `ErrorCode`.
- Include `trace_id` in a developer panel/copyable area; never show raw tokens.
- Network/WS retries with exponential backoff where idempotent.

## Testing
- Unit: services and providers (mock HTTP/WS).
- Widget: key screens (`lobby_screen`, `room_screen`, `game_screen`) and widgets (`vote_panel`).
- Integration: minimal golden tests for layout stability.
- Target: 80%+ for providers/services; skip golden coverage on first pass.
 - Layout: test files mirror `lib/` with names like `<widget>_test.dart`.

## Collaboration With Backend
- Single source of truth: `docs/api-spec.md` and WS contract in AGENTS.md.
- Any contract change: open PR updating docs + client adapters.
- Shared error codes adhered to strictly; add mapping before usage.

## Security & Privacy
- No secrets in repo; no prompt/token logs; redact PII.
- Respect rate limits; bubble `RATE_LIMITED` with retry UI where appropriate.

## Definition of Done
- Analyzer clean; formatted; unit/widget tests updated; loading/error states covered; contracts verified against running backend or mocks; UX acceptable at 1024px+.

---

# Development Plan (Frontend)

## Milestone 0 — Bootstrap (0.5d)
- Create Flutter project scaffold under `frontend/` with Web enabled.
- Add `analysis_options.yaml` (flutter_lints), basic theme tokens, routes skeleton.

## Milestone 1 — Infrastructure (1.5d)
- Implement `ApiClient` with `Result<T>`, `ApiError`, and `ErrorCode` mapping.
- Wire `--dart-define` config; lightweight service locator for base URLs.
- Add `AuthService` (guest, email request/verify) and `AuthProvider`.

## Milestone 2 — Rooms Flow (2d)
- Screens: `lobby_screen`, `room_screen` placeholders.
- `RoomProvider` with create/get/join/leave/start; optimistic UI for join.
- Basic widgets: `player_avatar`, `chat_list` (local-only placeholder).

## Milestone 3 — WebSocket & Game Loop (3d)
- `WebSocketService`: connect/heartbeat/reconnect/seq+ack; events stream.
- `WsProvider` to bridge events to `GameProvider`.
- `GameProvider`: visible state, phase machine, timers; actions API (`chat`, `vote`, `skill`).
- Widgets: `timer_bar`, `vote_panel`, `skill_panel`; `game_screen` MVP.

## Milestone 4 — AI Integration (1d)
- `aiGenerateSpeech` + `aiDecideAction` hooks in `GameProvider` for AI seats.
- Timeouts (5–10s) with graceful fallback messages.

## Milestone 5 — Replay (1d)
- `ReplayProvider` + screens to show timeline and summary.

## Milestone 6 — Polish (1.5d)
- Error UX polish; i18n scaffolding; dark theme; empty/edge states.
- Basic golden tests; performance pass (rebuild hotspots, list virtualization).

## Milestone 7 — Stabilization (1d)
- Cross-browser Web checks; loading skeletons; accessibility labels.
- CI hooks: `flutter analyze`, `dart format --set-exit-if-changed`, `flutter test`.

## Dependencies (initial)
- riverpod, flutter_riverpod (state) — or provider if preferred.
- dio or http (HTTP client) — choose one; start with `http` for simplicity.
- web_socket_channel (WS).
- freezed/json_serializable (optional) for models.
- intl (i18n), go_router (routing) optional.

## Risks & Mitigations
- Contract drift: lock to `docs/api-spec.md`; add test fixtures from backend.
- WS instability: aggressive retries bounded; user-visible reconnect banner.
- Time constraints: deliver MVP screens first; defer voice features behind flag.

## Acceptance Criteria (per milestone)
- All planned screens present; actions callable; errors user-friendly; analyzer/tests pass.

---

## Workflow & PRs (Aligned with AGENTS.md)
- Branching: short branches `feat/x`, `fix/y`, `chore/z`.
- Commits: Conventional Commits, minimal readable diffs (≤300 LOC preferred).
- Pull Requests must include:
  - Clear description + linked issue
  - Tests for changes (unit/widget as applicable)
  - Local run steps and screenshots/logs for UI/WS changes
- CI gates: `flutter analyze`, `dart format --set-exit-if-changed`, `flutter test`.

## Security & Rate Limiting (Aligned)
- Do not commit secrets; use `--dart-define` for runtime config.
- Respect server 429; map to `ErrorCode.rateLimited` and present retry UI.
- Logging: never include PII, tokens, or prompts; prefer `code + trace_id` only.

## API/WS Contract Discipline (Aligned)
- REST: strictly `{ ok:true, data } | { ok:false, error:{ code, message, details?, trace_id? } }`.
- Error codes: follow `SCOPE_REASON` upper snake case; extend `ErrorCode` enum before usage.
- WS: message `{ type, payload?, seq? }`; error frames `{ type:"error", code, message, details? }`.
- Backward-compatible changes preferred (add fields, don’t break semantics); update `docs/api-spec.md` first.
