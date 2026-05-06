"""
Harness Prompts · Persona Core 三层 prompt 拼装器

W1 D4 · 灵感:Persona Core 三层分离

三层逻辑:
  Layer 1 · system_prompt    永久人格   · agent.system_prompt(§0 对标 + 信条)
                                          + persona_perception 累积印象
                                          + relationship 关系坐标
                                          + active guides 规则
  Layer 2 · working_context  动态任务   · workflow_context + handoff_inputs
  Layer 3 · memory_recall    动态记忆   · top-K 召回(关键词 + 情绪 + 衰减加权)
                                          + 实际 user_input

输出:
  - 标准 OpenAI messages 数组(system + user)
  - 单字符串拼接版(call_llm 兼容)
  - HarnessContext 对象(给前端 trace 可视化)
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..store import store as main_store
from .schemas import (
    EmotionTag,
    EventMemoryRecallScore,
    GuideRule,
    HarnessContext,
    PersonaPerception,
    RelationshipNode,
)
from .store import HarnessStore, get_harness_store

# ============================================================
# Output schema
# ============================================================
class PromptAssemblyResult(BaseModel):
    """三层拼装结果 · 给 workflow 跑 LLM + 前端 trace 同时使用。"""
    system_prompt: str
    user_prompt: str
    full_prompt: str  # system + "\n\n" + user · 给 call_llm 单字符串接口
    messages: list[dict[str, str]]
    harness_context: HarnessContext

# ============================================================
# 主入口 · assemble_persona_prompt
# ============================================================
def assemble_persona_prompt(
    agent_id: str,
    user_input: str,
    workflow_context: str = "",
    handoff_inputs: Optional[list[dict[str, str]]] = None,
    user_id: str = "ceo",
    current_emotion: EmotionTag = "neutral",
    recall_limit: int = 5,
    harness_store: Optional[HarnessStore] = None,
) -> PromptAssemblyResult:
    """
    Persona Core 三层拼装 · 同款 system / working / memory 分离。

    Args:
        agent_id: 必填,要拼哪个岗位的 prompt
        user_input: 当前用户/上游输入
        workflow_context: workflow 的描述 + 当前阶段说明
        handoff_inputs: 上一棒输出列表,元素形如 {"agent_name": "R02", "output": "..."}
        user_id: 默认 "ceo"
        current_emotion: 当前对话情绪,影响召回排序
        recall_limit: top-K 召回条数(默认 5)
        harness_store: 测试时可注入,默认全局单例

    Returns:
        PromptAssemblyResult · system/user/full/messages + HarnessContext

    Raises:
        ValueError: agent 不存在
    """
    agent = main_store.get_agent(agent_id)
    if agent is None:
        raise ValueError(f"Agent not found: {agent_id}")

    h_store = harness_store or get_harness_store()

    # ---- Layer 1 · Persona Core(永久)----
    persona_core = (agent.system_prompt or "").strip() or "(no system_prompt)"
    persona = h_store.get_persona(agent_id, user_id)
    relationship = h_store.get_relationship(agent_id, user_id)
    guides = h_store.list_guides(agent_id=agent_id, active_only=True)

    # ---- Layer 3 · Memory Recall(动态)----
    if user_input.strip():
        recalled = h_store.recall_top_k(
            agent_id=agent_id,
            query_text=user_input,
            current_emotion=current_emotion,
            user_id=user_id,
            limit=recall_limit,
        )
    else:
        recalled = []

    # ---- 组装 system_prompt(Layer 1 + 累积印象 + 关系 + Guides)----
    system_parts: list[str] = [persona_core]

    if persona and (persona.perception_summary or persona.trait_keywords):
        system_parts.append(_format_persona_block(persona))

    if relationship:
        system_parts.append(_format_relationship_block(relationship))

    if guides:
        system_parts.append(_format_guides_block(guides))

    system_prompt = "\n\n".join(system_parts)

    # ---- 组装 user_prompt(Layer 2 + Layer 3 召回 + 实际 input)----
    handoffs = handoff_inputs or []
    user_parts: list[str] = []

    if workflow_context.strip():
        user_parts.append(f"—— 当前任务上下文 ——\n{workflow_context.strip()}")

    if handoffs:
        user_parts.append(_format_handoffs_block(handoffs))

    if recalled:
        user_parts.append(_format_recall_block(recalled))

    user_parts.append(f"—— 本次请求 ——\n{user_input.strip() or '(无)'}")

    user_prompt = "\n\n".join(user_parts)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    harness_context = HarnessContext(
        agent_id=agent_id,
        persona_core_prompt=persona_core,
        persona_perception=persona,
        user_input=user_input,
        workflow_context=workflow_context,
        handoff_inputs=handoffs,
        recalled_events=recalled,
        relationship=relationship,
        active_guides=guides,
    )

    return PromptAssemblyResult(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        full_prompt=full_prompt,
        messages=messages,
        harness_context=harness_context,
    )

# ============================================================
# Format helpers · 每段都用 "—— 段名 ——" 分隔,LLM 和前端都好读
# ============================================================
def _format_persona_block(p: PersonaPerception) -> str:
    lines = ["—— 你对 CEO 的累积认知(永久,不衰减)——"]
    if p.perception_summary:
        lines.append(f"印象: {p.perception_summary}")
    if p.trait_keywords:
        lines.append(f"画像: {', '.join(p.trait_keywords)}")
    lines.append(
        f"交互次数 {p.interaction_count} · 认知信度 {p.confidence_level:.2f}"
    )
    return "\n".join(lines)

def _format_relationship_block(r: RelationshipNode) -> str:
    return (
        "—— 你与 CEO 的关系坐标(永久,每对独立)——\n"
        f"信任 {r.trust_level:.2f} · 熟悉 {r.familiarity:.2f} · "
        f"对齐 {r.alignment_score:.2f} · 协作 {r.collaboration_count} 次 · "
        f"阶段 {r.current_phase}"
    )

def _format_guides_block(guides: list[GuideRule]) -> str:
    lines = ["—— Active Guides(前馈规则,必须遵守)——"]
    for i, g in enumerate(guides, 1):
        scope = "全局" if g.agent_id is None else "本岗位"
        content = g.rule_content if len(g.rule_content) <= 200 else g.rule_content[:200] + "…"
        lines.append(
            f"{i}. [{scope}|{g.rule_type}|{g.severity}] {g.rule_name}: {content}"
        )
    return "\n".join(lines)

def _format_recall_block(recalled: list[EventMemoryRecallScore]) -> str:
    lines = [f"—— 相关历史召回(top-{len(recalled)} · 关键词+情绪+衰减加权)——"]
    for i, s in enumerate(recalled, 1):
        e = s.event
        content_short = e.content if len(e.content) <= 200 else e.content[:200] + "…"
        lines.append(
            f"{i}. [imp={s.decayed_importance:.2f} | {e.emotion_tag} | "
            f"final={s.final_score:.3f}] {content_short}"
        )
    return "\n".join(lines)

def _format_handoffs_block(handoffs: list[dict[str, str]]) -> str:
    lines = ["—— 上一棒交接 ——"]
    for h in handoffs:
        name = h.get("agent_name") or h.get("from") or "(unknown)"
        out = h.get("output") or h.get("content") or ""
        out_short = out if len(out) <= 300 else out[:300] + "…"
        lines.append(f"- {name}: {out_short}")
    return "\n".join(lines)
