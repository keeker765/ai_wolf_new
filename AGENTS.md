# Repository Guidelines

This repository targets a Flutter client and a FastAPI (async) backend for an AI Werewolf game. Use the structure and conventions below to keep contributions consistent and easy to review.

## Project Structure & Module Organization
- backend/: FastAPI app, WebSocket handlers, AI adapters, DB models.
- frontend/: Flutter app (screens, providers, services, widgets).
- infra/: Docker, deployment, and CI configs.
- docs/: Design notes, API specs (e.g., `plan.md`).

Example layout:
```
backend/app/            # routers/, services/, models/, core/
frontend/lib/           # screens/, widgets/, services/, providers/
```

## Build, Test, and Development Commands
- Backend (dev): `uvicorn app.main:app --reload` (run from `backend/`).
- Backend tests: `pytest -q` (from `backend/`).
- Code quality (backend): `ruff check . && black --check .`.
- Frontend (run): `flutter run` (from `frontend/`).
- Frontend tests: `flutter test`.
- Frontend analyze/format: `flutter analyze && dart format .`.

Tip: Use a Python virtualenv for backend (`py -m venv .venv && . .venv/bin/activate` or `python -m venv .venv`).

## Coding Style & Naming Conventions
- Python: Follow PEP 8. Format with Black; import order via isort; lint with Ruff.
- Dart: Use `dart format` and `flutter analyze` defaults.
- Naming: snake_case for Python modules/functions; PascalCase for Dart classes; kebab-case for file/folder names except Flutter `lib/` which uses snake_case.
- Keep functions small; prefer pure services under `backend/app/services/` and `frontend/lib/services/`.

### Python 风格细则（Draft）
- 基本规则
  - 顶部加：`from __future__ import annotations`（避免前向引用问题）。
  - 全量类型标注：函数参数与返回值、模块常量、数据结构（Pydantic 模型除外字段注释不必重复）。
  - 使用内建泛型：`list[str]`、`dict[str, Any]`，避免 `List`/`Dict` 别名。
- 导入与分组（isort 规范）
  - 顺序：标准库 → 第三方 → 本地；每组之间空行；绝对导入优先。
  - 禁止 `from x import *`；仅在需要时局部 `as` 起别名。
  - 仅类型用到的大型依赖放在 `if TYPE_CHECKING:` 块内。
- typing 建议
  - 使用 `typing` 中的 `Literal`、`TypedDict`、`Protocol`、`Self`、`NewType` 视场景选用。
  - FastAPI 参数用 `Annotated[T, ...]` 搭配校验；ID 推荐 `UUID`；时间使用 `datetime`（UTC）。
  - 返回值明确：协程标注 `async def -> T`；生成器 `Iterator[T]`/`AsyncIterator[T]`。
- Docstring 与命名
  - 公共函数/类用简短一行 docstring；必要处列出参数/返回/异常。
  - 布尔变量用肯定语气（`is_alive`/`has_token`）。
- 错误处理
  - 只在边界层捕获（router/service 边界）；抛出自定义 `DomainError`（见“抛错约定”）。
  - 不吞异常；日志中记录 `trace_id` 与关键上下文（room_id/game_id/user_id）。
- 示例
  ```python
  from __future__ import annotations
  from typing import Any, Literal, TYPE_CHECKING
  from uuid import UUID
  from pydantic import BaseModel

  if TYPE_CHECKING:
      from .services.game_state import GameState

  class VotePayload(BaseModel):
      target_seat: int | None
      reason: str | None = None

  Phase = Literal["Init", "Night", "Day", "Vote", "Resolve", "End"]

  def tally(ballots: dict[int, int | None]) -> dict[int, int]:
      counts: dict[int, int] = {}
      for _seat, target in ballots.items():
          if target is None:
              continue
          counts[target] = counts.get(target, 0) + 1
      return counts

  if __name__ == "__main__":  # 仅限快速本地验证；正式用 pytest
      assert tally({1: 2, 2: 2, 3: None}) == {2: 2}
  ```

