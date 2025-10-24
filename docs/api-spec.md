# AI 狼人杀 · 后端 API 规格（测试期 v1）

> 约定已纳入：邮箱验证码仅记录日志（不真正发送）、回放保留 30 天、首版不启用实时语音但保留接口占位、提供语音转文字（STT）给大模型的接口入口（测试期可返回占位结果）。

## 通用
- 基础 URL：`/`（FastAPI）
- 认证：HTTP Header `Authorization: Bearer <jwt>`（除公开接口外）
 - 响应约定：
  - 成功：`{ "ok": true, "data": ... }`
  - 失败：`{ "ok": false, "error": { "code": "...", "message": "...", "details"?: { ... }, "trace_id"?: "..." } }`
- 速率限制（测试期建议）：
  - `/auth/*` 5 req/min/IP
  - `/ai/*` 10 req/min/user
  - WS 入站消息 20 msg/5s/conn

## 1) 鉴权 Auth（游客 + 邮箱验证码）
- POST `/auth/guest`
  - 入参：无
  - 出参：`{ token, refresh }`
  - 说明：生成 `guest_<shortid>` 用户并颁发短期 JWT。
- POST `/auth/email/request`
  - 入参：`{ email }`
  - 出参：`{ ok: true }`
  - 行为：生成 6 位验证码，仅写入日志（不发送邮件）。
- POST `/auth/email/verify`
  - 入参：`{ email, code }`
  - 出参：`{ token, refresh }`

## 2) 房间 Rooms
- POST `/rooms`
  - 入参：`{ name?, seats: 6|9|10, fill_ai: boolean }`
  - 出参：`{ id, ... }`
- POST `/rooms/{id}/join`
  - 入参：`{ seat? }`
  - 出参：`{ room }`
- POST `/rooms/{id}/leave`
  - 入参：无
  - 出参：`{ ok: true }`
- POST `/rooms/{id}/start`
  - 入参：无（仅房主）
  - 出参：`{ game_id }`
- GET `/rooms/{id}` → 房间详情

## 3) WebSocket 实时通道
- 连接：`/ws/{room_id}?token=<jwt>`
- 入站（示例）：
  ```json
  { "type": "chat_message", "text": "..." }
  { "type": "vote_event", "target": "player_5" }
  { "type": "skill_event", "skill": "witch_heal", "target": "player_2" }
  { "type": "ack", "seq": 123 }
  ```
- 出站（示例）：
  ```json
  { "type": "state_update", "phase": "Night", "tick": 23, "visible": { } }
  { "type": "system_log", "level": "info", "message": "player_3 joined" }
  { "type": "vote_result", "tally": {"p1":3,"p2":5}, "eliminated":"p2" }
  { "type": "chat_message", "from":"p4", "text":"..." }
  ```
- 可靠性：序列号+ack、断线重连补发最近 N 条。

## 4) 对局 Games / 动作 Actions
- GET `/games/{id}` → 基本状态（需成员/观战权限）
- POST `/games/{id}/action`
  - 入参（Union）：
    - 发言：`{ kind:"chat", text }`
    - 投票：`{ kind:"vote", target_seat }`
    - 技能：`{ kind:"skill", name, target_seat? }`
  - 出参：`{ ok: true }`

## 5) AI 服务（OpenAI 直连）
- POST `/ai/generate_speech`
  - 入参：`{ role, phase, visible_state, history_summary, persona? }`
  - 出参：`{ text, confidence? }`
- POST `/ai/decide_action`
  - 入参：`{ options:[...], role, phase, visible_state, history_summary }`
  - 出参：`{ pick, confidence }`
- 说明：测试期按用户/房间限流；失败回退到启发式规则并写日志。

## 6) 回放 Replay（保留 30 天）
- 事件写入范围：阶段切换、发言、投票、技能、系统事件。
- GET `/replay/{game_id}/timeline`
  - 入参：`?cursor&limit=50`
  - 出参：`{ items:[{seq, ts, type, payload}], next_cursor? }`
- GET `/replay/{game_id}/summary`
  - 出参：`{ seats, roles, winner, key_events:[...] }`
- 说明：仅对已结束对局开放；超 30 天的数据由后台任务清理。

## 7) 语音 Voice（接口占位，首版禁用）
- GET `/voice/token`
  - 出参：`{ enabled:false, token:null, vendor:null }`
  - HTTP：`200`（明确禁用状态，供前端判断）
