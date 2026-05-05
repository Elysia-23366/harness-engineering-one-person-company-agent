"""
一人公司架构 v1.8.0 · workflow prompts
基于:00_章程/项目入口SOP.md + 03_协作规则/_handoff矩阵.md + R07 CKO 四型蒸馏 SOP
"""
from __future__ import annotations

from ...schemas import AgentDefinition


def build_triage_prompt(user_input: str, agents: list[AgentDefinition]) -> str:
    """R07 CKO 分诊员视角 · 项目入口 SOP 第 1-3 步:
    定档位 + 排涉及岗位 + 出 handoff 链路 + 给"分诊提案"。"""
    roster = "\n".join(
        f"  - {a.name} · {a.description}"
        for a in agents
    )
    return f"""你现在以"R07 首席知识官 CKO · 项目分诊员"身份工作。
你的责任来自《00_章程/项目入口SOP.md》第 1-3 步:**分诊提案是 AI 的本职工作,不是反问推给 CEO**。

CEO 投喂的需求:
"\"\"
{user_input}
\"\"

本项目可调用的岗位团队:
{roster}

请按以下 4 步**自动**完成分诊,出一份给 CEO 看的提案(120-200 字):

1. **判档位**(从用户输入抽时间):
   - < 2 小时 → ⚡ 闪电档(跳过设计/客研/商业闸,直出 mini-PRD + 代码)
   - 2 小时 ~ 3 天 → 🚀 标准档(完整 7 步,商业闸压缩)
   - > 3 天 → 🏆 精品档(全岗位 + 全闸 + 全 reviewer)
   - 用户没说时间默认标准档,并提示"按标准档跑,要换档告诉我"
2. **判项目类型**(APP / Web 网站 / AI Agent / 公众号文章 / 分析报告 / PPT / 课程 / 品牌设计 等)
3. **挑岗位 + 排链路**:从可调用岗位里挑出本项目需要的子集,按 handoff 顺序串起来(用 → 连接)
4. **给 CEO 一句话提案**:档位 + 周期 + 岗位链 + 关键闸,等 CEO 点头开跑

**输出格式**(严格按此结构,Markdown):
```
## 分诊提案

**档位**: ⚡/🚀/🏆 + 名字 + 预估周期
**项目类型**: XX 类
**协作链**: 岗位 → 岗位 → 岗位
**关键闸**: 闸 1 PRD / 闸 2 设计 / 闸 3 代码 / 闸 4 上线前(按需选)
**分诊推理**: 一句话说明为什么这样选

CEO 点头我就开跑 →
```
不要客套,不要解释什么是分诊,直接出提案。"""


def build_worker_prompt(
    user_input: str,
    triage_proposal: str,
    prior_outputs: list[tuple[str, str]],
    current_agent: AgentDefinition,
    step_index: int,
    total_steps: int,
) -> str:
    """每个 worker 接力时的 prompt · 带上下文(原需求 + 分诊 + 前序产出)。"""
    prior_block = "\n\n".join(
        f"### 前序 · {name} 的产出\n{out}"
        for name, out in prior_outputs
    ) if prior_outputs else "(你是流水线第一棒,无前序产出)"

    return f"""# 流水线第 {step_index}/{total_steps} 棒 · {current_agent.name}

## CEO 原始需求
{user_input}

## 本项目分诊提案(由 R07 CKO 已定)
{triage_proposal}

## 前序岗位的交付物
{prior_block}

## 你的任务

按你岗位说明里的职责和方法论,**直接产出**本棒交付物。

要求:
1. 第一句话:用第一人称简述"我会怎么做、为什么这么做"(2-3 句)
2. 然后**直接产出具体内容**(交付物清单 / 文档 / 代码 / 方案 — 看你的岗位职责是什么)
3. 不要只给方向,要给得**下一棒能直接接着干**的程度
4. 末尾用 1 句话说"我交给下一棒的关键交付物是 XX"

不要客套,不要解释一人公司架构是什么。直接干。"""


def build_distillation_prompt(
    user_input: str,
    triage_proposal: str,
    all_outputs: list[tuple[str, str]],
) -> str:
    """R07 CKO 四型项目闭环蒸馏 · 五路径回写 prompt。"""
    timeline = "\n\n".join(
        f"### {i+1}. {name}\n{out[:600]}{' …' if len(out) > 600 else ''}"
        for i, (name, out) in enumerate(all_outputs)
    )
    return f"""你是 R07 首席知识官 CKO,执行《档案部/CKO/SOP_四型_项目闭环蒸馏.md》。
本项目刚交付完毕。请按四型闭环蒸馏 + 五路径回写,出一张蒸馏卡。

## CEO 原始需求
{user_input}

## 项目分诊
{triage_proposal}

## 项目执行全过程
{timeline}

## 你要产出的蒸馏卡(严格按此结构,Markdown)

```markdown
## 📚 CKO 四型蒸馏卡 · 项目闭环

### 一句话总结
(用 1 句话说本项目交付了什么、效果如何)

### 这次最值得复用的方法论
(1-3 条 · 每条都说明"在哪种类似场景可复用",必须能跨项目)

### 关键设计取舍
| 取舍 | 决策 | 何时复用 / 反向 |
|---|---|---|
| ... | ... | ... |
(2-4 行)

### 五路径回写(铁律 1 成熟度闸:1次观察/2次草案/3次规则)
- **A 岗位方法论**: (改哪个岗位的 SOP / 草稿区 · 标注 maturity_gate)
- **B 公司脑库**: (登记到 04_公司记忆/项目类型_记忆/XX 类/ 哪条)
- **C 模板升级**: (改哪份模板 · 标注 maturity_gate)
- **D 失败案例**: (有失败信号则登记 04_公司记忆/失败案例/,无则写"无")
- **E 历史作品**: (归档到哪个岗位的 历史作品/)

### 面试/客户可讲点
(给 CEO 提取 1 条这个项目最值得拿出去讲的故事 · 100 字内)
```

不要堆术语,要让 CEO 看到价值。每条都要带具体动作建议,不要只说概念。"""


def build_fallback_response(workflow_name: str, last_output: str) -> str:
    """无 LLM 时的兜底:把最后一棒的产出直接当最终结果。"""
    return f"[一人公司协作流 · {workflow_name}]\n\n最终交付:\n\n{last_output}"
