# 示例对局日志（覆盖关键规则）

说明
- 座位数：9 人；默认配置：女巫可自救、猎人夜杀可开枪、发言随机起始座位、二次仍平票则无放逐。
- 视图分为两种：内部事件日志（开发/排查用，含隐私信息）与观战回放视图（对玩家可见，隐藏夜间隐私）。
- 为简洁，省略具体时间戳，使用 `seq` 递增标记顺序。

参与者与角色（内部，仅开发可见）
- S1: Villager
- S2: Werewolf
- S3: Hunter
- S4: Villager
- S5: Seer
- S6: Witch
- S7: Werewolf
- S8: Villager
- S9: Werewolf

---

## A) 内部事件日志（Internal Event Log）

1. { seq:1,  type:"game_started", payload:{ room_id:"R1001", game_id:"G9001", seats:9 } }
2. { seq:2,  type:"role_assigned", actor_seat:2, payload:{ role:"W" } }
3. { seq:3,  type:"role_assigned", actor_seat:7, payload:{ role:"W" } }
4. { seq:4,  type:"role_assigned", actor_seat:9, payload:{ role:"W" } }
5. { seq:5,  type:"role_assigned", actor_seat:5, payload:{ role:"S" } }
6. { seq:6,  type:"role_assigned", actor_seat:6, payload:{ role:"Witch" } }
7. { seq:7,  type:"role_assigned", actor_seat:3, payload:{ role:"H" } }
8. { seq:8,  type:"phase_changed", payload:{ phase:"Night", round:1 } }

夜 1：
9.  { seq:9,  type:"wolf_kill_chosen", actor_seat:2, payload:{ target:6 } }
10. { seq:10, type:"witch_heal_used", actor_seat:6, payload:{ target:6, self_heal:true } }  // 自救
11. { seq:11, type:"witch_poison_used", actor_seat:6, payload:{ target:8 } }
12. { seq:12, type:"seer_checked", actor_seat:5, payload:{ target:2, is_wolf:true } }
13. { seq:13, type:"phase_changed", payload:{ phase:"Day", round:1 } }
14. { seq:14, type:"day_deaths_announced", payload:{ deaths:[8] } }
15. { seq:15, type:"chat_message", actor_seat:4, payload:{ text:"先我说，昨晚只有一死。" } } // 发言随机从 S4 开始依序
16. { seq:16, type:"chat_message", actor_seat:5, payload:{ text:"我验2，显示狼。" } }
17. { seq:17, type:"chat_message", actor_seat:2, payload:{ text:"5在抿我，别信。" } }
18. { seq:18, type:"phase_changed", payload:{ phase:"Vote", round:1 } }
19. { seq:19, type:"vote_cast", actor_seat:1, payload:{ target:2 } }
20. { seq:20, type:"vote_cast", actor_seat:2, payload:{ target:5 } }
21. { seq:21, type:"vote_cast", actor_seat:3, payload:{ target:2 } }
22. { seq:22, type:"vote_cast", actor_seat:4, payload:{ target:2 } }
23. { seq:23, type:"vote_cast", actor_seat:5, payload:{ target:2 } }
24. { seq:24, type:"vote_cast", actor_seat:6, payload:{ target:4 } }
25. { seq:25, type:"vote_cast", actor_seat:7, payload:{ target:5 } }
26. { seq:26, type:"vote_cast", actor_seat:8, payload:{ target:null } } // 弃权
27. { seq:27, type:"vote_cast", actor_seat:9, payload:{ target:5 } }
28. { seq:28, type:"lynch_result", payload:{ top:[2,5], tie:true, action:"revote" } }
29. { seq:29, type:"phase_changed", payload:{ phase:"Vote", round:1, revote:true } }
30. { seq:30, type:"vote_cast", actor_seat:1, payload:{ target:2 } }
31. { seq:31, type:"vote_cast", actor_seat:2, payload:{ target:5 } }
32. { seq:32, type:"vote_cast", actor_seat:3, payload:{ target:2 } }
33. { seq:33, type:"vote_cast", actor_seat:4, payload:{ target:5 } }
34. { seq:34, type:"vote_cast", actor_seat:5, payload:{ target:2 } }
35. { seq:35, type:"vote_cast", actor_seat:6, payload:{ target:5 } }
36. { seq:36, type:"vote_cast", actor_seat:7, payload:{ target:5 } }
37. { seq:37, type:"vote_cast", actor_seat:8, payload:{ target:null } }
38. { seq:38, type:"vote_cast", actor_seat:9, payload:{ target:2 } }
39. { seq:39, type:"lynch_result", payload:{ top:[2,5], tie:true, action:"no_lynch" } } // 二次仍平票，无放逐
40. { seq:40, type:"phase_changed", payload:{ phase:"Night", round:2 } }

