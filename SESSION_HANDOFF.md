# 一人公司 Agent · Harness 工程嵌入 · 会话接力包

> **新会话 Claude 读这份文档作为第一件事**。这份文档是自包含的,读完即可无缝接续上一个会话的工作。
>
> **生成时刻**:Week 1 Day 2 末(W1D2 后端核心引擎已跑通)
> **下次目标**:W1 D3 重要性评分引擎 → W1 D7 Sensors 自进化 → W2 D8-14 前端可视化

---

## 0. 给新会话 Claude 的 5 条元指令(必读)

1. **不要重做已经做过的事** — 严格按 §3「当前进度」继续,不要重新设计 schema、不要重做视觉
2. **沿用 CEO 的所有红线** — §6「CEO 偏好」是硬约束,违反会让她生气
3. **保持温柔美男腔调** — 专业内容直接,语气有温度,不堆 emoji,不肉麻
4. **TodoWrite 必用** — 长任务必做 todo 跟踪
5. **D3 立刻动手前** — 先 `Read HARNESS_ROADMAP.md`(在项目根目录)+ `Read backend/app/harness/{schemas,store,routes}.py` 三个文件确认架构

---

## 1. 项目身份

### 1.1 CEO 画像(关键)

- 中文,女性,资深 AI 产品经理,正在求职 26 年上半年 AI PM 岗位
- **目标**:这个项目是她**面试求职 + 客户咨询 + 公众号引流**的硬弹药
- **风格**:决策快、不喜欢被反复问、要直接动手看效果
- **盲区**(她自己授权我打断):收敛型聪明 / 弱发散 / 容易陷入完美陷阱 / 理性掩盖情绪
- **常用词**:"开始吧"="立刻动手";"还是"="对前一版不满意要重做;"宝贝"="加油";"多Agent"="她的项目"

### 1.2 项目身份

