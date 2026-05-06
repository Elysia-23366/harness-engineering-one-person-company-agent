"""
Harness Engineering 模块

公式:Agent = Model + Harness

核心子模块:
  - schemas      · 三库 + Sensors + Guides 的 Pydantic models
  - store        · 三库 CRUD + 衰减算法 + 召回算法
  - engine       · 重要性 3 维评分 + 写入路由(D3) + Sensors 自进化(D6-7)
  - prompts      · Persona Core 三层 prompt 组装器(D4)
  - routes       · /api/harness/* 全部端点

设计原则:
  1. 纯加法 · 不动现有 agents/workflows/conversations 表
  2. 通过 agent_id / workflow_id / conversation_id 关联现有数据
  3. 可独立运行 · 不破坏 5 种现有 workflow type
  4. 可秒回滚 · drop 5 张新表即可
"""

from .engine import (
    ImportanceScore,
    auto_route_event,
    evolve_thresholds,
    post_hook_update_libraries,
    score_event_importance,
    sensor_output_compliance,
    sensor_persona_drift,
    sensor_recall_hit_rate,
)
from .prompts import PromptAssemblyResult, assemble_persona_prompt
from .store import HarnessStore, get_harness_store

__all__ = [
    "ImportanceScore",
    "auto_route_event",
    "evolve_thresholds",
    "post_hook_update_libraries",
    "score_event_importance",
    "sensor_output_compliance",
    "sensor_persona_drift",
    "sensor_recall_hit_rate",
    "PromptAssemblyResult",
    "assemble_persona_prompt",
    "HarnessStore",
    "get_harness_store",
]

__version__ = "1.0.0-dev"