夜 2：
41. { seq:41, type:"wolf_kill_chosen", actor_seat:7, payload:{ target:3 } } // 狼杀猎人
42. { seq:42, type:"seer_checked", actor_seat:5, payload:{ target:9, is_wolf:true } }
43. { seq:43, type:"hunter_shot", actor_seat:3, payload:{ target:7, trigger:"night_kill" } } // 夜杀触发开枪
44. { seq:44, type:"phase_changed", payload:{ phase:"Day", round:2 } }
45. { seq:45, type:"day_deaths_announced", payload:{ deaths:[3,7] } }
46. { seq:46, type:"chat_message", actor_seat:1, payload:{ text:"今天我先说，昨晚双死。" } } // 发言随机从 S1 开始
47. { seq:47, type:"chat_message", actor_seat:5, payload:{ text:"昨晚我验9是狼，2也是狼。" } }
48. { seq:48, type:"phase_changed", payload:{ phase:"Vote", round:2 } }
49. { seq:49, type:"vote_cast", actor_seat:1, payload:{ target:2 } }
50. { seq:50, type:"vote_cast", actor_seat:2, payload:{ target:5 } }
51. { seq:51, type:"vote_cast", actor_seat:4, payload:{ target:2 } }
52. { seq:52, type:"vote_cast", actor_seat:5, payload:{ target:2 } }
53. { seq:53, type:"vote_cast", actor_seat:6, payload:{ target:2 } }
54. { seq:54, type:"vote_cast", actor_seat:8, payload:{ target:2 } }
55. { seq:55, type:"vote_cast", actor_seat:9, payload:{ target:5 } }
56. { seq:56, type:"lynch_result", payload:{ executed:2 } }
57. { seq:57, type:"phase_changed", payload:{ phase:"Night", round:3 } }

夜 3：
58. { seq:58, type:"wolf_kill_chosen", actor_seat:9, payload:{ target:5 } }
59. { seq:59, type:"phase_changed", payload:{ phase:"Day", round:3 } }
60. { seq:60, type:"day_deaths_announced", payload:{ deaths:[5] } }
61. { seq:61, type:"phase_changed", payload:{ phase:"Vote", round:3 } }
62. { seq:62, type:"vote_cast", actor_seat:1, payload:{ target:9 } }
63. { seq:63, type:"vote_cast", actor_seat:4, payload:{ target:9 } }
64. { seq:64, type:"vote_cast", actor_seat:6, payload:{ target:9 } }
65. { seq:65, type:"vote_cast", actor_seat:8, payload:{ target:9 } }
66. { seq:66, type:"vote_cast", actor_seat:9, payload:{ target:1 } }
67. { seq:67, type:"lynch_result", payload:{ executed:9 } }
68. { seq:68, type:"game_ended", payload:{ winner:"villagers", reason:"wolves_eliminated" } }

---

## B) 观战回放视图（Spectator Replay, 隐私裁剪）

- 裁剪规则：移除夜晚隐私信息（狼刀选择、女巫操作、预言家验人、猎人触发原因），仅保留对观众允许的信息。

示例节选：
- seq 13: phase→Day 1
- seq 14: 公示夜死：[8]
- seq 15–17: 白天发言（起始座位随机：S4）
- seq 28–39: 投票、复投、当日无放逐
- seq 44–45: Day 2 公示双死：[3,7]
- seq 46–47: 白天发言（起始座位随机：S1）
- seq 56: 放逐 S2
- seq 60: 公示夜死：[5]
- seq 67–68: 放逐 S9 → 好人胜利

注：内部日志用于调试与回放重建；前端回放应使用观战视图数据源。
