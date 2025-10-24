# 狼人杀游戏逻辑规格（标准规则 v1，后端实现指引）

> 适配席位 6/9/10；默认角色：狼人、预言家、女巫、猎人、平民。对齐 docs/api-spec.md 与 docs/dev-plan.md。

## 1. 角色与能力（默认）
- 狼人（W）：夜晚联合选择击杀 1 人/晚。
- 预言家（S）：每晚验 1 人，返回是否为狼。
- 女巫（Witch）：解药×1（可救被狼刀目标），毒药×1（可毒任意 1 人）。
- 猎人（H）：死亡时可开枪带走 1 人（白天被放逐必定可开枪；夜晚是否可开枪可配）。
- 平民（V）：无技能。

可配置项（Room.settings）：
- hunter.shoot_on_day_lynch=true；hunter.shoot_on_night_kill=true。
- witch.see_wolf_target=true；witch.can_self_heal=true。
- vote.tied_policy="revote_then_no_lynch"｜"revote_then_random"（默认前者）。
- day.talk_order="seating_random_start"｜"seating"｜"free"；phase.durations={ night:45s, day_talk:120s, vote:30s, resolve:5s }。

## 2. 阶段流程（状态机）
- Init：分配座位与角色，向对应身份推送可见情报。
- Night：狼人选刀→女巫看刀（可救/可毒）→预言家验人→形成夜死名单。
- Day：公示夜死名单→按随机起始座位顺序或自由发言。
- Vote：投票放逐；平票则复投一次，仍平票按策略处理（默认无放逐）。
- Resolve：执行放逐与猎人开枪等连锁→胜负判定→若未分胜负则进入下一夜。

## 3. 夜晚结算与冲突裁决
- 顺序：狼人刀→女巫解药→女巫毒药→预言家验人→夜死名单。
- 冲突：
  - 狼刀目标=毒药目标且用了解药：最终仍死亡（由毒药致死）。
  - 多来源致死记录合并为单一死亡事件，来源集合入事件详情。
  - 猎人夜晚被杀是否可开枪由配置决定（默认可）。

## 4. 投票与出局
- 投票期内可多次改票，计最后一次；可弃权。
- 统计最高票；若唯一最高票则放逐该玩家。
- 平票：首次平票→复投；仍平票→按策略（默认无放逐）。
- 放逐为猎人时：若 shoot_on_day_lynch=true 则进入开枪选择（限时）。

## 5. 胜负判定
- 狼人全灭→好人胜；存活狼人数≥非狼存活人数→狼人胜。
- 判定时机：Resolve 阶段与夜晚结算末尾均检查。

## 6. 可见性规则
- 预言家验人结果仅预言家可见。
- 女巫是否知晓被刀者由配置（默认可见）。
- 夜死名单仅在白天公示；放逐即时全员可见。
- 回放隐藏夜间隐私细节，仅显示观战可见版。
- 若 day.talk_order = seating_random_start，则每日随机选择起始座位，随后按座位号轮转。

## 7. 事件与回放（30 天保留）
- 事件类型：game_started、role_assigned、phase_changed、wolf_kill_chosen、witch_heal_used、witch_poison_used、seer_checked、day_deaths_announced、vote_cast、lynch_result、hunter_shot、game_ended、chat_message。
- 事件字段：{ game_id, seq, ts, type, actor_seat?, payload }；seq 递增。
- 清理：每日定时任务删除超过 30 天的 replay 数据。

## 8. 服务端状态（示例）
- meta：{ game_id, room_id, round, phase, timers }。
- seats：[{ seat, user_id, role(hidden), alive }]。
- night：{ wolf_target?, witch:{ heal_left:1, poison_left:1 }, poison_target?, seer_last_result? }。
- vote：{ ballots:{ seat->target|null }, revote_count:0|1 }。

## 9. 行为校验与幂等
- 校验：阶段、权限、目标座位、冷却/次数、是否存活。
- 幂等：以 (game_id, actor_seat, phase, action_key) 去重；投票为覆盖写入。
- WS 可靠性：seq+ack；断线重连补发最近 N 条。

## 10. AI 集成点
- generate_speech：输入 { role, phase, visible_state, history_summary, persona }，输出 { text, confidence? }。
- decide_action：输入 { options, role, phase, visible_state, history_summary }，输出 { pick, confidence }。
- 风控：对 /ai/* 做用户/房间限流；失败回退启发式策略并记录日志。

## 11. 默认配比（可覆盖）
- 6 人：2W 1S 1Witch 0H 2V。
- 9 人：3W 1S 1Witch 1H 3V。
- 10 人：3W 1S 1Witch 1H 4V。

## 12. 默认项（已确认）
- 女巫允许自救：true
- 猎人夜晚被杀可开枪：true
- 发言顺序：seating_random_start（每日随机起始座位）
- 平票策略：二次仍平票无放逐（revote_then_no_lynch）

以上作为默认房间模板，后端据此实现 services/game_state 与 ws/message_bus。
