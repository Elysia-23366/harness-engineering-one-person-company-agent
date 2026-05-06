"""
Harness Engine · 重要性 3 维评分 + 写入路由

W1 D3 · 灵感:三维打分机制

核心思路:
  - 用 LLM 给一段 content 在 3 个维度各打 0-3 分(emotion / novelty / relation)
  - total_score = 三维之和(0-9)
  - 根据 total 自动路由:
      total >= 6      → 写 event_memory(低衰减 0.05)
      3 <= total < 6  → 写 event_memory(高衰减 0.10)
      total < 3       → 不写

设计原则:
  - LLM 失败时降级返回中等分,绝不抛错让上游 workflow 中断
  - JSON 解析容忍 markdown 包裹 / 前后多余文字
  - mimo-v2.5-pro 是 reasoning 模型,max_tokens 必须 ≥ 1500
"""
from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from typing import Optional

from pydantic import BaseModel, Field

from ..runtime import llm_gateway
from ..settings_bridge import settings
from .schemas import (
    EmotionTag,
    EventMemory,
    EventMemoryCreate,
    GuideCheckResult,
    GuideRule,
    PersonaPerceptionCreate,
    PersonaPerceptionUpdate,
    RelationshipNodeCreate,
    RelationshipNodeUpdate,
    SensorEvent,
    SensorEventCreate,
)
from .store import HarnessStore, get_harness_store

logger = logging.getLogger(__name__)

# ============================================================
# Output schema · 给 routes / workflow hook 用
# ============================================================
class ImportanceScore(BaseModel):
    """3 维度打分 + 情绪标签 + LLM 推理简述。"""
    emotion_score: float = Field(ge=0, le=3)
    novelty_score: float = Field(ge=0, le=3)
    relation_score: float = Field(ge=0, le=3)
    total_score: float = Field(ge=0, le=9)
    emotion_tag: EmotionTag = "neutral"
    reasoning: str = ""
    used_fallback: bool = False  # True = 走的兜底,没真调到 LLM

# ============================================================
# Prompt 模板(系统侧)
# ============================================================
_SYSTEM_PROMPT = """\
你是事件重要性评分助手,工作于「一人公司 Agent · Harness 引擎」。
任务:给一段刚刚发生的事件,从 3 个维度各打 0-3 分,并打一个情绪标签。

3 个维度(允许 0、0.5、1、1.5、2、2.5、3 半分粒度):
1. emotion_score · 情绪激烈度
   0=纯客观陈述 / 1=轻微情绪色彩 / 2=明显喜悦|紧张|不满 / 3=强烈情绪(突破性兴奋、严重危机)
2. novelty_score · 是否带来新素材(必须对比 prior_context 判断)
   0=完全重复已知 / 1=细节变体 / 2=有新信息 / 3=突破性新素材(改变方向、推翻假设)
3. relation_score · 是否影响 agent 与用户的关系
   0=无关系影响 / 1=正常协作 / 2=信任或熟悉度变化 / 3=关系坐标质变

emotion_tag(必须从下列 5 个里选一个):
- neutral       · 中性事实陈述
- positive      · 积极推进、协作顺畅、获得肯定
- negative      · 受挫、被否决、出错
- urgent        · 紧急、deadline、需立刻决断
- breakthrough  · 突破性进展、关键转折点

total_score = emotion_score + novelty_score + relation_score(范围 0-9)。

⚠ 严格以 JSON 返回,不要 markdown 代码块,不要任何解释性文字,不要 ```:
{
  "emotion_score": 数字,
  "novelty_score": 数字,
  "relation_score": 数字,
  "total_score": 数字,
  "emotion_tag": "neutral|positive|negative|urgent|breakthrough",
  "reasoning": "30 字以内的打分理由"
}
"""

# ============================================================
# Fallback · LLM 不可用时的默认评分
# ============================================================
def _fallback_score(reason: str = "LLM 不可用,默认中等评分") -> ImportanceScore:
    return ImportanceScore(
        emotion_score=2.0,
        novelty_score=2.0,
        relation_score=1.0,
        total_score=5.0,
        emotion_tag="neutral",
        reasoning=reason,
        used_fallback=True,
    )