- 说明：后续若启用（如 Agora），将返回 `{ enabled:true, token, vendor:"agora", expire_at }`。

## 8) 语音转文字 STT（入口，占位实现）
- POST `/stt/transcribe`
  - 鉴权：需要登录
  - 入参（multipart/form-data）：`file=<audio>` 或 JSON：`{ audio_base64, mime }`
  - 出参（测试期占位）：
    - 同步：`{ text:"", note:"stub - test period" }`
    - 或异步：`202 Accepted` → `{ job_id }`，随后 `GET /stt/jobs/{job_id}` 返回 `{ status, text? }`
  - 行为（测试期）：仅校验并记录日志，不调用第三方；可配置开关接入真实 STT（如 Whisper/云服务）。

## 9) 商业化接口（占位）
- GET `/billing/products` → 固定假数据列表
- POST `/billing/purchase` → 回 `{ ok:true, order_id:"stub" }`

## 10) 健康检查与状态
- GET `/healthz` → `{ status:"ok" }`
- GET `/stats/room` → 当前房间/在线/WS 连接数等（需管理员）

## 11) 错误与异常约定（Authority）
- 命名规范：`SCOPE_REASON`（全大写、下划线），例如 `AUTH_INVALID_TOKEN`、`ROOM_FORBIDDEN`、`GAME_PHASE_ERROR`、`AI_PROVIDER_ERROR`、`RATE_LIMITED`。
- HTTP 映射建议：
  - 400 `VALIDATION_ERROR`（参数不合法；含 Pydantic 校验）
  - 401 `AUTH_INVALID_TOKEN` / `AUTH_REQUIRED`
  - 403 `ROOM_FORBIDDEN` / `NOT_MEMBER`
  - 404 `NOT_FOUND`
  - 409 `CONFLICT` / `GAME_PHASE_ERROR` / `ALREADY_EXISTS`
  - 429 `RATE_LIMITED`
  - 500 `INTERNAL_ERROR`；503 `DEPENDENCY_UNAVAILABLE`；504 `TIMEOUT`
- WS 错误：
  - 非致命：`{ type: "error", code, message, details? }`；致命错误发送后以应用码 4000–4099 关闭连接。

权威错误码清单（最小集）
- AUTH_REQUIRED, AUTH_INVALID_TOKEN, AUTH_RATE_LIMITED, AUTH_EXPIRED
- ROOM_NOT_FOUND, ROOM_FORBIDDEN, NOT_MEMBER, ROOM_FULL
- GAME_NOT_FOUND, GAME_PHASE_ERROR, GAME_INVALID_ACTION, CONFLICT
- AI_RATE_LIMITED, AI_PROVIDER_ERROR, AI_TIMEOUT
- VALIDATION_ERROR, NOT_FOUND, RATE_LIMITED, INTERNAL_ERROR, DEPENDENCY_UNAVAILABLE, TIMEOUT

REST 示例响应
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "field 'seats' must be one of [6,9,10]",
    "details": {"field":"seats"},
    "trace_id": "a1b2c3d4"
  }
}
```
```json
{
  "ok": false,
  "error": {"code":"AUTH_REQUIRED","message":"missing bearer token","trace_id":"e9f0aa"}
}
```
```json
{
  "ok": false,
  "error": {"code":"RATE_LIMITED","message":"too many requests","trace_id":"r-lmt-01"}
}
```
```json
{
  "ok": false,
  "error": {"code":"GAME_PHASE_ERROR","message":"action not allowed in phase Vote","trace_id":"phx-22"}
}
```
```json
{
  "ok": false,
  "error": {"code":"AI_TIMEOUT","message":"provider timeout","details":{"provider":"openai"},"trace_id":"ai-t-09"}
}
```

WS 错误示例
```json
{ "type":"error", "code":"GAME_INVALID_ACTION", "message":"cannot cast vote in Night" }
```

## 示例：邮箱验证码仅日志
- 日志记录：`[AUTH][EMAIL] send code 834912 to demo@example.com (test mode)`
- 客户端交互：`/auth/email/request` 返回 `{ ok:true }`，用户从日志（测试环境）或后端控制台获取验证码。

## 示例：回放清理（30 天）
- 后台任务（每日 03:00）：删除 `game_events`/`game_summary` 中 `ended_at < now()-30d` 的数据；生成指标日志。
