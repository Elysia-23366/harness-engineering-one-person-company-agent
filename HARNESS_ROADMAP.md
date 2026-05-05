# Harness Engineering 嵌入路线图 · v1.0

> **一句话定位**:把武艺《Harness Engineering 闭门分享 · 2026-04-28》的核心方法论真正嵌入「一人公司 Agent」产品,让它从"又一个多 Agent 编排平台"升级为**国内首个 Harness 工程可视化产品 demo**。

**起始**: 2026-05-05
**预算**: 14 天(精品档)
**主理**: AI 自跑 + CEO 关键节点确认

---

## 0. 武艺 Harness 核心机制 4 大点(我严格遵循的"圣经")

### 0.1 三层进化范式(传承关系,不是替代)
- 23 年 = Prompt Engineering(怎么问)
- 24-25 年 = Context Engineering(给什么信息)
- **26 年 = Harness Engineering(用什么 OS 驾驭模型)**
- **核心公式**: `Agent = Model + Harness`

### 0.2 Guides ⊕ Sensors 双控制(行业首次共识命名)
- **Guides 前馈** — 行动**之前**的护栏,设规则/边界,模型只能在轨道里走
- **Sensors 反馈** — 行动**之后**的检测,自动度量/命中率监控/自纠错
- → **完整闭环系统会自我进化,不是一次性配置**

### 0.3 三库记忆架构(角色漂移 OOC 的工程解)
| 库 | 内容 | 衰减 | 共享 |
|---|---|---|---|
| **事件库** Episodic | 发生了什么(情绪标签) | ✓ 遗忘曲线 | 跨人物 |
| **角色认知** Persona | 角色对用户的印象 | ✗ 永久 | 跨人物 |
| **关系节点** Relationship | 双方关系坐标 | ✗ 永久 | **每对独立** |

### 0.4 重要性 3 维打分(Guides 入口规则)
- 情绪激烈度(0-3)
- 是否带来新素材(0-3)
- 是否影响关系(0-3)
- 阈值: ≥6 写入 / 3-6 写入但高衰减 / <3 不写

### 0.5 召回机制(top-5 精准 > 全量塞)
> "记忆过载是另一种记忆失焦"——武艺原话

- 关键词 + 情绪 + 重要性加权
- 取 top-5 注入 prompt
- 不是 RAG 全量,是精选

---

## 1. 6 大嵌入模块(产品级)

### M1 · 三库记忆系统(P0 · W1 D1-2)

**SQLite 增加 5 张表**:
- `event_memory` — 衰减式事件库
- `persona_perception` — 17 岗位对 CEO 的累积印象
- `relationship_node` — 17 × CEO 信任度坐标
- `sensor_event` — Sensors 自进化日志
- `guide_rule` — Guides 规则表(CEO 可编辑)

**API**:`/api/harness/memory/*` · CRUD + 召回

**集成**:`one_person_company` workflow 每个 worker 节点执行后写入

### M2 · 重要性评分引擎(P0 · W1 D3)

**3 维度自动打分** + 阈值路由 + 衰减算法

### M3 · 召回机制(P0 · W1 D4)

**top-5 精准检索** + 上下文注入到下一个 agent 的 prompt

### M4 · Persona Core 三层分离(P0 · W1 D5)

**Prompt = system_prompt(永久) + working_context(动态) + memory_recall(召回)**

每个 R01-R23 的 prompt 在执行时**动态拼装**。

### M5 · Sensors 自进化引擎(P0 · W1 D6-7)

- 召回命中率监控
- Persona 漂移检测(余弦相似度)
- 输出合规度检测
- 命中率下降 → 自动调整阈值/规则

### M6 · 前端可视化(P0+P1 · W2 全部)

- **Guides + Sensors 双控台**(主组件)
- 三库记忆面板(衰减曲线 + 评分可视化)
- Persona Drift 雷达图
- Harness 七模块 Dashboard(主页 hero 替换)
- 命中率自进化可视化

---

## 2. 14 天工作分布

### Week 1 · 后端核心(数据 + 逻辑)

| Day | 任务 | 产出 |
|---|---|---|
| D1 | 三库 schema + DB migration 脚本 | SQL 文件 + 可执行 migration |
| D2 | Pydantic models + CRUD API | `/api/harness/memory/*` |
| D3 | 重要性评分引擎 + 写入路由 | `/api/harness/score` |
| D4 | 召回机制 top-5 + 注入 hook | workflow 调用时自动注入 |
| D5 | Persona Core 三层分离 + prompt 组装器 | 17 岗位 prompt 全升级 |
| D6 | Sensors 自进化引擎(命中率) | `/api/harness/sensors/*` |
| D7 | Sensors Persona Drift + 输出合规度 | 完整闭环 |

**W1 验收**:跑一个 workflow,backend 应:
- 自动给每个 worker 输出打 3 维度分数
- 自动写入合适的库
- 下次跑时自动召回 top-5
- 检测 Persona 漂移 → 触发警报

### Week 2 · 前端可视化(讲故事)

