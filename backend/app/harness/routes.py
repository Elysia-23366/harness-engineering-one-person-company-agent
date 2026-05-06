"""
Harness API Routes · /api/harness/*

所有端点都是叠加,不影响现有 /api/agents、/api/workflows、/api/runs。
前端通过这些端点拿数据画 Guides+Sensors 双控台、三库面板、Drift 雷达。
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .engine import (
    ImportanceScore,
    auto_route_event,
    evolve_thresholds,
    score_event_importance,
    sensor_output_compliance,
    sensor_persona_drift,
    sensor_recall_hit_rate,
)
from .prompts import PromptAssemblyResult, assemble_persona_prompt
from .schemas import (
    EventMemory,
    EventMemoryCreate,
    EventMemoryRecallScore,
    GuideRule,
    GuideRuleCreate,
    GuideRuleUpdate,
    PersonaPerception,
    PersonaPerceptionCreate,
    RelationshipNode,
    RelationshipNodeCreate,
    SensorEvent,
    SensorEventCreate,
)
from .store import get_harness_store

router = APIRouter(prefix="/api/harness", tags=["harness"])

# ============================================================
# Event Memory
# ============================================================
@router.get("/events", response_model=list[EventMemory])
def list_events(
    agent_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    user_id: str = "ceo",
    active_only: bool = True,
    limit: int = Query(default=100, le=500),
):
    return get_harness_store().list_events(
        agent_id=agent_id,
        workflow_id=workflow_id,
        user_id=user_id,
        active_only=active_only,
        limit=limit,
    )

@router.get("/events/{event_id}", response_model=EventMemory)
def get_event(event_id: str):
    evt = get_harness_store().get_event(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt

@router.post("/events", response_model=EventMemory)
def create_event(payload: EventMemoryCreate):
    return get_harness_store().create_event(payload)

@router.post("/events/recall", response_model=list[EventMemoryRecallScore])
def recall_events(
    agent_id: str,
    query_text: str,
    current_emotion: str = "neutral",
    user_id: str = "ceo",
    limit: int = Query(default=5, le=20),
):
    """召回 top-K · 同款 · final_score = 0.4 衰减重要性 + 0.4 关键词 + 0.2 情绪。"""
    return get_harness_store().recall_top_k(
        agent_id=agent_id,
        query_text=query_text,
        current_emotion=current_emotion,  # type: ignore[arg-type]
        user_id=user_id,
        limit=limit,
    )

@router.post("/events/sweep")
def sweep_low_score_events(threshold: float = 2.0):
    """周期性扫描 · 把 decayed_importance < threshold 的事件标记 inactive。"""
    deactivated = get_harness_store().sweep_low_score_events(threshold=threshold)
    return {"deactivated_count": deactivated, "threshold": threshold}

# ============================================================
# Persona Perception · 17 岗位对 CEO 的认知
# ============================================================
@router.get("/personas", response_model=list[PersonaPerception])
def list_personas(user_id: str = "ceo"):
    return get_harness_store().list_personas(user_id=user_id)

@router.get("/personas/{agent_id}", response_model=PersonaPerception)
def get_persona(agent_id: str, user_id: str = "ceo"):
    p = get_harness_store().get_persona(agent_id, user_id)
    if not p:
        raise HTTPException(status_code=404, detail="Persona not found")
    return p

@router.post("/personas", response_model=PersonaPerception)
def upsert_persona(payload: PersonaPerceptionCreate):
    return get_harness_store().upsert_persona(payload)

# ============================================================
# Relationship Node · 17 × CEO 关系坐标
# ============================================================
@router.get("/relationships", response_model=list[RelationshipNode])
def list_relationships(user_id: str = "ceo"):
    return get_harness_store().list_relationships(user_id=user_id)

@router.get("/relationships/{agent_id}", response_model=RelationshipNode)
def get_relationship(agent_id: str, user_id: str = "ceo"):
    r = get_harness_store().get_relationship(agent_id, user_id)
    if not r:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return r

@router.post("/relationships", response_model=RelationshipNode)
def upsert_relationship(payload: RelationshipNodeCreate):
    return get_harness_store().upsert_relationship(payload)

# ============================================================
# Sensors · 自进化日志
# ============================================================
@router.get("/sensors", response_model=list[SensorEvent])
def list_sensor_events(
    sensor_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    passed: Optional[bool] = None,
    limit: int = Query(default=100, le=500),
):
    return get_harness_store().list_sensor_events(
        sensor_type=sensor_type,
        agent_id=agent_id,
        passed=passed,
        limit=limit,
    )

@router.post("/sensors", response_model=SensorEvent)
def log_sensor(payload: SensorEventCreate):
    return get_harness_store().log_sensor(payload)

# ============================================================
# Guides · 规则
# ============================================================
@router.get("/guides", response_model=list[GuideRule])
def list_guides(
    agent_id: Optional[str] = None,
    only_global: bool = False,
    active_only: bool = True,
):
    """
    agent_id 不传 → 返回所有(全局+特定)
    agent_id='X' → 返回 X 的全局+专属
    only_global=True → 仅全局
    """
    if only_global:
        return get_harness_store().list_guides(agent_id=None, active_only=active_only)
    return get_harness_store().list_guides(
        agent_id=agent_id if agent_id else "__any__",
        active_only=active_only,
    )

@router.post("/guides", response_model=GuideRule)
def create_guide(payload: GuideRuleCreate):
    return get_harness_store().create_guide(payload)

@router.put("/guides/{guide_id}", response_model=GuideRule)
def update_guide(guide_id: str, payload: GuideRuleUpdate):
    g = get_harness_store().update_guide(guide_id, payload)
    if not g:
        raise HTTPException(status_code=404, detail="Guide not found")
    return g

@router.delete("/guides/{guide_id}")
def delete_guide(guide_id: str):
    deleted = get_harness_store().delete_guide(guide_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Guide not found")
    return {"deleted": True}

# ============================================================
# Score Engine · 重要性 3 维评分 + 写入路由(W1 D3)
# ============================================================
class ScoreRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    agent_id: str = Field(min_length=1)
    prior_context: str = Field(default="", max_length=4000)

class AutoRouteRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    agent_id: str = Field(min_length=1)
    workflow_id: str = Field(min_length=1)
    conversation_id: Optional[str] = None
    user_id: str = "ceo"
    prior_context: str = Field(default="", max_length=4000)

class AutoRouteResponse(BaseModel):
    wrote: bool
    decision: str  # "kept_low_decay" | "kept_high_decay" | "discarded"
    score: ImportanceScore
    event: Optional[EventMemory] = None

@router.post("/score", response_model=ImportanceScore)
def score_endpoint(payload: ScoreRequest):
    """用 LLM 给 content 打 3 维度分(0-3 各 + 总分 0-9)+ 情绪标签。"""
    return score_event_importance(
        content=payload.content,
        agent_id=payload.agent_id,
        prior_context=payload.prior_context,
    )

@router.post("/auto_route", response_model=AutoRouteResponse)
def auto_route_endpoint(payload: AutoRouteRequest):
    """
    自动评分 + 路由:
      - total >= 6      → 写 event_memory(decay 0.05)
      - 3 <= total < 6  → 写 event_memory(decay 0.10)
      - total < 3       → 不写
    """
    event, score = auto_route_event(
        content=payload.content,
        agent_id=payload.agent_id,
        workflow_id=payload.workflow_id,
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
        prior_context=payload.prior_context,
    )
    if event is None:
        decision = "discarded"
    elif score.total_score >= 6.0:
        decision = "kept_low_decay"
    else:
        decision = "kept_high_decay"
    return AutoRouteResponse(
        wrote=event is not None,
        decision=decision,
        score=score,
        event=event,
    )

# ============================================================
# Sensors · 反馈控制器(W1 D6)· 手动触发用于面板/调试
# ============================================================
class RunComplianceRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    output: str = Field(min_length=1, max_length=8000)
    workflow_id: Optional[str] = None
    conversation_id: Optional[str] = None

@router.post("/sensors/run/output_compliance", response_model=SensorEvent)
def run_output_compliance(payload: RunComplianceRequest):
    """手动跑一次输出合规度检查 · 给前端面板/调试用。"""
    return sensor_output_compliance(
        agent_id=payload.agent_id,
        output=payload.output,
        workflow_id=payload.workflow_id,
        conversation_id=payload.conversation_id,
    )

class RunHitRateRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    workflow_id: Optional[str] = None
    conversation_id: Optional[str] = None
    recent_n: int = Field(default=10, ge=1, le=100)

@router.post("/sensors/run/recall_hit_rate", response_model=SensorEvent)
def run_recall_hit_rate(payload: RunHitRateRequest):
    """手动跑一次召回命中率检查 · 给前端面板/调试用。"""
    return sensor_recall_hit_rate(
        agent_id=payload.agent_id,
        workflow_id=payload.workflow_id,
        conversation_id=payload.conversation_id,
        recent_n=payload.recent_n,
    )

class RunPersonaDriftRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    current_output: str = Field(min_length=1, max_length=8000)
    workflow_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: str = "ceo"
    history_limit: int = Field(default=5, ge=2, le=20)

@router.post("/sensors/run/persona_drift", response_model=SensorEvent)
def run_persona_drift(payload: RunPersonaDriftRequest):
    """手动跑一次 Persona Drift 检测 · 余弦相似度衡量人格漂移。"""
    return sensor_persona_drift(
        agent_id=payload.agent_id,
        current_output=payload.current_output,
        workflow_id=payload.workflow_id,
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
        history_limit=payload.history_limit,
    )

@router.post("/sensors/evolve")
def run_evolve_thresholds(
    agent_id: Optional[str] = None,
    sample_size: int = Query(default=10, ge=5, le=100),
):
    """
    自进化引擎 · 扫描最近 N 条 sensor_event,生成调整建议。
    触发的建议会落库 sensor_event(type=importance_calibration),前端面板可渲染。
    """
    return evolve_thresholds(agent_id=agent_id, sample_size=sample_size)

# ============================================================
# Prompt Assembler · Persona Core 三层拼装(W1 D4)
# ============================================================
class AssemblePromptRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    user_input: str = Field(min_length=1, max_length=4000)
    workflow_context: str = Field(default="", max_length=4000)
    handoff_inputs: list[dict[str, str]] = Field(default_factory=list)
    user_id: str = "ceo"
    current_emotion: str = "neutral"
    recall_limit: int = Field(default=5, ge=1, le=20)

@router.post("/assemble_prompt", response_model=PromptAssemblyResult)
def assemble_prompt_endpoint(payload: AssemblePromptRequest):
    """
    Persona Core 三层拼装(同款 system / working / memory 分离):
      Layer 1 · system_prompt    永久人格 + 累积认知 + 关系坐标 + active guides
      Layer 2 · working_context  workflow + handoff
      Layer 3 · memory_recall    top-K 召回 + 当前 user_input

    返回 system / user / full / messages + HarnessContext。
    """
    try:
        return assemble_persona_prompt(
            agent_id=payload.agent_id,
            user_input=payload.user_input,
            workflow_context=payload.workflow_context,
            handoff_inputs=payload.handoff_inputs,
            user_id=payload.user_id,
            current_emotion=payload.current_emotion,  # type: ignore[arg-type]
            recall_limit=payload.recall_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

# ============================================================
# Dashboard · 七模块汇总(给前端首页 hero 用)
# ============================================================
@router.get("/dashboard")
def get_dashboard(user_id: str = "ceo"):
    """Harness 七模块仪表盘 · 一次性拉所有指标。"""
    store = get_harness_store()

    events = store.list_events(user_id=user_id, active_only=True, limit=500)
    personas = store.list_personas(user_id=user_id)
    relationships = store.list_relationships(user_id=user_id)
    sensors_recent = store.list_sensor_events(limit=50)
    guides_active = store.list_guides(active_only=True)

    # 七模块状态
    avg_importance = (
        sum(e.importance_score for e in events) / max(1, len(events))
        if events else 0.0
    )
    sensors_passed = sum(1 for s in sensors_recent if s.passed)
    pass_rate = sensors_passed / max(1, len(sensors_recent))

    return {
        "modules": {
            "model_evaluation": {"icon": "🧠", "name": "模型评判", "active": True, "metric": pass_rate, "metric_label": "Sensors 通过率"},
            "tool_invocation": {"icon": "🔧", "name": "工具调用", "active": True, "metric": len(events), "metric_label": "事件总数"},
            "memory_management": {"icon": "📚", "name": "记忆管理", "active": True, "metric": avg_importance, "metric_label": "平均重要性"},
            "context_control": {"icon": "🎯", "name": "上下文管控", "active": True, "metric": 5, "metric_label": "Top-K 召回"},
            "state_persistence": {"icon": "💾", "name": "状态持久化", "active": True, "metric": len(personas) + len(relationships), "metric_label": "持久化条目"},
            "error_handling": {"icon": "🛡️", "name": "错误处理", "active": True, "metric": len(sensors_recent) - sensors_passed, "metric_label": "近期警报"},
            "safety_protection": {"icon": "🚧", "name": "安全防护", "active": True, "metric": len(guides_active), "metric_label": "活跃 Guides"},
        },
        "summary": {
            "total_events": len(events),
            "total_personas": len(personas),
            "total_relationships": len(relationships),
            "active_guides": len(guides_active),
            "recent_sensors": len(sensors_recent),
            "sensors_pass_rate": pass_rate,
            "avg_importance": avg_importance,
        },
    }

@router.get("/health")
def harness_health():
    """快速验证 harness 模块在线。"""
    store = get_harness_store()
    g_count = len(store.list_guides())
    return {
        "status": "ok",
        "module": "harness",
        "version": "1.0.0-dev",
        "guides_count": g_count,
    }