# ============================================================
# 主入口 · score_event_importance
# ============================================================
def score_event_importance(
    content: str,
    agent_id: str,
    prior_context: str = "",
) -> ImportanceScore:
    """
    给一段事件打 3 维度分。

    Args:
        content: 待评分的事件内容
        agent_id: 哪个岗位产生的事件(供 LLM 参考语境)
        prior_context: 此前的对话/任务上下文,用于 novelty 维度对比

    Returns:
        ImportanceScore · 失败时降级为 total=5.0 / neutral / used_fallback=True
    """
    if not content or not content.strip():
        return _fallback_score("content 为空,默认评分")

    if llm_gateway.client is None or not llm_gateway.api_configured:
        logger.warning("[harness/engine] LLM 未配置,score 走 fallback")
        return _fallback_score()

    user_prompt = (
        f"agent_id: {agent_id}\n\n"
        f"prior_context (此前的对话/任务上下文):\n"
        f"{(prior_context or '(无)')[:1500]}\n\n"
        f"current_event (本次需评分的事件):\n"
        f"{content[:1500]}\n\n"
        "请按系统提示返回严格 JSON。"
    )

    try:
        response = llm_gateway.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=0,
            max_tokens=2000,  # mimo-v2.5-pro reasoning 模型必备
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[harness/engine] LLM call failed: %s", exc)
        return _fallback_score(f"LLM 调用异常: {type(exc).__name__}")

    raw = (response.choices[0].message.content or "").strip()
    parsed = _parse_score(raw)
    if parsed is None:
        logger.warning(
            "[harness/engine] 解析 LLM 输出失败,raw 前 200 字: %s",
            raw[:200],
        )
        return _fallback_score("LLM 输出无法解析为 JSON")
    return parsed

# ============================================================
# JSON 解析 · 容忍 markdown 包裹 / 前后多余文字
# ============================================================
def _parse_score(raw: str) -> Optional[ImportanceScore]:
    if not raw:
        return None

    text = raw.strip()

    # 剥 markdown 代码块(若有)
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 定位 {...} 区块(LLM 偶尔会前后多说话)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    json_str = text[start : end + 1]

    try:
        data = json.loads(json_str)
    except Exception:  # noqa: BLE001
        return None

    if not isinstance(data, dict):
        return None

    emotion = _clamp(data.get("emotion_score", 0), 0, 3)
    novelty = _clamp(data.get("novelty_score", 0), 0, 3)
    relation = _clamp(data.get("relation_score", 0), 0, 3)

    # total 校准:若 LLM 给的与三维之和偏差 > 1,以三维之和为准(防它算错)
    raw_total = data.get("total_score")
    summed = emotion + novelty + relation
    if raw_total is None:
        total = summed
    else:
        total = _clamp(raw_total, 0, 9)
        if abs(total - summed) > 1.0:
            total = summed

    tag = str(data.get("emotion_tag", "neutral")).strip().lower()
    if tag not in ("neutral", "positive", "negative", "urgent", "breakthrough"):
        tag = "neutral"

    reasoning = str(data.get("reasoning", ""))[:200]

    try:
        return ImportanceScore(
            emotion_score=emotion,
            novelty_score=novelty,
            relation_score=relation,
            total_score=total,
            emotion_tag=tag,  # type: ignore[arg-type]
            reasoning=reasoning,
            used_fallback=False,
        )
    except Exception:  # noqa: BLE001
        return None

def _clamp(v, lo: float, hi: float) -> float:
    try:
        f = float(v)
    except Exception:  # noqa: BLE001
        return lo
    return max(lo, min(hi, f))

# ============================================================
# 写入路由 · auto_route_event
# ============================================================
def auto_route_event(
    content: str,
    agent_id: str,
    workflow_id: str,
    conversation_id: Optional[str] = None,
    user_id: str = "ceo",
    prior_context: str = "",
    store: Optional[HarnessStore] = None,
) -> tuple[Optional[EventMemory], ImportanceScore]:
    """
    根据 3 维评分自动决定是否写入 event_memory + 用什么衰减率。

    原版阈值:
      - total >= 6      → 写入,decay_rate=0.05(慢忘)
      - 3 <= total < 6  → 写入,decay_rate=0.10(快忘)
      - total < 3       → 不写

    Args:
        content / agent_id / workflow_id 必填
        conversation_id / prior_context 可选
        store · 默认拿全局单例,测试时可传 mock

    Returns:
        (写入的 EventMemory 或 None, ImportanceScore)
    """
    score = score_event_importance(content, agent_id, prior_context)
    target_store = store or get_harness_store()

    if score.total_score < 3.0:
        return None, score

    decay_rate = 0.05 if score.total_score >= 6.0 else 0.10

    payload = EventMemoryCreate(
        workflow_id=workflow_id,
        conversation_id=conversation_id,
        agent_id=agent_id,
        user_id=user_id,
        content=content[:2000],
        emotion_tag=score.emotion_tag,
        importance_score=score.total_score,
        importance_emotion=score.emotion_score,
        importance_novelty=score.novelty_score,
        importance_relation=score.relation_score,
        decay_rate=decay_rate,
    )
    event = target_store.create_event(payload)
    return event, score