| Day | 任务 | 产出 |
|---|---|---|
| D8 | Guides 前馈面板组件 | `<GuidesPanel>` Vue |
| D9 | Sensors 反馈面板组件 | `<SensorsPanel>` Vue |
| D10 | 三库记忆面板 + 衰减曲线 | `<MemoryDashboard>` |
| D11 | Persona Drift 雷达图 | `<DriftRadar>` |
| D12 | Harness 七模块主页 hero | 替换现有 OverviewPage hero |
| D13 | 命中率自进化可视化 + 端到端测试 | `<EvolutionChart>` |
| D14 | 录 demo 视频 + 蒸馏卡 + 部署 | 完整交付 |

**W2 验收**:面试官打开 demo,在 60 秒内能说出这 3 句话:
1. "这是 Harness 工程的可视化"(看到 Guides+Sensors 双控)
2. "这是真有记忆系统"(看到三库面板 + 衰减曲线)
3. "这能自进化"(看到命中率/漂移雷达图)

---

## 3. 与现有架构的兼容性

### 3.1 不动的(保持现状)
- 所有现有 workflow type(router/planner/supervisor/peer/single)
- 17 岗位 agents 表(只是 prompt 组装方式改)
- 5173 前端的视觉系统(Claude.ai 暖米白)
- LangGraph workflow 引擎核心

### 3.2 增强的(挂钩点)
- **`backend/app/workflows/one_person_company/workflow.py`** — 在每个 worker 节点前后挂 hook
  - **Pre-hook**:Guides 检查 + Memory recall 注入
  - **Post-hook**:Sensors 度量 + 写入三库
- **`backend/app/runtime.py`** — `run_agent()` 接受新参数 `harness_context`
- **`frontend/src/pages/PlaygroundPage.vue`** — 加 Harness 双控台侧栏

### 3.3 新增的(纯加法)
- `backend/app/harness/`(新模块)
  - `schemas.py` · Pydantic models
  - `store.py` · 三库 CRUD + 衰减/召回算法
  - `engine.py` · 评分 + Sensors
  - `prompts.py` · 三层 prompt 组装器
  - `routes.py` · `/api/harness/*` 全部端点
- `backend/scripts/harness_migration.sql` · DB 增表脚本
- `frontend/src/components/harness/`(新目录)
  - `GuidesPanel.vue`
  - `SensorsPanel.vue`
  - `MemoryDashboard.vue`
  - `DriftRadar.vue`
  - `SevenModuleDashboard.vue`
  - `EvolutionChart.vue`

**全部是叠加,不破坏现有功能。每一步可 git revert。**

---

## 4. 风险清单(透明告知)

| 风险 | 概率 | 影响 | 对冲 |
|---|---|---|---|
| 14 天做不完 | 中 | 高 | 严格按 P0/P1 优先级,W2 末砍 P1 |
| 召回算法调不出效果 | 低 | 中 | 简单 BM25 + 重要性加权打底 · 不上向量库 |
| Persona Drift 误报多 | 中 | 低 | 阈值可调 · 默认放宽 |
| LangGraph hook 影响现有 workflow | 低 | 高 | 单独跑 one_person_company 测试 · 不动其他 5 种 |
| 前端组件影响整站性能 | 低 | 中 | 懒加载 + 虚拟滚动 |

---

## 5. 关键节点 ping CEO

只在以下 4 个时刻 ping(不每天打扰):

1. **D2 末** · "三库 schema + API 完成,跑通了写入" · 5 分钟看效果
2. **W1 末**(D7) · "Week 1 后端全部完成,跑一遍 workflow 看记忆累积" · 15 分钟看 demo
3. **D9 末** · "前端双控台主组件完成,可以点开看 Guides/Sensors" · 5 分钟看视觉
4. **D14 末** · "全部完成,录视频前最后确认" · 验收

---

## 6. 验收标准(最终交付)

### 6.1 业务深度
- ✓ 三库记忆全部能跑(事件/认知/关系)
- ✓ 重要性评分实时显示
- ✓ 召回 top-5 直接显示在下一棒 worker 的输入区
- ✓ Persona Drift 检测有真实数据(跑 ≥ 5 次 workflow)
- ✓ Sensors 自进化能演示(故意制造漂移看系统自动调整)

### 6.2 视觉品质
- ✓ Guides+Sensors 双控台 UI 美观,Claude.ai 调性统一
- ✓ 衰减曲线动画流畅
- ✓ Drift 雷达图美观
- ✓ 移动端可看(虽然不是主要场景)

### 6.3 面试故事
- ✓ 30 秒能讲清楚"这是 Harness 工程可视化"
- ✓ 演示流程 ≤ 5 分钟
- ✓ 有 1 个"卧槽时刻"(预定:Persona Drift 自动纠正)

---

## 7. 一句话使命

**让任何看到这个 demo 的 AI PM/工程师/面试官,在 30 秒内说出**:

> "这不是又一个 multi-agent 玩具,这是把 Harness Engineering 真正工程化的产品。"

---

**版本**: v1.0
**创建**: 2026-05-05
**下次迭代**: D2 末(三库 schema 完成时)
**负责**: AI 自跑,CEO 在 4 个关键节点确认
