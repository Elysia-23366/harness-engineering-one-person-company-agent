"""
Harness 模块 · Pydantic models
镜像 SQL schema(harness_migration.sql),给 API + 内部逻辑用。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================
# 共用类型
# ============================================================
EmotionTag = Literal[
    "neutral", "positive", "negative", "urgent", "breakthrough"
]
SensorType = Literal[
    "recall_hit_rate",
    "persona_drift",
    "output_compliance",
    "importance_calibration",
]
GuideRuleType = Literal[
    "output_schema",
    "forbidden_topic",
    "authority_min",
    "tone_constraint",
    "capability_boundary",
]
GuideSeverity = Literal["warn", "block"]
RelationshipPhase = Literal["cold_start", "warming", "established", "deep"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 库 1 · 事件库(Episodic) · 衰减式
# ============================================================
class EventMemoryCreate(BaseModel):
    """新事件写入(由 Harness 引擎自动调用,不是 CEO 直接写)。"""
    workflow_id: str = Field(min_length=1)
    conversation_id: str | None = None
    agent_id: str = Field(min_length=1)
    user_id: str = Field(default="ceo")
    content: str = Field(min_length=1, max_length=2000)
    emotion_tag: EmotionTag = "neutral"
    importance_score: float = Field(default=5.0, ge=0, le=9)
    importance_emotion: float = Field(default=0, ge=0, le=3)
    importance_novelty: float = Field(default=0, ge=0, le=3)
    importance_relation: float = Field(default=0, ge=0, le=3)
    decay_rate: float = Field(default=0.05, ge=0, le=1)
    metadata: dict[str, Any] | None = None


class EventMemory(EventMemoryCreate):
    id: str
    created_at: str
    last_accessed_at: str | None = None
    access_count: int = 0
    is_active: bool = True


class EventMemoryRecallScore(BaseModel):
    """召回时给每条事件附加的实时分数(不存 DB)。"""
    event: EventMemory
    decayed_importance: float  # importance_score * exp(-decay_rate * days_since)
    keyword_match: float       # 0-1
    emotion_match: float       # 0-1
    final_score: float         # 综合


# ============================================================
# 库 2 · 角色认知(Persona Perception) · 永久
# ============================================================
class PersonaPerceptionCreate(BaseModel):
    agent_id: str = Field(min_length=1)
    user_id: str = Field(default="ceo")
    perception_summary: str = Field(default="", max_length=1500)
    trait_keywords: list[str] = Field(default_factory=list)
    interaction_count: int = 0
    confidence_level: float = Field(default=0.0, ge=0, le=1)
    last_event_id: str | None = None


class PersonaPerception(PersonaPerceptionCreate):
    id: str
    created_at: str
    last_updated: str


class PersonaPerceptionUpdate(BaseModel):
    perception_summary: str | None = None
    trait_keywords: list[str] | None = None
    interaction_count_delta: int = 0
    confidence_level: float | None = None
    last_event_id: str | None = None


# ============================================================
# 库 3 · 关系节点(Relationship) · 永久 + 每对独立
# ============================================================
class RelationshipNodeCreate(BaseModel):
    agent_id: str = Field(min_length=1)
    user_id: str = Field(default="ceo")
    trust_level: float = Field(default=0.5, ge=0, le=1)
    familiarity: float = Field(default=0.0, ge=0, le=1)
    collaboration_count: int = 0
    alignment_score: float = Field(default=0.5, ge=0, le=1)
    milestones: list[dict[str, Any]] = Field(default_factory=list)
    current_phase: RelationshipPhase = "cold_start"


class RelationshipNode(RelationshipNodeCreate):
    id: str
    created_at: str
    last_updated: str


class RelationshipNodeUpdate(BaseModel):
    trust_delta: float = 0
    familiarity_delta: float = 0
    collaboration_count_delta: int = 0
    alignment_delta: float = 0
    new_milestone: dict[str, Any] | None = None


# ============================================================
# Sensors · 自进化日志
# ============================================================
class SensorEventCreate(BaseModel):
    workflow_id: str | None = None
    conversation_id: str | None = None
    agent_id: str | None = None
    sensor_type: SensorType
    metric_value: float
    threshold: float
    passed: bool
    remediation: str | None = None
    raw_data: dict[str, Any] | None = None


class SensorEvent(SensorEventCreate):
    id: str
    created_at: str


# ============================================================
# Guides · 规则
# ============================================================
class GuideRuleCreate(BaseModel):
    agent_id: str | None = None  # NULL = 全局
    rule_type: GuideRuleType
    rule_name: str = Field(min_length=1, max_length=80)
    rule_content: str = Field(min_length=1)
    severity: GuideSeverity = "warn"
    is_active: bool = True


class GuideRule(GuideRuleCreate):
    id: str
    created_at: str
    last_updated: str


class GuideRuleUpdate(BaseModel):
    rule_name: str | None = None
    rule_content: str | None = None
    severity: GuideSeverity | None = None
    is_active: bool | None = None


class GuideCheckResult(BaseModel):
    """对单次输出做 Guides 检查的结果。"""
    rule_id: str
    rule_name: str
    rule_type: GuideRuleType
    severity: GuideSeverity
    passed: bool
    detail: str  # 解释为什么过/不过
    matched_keywords: list[str] = Field(default_factory=list)


# ============================================================
# 顶层组合 · Harness 上下文(给 prompt 组装器用)
# ============================================================
class HarnessContext(BaseModel):
    """每次 agent 执行前,Harness 注入的完整上下文。"""
    # Persona Core(永久)
    agent_id: str
    persona_core_prompt: str           # §0 对标 + 信条
    persona_perception: PersonaPerception | None = None

    # Working Context(动态,每次任务专属)
    user_input: str
    workflow_context: str              # 来自 workflow 的上下文
    handoff_inputs: list[dict[str, str]] = Field(default_factory=list)

    # Memory Recall(动态,从三库召回)
    recalled_events: list[EventMemoryRecallScore] = Field(default_factory=list)
    relationship: RelationshipNode | None = None

    # Guides(规则)
    active_guides: list[GuideRule] = Field(default_factory=list)


class HarnessExecutionResult(BaseModel):
    """每次 agent 执行后的完整 Harness 度量结果。"""
    agent_id: str
    output: str
    execution_time_ms: int
    importance_score: float | None = None        # 评分引擎打的
    sensors_passed: list[SensorEvent] = Field(default_factory=list)
    guides_results: list[GuideCheckResult] = Field(default_factory=list)
    new_event_id: str | None = None              # 写入哪个事件
    persona_drift_score: float | None = None     # 漂移度
