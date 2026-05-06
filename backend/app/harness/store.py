"""
Harness Store · 三库 CRUD + 衰减算法 + 召回算法

核心算法(灵感自武艺分享):
  - 衰减计算:decayed_importance = score * exp(-decay_rate * days_since)
  - 召回评分:final_score = 0.4 * decayed/9 + 0.4 * keyword_match + 0.2 * emotion_match
  - 阈值淘汰:final_score < 2.0 标记 is_active=0(可恢复)

设计原则:
  - 跟主项目的 InMemoryPlaygroundStore 平行,各管各的表
  - sqlite3 直连,不引 SQLAlchemy
  - 所有列表操作有 limit 上限(防滥读)
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schemas import (
    EmotionTag,
    EventMemory,
    EventMemoryCreate,
    EventMemoryRecallScore,
    GuideRule,
    GuideRuleCreate,
    GuideRuleUpdate,
    PersonaPerception,
    PersonaPerceptionCreate,
    PersonaPerceptionUpdate,
    RelationshipNode,
    RelationshipNodeCreate,
    RelationshipNodeUpdate,
    SensorEvent,
    SensorEventCreate,
    utc_now_iso,
)


# ============================================================
# 工具函数
# ============================================================
def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _parse_iso(s: str) -> datetime:
    """ISO 8601 → datetime · 兼容 'Z' 后缀。"""
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.now(timezone.utc)


def _days_since(iso_str: str) -> float:
    """到现在多少天(可能是小数)。"""
    delta = datetime.now(timezone.utc) - _parse_iso(iso_str)
    return max(0.0, delta.total_seconds() / 86400.0)


def _decayed_importance(score: float, decay_rate: float, days_since: float) -> float:
    """衰减公式 · 武艺原版:e^(-decay_rate * days)。"""
    return score * math.exp(-decay_rate * days_since)


# ============================================================
# 关键词 + 情绪匹配算法(MVP · 简单实现)
# ============================================================
_TOKEN_RE = re.compile(r"[一-鿿]|[a-zA-Z0-9]+", re.UNICODE)


def _tokenize(text: str) -> set[str]:
    """中文按字 + 英文按词,简易版分词。"""
    if not text:
        return set()
    return set(t.lower() for t in _TOKEN_RE.findall(text))


def _keyword_match_score(query: str, content: str) -> float:
    """
    返回 0-1 的关键词匹配分。
    简易 Jaccard:|交集| / |并集|,但更偏向 query 命中(召回精准为主)。
    """
    q_tokens = _tokenize(query)
    c_tokens = _tokenize(content)
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = q_tokens & c_tokens
    # 偏向 query 命中(分母用 query 长度,而不是并集)
    return len(overlap) / max(1, len(q_tokens))


_EMOTION_DISTANCE = {
    ("neutral", "neutral"): 1.0,
    ("positive", "positive"): 1.0,
    ("negative", "negative"): 1.0,
    ("urgent", "urgent"): 1.0,
    ("breakthrough", "breakthrough"): 1.0,
    # 相邻
    ("positive", "breakthrough"): 0.7,
    ("breakthrough", "positive"): 0.7,
    ("negative", "urgent"): 0.7,
    ("urgent", "negative"): 0.7,
    # 中性 vs 任何
    ("neutral", "positive"): 0.5,
    ("neutral", "negative"): 0.4,
    ("neutral", "urgent"): 0.5,
    ("neutral", "breakthrough"): 0.5,
}


def _emotion_match_score(current: str, event: str) -> float:
    """情绪匹配 · 0-1。"""
    key = (current, event)
    if key in _EMOTION_DISTANCE:
        return _EMOTION_DISTANCE[key]
    rev = (event, current)
    if rev in _EMOTION_DISTANCE:
        return _EMOTION_DISTANCE[rev]
    return 0.3  # 跨情绪默认低分


# ============================================================
# Harness Store
# ============================================================
def _ensure_harness_schema(db_path: str) -> None:
    """
    启动时执行一次 · 保证 Harness 6 张表存在(idempotent · IF NOT EXISTS)
    schema 来源:backend/scripts/harness_migration.sql
    云端首次部署没人手动跑过 migration,这里兜底建表
    """
    sql_path = Path(__file__).resolve().parents[2] / "scripts" / "harness_migration.sql"
    if not sql_path.exists():
        # 找不到也不阻断启动 · 让后续 query 自己报错
        import sys as _sys
        print(f"[harness] migration sql missing: {sql_path}", file=_sys.stderr, flush=True)
        return
    sql = sql_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)


class HarnessStore:
    """三库 CRUD + 衰减/召回算法 · 独立于主 store。"""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        # 兜底建表 · 云端首次启动一定跑一次,本地已存在表也是 no-op
        try:
            _ensure_harness_schema(self.db_path)
        except Exception as exc:
            import sys as _sys
            print(f"[harness] ensure_schema failed (continuing): {exc}", file=_sys.stderr, flush=True)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ============================================================
    # 库 1 · Event Memory
    # ============================================================
    def create_event(self, payload: EventMemoryCreate) -> EventMemory:
        eid = _new_id("evt")
        now = utc_now_iso()
        meta_json = json.dumps(payload.metadata, ensure_ascii=False) if payload.metadata else None
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO event_memory
                  (id, workflow_id, conversation_id, agent_id, user_id,
                   content, emotion_tag, importance_score,
                   importance_emotion, importance_novelty, importance_relation,
                   decay_rate, created_at, last_accessed_at, access_count, is_active, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, 1, ?)
                """,
                (
                    eid, payload.workflow_id, payload.conversation_id,
                    payload.agent_id, payload.user_id,
                    payload.content, payload.emotion_tag, payload.importance_score,
                    payload.importance_emotion, payload.importance_novelty, payload.importance_relation,
                    payload.decay_rate, now, meta_json,
                ),
            )
        return self.get_event(eid)  # type: ignore[return-value]

    def get_event(self, event_id: str) -> Optional[EventMemory]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM event_memory WHERE id = ?", (event_id,)
            ).fetchone()
        return self._row_to_event(row) if row else None

    def list_events(
        self,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        user_id: str = "ceo",
        active_only: bool = True,
        limit: int = 100,
    ) -> list[EventMemory]:
        sql = "SELECT * FROM event_memory WHERE user_id = ?"
        params: list = [user_id]
        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)
        if workflow_id:
            sql += " AND workflow_id = ?"
            params.append(workflow_id)
        if active_only:
            sql += " AND is_active = 1"
        sql += " ORDER BY importance_score DESC, created_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_event(r) for r in rows]

    def touch_event_access(self, event_id: str) -> None:
        """召回时更新 last_accessed_at + access_count。"""
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE event_memory
                   SET last_accessed_at = ?,
                       access_count = access_count + 1
                 WHERE id = ?
                """,
                (utc_now_iso(), event_id),
            )

    def sweep_low_score_events(self, threshold: float = 2.0) -> int:
        """周期性扫描:对每个 active event 计算 decayed_importance,< threshold → 标记 inactive。"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, importance_score, decay_rate, created_at "
                "FROM event_memory WHERE is_active = 1"
            ).fetchall()
            deactivate_ids = []
            for r in rows:
                d = _decayed_importance(r["importance_score"], r["decay_rate"], _days_since(r["created_at"]))
                if d < threshold:
                    deactivate_ids.append(r["id"])
            if deactivate_ids:
                conn.executemany(
                    "UPDATE event_memory SET is_active = 0 WHERE id = ?",
                    [(eid,) for eid in deactivate_ids],
                )
        return len(deactivate_ids)

    # ============================================================
    # 召回算法 · top-K
    # ============================================================
    def recall_top_k(
        self,
        agent_id: str,
        query_text: str,
        current_emotion: EmotionTag = "neutral",
        user_id: str = "ceo",
        limit: int = 5,
    ) -> list[EventMemoryRecallScore]:
        """
        召回 top-K 最相关事件 · 武艺分享同款 5 条精准 > 全量塞。

        最终评分 = 0.4 * decayed/9 + 0.4 * keyword_match + 0.2 * emotion_match
        """
        candidates = self.list_events(agent_id=agent_id, user_id=user_id, active_only=True, limit=200)
        scored: list[EventMemoryRecallScore] = []

        for evt in candidates:
            days = _days_since(evt.created_at)
            decayed = _decayed_importance(evt.importance_score, evt.decay_rate, days)
            kw = _keyword_match_score(query_text, evt.content)
            em = _emotion_match_score(current_emotion, evt.emotion_tag)
            final = 0.4 * (decayed / 9.0) + 0.4 * kw + 0.2 * em
            scored.append(
                EventMemoryRecallScore(
                    event=evt,
                    decayed_importance=decayed,
                    keyword_match=kw,
                    emotion_match=em,
                    final_score=final,
                )
            )

        scored.sort(key=lambda s: s.final_score, reverse=True)
        top = scored[:limit]

        # 召回时更新 access 信息
        for s in top:
            self.touch_event_access(s.event.id)
        return top

    # ============================================================
    # 库 2 · Persona Perception
    # ============================================================
    def get_persona(self, agent_id: str, user_id: str = "ceo") -> Optional[PersonaPerception]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM persona_perception WHERE agent_id = ? AND user_id = ?",
                (agent_id, user_id),
            ).fetchone()
        return self._row_to_persona(row) if row else None

    def upsert_persona(self, payload: PersonaPerceptionCreate) -> PersonaPerception:
        existing = self.get_persona(payload.agent_id, payload.user_id)
        now = utc_now_iso()
        traits_json = json.dumps(payload.trait_keywords, ensure_ascii=False)
        if existing:
            with self._conn() as conn:
                conn.execute(
                    """
                    UPDATE persona_perception SET
                      perception_summary = ?,
                      trait_keywords = ?,
                      interaction_count = ?,
                      confidence_level = ?,
                      last_event_id = ?,
                      last_updated = ?
                    WHERE agent_id = ? AND user_id = ?
                    """,
                    (
                        payload.perception_summary, traits_json,
                        payload.interaction_count, payload.confidence_level,
                        payload.last_event_id, now,
                        payload.agent_id, payload.user_id,
                    ),
                )
            return self.get_persona(payload.agent_id, payload.user_id)  # type: ignore[return-value]
        # INSERT
        pid = _new_id("psn")
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO persona_perception
                  (id, agent_id, user_id, perception_summary, trait_keywords,
                   interaction_count, confidence_level, last_event_id, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid, payload.agent_id, payload.user_id,
                    payload.perception_summary, traits_json,
                    payload.interaction_count, payload.confidence_level,
                    payload.last_event_id, now, now,
                ),
            )
        return self.get_persona(payload.agent_id, payload.user_id)  # type: ignore[return-value]

    def update_persona(
        self, agent_id: str, user_id: str, payload: PersonaPerceptionUpdate
    ) -> Optional[PersonaPerception]:
        existing = self.get_persona(agent_id, user_id)
        if not existing:
            return None
        new_summary = payload.perception_summary if payload.perception_summary is not None else existing.perception_summary
        new_traits = payload.trait_keywords if payload.trait_keywords is not None else existing.trait_keywords
        new_count = existing.interaction_count + payload.interaction_count_delta
        new_conf = payload.confidence_level if payload.confidence_level is not None else existing.confidence_level
        new_last_event = payload.last_event_id if payload.last_event_id is not None else existing.last_event_id
        return self.upsert_persona(
            PersonaPerceptionCreate(
                agent_id=agent_id,
                user_id=user_id,
                perception_summary=new_summary,
                trait_keywords=new_traits,
                interaction_count=new_count,
                confidence_level=new_conf,
                last_event_id=new_last_event,
            )
        )

    def list_personas(self, user_id: str = "ceo") -> list[PersonaPerception]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM persona_perception WHERE user_id = ? ORDER BY last_updated DESC",
                (user_id,),
            ).fetchall()
        return [self._row_to_persona(r) for r in rows]

    # ============================================================
    # 库 3 · Relationship Node
    # ============================================================
    def get_relationship(self, agent_id: str, user_id: str = "ceo") -> Optional[RelationshipNode]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM relationship_node WHERE agent_id = ? AND user_id = ?",
                (agent_id, user_id),
            ).fetchone()
        return self._row_to_relationship(row) if row else None

    def upsert_relationship(self, payload: RelationshipNodeCreate) -> RelationshipNode:
        existing = self.get_relationship(payload.agent_id, payload.user_id)
        now = utc_now_iso()
        ms_json = json.dumps(payload.milestones, ensure_ascii=False)
        if existing:
            with self._conn() as conn:
                conn.execute(
                    """
                    UPDATE relationship_node SET
                      trust_level = ?, familiarity = ?, collaboration_count = ?,
                      alignment_score = ?, milestones_json = ?, current_phase = ?,
                      last_updated = ?
                    WHERE agent_id = ? AND user_id = ?
                    """,
                    (
                        payload.trust_level, payload.familiarity, payload.collaboration_count,
                        payload.alignment_score, ms_json, payload.current_phase,
                        now, payload.agent_id, payload.user_id,
                    ),
                )
            return self.get_relationship(payload.agent_id, payload.user_id)  # type: ignore[return-value]
        rid = _new_id("rel")
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO relationship_node
                  (id, agent_id, user_id, trust_level, familiarity, collaboration_count,
                   alignment_score, milestones_json, current_phase, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rid, payload.agent_id, payload.user_id,
                    payload.trust_level, payload.familiarity, payload.collaboration_count,
                    payload.alignment_score, ms_json, payload.current_phase,
                    now, now,
                ),
            )
        return self.get_relationship(payload.agent_id, payload.user_id)  # type: ignore[return-value]

    def apply_relationship_delta(
        self, agent_id: str, user_id: str, delta: RelationshipNodeUpdate
    ) -> Optional[RelationshipNode]:
        existing = self.get_relationship(agent_id, user_id)
        if not existing:
            return None
        ms = list(existing.milestones)
        if delta.new_milestone:
            ms.append(delta.new_milestone)
        new_trust = max(0.0, min(1.0, existing.trust_level + delta.trust_delta))
        new_fam = max(0.0, min(1.0, existing.familiarity + delta.familiarity_delta))
        new_count = existing.collaboration_count + delta.collaboration_count_delta
        new_align = max(0.0, min(1.0, existing.alignment_score + delta.alignment_delta))

        # 自动 phase 升级
        new_phase = existing.current_phase
        if new_count >= 20 and new_trust >= 0.8:
            new_phase = "deep"
        elif new_count >= 10 and new_trust >= 0.6:
            new_phase = "established"
        elif new_count >= 3:
            new_phase = "warming"

        return self.upsert_relationship(
            RelationshipNodeCreate(
                agent_id=agent_id, user_id=user_id,
                trust_level=new_trust, familiarity=new_fam,
                collaboration_count=new_count, alignment_score=new_align,
                milestones=ms, current_phase=new_phase,
            )
        )

    def list_relationships(self, user_id: str = "ceo") -> list[RelationshipNode]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM relationship_node WHERE user_id = ? ORDER BY last_updated DESC",
                (user_id,),
            ).fetchall()
        return [self._row_to_relationship(r) for r in rows]

    # ============================================================
    # Sensors
    # ============================================================
    def log_sensor(self, payload: SensorEventCreate) -> SensorEvent:
        sid = _new_id("snr")
        raw_json = json.dumps(payload.raw_data, ensure_ascii=False) if payload.raw_data else None
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sensor_event
                  (id, workflow_id, conversation_id, agent_id, sensor_type,
                   metric_value, threshold, passed, remediation, raw_data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid, payload.workflow_id, payload.conversation_id, payload.agent_id,
                    payload.sensor_type, payload.metric_value, payload.threshold,
                    1 if payload.passed else 0, payload.remediation, raw_json,
                    utc_now_iso(),
                ),
            )
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM sensor_event WHERE id = ?", (sid,)).fetchone()
        return self._row_to_sensor(row)

    def list_sensor_events(
        self,
        sensor_type: str | None = None,
        agent_id: str | None = None,
        passed: bool | None = None,
        limit: int = 100,
    ) -> list[SensorEvent]:
        sql = "SELECT * FROM sensor_event WHERE 1=1"
        params: list = []
        if sensor_type:
            sql += " AND sensor_type = ?"; params.append(sensor_type)
        if agent_id:
            sql += " AND agent_id = ?"; params.append(agent_id)
        if passed is not None:
            sql += " AND passed = ?"; params.append(1 if passed else 0)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_sensor(r) for r in rows]

    # ============================================================
    # Guides
    # ============================================================
    def list_guides(
        self,
        agent_id: str | None = "__any__",  # __any__ = 所有(全局+特定); None = 仅全局
        active_only: bool = True,
    ) -> list[GuideRule]:
        sql = "SELECT * FROM guide_rule WHERE 1=1"
        params: list = []
        if agent_id is None:
            sql += " AND agent_id IS NULL"
        elif agent_id != "__any__":
            sql += " AND (agent_id IS NULL OR agent_id = ?)"
            params.append(agent_id)
        if active_only:
            sql += " AND is_active = 1"
        sql += " ORDER BY agent_id IS NULL DESC, created_at DESC"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_guide(r) for r in rows]

    def create_guide(self, payload: GuideRuleCreate) -> GuideRule:
        gid = _new_id("gid")
        now = utc_now_iso()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO guide_rule
                  (id, agent_id, rule_type, rule_name, rule_content, severity,
                   is_active, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gid, payload.agent_id, payload.rule_type, payload.rule_name,
                    payload.rule_content, payload.severity,
                    1 if payload.is_active else 0, now, now,
                ),
            )
        return self.get_guide(gid)  # type: ignore[return-value]

    def get_guide(self, guide_id: str) -> Optional[GuideRule]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM guide_rule WHERE id = ?", (guide_id,)).fetchone()
        return self._row_to_guide(row) if row else None

    def update_guide(self, guide_id: str, payload: GuideRuleUpdate) -> Optional[GuideRule]:
        existing = self.get_guide(guide_id)
        if not existing:
            return None
        new_name = payload.rule_name if payload.rule_name is not None else existing.rule_name
        new_content = payload.rule_content if payload.rule_content is not None else existing.rule_content
        new_severity = payload.severity if payload.severity is not None else existing.severity
        new_active = payload.is_active if payload.is_active is not None else existing.is_active
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE guide_rule SET
                  rule_name = ?, rule_content = ?, severity = ?, is_active = ?, last_updated = ?
                WHERE id = ?
                """,
                (new_name, new_content, new_severity, 1 if new_active else 0, utc_now_iso(), guide_id),
            )
        return self.get_guide(guide_id)

    def delete_guide(self, guide_id: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM guide_rule WHERE id = ?", (guide_id,))
            return cur.rowcount > 0

    # ============================================================
    # Row → Pydantic 转换器
    # ============================================================
    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> EventMemory:
        return EventMemory(
            id=row["id"],
            workflow_id=row["workflow_id"],
            conversation_id=row["conversation_id"],
            agent_id=row["agent_id"],
            user_id=row["user_id"],
            content=row["content"],
            emotion_tag=row["emotion_tag"],
            importance_score=row["importance_score"],
            importance_emotion=row["importance_emotion"],
            importance_novelty=row["importance_novelty"],
            importance_relation=row["importance_relation"],
            decay_rate=row["decay_rate"],
            created_at=row["created_at"],
            last_accessed_at=row["last_accessed_at"],
            access_count=row["access_count"],
            is_active=bool(row["is_active"]),
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None,
        )

    @staticmethod
    def _row_to_persona(row: sqlite3.Row) -> PersonaPerception:
        return PersonaPerception(
            id=row["id"],
            agent_id=row["agent_id"],
            user_id=row["user_id"],
            perception_summary=row["perception_summary"],
            trait_keywords=json.loads(row["trait_keywords"]) if row["trait_keywords"] else [],
            interaction_count=row["interaction_count"],
            confidence_level=row["confidence_level"],
            last_event_id=row["last_event_id"],
            created_at=row["created_at"],
            last_updated=row["last_updated"],
        )

    @staticmethod
    def _row_to_relationship(row: sqlite3.Row) -> RelationshipNode:
        return RelationshipNode(
            id=row["id"],
            agent_id=row["agent_id"],
            user_id=row["user_id"],
            trust_level=row["trust_level"],
            familiarity=row["familiarity"],
            collaboration_count=row["collaboration_count"],
            alignment_score=row["alignment_score"],
            milestones=json.loads(row["milestones_json"]) if row["milestones_json"] else [],
            current_phase=row["current_phase"],
            created_at=row["created_at"],
            last_updated=row["last_updated"],
        )

    @staticmethod
    def _row_to_sensor(row: sqlite3.Row) -> SensorEvent:
        return SensorEvent(
            id=row["id"],
            workflow_id=row["workflow_id"],
            conversation_id=row["conversation_id"],
            agent_id=row["agent_id"],
            sensor_type=row["sensor_type"],
            metric_value=row["metric_value"],
            threshold=row["threshold"],
            passed=bool(row["passed"]),
            remediation=row["remediation"],
            raw_data=json.loads(row["raw_data_json"]) if row["raw_data_json"] else None,
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_guide(row: sqlite3.Row) -> GuideRule:
        return GuideRule(
            id=row["id"],
            agent_id=row["agent_id"],
            rule_type=row["rule_type"],
            rule_name=row["rule_name"],
            rule_content=row["rule_content"],
            severity=row["severity"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            last_updated=row["last_updated"],
        )


# ============================================================
# 单例(给 routes / engine / workflow hook 用)
# ============================================================
_default_store: HarnessStore | None = None


def _resolve_writable_db_path(default_path: Path) -> Path:
    """
    选 DB 路径并保证可写:
    1. 优先 DB_PATH 环境变量
    2. fallback 到给定 default_path
    3. 仍不可写时再降级到 /tmp/agent_playground.db(任何云容器都能写)
    """
    import os as _os
    import sys as _sys

    env_db = _os.environ.get("DB_PATH", "").strip()
    candidates = []
    if env_db:
        candidates.append(Path(env_db))
    candidates.append(default_path)
    candidates.append(Path("/tmp/agent_playground.db"))

    for cand in candidates:
        try:
            cand.parent.mkdir(parents=True, exist_ok=True)
            # touch 一下试试可写
            with sqlite3.connect(str(cand)) as _c:
                _c.execute("SELECT 1")
            return cand
        except Exception as exc:
            print(f"[harness] db_path candidate {cand} unusable: {exc}", file=_sys.stderr, flush=True)
            continue
    # 极端情况 · 全部失败,返回最后一个让上层报错
    return candidates[-1]


def get_harness_store(db_path: str | Path | None = None) -> HarnessStore:
    global _default_store
    if _default_store is None:
        if db_path is None:
            default_path = Path(__file__).resolve().parents[2] / "data" / "agent_playground.db"
            db_path = _resolve_writable_db_path(default_path)
        _default_store = HarnessStore(db_path)
    return _default_store