### 类型检查与工具（mypy）
- 目标：在核心目录启用严格模式，提交前本地通过。
- 运行：`mypy backend/app backend/tests`
- 建议配置（任选其一）：
  - `pyproject.toml`
    ```toml
    [tool.mypy]
    python_version = "3.11"
    warn_redundant_casts = true
    warn_unused_ignores = true
    warn_return_any = true
    warn_unreachable = true
    disallow_untyped_defs = true
    disallow_incomplete_defs = true
    disallow_untyped_calls = true
    no_implicit_optional = true
    strict_optional = true
    check_untyped_defs = true
    ignore_missing_imports = true  # 优先安装类型stub；必要时再临时放宽
    ```
  - 或 `mypy.ini` 同等配置。
- 可选：启用 Pydantic 插件（如使用 v2）：`plugins = ["pydantic.mypy"]`。

### FastAPI Annotated 示例
```python
from __future__ import annotations
from typing import Annotated, Literal
from fastapi import APIRouter, Path, Query, Body
from pydantic import BaseModel, Field

router = APIRouter()

class ActionIn(BaseModel):
    kind: Literal["chat", "vote", "skill"]
    text: str | None = None
    target_seat: int | None = Field(default=None, ge=1, le=10)

@router.post("/games/{game_id}/action")
async def post_action(
    game_id: Annotated[str, Path(min_length=1)],
    payload: Annotated[ActionIn, Body()],
):
    # TODO: 调用 service 层执行业务逻辑
    return {"ok": True}

@router.get("/rooms/{room_id}")
async def get_room(
    room_id: Annotated[str, Path(min_length=1)],
    verbose: Annotated[bool, Query()] = False,
):
  return {"ok": True, "data": {"id": room_id, "verbose": verbose}}
```

### FastAPI 路由骨架（含 DomainError 处理）
```python
# backend/app/core/errors.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class DomainError(Exception):
    code: str
    http_status: int = 400
    message: str = ""
    details: dict[str, Any] | None = None

def to_error_payload(code: str, message: str, trace_id: str | None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    err = {"code": code, "message": message}
    if details:
        err["details"] = details
    if trace_id:
        err["trace_id"] = trace_id
    return {"ok": False, "error": err}
```
```python
# backend/app/core/middleware.py
from __future__ import annotations
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["x-request-id"] = trace_id
        return response
```
```python
# backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from app.core.errors import DomainError, to_error_payload
from app.core.middleware import TraceIdMiddleware
from app.routers import rooms, games

app = FastAPI(title="AI Werewolf API")
app.add_middleware(TraceIdMiddleware)

@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, exc: DomainError):
    trace_id = _.state.trace_id if hasattr(_, "state") else None
    payload = to_error_payload(exc.code, exc.message or exc.code, trace_id, exc.details)
    return JSONResponse(status_code=exc.http_status, content=payload)

@app.exception_handler(RequestValidationError)
async def handle_validation(_: Request, exc: RequestValidationError):
    trace_id = _.state.trace_id if hasattr(_, "state") else None
    payload = to_error_payload("VALIDATION_ERROR", "invalid request", trace_id, {"errors": exc.errors()})
    return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content=payload)

@app.middleware("http")
async def internal_error_guard(request: Request, call_next):
    try:
        return await call_next(request)
    except DomainError:
        raise
    except Exception as e:  # noqa: BLE001
        trace_id = getattr(request.state, "trace_id", None)
        payload = to_error_payload("INTERNAL_ERROR", "unexpected server error", trace_id)
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=payload)

app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(games.router, prefix="/games", tags=["games"])

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
```
```python
# backend/app/routers/rooms.py
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Body, Depends, Path
from pydantic import BaseModel, Field
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.errors import DomainError

router = APIRouter()

class CreateRoomIn(BaseModel):
    seats: int = Field(ge=6, le=10)
    fill_ai: bool = False
    name: str | None = None

class RoomOut(BaseModel):
    id: str
    seats: int
    name: str | None

def get_current_user():  # stub
    return {"id": "u1", "role": "guest"}

@router.post("")
async def create_room(
    payload: Annotated[CreateRoomIn, Body(...)],
    user: Annotated[dict, Depends(get_current_user)],
):
    if user is None:
        raise DomainError(code="AUTH_REQUIRED", http_status=401, message="login required")
    if payload.seats not in (6, 9, 10):
        raise DomainError(code="VALIDATION_ERROR", http_status=400, message="seats must be 6|9|10")
    room = RoomOut(id="r123", seats=payload.seats, name=payload.name)
    return {"ok": True, "data": room.model_dump()}

@router.get("/{room_id}")
async def get_room(room_id: Annotated[str, Path(min_length=1)]):
    # demo：房间不存在
    raise DomainError(code="ROOM_NOT_FOUND", http_status=HTTP_404_NOT_FOUND, message="room not found")
```
```python
# backend/app/routers/games.py（含 WS 错误示例）
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Path, WebSocket, WebSocketDisconnect
from app.core.errors import DomainError

router = APIRouter()

@router.websocket("/ws/{room_id}")
async def ws(room_id: Annotated[str, Path(min_length=1)], ws: WebSocket):
    await ws.accept()
    try:
        # 简化：演示错误帧
        await ws.send_json({"type": "error", "code": "GAME_INVALID_ACTION", "message": "cannot chat in Night"})
        await ws.close(code=4001)
    except WebSocketDisconnect:
        pass
```

