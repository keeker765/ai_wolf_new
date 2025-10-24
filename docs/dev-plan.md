# AI 狼人杀｜详细开发计划 v2（后端优先）

> 根据产品答复已纳入：使用 OpenAI、Web 优先、支持游客+邮箱登录、提供回放、暂无数据合规要求、预留商业化接口、需要统一 UI（后续推进），当前阶段优先完成后端。

## 0. 目标与指标
- 平台：Web 优先（Flutter Web 客户端对接 FastAPI 后端）。
- AI：直接使用 OpenAI API（可留本地 LLM 备选接口）。
- 并发与稳定：同区消息延迟 P95 ≤ 150ms；房间并发≥2k；后端可用性≥99.9%。
- 测试覆盖：核心逻辑（状态机/投票/AI 接口）覆盖率≥80%。

## 1. 时间轴与里程碑（后端优先，12–13 周）
- W1–W2 M1 基建与原型：项目脚手架、DB/Redis 初始化、鉴权骨架、CI/CD。
- W3–W4 M2 房间与 WebSocket：房间创建/加入、状态同步、断线重连、心跳。
- W5–W7 M3 核心规则与状态机：身份分配、夜/昼、技能、发言、投票、结算。
- W8–W9 M4 AI 服务：OpenAI 接入、发言生成/决策接口、速率限制与缓存。
- W10 M5 回放系统：事件存储、回放时间线 API、对局摘要。
- W11 M6 压测与优化：WS 广播、热点房间、Redis/DB 调优、告警。
- W12 上线准备：灰度/回滚策略、运维手册与验收。

## 2. 架构与目录
- 后端：FastAPI + Uvicorn；Redis（状态与广播）；PostgreSQL（持久化）；APScheduler；Docker。
- 目录建议（backend/）：
  - app/
    - core/（配置、启动、中间件、安全）
    - routers/（auth、rooms、games、ai、replay、stats、health）
    - services/（game_state、vote、role、ai, replay、room_manager、voice_token_stub）
    - ws/（connection、room_manager、message_bus）
    - models/（SQLAlchemy async + Pydantic schemas）
    - utils/（id、time、rate_limit、logging）
  - tests/（单元与集成）

## 3. 环境与配置
- 环境变量
  - `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`、`OPENAI_API_KEY`、`CORS_ORIGINS`
- 运行
  - 本地：`uvicorn app.main:app --reload`
  - 测试：`pytest -q`
  - 质量：`ruff check . && black --check .`
- CI：PR 触发 lint+test；main 构建镜像，预发自动部署。

## 4. 鉴权与用户体系（游客 + 邮箱）
- 游客登录：匿名会话生成 `guest_<shortid>`，颁发短期 JWT（仅限测试房间）。
- 邮箱登录（测试期）：密码less 邮箱验证码（默认打印到日志，可接 SMTP）；颁发短期 JWT + 刷新。
- 路由
  - POST `/auth/guest` → {token}
  - POST `/auth/email/request` → {ok}（发送/日志验证码）
  - POST `/auth/email/verify` → {token, refresh}
- 安全：房间操作均需 JWT；房主/成员/观战权限检查；速率限制（IP/用户）。

## 5. 房间与游戏生命周期
- 房间
  - POST `/rooms`（参数：人数、是否 AI 补位、房名）
  - POST `/rooms/{id}/join` / `leave`
  - GET `/rooms/{id}` 房间详情
  - WS `/ws/{room_id}`：加入即订阅广播；心跳 `ping/pong`
- 生命周期
  - Init → Night → Day → Vote → Resolve → End（异常：Abort/Timeout）
  - Redis 维护房间快照与计时；APScheduler 定时阶段切换。
- 权限
  - 房主可开始/解散；超时自动解散；断线重连保留席位（超时释放）。

## 6. WebSocket 协议（草案）
- 入站消息（客户端→服务器）
```
{ "type": "chat_message", "text": "..." }
{ "type": "vote_event", "target": "player_5" }
{ "type": "skill_event", "skill": "witch_heal", "target": "player_2" }
{ "type": "ack", "seq": 123 }
```
- 出站消息（服务器→客户端）
```
{ "type": "state_update", "phase": "Night", "tick": 23, "visible": { ... } }
{ "type": "system_log", "level": "info", "message": "player_3 joined" }
{ "type": "vote_result", "tally": {"p1":3,"p2":5}, "eliminated":"p2" }
{ "type": "chat_message", "from":"p4", "text":"..." }
```
- 可靠性：序列号+ack；断线重连后补发最近 N 条（Redis 列表）；限流与风控策略。

## 7. 核心规则与服务
- RoleService：身份池与分配（狼人/预言家/女巫/猎人/平民）。
- GameStateService：状态机，推进阶段与可用动作校验；超时策略（默认发言/弃权）。
- VoteService：投票与结算，幂等校验与最后有效提交；公示结果。
- Visibility 规则：夜晚仅向有权限的座位推送可见字段（后端裁剪）。

