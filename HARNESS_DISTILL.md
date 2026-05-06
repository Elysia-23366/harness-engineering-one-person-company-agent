# Harness Distillation Card · 工程化总结

> **一句话源起**: `Agent = Model + Harness`,我把这套机制拆成 7 个工程模块,全部嵌入「一人公司 Agent」。
>
> **本卡定位**:一页讲清是什么、做了什么、可以从哪里看到效果。

---

## 1. 七模块 → 实现一图对应

| #  | Harness 模块            | 工程实现                                                                | 数据落点                                          |
|----|------------------------|------------------------------------------------------------------------|--------------------------------------------------|
| 01 | 模型评判 model_evaluation     | `app/harness/sensors.py` · 三类 sensor 总通过率                        | `harness_sensor_event.passed`                    |
| 02 | 工具调用 tool_invocation      | `app/workflow/one_person_company.py` pre/post hook 落事件                | `harness_event` 表                               |
| 03 | 记忆管理 memory_management    | `app/harness/engine.py` 重要性 3 维评分 + `auto_route_event`          | `harness_event` + `persona_card` + `relationship` |
| 04 | 上下文管控 context_control    | `app/harness/prompts.py` 三层 prompt + Top-K 召回                       | `assemble_persona_prompt()`                      |
| 05 | 状态持久化 state_persistence  | persona_card / relationship 永久表                                      | `persona_card` + `relationship`                   |
| 06 | 错误处理 error_handling       | sensors 失败事件 + `evolve_thresholds` 自动建议                         | `harness_sensor_event.passed=false`              |
| 07 | 安全防护 safety_protection    | Guides 三级 (global / role / agent) 前馈护栏                            | `harness_guide` 表                                |

---

## 2. 三库记忆 · OOC 角色漂移工程解

```
┌─────────────────┬─────────────────┬─────────────────┐
│ 事件库 Episodic  │ 角色认知 Persona │ 关系节点 Relation │
├─────────────────┼─────────────────┼─────────────────┤
│ 衰减式存活        │ 永久 · 累积印象    │ 永久 · 每对独立    │
│ score × e^(-rt) │ trait_keywords + │ trust × familiarity │
│ 阈值 2.0 → 淘汰   │ confidence_level │ × phase 升级       │
│ 跨人物共享        │ 跨人物            │ 每对 (A,B) 一行    │
└─────────────────┴─────────────────┴─────────────────┘
       ↑                ↑                  ↑
       └─── auto_route_event() 三库联写 ───┘
```

**为什么三库?**
- 单事件库 → 重要事实会被衰减,角色"失忆"。
- 单总结库 → 没法回到原始事件做证据回溯。
- **三库分工**:事件可衰减 + 认知/关系永久,既保留鲜活原文,又有稳定人格。

---

## 3. 前馈 ⊕ 反馈双控

```
       Guides(前馈 · 启动前注入)
            │
            ▼
  ┌────────────────────┐
  │  Workflow          │   每次 LLM 调用都被记账
  │  one_person_company│ ───────────────►  事件库
  └────────────────────┘                    │
            │                               ▼
            │                          Top-K 召回
            ▼                               │
       Sensors(反馈 · 输出后检测)            ▼
            │                          下次 prompt
            ▼
   evolve_thresholds(自进化)
            │
            ▼
   建议 → importance_calibration 落库
```

- **Guides 前馈**:`assemble_persona_prompt()` 拼装时,把命中的 guide 文本拼到 system prompt 顶端
- **Sensors 反馈**:命中率 / 输出合规度 / Persona Drift 三类传感器,每次 workflow 跑完后异步写一笔
- **自进化**:每 N 次采样自动诊断,输出可读的 `suggestion` 落 `importance_calibration` 表

---

## 4. 关键 API 一览(全部已通过 e2e smoke)