## Testing Guidelines
- Frameworks: `pytest` for backend; `flutter_test` for frontend.
- Location: `backend/tests/` mirrors `app/`; `frontend/test/` mirrors `lib/`.
- Naming: `test_<module>.py` (backend), `<widget>_test.dart` (frontend).
- Coverage target: 80%+ for core logic (game state, AI decision interfaces, room lifecycle).

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat: add vote tally logic`, `fix(ws): handle disconnect`).
- PRs must include: clear description, linked issue, test coverage for changes, and local run steps.
- Keep PRs focused and under ~300 lines when possible; add screenshots or logs for UI/WS changes.

## Security & Configuration
- Do not commit secrets. Use `.env` in `backend/` and `--dart-define` for Flutter; provide `.env.example`.
- Validate and sanitize all WebSocket and REST inputs. Log decisions, not raw prompts or tokens.
- Use Redis for ephemeral state; persist only required game records to the database.

## 开发守则（Draft）
- 分支与提交
  - 使用短分支：`feat/x`, `fix/y`, `chore/z`；主干受保护，PR 合并。
  - 提交遵循 Conventional Commits，并保证可读的最小变更集（≤300 行优先）。
- 代码与风格
  - Python：Ruff+Black+isort 通过后方可提交；Dart：`flutter analyze` 与 `dart format` 通过。
  - 严格模块边界：`routers` 只做 I/O 与校验；业务在 `services`；数据在 `models`/`repos`。
  - 命名清晰、函数短小、无隐藏副作用；拒绝上帝对象与循环依赖。
- 测试与覆盖率
  - 新功能必须附单元/集成用例；核心逻辑覆盖≥80%。
  - 先红后绿：先写可复现失败的用例，再实现修复。
- API 契约与兼容
  - 改动 `docs/api-spec.md` 同步更新后端实现与前端类型；尽量非破坏性变更（添加字段而非修改语义）。
  - WebSocket 消息包含 `type` 与 `payload`；保持前后端契约一致，版本化管理如有必要。
- 安全与数据
  - 严禁明文日志输出个人信息、Access Token、Prompt 原文；必要时写入脱敏摘要与追踪 ID。
  - 对 `/auth/*`、`/ai/*`、WS 入站做限流；所有输入做白名单/枚举校验。
- 迁移与运维
  - DB 变更必须有 Alembic 迁移与回滚脚本；变更需注明影响范围与数据体量评估。
  - 所有长任务使用异步与超时/重试策略；关键路径埋点（延迟、错误率、吞吐）。
- 性能与可观测性
  - Redis/DB 调用避免 N+1；广播合批；必要处加缓存并设失效策略。
  - 重要函数加入结构化日志（包含 `room_id`/`game_id`/`user_id`）。
- 配置与机密
  - 所有密钥经环境变量注入；提供 `.env.example`；在 README/ docs 标注需要的变量说明。
  - 本地与测试环境的邮箱验证码、STT 等外部服务默认走“仅写日志”模式。
- 回放与规则一致性
  - 按 `docs/game-logic.md` 与 `docs/sample-game-log.md` 记录事件；任何变更需同步更新文档与回放生成器。
- 代码评审
  - PR 需：变更说明、相关 issue、截图/日志（如 UI/WS）、测试说明；至少 1 名 Reviewer 通过。
  - Reviewer 关注：正确性、边界条件、并发/异常、可读性与回退方案。

### 抛错约定（Errors & Exceptions）
- 统一响应结构
  - REST 失败：`{ ok:false, error:{ code, message, details?, trace_id? } }`；成功用 `{ ok:true, data }`。
  - WS 失败：推送 `{ type:"error", code, message, details? }`；致命错误再关闭连接。
- 错误码规范
  - 命名：`SCOPE_REASON` 全大写下划线（示例：`AUTH_INVALID_TOKEN`, `ROOM_FORBIDDEN`, `GAME_PHASE_ERROR`, `AI_PROVIDER_ERROR`, `RATE_LIMITED`）。
  - 映射（HTTP）：
    - 400 `VALIDATION_ERROR`（参数不合法，含 Pydantic 校验）
    - 401 `AUTH_INVALID_TOKEN` / `AUTH_REQUIRED`
    - 403 `ROOM_FORBIDDEN` / `NOT_MEMBER`
    - 404 `NOT_FOUND`
    - 409 `CONFLICT` / `GAME_PHASE_ERROR` / `ALREADY_EXISTS`
    - 429 `RATE_LIMITED`
    - 500 `INTERNAL_ERROR`；503 `DEPENDENCY_UNAVAILABLE`；504 `TIMEOUT`
- 实现建议（FastAPI）
  - 集中异常处理：`backend/app/core/errors.py` 定义 `DomainError(code, http_status, message, details?)` 与全局 `exception_handler`，将未捕获异常规范化为 500 响应，并生成 `trace_id`。
  - 参数校验交由 Pydantic；将 422 统一转换为 400 并使用 `VALIDATION_ERROR`。
  - 记录结构化日志：`level=error code=... trace_id=... room_id/game_id/user_id`；消息不包含敏感数据或 Prompt 原文。
- WebSocket 约定
  - 非致命错误：仅下发 `error` 帧并继续会话；致命错误：先发 `error` 再以应用码（4000–4099）关闭。
  - 动作幂等冲突返回 `CONFLICT`（不关闭连接）。
- 外部依赖与限流
  - OpenAI 超时/配额：`AI_TIMEOUT`/`AI_RATE_LIMITED`；提供回退策略并记录 `provider_request_id`（如可得）。
- 统一返回 429 处理限流，不得以 500 代替。
- 前端处理（建议）
  - 以 `error.code` 做分支；向用户展示本地化友好文案；日志保留 `code + trace_id`，不上传敏感信息。

## 项目文件树模板（Draft）
```text
ai_wolf_kill/
├─ AGENTS.md                          # 贡献与规范（本文件）
├─ plan.md                            # 早期总体计划（参考）
├─ docs/                              # 规格/计划/逻辑/示例
│  ├─ api-spec.md                     # 后端接口权威规格
│  ├─ dev-plan.md                     # 开发计划（后端优先）
│  ├─ game-logic.md                   # 规则与实现指引
│  └─ sample-game-log.md              # 示例对局日志（内部/观战视图）
├─ backend/
│  ├─ pyproject.toml                  # 可选：black/ruff/mypy/isort 配置
│  ├─ requirements.txt                # 或使用 poetry/uv
│  ├─ .env.example                    # 环境变量示例（不含密钥）
│  └─ app/
│     ├─ __init__.py
│     ├─ main.py                      # FastAPI 入口：中间件/路由/异常处理
│     ├─ core/
│     │  ├─ errors.py                 # DomainError/错误负载
│     │  └─ middleware.py             # TraceId 等中间件
│     ├─ routers/
│     │  ├─ __init__.py
│     │  ├─ auth.py                   # 游客/邮箱验证码（仅日志）
│     │  ├─ rooms.py                  # 房间 CRUD/入房/开局
│     │  ├─ games.py                  # 对局查询/动作/WS 端点
│     │  ├─ ai.py                     # generate_speech/decide_action
│     │  ├─ replay.py                 # 时间线/摘要查询
│     │  ├─ stt.py                    # 语音转文字（占位）
│     │  ├─ billing.py                # 商业化占位接口
│     │  └─ stats.py                  # 运营指标/健康检查扩展
│     ├─ services/
│     │  ├─ __init__.py
│     │  ├─ game_state.py             # 状态机/阶段推进/可见性裁剪
│     │  ├─ vote.py                   # 投票/复投/结算
│     │  ├─ role.py                   # 角色池与分配
│     │  ├─ ai_service.py             # OpenAI 适配/缓存/回退
│     │  ├─ replay_service.py         # 事件落库/分页查询
│     │  ├─ room_manager.py           # 内存态/Redis 快照/计时器
│     │  └─ rate_limit.py             # 限流/防刷
│     ├─ ws/
│     │  ├─ __init__.py
│     │  ├─ connection.py             # 心跳/seq+ack/重连
│     │  └─ message_bus.py            # 广播/订阅（Redis Pub/Sub）
│     ├─ models/
│     │  ├─ __init__.py
│     │  ├─ db.py                     # SQLAlchemy async 会话
│     │  ├─ schemas.py                # Pydantic I/O
│     │  └─ orm.py                    # ORM 实体：users/rooms/games/events
│     ├─ utils/
│     │  ├─ __init__.py
│     │  ├─ ids.py                    # 短 ID
│     │  └─ logging.py                # 结构化日志封装
│     └─ tests/
│        ├─ __init__.py
│        ├─ test_rooms.py
│        ├─ test_game_state.py
│        └─ test_ai_api.py
├─ frontend/                           # Flutter Web 客户端（Web 优先）
│  ├─ pubspec.yaml
│  ├─ analysis_options.yaml            # Lints（推荐 flutter_lints）
│  ├─ assets/
│  │  ├─ images/
│  │  └─ i18n/
│  ├─ web/
│  │  └─ index.html
│  └─ lib/
│     ├─ main.dart
│     ├─ routes.dart
│     ├─ theme/
│     │  ├─ tokens.dart                # 设计 Token（颜色/字号/间距）
│     │  └─ theme.dart                 # 全局主题
│     ├─ models/
│     │  ├─ room.dart
│     │  ├─ game.dart
│     │  └─ message.dart
│     ├─ services/
│     │  ├─ api_client.dart            # REST 封装（含错误码处理）
│     │  ├─ websocket_service.dart     # WS 心跳/重连/消息分发
│     │  ├─ auth_service.dart          # 游客/邮箱登录对接
│     │  └─ stt_service.dart           # STT 占位
│     ├─ providers/
│     │  ├─ auth_provider.dart
│     │  ├─ room_provider.dart
│     │  ├─ game_provider.dart
│     │  ├─ ws_provider.dart
│     │  └─ replay_provider.dart
│     ├─ screens/
│     │  ├─ lobby_screen.dart
│     │  ├─ room_screen.dart
│     │  ├─ game_screen.dart
│     │  ├─ spectator_screen.dart
│     │  ├─ voice_chat_screen.dart     # 首版禁用，UI 占位
│     │  └─ settings_screen.dart
│     ├─ widgets/
│     │  ├─ player_avatar.dart
│     │  ├─ timer_bar.dart
│     │  ├─ vote_panel.dart
│     │  ├─ skill_panel.dart
│     │  └─ chat_list.dart
│     └─ utils/
│        ├─ debounce.dart
│        └─ formatters.dart
│  └─ test/
│     ├─ widget_test.dart
│     ├─ providers/
│     │  ├─ game_provider_test.dart
│     │  └─ room_provider_test.dart
│     └─ widgets/
│        └─ vote_panel_test.dart
└─ infra/
   ├─ docker/
   │  ├─ backend.Dockerfile
   │  └─ compose.yml
   └─ k8s/                             # 可选：K8s 清单
```

说明
- 模板为“目标结构”，允许逐步补齐；创建/移动文件需同步更新此处结构。
- 路由仅处理 I/O 与参数校验；业务逻辑一律落在 services 层；存取在 models 层。

## 后端×前端协作守则（Draft）
- 单一真相来源（SSOT）
  - 权威文档：`docs/api-spec.md`、`docs/game-logic.md`、`docs/sample-game-log.md`；运行态以 `/openapi.json` 和 `/docs` 为准。
  - 协议变更遵循“向后兼容优先”：优先新增字段，不改语义；确需破坏时走版本化或特性开关。
- 变更流程与冻结
  - 任何接口/消息格式变更先开 Issue（`type:api-change`），附示例请求/响应与影响面；PR 合并后同步更新文档与变更记录。
  - 冻结窗口：每个迭代末 24h 为“接口冻结”，仅修复 Bug，不做破坏性调整。
- 同步节奏与沟通
  - 每日短同步（<=10min）：昨天/今天/阻塞；重大风险即时在 Issue 标注 `blocker` 并 @相关人。
  - 需求澄清优先在 Issue 记录结论，必要时语音 15 分钟定调，事后补文字结论。
- 集成与验收
  - 提供 Postman/Thunder 集合与 cURL 示例、以及 `docs/mocks/` 下的响应样例（用于前端离线联调）。
  - Dev 环境基线：`/healthz` 正常、`/auth/guest` 可用、`/ws/{room_id}` 可连；提供测试账号与示例房间。
  - 联调清单：创建房间→入房→开局→夜1结算→Day 投票→结算→回放查询（至少跑通 1 条完整链路）。
- 错误与可观测性
  - 所有失败返回 `{ok:false,error:{code,message,trace_id}}`；前端日志上报附 `code+trace_id`，便于后端检索。
  - 关键请求在响应头返回 `x-request-id`；前端报错面板展示该值（便于远程协查）。
- WebSocket 契约
  - 统一 `type+payload(+seq)`；ack 仅回传数字 `seq`；断线重连带 `lastSeq` 请求补发最近事件。
  - 心跳：前端 15s `ping`，服务 `pong`；>30s 无帧判定断线并重连；致命错误以 4000–4099 关闭码。
- 迭代内服务质量（SLA）
  - 工作时段响应：一般问题 4h 内回复，阻塞类 2h 内响应；修复优先级：P0 立即、P1 当日、P2 下个工作日。
  - 限流与配额：Dev 环境适度放宽；遇到 429 请附上 `trace_id` 与复现步骤。
- 交接与发布
  - 合并前跑最小冒烟：`/healthz`、`/auth/guest`、`/rooms`、`/ws/{room_id}`；必要时前后端结对 30min 过一遍关键路径。
  - 发布变更需附“前端变更点”列表（新增字段/弃用字段/默认值/兼容策略），并在群里同步时间点与回滚方案。

## Dart API/WS 契约（Draft）

### REST API 客户端契约
```dart
// lib/services/api_client.dart
// 约定：所有 REST 成功响应 { ok: true, data: T }；失败 { ok: false, error: { code, message, details?, trace_id? } }

enum ErrorCode {
  authRequired,
  authInvalidToken,
  validationError,
  roomNotFound,
  roomForbidden,
  notMember,
  gameNotFound,
  gamePhaseError,
  gameInvalidAction,
  aiTimeout,
  aiProviderError,
  rateLimited,
  internalError,
  dependencyUnavailable,
  timeout,
}

ErrorCode mapErrorCode(String code) {
  switch (code) {
    case 'AUTH_REQUIRED': return ErrorCode.authRequired;
    case 'AUTH_INVALID_TOKEN': return ErrorCode.authInvalidToken;
    case 'VALIDATION_ERROR': return ErrorCode.validationError;
    case 'ROOM_NOT_FOUND': return ErrorCode.roomNotFound;
    case 'ROOM_FORBIDDEN': return ErrorCode.roomForbidden;
    case 'NOT_MEMBER': return ErrorCode.notMember;
    case 'GAME_NOT_FOUND': return ErrorCode.gameNotFound;
    case 'GAME_PHASE_ERROR': return ErrorCode.gamePhaseError;
    case 'GAME_INVALID_ACTION': return ErrorCode.gameInvalidAction;
    case 'AI_TIMEOUT': return ErrorCode.aiTimeout;
    case 'AI_PROVIDER_ERROR': return ErrorCode.aiProviderError;
    case 'RATE_LIMITED': return ErrorCode.rateLimited;
    case 'DEPENDENCY_UNAVAILABLE': return ErrorCode.dependencyUnavailable;
    case 'TIMEOUT': return ErrorCode.timeout;
    case 'INTERNAL_ERROR':
    default: return ErrorCode.internalError;
  }
}

class ApiError implements Exception {
  final ErrorCode code; final String message; final Map<String, dynamic>? details; final String? traceId; final int? status;
  ApiError(this.code, this.message, {this.details, this.traceId, this.status});
}

sealed class Result<T> { const Result(); }
class Ok<T> extends Result<T> { final T data; const Ok(this.data); }
class Err<T> extends Result<T> { final ApiError error; const Err(this.error); }

class ApiClient {
  ApiClient(this.baseUrl, {this.getToken});
  final String baseUrl; final Future<String?> Function()? getToken;

  Future<Result<T>> get<T>(String path, T Function(Object?) decode) async { /* ... */ }
  Future<Result<T>> post<T>(String path, Object? body, T Function(Object?) decode) async { /* ... */ }

  // Auth
  Future<Result<Map<String, dynamic>>> authGuest() => post('/auth/guest', null, (d) => d as Map<String, dynamic>);
  Future<Result<void>> authEmailRequest(String email) => post('/auth/email/request', {'email': email}, (_) => null);
  Future<Result<Map<String, dynamic>>> authEmailVerify(String email, String code) => post('/auth/email/verify', {'email': email, 'code': code}, (d) => d as Map<String, dynamic>);

  // Rooms
  Future<Result<Map<String, dynamic>>> createRoom({required int seats, required bool fillAi, String? name}) =>
    post('/rooms', {'seats': seats, 'fill_ai': fillAi, if (name != null) 'name': name}, (d) => d as Map<String, dynamic>);
  Future<Result<Map<String, dynamic>>> getRoom(String id) => get('/rooms/$id', (d) => d as Map<String, dynamic>);
  Future<Result<Map<String, dynamic>>> joinRoom(String id, {int? seat}) => post('/rooms/$id/join', {'seat': seat}, (d) => d as Map<String, dynamic>);
  Future<Result<void>> leaveRoom(String id) => post('/rooms/$id/leave', null, (_) => null);
  Future<Result<Map<String, dynamic>>> startRoom(String id) => post('/rooms/$id/start', null, (d) => d as Map<String, dynamic>);

  // Games
  Future<Result<void>> gameAction(String gameId, Map<String, Object?> action) => post('/games/$gameId/action', action, (_) => null);

  // AI
  Future<Result<Map<String, dynamic>>> aiGenerateSpeech(Map<String, Object?> input) => post('/ai/generate_speech', input, (d) => d as Map<String, dynamic>);
  Future<Result<Map<String, dynamic>>> aiDecideAction(Map<String, Object?> input) => post('/ai/decide_action', input, (d) => d as Map<String, dynamic>);

  // Replay
  Future<Result<Map<String, dynamic>>> replayTimeline(String gameId, {String? cursor, int limit = 50}) =>
    get('/replay/$gameId/timeline?${cursor != null ? 'cursor=$cursor&' : ''}limit=$limit', (d) => d as Map<String, dynamic>);
  Future<Result<Map<String, dynamic>>> replaySummary(String gameId) => get('/replay/$gameId/summary', (d) => d as Map<String, dynamic>);

  // STT & Voice
  Future<Result<Map<String, dynamic>>> sttTranscribe(/* file or base64 */) => post('/stt/transcribe', {/*...*/}, (d) => d as Map<String, dynamic>);
  Future<Result<Map<String, dynamic>>> voiceToken() => get('/voice/token', (d) => d as Map<String, dynamic>);
}
```

实现约束
- 统一解析 `{ok, data|error}`；当 `ok=false` 时抛/返回 `ApiError`（含 traceId），以 `ErrorCode` 枚举做分支。
- 超时/重试：AI/WS 相关接口建议超时 5–10s，幂等操作可指数退避重试（最多 2 次）。
- 身份：在 `getToken` 中注入 `Authorization: Bearer <jwt>`；未登录按 `AUTH_REQUIRED` 处理。

### WebSocket 服务契约
```dart
// lib/services/websocket_service.dart
// 约定：连接 /ws/{room_id}?token=<jwt>，消息形如 { type, payload?, seq? }；错误 { type:"error", code, message, details? }