## 8. AI 服务（OpenAI 直连）
- AI 接口
  - POST `/ai/generate_speech`：输入（角色、阶段、可见信息、历史摘要）→ 文本
  - POST `/ai/decide_action`：输入（可选目标列表、局势摘要）→ 目标 + 置信度
- 实现
  - OpenAI Chat Completions（gpt-4o-mini / gpt-4.1 可配置）；温度与人格参数可调。
  - Prompt 结构：系统规则 + 可见上下文 + 指令模板；禁止泄露隐藏身份。
  - 速率限制与缓存：用户/房间维度 QPS；按上下文哈希缓存短期结果（Redis）。
  - 失败回退：超时/配额不足 → 使用简化启发式规则。

## 9. 回放系统（首版只读）
- 事件模型：对局内所有可重建动作序列（时间戳、座位、动作、可见内容）。
- 存储：PostgreSQL `game_events`（按 game_id 分片表）+ 精简索引；大文本入压缩JSON。
- 写入：阶段切换、发言、投票、技能、系统事件均写入事件表；结束后生成 `game_summary`。
- API
  - GET `/replay/{game_id}/timeline` → 事件列表（分页）
  - GET `/replay/{game_id}/summary` → 角色分配、胜负、关键节点
- 安全：仅对已结束对局开放；隐私：不返回夜晚隐藏信息的真实细节，仅返回「对回放观看者允许的可见版」。

## 10. 数据模型（核心表，简要）
- users(id, email?, is_guest, created_at)
- rooms(id, owner_id, status, settings_json, created_at)
- room_members(id, room_id, user_id, seat, role?, joined_at, left_at)
- games(id, room_id, status, round, started_at, ended_at)
- game_actions(id, game_id, actor_seat, type, payload_json, ts)
- game_events(id, game_id, seq, type, payload_json, ts)
- ai_profiles(id, name, persona_json)
- logs(id, level, message, ctx_json, ts)

## 11. 安全与合规（按产品要求简化）
- 无地域合规要求；仍执行最小化采集与日志脱敏。
- JWT 短期有效+刷新；WS 鉴权（连接参数+定期校验）。
- 速率限制：登录、AI 接口、WS 消息提交；IP+用户双维度。

## 12. DevOps 与运维
- 构建：多阶段 Docker；`backend/Dockerfile` 输出 slim 镜像。
- 配置：`.env` + Secret 管理；预发/生产分环境变量。
- 监控：APM（延迟/错误率）、WS 在线与消息速率、Redis 命中率、DB 连接池。
- 告警：P95 延迟、5xx 比例、Redis 饱和、DB 慢查询。

## 13. 测试与验收
- 单元：状态机、投票、可见性裁剪、AI 输出格式校验。
- 集成：房间→开局→阶段推进→结算；断线重连；AI 调用超时回退。
- E2E（脚本化模拟）：10 人局，全流程 50 场稳定完成。
- 压测：WS 广播、房间/节点扩展；目标 P95 ≤ 150ms。
- 验收：达成指标与关键用例，Bug 等级不高于中位的全部清理。

## 14. 商业化接口（预留）
- 路由占位：`/billing/products`、`/billing/purchase`（返回固定假数据）。
- 权限占位：`feature_flags`（例如高级皮肤/快速开局标志）。

## 15. 前端协作要点（Web 优先）
- CORS：允许前端域名；WS 使用 `wss` in prod。
- 协议契约：严格遵循 `type + payload` 的 WS 消息格式。
- 设计统一：后续提供 Design Tokens(JSON)；当前阶段后端先行。

## 16. 任务拆分（后端待办列表）
- W1–W2
  - 初始化项目结构、配置管理、日志体系
  - SQLAlchemy(Async) 与 Alembic 迁移；Redis 连接池
  - JWT 鉴权与中间件；游客+邮箱登录全流程
  - 健康检查 `/healthz`、基本监控埋点
- W3–W4
  - RoomManager + WS 心跳/重连
  - 房间 CRUD + 成员席位管理 + 权限
  - 消息协议与广播总线；限流与防刷
- W5–W7
  - 状态机与规则实现；夜/昼/技能/投票/结算
  - 可见性裁剪与服务端校验；边界与异常流
  - 集成测试用例与契约测试
- W8–W9
  - OpenAI 集成：发言与动作决策；缓存与回退
  - Prompt 模板与人格参数；速率限制
- W10
  - 回放事件落库与时间线 API；摘要生成
- W11–W12
  - 压测与调优；安全审查；文档与上线准备

---

## 待确认（简短）
1) 语音方案供应商偏好：Agora 还是自建 WebRTC（仅留后端令牌签发 stub，无需前期投入也可）？
2) 邮箱验证码是否需要真实发送（SMTP/服务商）还是测试期仅打印日志？
3) 回放保留时长与数据量目标（例如 30 天/每局上限 1MB）？

如确认以上选项，我将开始搭建后端骨架与首批路由/模型。 