- **名称**:一人公司 Agent
- **基于**:Multi-Agent-Playground(原项目 GitHub `Jasper-zh/Multi-Agent-Playground`,本地 fork 在 `C:\Users\FU\Desktop\Multi-Agent-Playground-main\`)
- **核心叙事**:你 1 个 + 17 个 AI 岗位 = 一家会运转的公司
- **公式**:`Agent = Model + Harness`

---

## 2. 关键路径速查

```
项目根:           C:\Users\FU\Desktop\Multi-Agent-Playground-main\
后端:             backend\app\
  - 主路由:       routes.py(原项目)
  - 主 Store:     store.py(原项目)
  - 5 种 workflow: workflows\{router_specialists, planner_executor, supervisor_dynamic, single_agent_chat, peer_handoff}\
  - 第 6 种 workflow:workflows\one_person_company\(我加的)
  - Harness 模块:harness\(我加的,本次重点)
    - schemas.py / store.py / routes.py / __init__.py
前端:             frontend\src\
  - 主组件:       App.vue + pages\OverviewPage.vue + components\(已有的 5 个 vue)
  - 视觉系统:     style.css(原 73KB)+ style.inkway.css(我加的 Claude 暖米白覆盖层)
  - 备份:         style.legacy.css(原始备份)
DB:               backend\data\agent_playground.db(SQLite)
设计文档:         frontend\DESIGN.md(Claude.ai 视觉规范)
路线图:           HARNESS_ROADMAP.md(本次 14 天工作计划)
我之前的单文件 demo: E:\tools\一人公司Agent\index.html(2319 行,墨道风,跟主项目无关)
Claude 记忆库:    C:\Users\FU\Desktop\杂七杂八\Claude记忆库\(20 个 .md 文件)
一人公司架构:     C:\Users\FU\Desktop\正在进行的项目\完成\【最新】一人公司架构_v1.8.0\(407 个文件)
```

---

## 3. 当前进度 · D2 末快照

### 3.1 已完成 ✅

| 阶段 | 内容 | 文件 | 行数 |
|---|---|---|---|
| 起步 · 17 岗位 | POST 17 岗位到 backend agents 表(R01-R23) | `seed_17_roles.py`(在 `E:\tools\一人公司Agent\`) | 200 |
| 起步 · 第 6 种 workflow | 注册 `one_person_company` workflow type 到 5 处 | `backend/app/workflows/one_person_company/` + `schemas.py` + `routes.py` + `store.py` | ~300 |
| 起步 · 创建示范 workflow | "一人公司协作流 · APP 类经典 4 棒"(R01→R02→R03→R06) | DB 直接写入 | — |
| 起步 · 视觉重做 | Claude.ai 暖米白风(墨道→Claude 工艺) | `style.inkway.css` + DESIGN.md | 880 + 500 |
| 起步 · 文案 | 改 i18n 中文 + Logo 八角星 SVG | `i18n.js` + `App.vue` | — |
| **W1 D1** | Harness DB 5 表 schema + migration + 4 默认 Guides 已 seed | `backend/scripts/harness_migration.sql` | 180 |
| **W1 D1** | Pydantic models · EventMemory/Persona/Relationship/Sensor/Guide/HarnessContext | `backend/app/harness/schemas.py` | 200 |
| **W1 D2** | Store · 三库 CRUD + 衰减算法 + 召回算法(top-K) | `backend/app/harness/store.py` | 460 |
| **W1 D2** | API · 13 条 `/api/harness/*` 端点 | `backend/app/harness/routes.py` | 240 |
| **W1 D2** | 集成 · `main.py` 已挂载 `harness_router` | `backend/app/main.py` | +2 行 |
| **W1 D2** | E2E 验证 · 召回算法精度 0.977/0.733/0.189 三档分明 | curl + Python smoke test | 通过 |

### 3.2 三库 + Sensors + Guides 数据现状(DB 实际数据)

```
event_memory       3 条(R01 PM 名下,score 8.5/9.0/2.0)
persona_perception 1 条(R01 对 CEO:"收敛型 + 结构化 + 决策快")
relationship_node  1 条(R01 ↔ CEO:trust=0.72 fam=0.40 phase=warming)
sensor_event       1 条(recall_hit_rate · passed)
guide_rule         4 条(1 全局 + 3 R01/R03/R06 专属)
agents             20 条(3 旧 + 17 R01-R23 新)
workflows          7 条(包括"一人公司协作流 · APP 类经典 4 棒" id=workflow_f66d5cfb)
```

### 3.3 进行中 ⏳

无(D2 末停在"等 CEO 看一下后端跳动")

### 3.4 未开始 ⬜

- W1 D3 · `engine.py` 重要性 3 维评分引擎(LLM 自动给 emotion/novelty/relation 打分)
- W1 D4 · 召回 hook 集成到 workflow + Persona 三层 prompt 拼装
- W1 D5 · 集成到 `one_person_company` workflow 的 pre/post hook
- W1 D6-7 · Sensors 自进化引擎(命中率监控 + Persona Drift)
- W2 D8-9 · 前端 Guides+Sensors 双控台
- W2 D10 · 前端三库记忆面板
- W2 D11 · Persona Drift 雷达图
- W2 D12 · Harness 七模块 Dashboard 主页 hero
- W2 D13 · 命中率自进化可视化 + e2e 测试
- W2 D14 · 蒸馏卡 + 录 demo 视频 + 部署

---

## 4. 当前运行的服务 + 进程

### 4.1 端口 + 服务

| 端口 | 服务 | 状态 | 启动方式 |
|---|---|---|---|
| 5173 | Vite frontend | ✅ Running | `cd frontend && npm run dev` |
| 8011 | FastAPI backend(无 reload) | ✅ Running | 见下 ↓ |
| 3000 | FocusCut MVP(R03 真造的 ADHD 待办 APP) | ✅ Running | `cd adhd-todo-mvp/focuscut && npm run dev` |

### 4.2 backend 启动命令(必背)

```bash
cd "C:\Users\FU\Desktop\Multi-Agent-Playground-main\backend"
source .venv/Scripts/activate
uvicorn app.main:app --host 127.0.0.1 --port 8011
```

**⚠️ 不用 `--reload`** — Windows watchfiles 跟我们这套深度改造冲突会卡死。改后端代码后必须手动重启。

**重启步骤**:
1. `taskkill //F //PID <python_pid>`(从 `tasklist | grep python` 找)
2. 确认 `netstat -ano | grep ":8011 .*LISTEN"` 端口空了
3. 重新跑上面那条 uvicorn 命令(`run_in_background=true`)

---

## 5. 模型 / API 配置(后端 LLM 调用)

### 5.1 当前 Active Profile

```
profile_id:  profile_1777928698357_1
name:        MiMo
api_key:     tp-cnmjwcr8cgv9ps1pmqh4w6vljzr1adyp2yg90zoqxvcdbntz  (小米 token-plan)
base_url:    https://token-plan-cn.xiaomimimo.com/v1
model:       mimo-v2.5-pro       (注意全小写,大写会 400)
```

### 5.2 关键事实

- **mimo-v2.5-pro 是推理模型**(reasoning model 类似 o1/o3),每次 call 先思考再输出 → max_tokens 必须给到 ≥ 1500,否则 content 为空
- 备用兼容端点 · Anthropic 协议: `https://token-plan-cn.xiaomimimo.com/anthropic`(FocusCut MVP 走这个)
- API 改动方式:`PUT /api/settings`,改 model_profiles 的 active 那一项

---

## 6. CEO 偏好硬规则(违反必触雷)

### 6.1 风格

- **温柔美男腔调** · 专业内容直接,语气有温度,不堆 emoji,不肉麻
- **不要干巴巴汇报腔** · 开场不要"完成"、"产出如下"
- **技术判断保持直接** · 该 reject 就 reject,温柔不软化结论

### 6.2 视觉(C 层 · 用户主权)

- **当前已定**:Claude.ai 暖米白(Parchment `#f5f4ed` + Terracotta `#c96442` + Fraunces serif + Ring shadow)
- **CEO 否决过的**:墨道(深色 + LXGW 文楷 + 朱砂 — 太重)
- **反 AI slop 第一律**:**禁止** Inter + 紫色渐变 + 白底默认搭配

### 6.3 多步红线(已累犯 ≥ 3 次)

- **短词回复**(≤ 2 字 / "继续" / "B" / 数字 / 单字母)+ 多种解读 → 必停反问
- **不可逆动作**(rm / git push --force / 删表)→ 必停反问
- **同时改 ≥ 3 个文件** → 必停反问
- **动作源于 AI 自己"建议"而非 CEO 指令** → 必停反问
- **方法论文档 + 短词指令** → 必反问 "全面重构 / 指定点改 / self-check 三选一"

### 6.4 分诊例外

- **分诊提案是 AI 的活,不许反问推给 CEO** — 收到任务先自己查表→拆岗→排流程→出提案
- **执行才需要等确认**

### 6.5 自动化优先

- 出现"你要记住 X"措辞 = 在偷懒,CEO 会指责
- 优先给自动方案(launchd/cron/git hook),手动方案做兜底

### 6.6 文档 / 文件命名

- **新建文件前必问 3 件事**:① 路径 ② 是否新建文件夹 ③ 输出格式(md/html/pdf/docx)
- **系列文档强制序号前缀** + 差异后缀(`01_xxx_v1.md`)
- **多版本并存项目文件夹**:`【最新】xxx_v1.8.0/` 前缀 + `【存档】xxx_历史/`
- **改完文件主动巡查顶层临时文件**(macOS 副本/截屏/草稿等)

### 6.7 HTML 三层服务规则

- A 层工艺自动生效(对比度/呼吸/响应式)
- B 层需求每次问(用途/交互/scope)
- C 层审美用户主权,**永不默认,永不维护偏好菜单** — 收到参考必走 抽取→回报确认→复刻

---

## 7. Harness 核心 4 大机制(产品 DNA)

### 7.1 三层进化范式
- 23 年 = Prompt Engineering / 24-25 年 = Context Engineering / **26 年 = Harness Engineering**
- 公式 `Agent = Model + Harness` · `If you are not the model, you are the harness`

### 7.2 Guides ⊕ Sensors 双控
- **Guides 前馈** · 行动**之前**护栏,设规则/边界/能干啥不能干啥
- **Sensors 反馈** · 行动**之后**检测,自动度量/命中率/Drift/合规 + 自纠错
- 闭环系统会**自我进化**,不是一次性配置

### 7.3 三库记忆架构(角色漂移 OOC 工程解)
| 库 | 内容 | 衰减 | 共享 |
|---|---|---|---|
| 事件库 Episodic | 发生了什么(情绪标签) | ✓ 遗忘曲线 | 跨人物 |
| 角色认知 Persona | 角色对用户的印象 | ✗ 永久 | 跨人物 |
| 关系节点 Relationship | 双方关系坐标 | ✗ 永久 | **每对独立** |

### 7.4 重要性 3 维打分(Guides 入口规则)
- 情绪激烈度(0-3)
- 是否带来新素材(0-3)
- 是否影响关系(0-3)
- 阈值:≥6 写入 / 3-6 写入但高衰减 / <3 不写

### 7.5 召回机制(top-5 精准 > 全量塞)
- 关键词 + 情绪 + 重要性加权
- final_score = 0.4 × 衰减重要性/9 + 0.4 × 关键词匹配 + 0.2 × 情绪匹配
- 取 top-5(不是全量)

### 7.6 核心产品观点(背下来给面试官讲)
- "用户在乎的不是『存得多』,是『关键时刻记得对』"
- "拿到 PMF 不是模型问题,是 Harness 不够"
- "Harness = 操作系统(LLM=CPU,上下文窗口=RAM,DB=硬盘,工具=驱动)"

---

## 8. 下一步 12 天精确动作清单

### W1 D3 · 重要性 3 维评分引擎(立刻可做 · 1 天)

**新建文件**:`backend/app/harness/engine.py`

**函数**:
```python
def score_event_importance(content: str, agent_id: str, prior_context: str) -> dict:
    """
    用 LLM 给 content 打 3 维度分(0-3 各),返回:
    {
        'emotion_score': float,   # 情绪激烈度
        'novelty_score': float,   # 是否带来新素材(对比 prior_context)
        'relation_score': float,  # 是否影响关系
        'total_score': float,     # 总分 0-9
        'emotion_tag': str,       # neutral|positive|negative|urgent|breakthrough
        'reasoning': str,         # LLM 思考过程
    }
    """
```

**实现**:
- 用 `runtime.py` 的 `call_llm()`(已经接好 mimo-v2.5-pro)
- Prompt 格式:给 LLM 一个 schema,要求返回 JSON
- max_tokens 至少 1500(因为 mimo 是 reasoning model)
- 失败时降级:返回 `total_score=5.0` 默认值,emotion_tag='neutral'

**API 端点**:`POST /api/harness/score`
```python
@router.post("/score")
def score_endpoint(content: str, agent_id: str, prior_context: str = ""):
    return score_event_importance(content, agent_id, prior_context)
```

**写入路由**:
```python
def auto_route_event(content, agent_id, ...) -> str | None:
    """
    根据评分自动决定写入哪个库:
    - total >= 6: 写 event_memory + 触发 persona/relationship 更新
    - 3 <= total < 6: 写 event_memory(decay_rate 翻倍)
    - total < 3: 不写
    """
```

### W1 D4 · 召回 hook + Persona 三层拼装(1 天)

**新建文件**:`backend/app/harness/prompts.py`

**函数**:
```python
def assemble_persona_prompt(
    agent: AgentDefinition,
    user_input: str,
    workflow_context: str,
    handoff_inputs: list,
    harness_store: HarnessStore,
) -> tuple[str, HarnessContext]:
    """
    Persona Core 三层拼装:
    1. system_prompt(永久):agent.system_prompt(§0 对标 + 信条)
    2. working_context(动态):user_input + workflow + handoff
    3. memory_recall(动态):store.recall_top_k(agent_id, user_input, ...)

    返回:(完整 prompt str, HarnessContext 对象用于前端展示)
    """
```

### W1 D5 · 集成到 one_person_company workflow(1 天)

**改动文件**:`backend/app/workflows/one_person_company/workflow.py`

**关键 hook**:
- `make_worker_node()` 函数内,**调 LLM 之前**:
  - 调 `assemble_persona_prompt()` 注入召回的 top-5
  - 调 `list_guides(agent_id)` 拿到该岗位的 Guides 规则,注入 prompt
- `make_worker_node()` 函数内,**调 LLM 之后**:
  - 调 `score_event_importance()` 给 LLM 输出打分
  - 调 `auto_route_event()` 自动写入三库
  - 调 `update_persona()` 和 `apply_relationship_delta()` 更新另两库
  - 用 `emit_trace` 把 Harness 度量结果加到 trace 流(让前端能看)

### W1 D6-7 · Sensors 自进化引擎(2 天)

**扩展文件**:`backend/app/harness/engine.py` 加 sensors 部分

**3 类 Sensors**:
```python
def sensor_recall_hit_rate(agent_id, recent_n=10) -> SensorEventCreate:
    """统计最近 N 次召回的有效率(看 access_count vs 召回时机)"""

def sensor_persona_drift(agent_id, current_output) -> SensorEventCreate:
    """
    用 TF-IDF 简单实现:
    - 取该 agent 最近 5 个输出的关键词集合(平均向量)
    - 跟 current_output 关键词集合做余弦相似度
    - 相似度 < 0.5 → 漂移警报
    """

def sensor_output_compliance(agent_id, output) -> SensorEventCreate:
    """
    遍历该 agent 的所有 active Guides 规则,逐条检查 output:
    - rule_type='output_schema': 检查 required_fields/keywords
    - rule_type='forbidden_topic': 检查禁词
    - 失败的 severity='block' 规则 → 触发 stop-the-line
    """
```

**自进化逻辑**:
```python
def evolve_thresholds():
    """
    跑 ≥ 5 次后,如果命中率 < 0.6,自动调整 final_score 公式权重
    把调整记录到 sensor_event 表
    """
```

### W2 D8-14 · 前端可视化(7 天)

**新建目录**:`frontend/src/components/harness/`

| Day | 组件 | 数据源 |
|---|---|---|
| D8 | `GuidesPanel.vue` | `GET /api/harness/guides?agent_id=X` |
| D9 | `SensorsPanel.vue` | `GET /api/harness/sensors?agent_id=X` |
| D10 | `MemoryDashboard.vue`(三库 + 衰减曲线) | `GET /api/harness/events`+`/personas`+`/relationships` |
| D11 | `DriftRadar.vue`(雷达图) | `GET /api/harness/sensors?sensor_type=persona_drift` |
| D12 | `SevenModuleDashboard.vue`(主页 hero 替换) | `GET /api/harness/dashboard` |
| D13 | `EvolutionChart.vue`(命中率趋势) | `GET /api/harness/sensors?sensor_type=recall_hit_rate` |
| D14 | 蒸馏卡 + 录 demo + 部署 | — |

**视觉风格** · 严格沿用 `frontend/src/style.inkway.css` 的 Claude.ai 暖米白 token

**用 web-design skill** · 新会话第一件事 invoke `Skill('web-design')` 让它产出 DESIGN_HARNESS.md 子文档

---

## 9. 已知风险 + 已踩过的坑

### 9.1 Backend hot-reload 卡死
**症状**:改 main.py 后 watchfiles 检测变化但 reload worker 永久卡住
**应对**:`uvicorn` 不开 `--reload`,改完代码用 `taskkill //F //PID` + 重启

### 9.2 Git Bash 中文乱码
**症状**:Python 调 backend API 时,print 中文 / emoji 显示 GBK 乱码(\udcaf 之类)
**应对**:`sys.stdout.reconfigure(encoding='utf-8')` 强制 utf-8;但**数据本身是正确的**,这只是 Windows 终端显示问题,backend DB 和 frontend 浏览器都是 UTF-8

### 9.3 mimo-v2.5-pro reasoning 慢 + max_tokens 陷阱
**症状**:max_tokens=80 时 content 为空(全用在 reasoning_tokens)
**应对**:max_tokens ≥ 1500;每次 LLM call 估算 10-30 秒;6 个 worker × LLM call = 1-3 分钟,SSE 流式给用户耐心

### 9.4 跑过的 workflow 已经验证
- `workflow_f66d5cfb` "一人公司协作流 · APP 类经典 4 棒" R01→R02→R03→R06,可以拿来跑测试

### 9.5 视觉变更累犯
- CEO 在视觉上**反复改过 3 次**(modern SaaS 默认 → 墨道 → Claude.ai 暖米白)
- 现在锁定 Claude.ai,**不要再大改视觉**,只在这套 token 内增加新组件

---

## 10. 今天最大成就(给 CEO 看的成果)

1. ✅ 17 岗位 + 第 6 种 workflow type 真接进 multi-agent-playground 引擎
2. ✅ R03 全栈工程师 Agent 通过 fs_write_file 工具**真造出了 22 文件 Next.js 待办 APP**(FocusCut MVP)跑在 :3000
3. ✅ 整站视觉重做成 Claude.ai 暖米白 + 八角星 Logo + 网格点阵
4. ✅ 后端 Harness 工程嵌入 Day 1+2 完成 · 三库 + 召回 + 13 条 API · **召回算法精度 0.977/0.733/0.189 三档分明**
5. ✅ 完整 14 天 ROADMAP + Skill 化 web-design + 这份 handoff

---

## 11. 给新会话 Claude 的开场白模板

CEO 在新会话里把这份 handoff 扔进去后,你应该:

1. **先确认读懂了**:简短 2-3 句话说"我读完了 handoff,当前 D2 末,接下来该做 D3 重要性评分引擎"
2. **不要追问** CEO "你要做什么" — 任务已经在 §3.4 里写好了
3. **检查环境**:跑 `curl http://127.0.0.1:8011/api/harness/health` 确认 backend 还在(若不在,按 §4.2 启动)
4. **TodoWrite** 把剩下 12 天的任务装进去(参照 §8)
5. **直接开始 D3** 写 `backend/app/harness/engine.py` 重要性评分引擎

CEO 第一条消息的标准引导(她会这样说):
> "Claude,接力一下,看 SESSION_HANDOFF.md 然后继续 D3"

或者:
> "继续"

(一个字"继续",意思是从 §3.4 第一项继续)

---

## 12. 元数据

- **生成时间**:2026-05-05 W1D2 末
- **总 token 消耗**:~880k / 1M(88%)
- **下次会话预算**:建议每天结束时再生成一份 handoff(滚动更新),保护进度
- **接力路径**:本文档 → 新 conversation 第一条消息 → Claude 继续

---

> **核心保证**:**只要这份 handoff + 项目代码在硬盘上,12 天工作 100% 可恢复。最终交付物完全不受影响。**