| 端点                                              | 用途                                            |
|---------------------------------------------------|------------------------------------------------|
| `GET  /api/harness/dashboard`                     | 七模块 + 总览 metrics(SevenModuleDashboard)    |
| `POST /api/harness/score`                         | 评分单条候选事件(D3 引擎)                       |
| `GET  /api/harness/events?active_only&limit`      | 事件库 · 衰减后 importance 排序                  |
| `GET  /api/harness/personas`                      | 17 个岗位的角色认知                              |
| `GET  /api/harness/relationships`                 | CEO ↔ 17 个岗位的关系节点                        |
| `GET  /api/harness/guides[?scope=&agent_id=]`     | Guides 前馈护栏(三级作用域)                     |
| `POST /api/harness/guides`                        | 创建 guide                                      |
| `PUT  /api/harness/guides/{id}`                   | 更新                                            |
| `DELETE /api/harness/guides/{id}`                 | 删除                                            |
| `GET  /api/harness/sensors?sensor_type=&limit`    | 4 类传感器事件(命中/合规/漂移/校准)              |
| `POST /api/harness/sensors/evolve`                | 触发阈值自进化(EvolutionChart "立刻诊断"按钮) |

---

## 5. 关键文件 map

```
backend/app/harness/
├── engine.py        · 重要性 3 维评分 + auto_route_event
├── prompts.py       · 三层 prompt 拼装 + 召回 hook
├── sensors.py       · 4 类 sensor + evolve_thresholds
├── routes.py        · 全部 /api/harness/* 端点
└── schemas.py       · pydantic 模型

backend/app/workflow/one_person_company.py
  └─ pre_llm_hook + post_llm_hook 集成 Harness

frontend/src/components/harness/
├── SevenModuleDashboard.vue  · D12 hero(7 模块仪表)
├── GuidesPanel.vue           · D8 前馈面板(CRUD)
├── SensorsPanel.vue          · D9 反馈面板
├── MemoryDashboard.vue       · D10 三库 + 衰减曲线 SVG
├── DriftRadar.vue            · D11 漂移雷达
└── EvolutionChart.vue        · D13 命中率时序 + 自进化时间线

frontend/src/pages/HarnessPage.vue
  └─ 上述 6 大组件按 hero → 前馈 → 反馈 → 记忆 → 漂移 → 自进化 顺序排列

backend/test_harness_e2e.py · 8 段 e2e smoke,跑一次 27 秒,全绿
```

---

## 6. 怎么 demo(给 CEO / 给观众看)

1. **打开 `/harness`** → 上来一眼七模块大图,7 个数字全活,在线指示灯绿。
2. **新建一条 Guide** → "测试中说话再口语化",刷新事件库下次 prompt 就拼上了。
3. **跑一次 workflow** → 命中率 / 合规度 / 漂移度三个 sensor 同时在 SensorsPanel 跳数。
4. **MemoryDashboard 切到 "事件库"** → 衰减曲线 8 条线一目了然,谁会被淘汰、谁能撑 30 天。
5. **EvolutionChart 点 "立刻诊断"** → 系统读出当前指标 → 给出可执行的 `suggestion`(例:阈值从 0.5 降到 0.4)。
6. **跑 `python backend/test_harness_e2e.py`** → 27 秒打 8 段对勾,工程化全链路通。

---

## 7. 这套东西"值"在哪

- **一句话**:把"Harness 机制"翻译成"可点的按钮 + 可读的数字 + 可演的 demo"。
- 业务上:**OOC 角色漂移**这个长期心病 → 三库 + 漂移雷达 → 真正可观测、可矫正。
- 工程上:**Agent ≠ 一次性 prompt**,而是有记忆 / 会被检测 / 会自进化的常驻系统 → 这套代码就是那个系统。
- 路演上:本卡 + EvolutionChart 单独一张图就够讲 5 分钟,数据自己会说话。

---

> 蒸馏作者: 一人公司 Agent · 完成于 2026-05-05
> 工程实现周期: W1 D3 → W2 D14,共 12 个工作日