class WsState {
  final bool connected; final int retries; final String? roomId; final int lastSeq;
  const WsState({required this.connected, required this.retries, this.roomId, this.lastSeq = 0});
}

sealed class WsEvent { const WsEvent(); }
class StateUpdate extends WsEvent { final Map<String, dynamic> visible; final String phase; final int tick; const StateUpdate(this.visible, this.phase, this.tick); }
class ChatMessage extends WsEvent { final String from; final String text; const ChatMessage(this.from, this.text); }
class VoteResult extends WsEvent { final Map<String, int> tally; final String? eliminated; const VoteResult(this.tally, this.eliminated); }
class ErrorEvent extends WsEvent { final ErrorCode code; final String message; const ErrorEvent(this.code, this.message); }

typedef MessageEncoder = Map<String, Object?> Function(String type, Map<String, Object?> payload, int? seq);

class WebSocketService {
  WebSocketService(this.baseUrl, {this.pingInterval = const Duration(seconds: 15)});
  final String baseUrl; final Duration pingInterval;
  Stream<WsEvent> get events => _controller.stream; // 统一事件流

  Future<void> connect({required String roomId, required String token});
  Future<void> disconnect([int code = 1000, String reason = 'normal']);
  Future<void> sendChat(String text);
  Future<void> sendVote(int? targetSeat);
  Future<void> sendSkill(String name, {int? targetSeat});
  void ack(int seq);
}
```

连接/重连约定
- 鉴权失败：收到 4401/错误帧 `AUTH_INVALID_TOKEN`，上层触发重新登录流程。
- 心跳：每 15s 发送 `ping`，服务器 `pong`；超 30s 未收到任何帧则视为断线。
- 断线重连：指数退避（0.5s → 1s → 2s → 5s 上限），带上 `lastSeq` 请求补发最近事件。
- 错误帧：不自动断开（除非致命），上报 `ErrorEvent(code,message)` 给上层。

消息示例
```json
// 入站（客户端→服务器）
{ "type": "chat_message", "text": "...", "seq": 101 }
{ "type": "vote_event", "target": "player_5", "seq": 102 }
{ "type": "skill_event", "skill": "witch_heal", "target": "player_2", "seq": 103 }
{ "type": "ack", "seq": 104 }
```
```json
// 出站（服务器→客户端）
{ "type": "state_update", "phase": "Night", "tick": 23, "visible": { } }
{ "type": "vote_result", "tally": {"p1":3,"p2":5}, "eliminated":"p2" }
{ "type": "error", "code": "GAME_INVALID_ACTION", "message": "cannot cast vote in Night" }
```

前端处理建议
- 将 REST 与 WS 错误统一映射到 `ErrorCode`；弹窗展示用户友好文案，同时日志上报 `code + traceId(REST)`。
- 在 Provider 层合并 `WsEvent`，维护 `game/room` 可见状态；所有 UI 组件从 Provider 读取。