# ============================================================
# Workflow post-hook · 一键三库联动(W1 D5)
# ============================================================
# emotion_tag → (trust_delta, familiarity_delta) 映射
# 设计:positive/breakthrough 加信任,negative 减一点,中性只增熟悉度
_REL_DELTA_BY_EMOTION: dict[str, tuple[float, float]] = {
    "breakthrough": (0.03, 0.02),
    "positive":     (0.01, 0.02),
    "urgent":       (0.00, 0.02),
    "neutral":      (0.00, 0.01),
    "negative":     (-0.01, 0.01),
}

_PERSONA_CONFIDENCE_STEP = 0.02
_PERSONA_CONFIDENCE_CAP = 0.95

def post_hook_update_libraries(
    agent_id: str,
    output: str,
    workflow_id: str,
    conversation_id: Optional[str] = None,
    user_id: str = "ceo",
    prior_context: str = "",
    store: Optional[HarnessStore] = None,
) -> dict:
    """
    workflow worker 调 LLM 之后的统一 post-hook。

    一次调用做 4 件事:
      1. 评分 + auto_route 写入 event_memory(W1 D3 已有逻辑)
      2. Persona · 没有就建,有就 bump interaction_count + confidence
      3. Relationship · 没有就建,有就按 emotion_tag 加 trust/familiarity delta + 协作 +1
      4. 返回结构化结果给 trace 流(让前端能看)

    保证:任一步异常都不中断 workflow,异常以 result["errors"] 返回。

    Returns:
        {
          "score": ImportanceScore.model_dump(),
          "event_id": Optional[str],
          "wrote_event": bool,
          "trust_delta": float,
          "familiarity_delta": float,
          "collaboration_count": int,
          "trust_level": float,
          "current_phase": str,
          "errors": list[str],
        }
    """
    s = store or get_harness_store()
    errors: list[str] = []

    # ---- 1. 评分 + 路由 ----
    try:
        event, score = auto_route_event(
            content=output,
            agent_id=agent_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            user_id=user_id,
            prior_context=prior_context,
            store=s,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[harness/post_hook] auto_route_event 失败")
        errors.append(f"auto_route: {type(exc).__name__}")
        event = None
        score = _fallback_score("post_hook 异常")

    # ---- 2. Persona ----
    try:
        persona = s.get_persona(agent_id, user_id)
        if persona is None:
            s.upsert_persona(PersonaPerceptionCreate(
                agent_id=agent_id,
                user_id=user_id,
                perception_summary="(等待累积)",
                trait_keywords=[],
                interaction_count=1,
                confidence_level=0.05,
                last_event_id=event.id if event else None,
            ))
        else:
            new_conf = min(_PERSONA_CONFIDENCE_CAP,
                           persona.confidence_level + _PERSONA_CONFIDENCE_STEP)
            s.update_persona(
                agent_id, user_id,
                PersonaPerceptionUpdate(
                    interaction_count_delta=1,
                    confidence_level=new_conf,
                    last_event_id=event.id if event else None,
                ),
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[harness/post_hook] persona update 失败")
        errors.append(f"persona: {type(exc).__name__}")

    # ---- 3. Relationship ----
    trust_d, fam_d = _REL_DELTA_BY_EMOTION.get(score.emotion_tag, (0.0, 0.01))
    rel_after = None
    try:
        rel = s.get_relationship(agent_id, user_id)
        if rel is None:
            rel_after = s.upsert_relationship(RelationshipNodeCreate(
                agent_id=agent_id,
                user_id=user_id,
                trust_level=0.5 + trust_d,
                familiarity=fam_d,
                collaboration_count=1,
                alignment_score=0.5,
                milestones=[],
                current_phase="cold_start",
            ))
        else:
            rel_after = s.apply_relationship_delta(
                agent_id, user_id,
                RelationshipNodeUpdate(
                    trust_delta=trust_d,
                    familiarity_delta=fam_d,
                    collaboration_count_delta=1,
                    alignment_delta=0.0,
                ),
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[harness/post_hook] relationship update 失败")
        errors.append(f"relationship: {type(exc).__name__}")

    # ---- 4. Sensors · 输出合规度 + 召回命中率(W1 D6)----
    sensors_summary: list[dict] = []
    try:
        comp_sensor = sensor_output_compliance(
            agent_id=agent_id,
            output=output,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            store=s,
        )
        sensors_summary.append({
            "type": "output_compliance",
            "metric": comp_sensor.metric_value,
            "threshold": comp_sensor.threshold,
            "passed": comp_sensor.passed,
            "remediation": comp_sensor.remediation,
        })
    except Exception as exc:  # noqa: BLE001
        logger.exception("[harness/post_hook] output_compliance sensor 失败")
        errors.append(f"sensor_compliance: {type(exc).__name__}")

    try:
        hit_sensor = sensor_recall_hit_rate(
            agent_id=agent_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            store=s,
        )
        sensors_summary.append({
            "type": "recall_hit_rate",
            "metric": hit_sensor.metric_value,
            "threshold": hit_sensor.threshold,
            "passed": hit_sensor.passed,
            "remediation": hit_sensor.remediation,
        })
    except Exception as exc:  # noqa: BLE001
        logger.exception("[harness/post_hook] recall_hit_rate sensor 失败")
        errors.append(f"sensor_hit_rate: {type(exc).__name__}")

    try:
        drift_sensor = sensor_persona_drift(
            agent_id=agent_id,
            current_output=output,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            store=s,
        )
        sensors_summary.append({
            "type": "persona_drift",
            "metric": drift_sensor.metric_value,
            "threshold": drift_sensor.threshold,
            "passed": drift_sensor.passed,
            "remediation": drift_sensor.remediation,
        })
    except Exception as exc:  # noqa: BLE001
        logger.exception("[harness/post_hook] persona_drift sensor 失败")
        errors.append(f"sensor_drift: {type(exc).__name__}")

    return {
        "score": score.model_dump(),
        "event_id": event.id if event else None,
        "wrote_event": event is not None,
        "trust_delta": trust_d,
        "familiarity_delta": fam_d,
        "collaboration_count": rel_after.collaboration_count if rel_after else 0,
        "trust_level": rel_after.trust_level if rel_after else 0.5,
        "current_phase": rel_after.current_phase if rel_after else "cold_start",
        "sensors": sensors_summary,
        "errors": errors,
    }

# ============================================================
# Sensors · 反馈控制器(W1 D6)
# 灵感:Sensors 自进化机制
# ============================================================
_COMPLIANCE_PASS_THRESHOLD = 0.8   # 至少 80% guides 通过才算合规
_HIT_RATE_THRESHOLD = 0.5          # 至少 50% 事件被反复召回才算命中率达标

def sensor_output_compliance(
    agent_id: str,
    output: str,
    workflow_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    store: Optional[HarnessStore] = None,
) -> SensorEvent:
    """
    输出合规度 sensor · 反馈控制器之一。

    遍历该 agent 的所有 active Guides,逐条检查 output:
      - rule_type='output_schema'    · 检查 required_fields/keywords/pattern 是否出现
      - rule_type='forbidden_topic'  · 检查 output 是否包含禁词
      - rule_type='tone_constraint'  · "中文输出"类:验证中文字符比例 >= 30%
      - 其余类型(capability_boundary/authority_min): MVP 默认通过

    severity='block' 失败 → 触发 stop-the-line(passed=False 即使其他规则全过)
    severity='warn' 失败 → 计入未通过率,但 80% 通过率以上仍判 passed=True
    """
    s = store or get_harness_store()
    guides = s.list_guides(agent_id=agent_id, active_only=True)

    if not guides:
        return s.log_sensor(SensorEventCreate(
            sensor_type="output_compliance",
            agent_id=agent_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            metric_value=1.0,
            threshold=_COMPLIANCE_PASS_THRESHOLD,
            passed=True,
            remediation=None,
            raw_data={"note": "no active guides", "guides_checked": 0},
        ))

    results = [_check_guide(g, output or "") for g in guides]
    total = len(results)
    pass_count = sum(1 for r in results if r.passed)
    rate = pass_count / total

    block_failed = [r for r in results if r.severity == "block" and not r.passed]
    passed = (not block_failed) and rate >= _COMPLIANCE_PASS_THRESHOLD

    remediation = None
    if not passed:
        failed_names = [r.rule_name for r in results if not r.passed]
        if block_failed:
            remediation = f"BLOCK 级规则未通过: {', '.join(r.rule_name for r in block_failed)} · 建议立刻修复"
        else:
            remediation = f"warn 级规则未通过率过高({1-rate:.0%}): {', '.join(failed_names)}"

    return s.log_sensor(SensorEventCreate(
        sensor_type="output_compliance",
        agent_id=agent_id,
        workflow_id=workflow_id,
        conversation_id=conversation_id,
        metric_value=rate,
        threshold=_COMPLIANCE_PASS_THRESHOLD,
        passed=passed,
        remediation=remediation,
        raw_data={
            "guides_checked": total,
            "pass_count": pass_count,
            "block_failed_count": len(block_failed),
            "results": [r.model_dump() for r in results],
        },
    ))

def sensor_recall_hit_rate(
    agent_id: str,
    workflow_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    recent_n: int = 10,
    store: Optional[HarnessStore] = None,
) -> SensorEvent:
    """
    召回命中率 sensor · 反馈控制器之二。

    定义:取该 agent 最近 N 条 active 事件,统计被召回过的占比
         (access_count >= 1 视为有效命中)。
    含义:
      - 比例高 = 召回算法把"真值得记的"事件反复召出来
      - 比例低 = 事件库里很多"死内存",排序权重需要调整

    阈值默认 50%。低于阈值时 remediation 给前端面板用。
    """
    s = store or get_harness_store()
    events = s.list_events(agent_id=agent_id, active_only=True, limit=recent_n)

    if not events:
        return s.log_sensor(SensorEventCreate(
            sensor_type="recall_hit_rate",
            agent_id=agent_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            metric_value=0.0,
            threshold=_HIT_RATE_THRESHOLD,
            passed=True,
            remediation=None,
            raw_data={"event_count": 0, "note": "no events yet"},
        ))

    hit_count = sum(1 for e in events if e.access_count >= 1)
    rate = hit_count / len(events)
    passed = rate >= _HIT_RATE_THRESHOLD

    remediation = None
    if not passed:
        remediation = (
            f"命中率 {rate:.0%} < 阈值 {_HIT_RATE_THRESHOLD:.0%},"
            "建议:1) 调高 keyword_match 权重 2) 缩短 query 提取长度 3) 检查衰减率是否过快"
        )

    return s.log_sensor(SensorEventCreate(
        sensor_type="recall_hit_rate",
        agent_id=agent_id,
        workflow_id=workflow_id,
        conversation_id=conversation_id,
        metric_value=rate,
        threshold=_HIT_RATE_THRESHOLD,
        passed=passed,
        remediation=remediation,
        raw_data={
            "event_count": len(events),
            "hit_count": hit_count,
            "events_sampled": [
                {"id": e.id, "access_count": e.access_count, "imp": e.importance_score}
                for e in events[:recent_n]
            ],
        },
    ))

# ============================================================
# Single-guide checkers · 给 sensor_output_compliance 用
# ============================================================
def _check_guide(g: GuideRule, output: str) -> GuideCheckResult:
    """根据 rule_type 分发到具体检查器。"""
    if g.rule_type == "output_schema":
        return _check_output_schema(g, output)
    if g.rule_type == "forbidden_topic":
        return _check_forbidden_topic(g, output)
    if g.rule_type == "tone_constraint":
        return _check_tone_constraint(g, output)
    # capability_boundary / authority_min · MVP 默认通过
    return GuideCheckResult(
        rule_id=g.id,
        rule_name=g.rule_name,
        rule_type=g.rule_type,
        severity=g.severity,
        passed=True,
        detail=f"({g.rule_type} 规则 MVP 默认通过)",
    )

def _check_output_schema(g: GuideRule, text: str) -> GuideCheckResult:
    """
    output_schema 规则支持三种字段:
      {"required_fields": [...], "min_count": n}
      {"required_keywords": [...], "min_count": n}
      {"required_pattern": "regex", "min_occurrences": n}
    可同时存在,需都满足。
    """
    try:
        spec = json.loads(g.rule_content)
    except Exception:  # noqa: BLE001
        return GuideCheckResult(
            rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
            severity=g.severity, passed=True,
            detail="rule_content 非 JSON,默认通过",
        )

    if not isinstance(spec, dict):
        return GuideCheckResult(
            rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
            severity=g.severity, passed=True,
            detail="rule_content JSON 非 dict,默认通过",
        )

    matched: list[str] = []
    sub_passed: list[bool] = []
    detail_parts: list[str] = []

    required = (
        spec.get("required_fields")
        or spec.get("required_keywords")
        or []
    )
    if required:
        min_count = int(spec.get("min_count", 1))
        for kw in required:
            if kw and str(kw) in text:
                matched.append(str(kw))
        ok = len(matched) >= min_count
        sub_passed.append(ok)
        detail_parts.append(f"keywords 匹配 {len(matched)}/{min_count} {'✓' if ok else '✗'}")

    if "required_pattern" in spec:
        pattern = spec["required_pattern"]
        min_occ = int(spec.get("min_occurrences", 1))
        try:
            cnt = len(re.findall(pattern, text))
        except Exception:  # noqa: BLE001
            cnt = 0
        ok = cnt >= min_occ
        sub_passed.append(ok)
        detail_parts.append(f"pattern '{pattern}' 命中 {cnt}/{min_occ} {'✓' if ok else '✗'}")

    if not sub_passed:
        return GuideCheckResult(
            rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
            severity=g.severity, passed=True,
            detail="output_schema spec 未声明任何检查项,默认通过",
        )

    passed = all(sub_passed)
    return GuideCheckResult(
        rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
        severity=g.severity, passed=passed,
        detail=" · ".join(detail_parts),
        matched_keywords=matched,
    )

def _check_forbidden_topic(g: GuideRule, text: str) -> GuideCheckResult:
    """rule_content 是逗号或换行分隔的禁词列表。"""
    raw = (g.rule_content or "").replace("\n", ",")
    forbidden = [w.strip() for w in raw.split(",") if w.strip()]
    hit = [w for w in forbidden if w in text]
    passed = not hit
    return GuideCheckResult(
        rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
        severity=g.severity, passed=passed,
        detail="未命中禁词" if passed else f"命中禁词: {', '.join(hit)}",
        matched_keywords=hit,
    )

def _check_tone_constraint(g: GuideRule, text: str) -> GuideCheckResult:
    """
    tone_constraint MVP 实现:
      - 若规则名/内容含"中文" → 校验中文字符比例 ≥ 30%
      - 否则默认通过
    """
    needs_chinese = ("中文" in (g.rule_name or "")) or ("中文" in (g.rule_content or ""))

    if not needs_chinese:
        return GuideCheckResult(
            rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
            severity=g.severity, passed=True,
            detail="(非中文 tone 规则,MVP 默认通过)",
        )

    if not text:
        return GuideCheckResult(
            rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
            severity=g.severity, passed=True,
            detail="(空文本,默认通过)",
        )

    zh_count = sum(1 for c in text if "一" <= c <= "鿿")
    ratio = zh_count / max(1, len(text))
    passed = ratio >= 0.3
    return GuideCheckResult(
        rule_id=g.id, rule_name=g.rule_name, rule_type=g.rule_type,
        severity=g.severity, passed=passed,
        detail=f"中文字符 {zh_count}/{len(text)} ({ratio:.1%})",
    )

# ============================================================
# Persona Drift sensor + 自进化引擎(W1 D7)
# ============================================================
_DRIFT_SIM_THRESHOLD = 0.35     # 相似度低于此 → 漂移警报
_DRIFT_HISTORY_LIMIT = 5
_EVOLVE_HIT_RATE_TARGET = 0.6
_EVOLVE_COMPLIANCE_TARGET = 0.7
_EVOLVE_DRIFT_TARGET = 0.4

# 简单中英文停用词 · 给 token 频率统计去噪
_STOPWORDS: set[str] = {
    "的", "了", "是", "在", "和", "有", "我", "你", "他", "她", "它", "们",
    "也", "都", "就", "要", "会", "可以", "这", "那", "个", "上", "下", "把",
    "从", "对", "为", "与", "及", "或", "但", "等", "中", "里", "时", "之", "以",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "to", "of",
    "and", "or", "in", "on", "at", "for", "with", "by", "as", "this", "that",
    "it", "its", "we", "you", "he", "she", "i",
}

# 复用 store.py 里同款 token 正则
_TOKEN_RE_DRIFT = re.compile(r"[一-鿿]|[a-zA-Z0-9]+", re.UNICODE)

def _token_freq(text: str) -> Counter:
    if not text:
        return Counter()
    raw = (t.lower() for t in _TOKEN_RE_DRIFT.findall(text))
    return Counter(t for t in raw if t and t not in _STOPWORDS)

def _cosine_similarity(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def sensor_persona_drift(
    agent_id: str,
    current_output: str,
    workflow_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    user_id: str = "ceo",
    history_limit: int = _DRIFT_HISTORY_LIMIT,
    threshold: float = _DRIFT_SIM_THRESHOLD,
    store: Optional[HarnessStore] = None,
) -> SensorEvent:
    """
    Persona Drift sensor · 自纠错闭环最关键的一环。

    取该 agent 最近 history_limit 条事件(代表"过去的人格语言风格"),
    跟 current_output 算 token 词频余弦相似度。

    含义:
      - 相似度高 = 风格稳定,人格不漂
      - 相似度低 = 漂了,需要 Persona Anchor 强化或检查 prompt

    特殊情况:
      - 历史 < 2 条: 默认通过(没法判断漂没漂)
      - 当前输出极短(< 20 token): 默认通过(样本太小)
    """
    s = store or get_harness_store()
    events = s.list_events(
        agent_id=agent_id, user_id=user_id, active_only=True, limit=history_limit
    )

    if len(events) < 2:
        return s.log_sensor(SensorEventCreate(
            sensor_type="persona_drift",
            agent_id=agent_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            metric_value=1.0,
            threshold=threshold,
            passed=True,
            remediation=None,
            raw_data={"history_count": len(events), "note": "历史不足 2 条,默认通过"},
        ))

    history_text = "\n".join(e.content for e in events)
    history_freq = _token_freq(history_text)
    current_freq = _token_freq(current_output)

    if sum(current_freq.values()) < 20:
        return s.log_sensor(SensorEventCreate(
            sensor_type="persona_drift",
            agent_id=agent_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            metric_value=1.0,
            threshold=threshold,
            passed=True,
            remediation=None,
            raw_data={
                "history_count": len(events),
                "current_token_count": sum(current_freq.values()),
                "note": "current_output 太短,样本不足以判断漂移",
            },
        ))

    similarity = _cosine_similarity(history_freq, current_freq)
    passed = similarity >= threshold

    remediation = None
    if not passed:
        remediation = (
            f"当前输出与历史 {len(events)} 条事件相似度仅 {similarity:.2f} < {threshold:.2f},"
            "建议:1) 在 system_prompt 加 Persona Anchor 段强化人格 "
            "2) 检查 user_input 是否引导跑题 "
            "3) 若用户在主动转移话题,可放宽阈值"
        )

    common_tokens = sorted(
        set(history_freq) & set(current_freq),
        key=lambda t: -(history_freq[t] + current_freq[t]),
    )[:20]

    return s.log_sensor(SensorEventCreate(
        sensor_type="persona_drift",
        agent_id=agent_id,
        workflow_id=workflow_id,
        conversation_id=conversation_id,
        metric_value=similarity,
        threshold=threshold,
        passed=passed,
        remediation=remediation,
        raw_data={
            "history_count": len(events),
            "history_token_count": sum(history_freq.values()),
            "current_token_count": sum(current_freq.values()),
            "common_tokens_top20": common_tokens,
        },
    ))

# ============================================================
# 自进化引擎 · evolve_thresholds(W1 D7 闭环最后一棒)
# ============================================================
def evolve_thresholds(
    agent_id: Optional[str] = None,
    sample_size: int = 10,
    store: Optional[HarnessStore] = None,
) -> dict:
    """
    自进化引擎 · 反馈控制器闭环。

    扫描最近 sample_size 条 sensor_event,如果某个维度持续低于目标阈值,
    生成"调整建议"并落库一条 importance_calibration 记录(给前端面板演示用)。

    判断维度:
      - recall_hit_rate     · 平均 < 0.6 → 召回算法权重需要调整
      - output_compliance   · 平均 < 0.7 → guides 描述需要补强
      - persona_drift       · 平均 < 0.4 → Persona Anchor 需要强化

    设计:本函数不直接改硬编码权重(那需要把权重写到 DB,超出 D7 范围),
         而是把"诊断结论"+"建议动作"写进 sensor_event(type=importance_calibration),
         前端面板可以渲染成"系统检测到漂移并自动建议..."的卧槽时刻。

    Args:
        agent_id: 限定只看某个岗位(None = 所有 agents)
        sample_size: 取最近多少条 sensor_event 做评估

    Returns:
        {
            "evolved": bool,         # 是否触发了任何调整
            "sample_size": int,      # 实际评估的样本数
            "by_sensor_type": dict,  # 各 sensor_type 的统计
            "actions": list[dict],   # 触发的具体调整建议
        }
    """
    s = store or get_harness_store()
    sensors = s.list_sensor_events(limit=sample_size * 4)
    if agent_id is not None:
        sensors = [e for e in sensors if e.agent_id == agent_id]

    sensors = sensors[:sample_size]

    if len(sensors) < 5:
        return {
            "evolved": False,
            "sample_size": len(sensors),
            "by_sensor_type": {},
            "actions": [],
            "reason": f"sensor 样本数 {len(sensors)} < 5,等更多数据再判断",
        }

    by_type: dict[str, list[SensorEvent]] = {}
    for e in sensors:
        by_type.setdefault(e.sensor_type, []).append(e)

    by_type_summary = {
        t: {
            "sample_size": len(es),
            "avg_metric": sum(e.metric_value for e in es) / len(es),
            "pass_count": sum(1 for e in es if e.passed),
        }
        for t, es in by_type.items()
    }

    actions: list[dict] = []

    hit_es = by_type.get("recall_hit_rate", [])
    if hit_es:
        avg = sum(e.metric_value for e in hit_es) / len(hit_es)
        if avg < _EVOLVE_HIT_RATE_TARGET:
            actions.append({
                "trigger": "recall_hit_rate",
                "metric_observed": round(avg, 3),
                "target": _EVOLVE_HIT_RATE_TARGET,
                "suggestion": "提升 keyword_match 权重 +0.05(0.4 → 0.45),弱化情绪权重",
                "scope": "store.recall_top_k 公式参数",
            })

    comp_es = by_type.get("output_compliance", [])
    if comp_es:
        avg = sum(e.metric_value for e in comp_es) / len(comp_es)
        if avg < _EVOLVE_COMPLIANCE_TARGET:
            actions.append({
                "trigger": "output_compliance",
                "metric_observed": round(avg, 3),
                "target": _EVOLVE_COMPLIANCE_TARGET,
                "suggestion": "在 agent.system_prompt 增加 schema 字段示例 / 调整 guides 内容",
                "scope": "agent.system_prompt + guides",
            })

    drift_es = by_type.get("persona_drift", [])
    if drift_es:
        avg = sum(e.metric_value for e in drift_es) / len(drift_es)
        if avg < _EVOLVE_DRIFT_TARGET:
            actions.append({
                "trigger": "persona_drift",
                "metric_observed": round(avg, 3),
                "target": _EVOLVE_DRIFT_TARGET,
                "suggestion": "在 system_prompt 加 Persona Anchor 段(关键词 / 口头禅 / 信条)",
                "scope": "agent.system_prompt",
            })

    if actions:
        s.log_sensor(SensorEventCreate(
            sensor_type="importance_calibration",
            agent_id=agent_id,
            metric_value=float(len(actions)),
            threshold=0.0,
            passed=True,
            remediation=" | ".join(a["suggestion"] for a in actions),
            raw_data={
                "by_sensor_type": by_type_summary,
                "actions": actions,
            },
        ))

    return {
        "evolved": bool(actions),
        "sample_size": len(sensors),
        "by_sensor_type": by_type_summary,
        "actions": actions,
    }
