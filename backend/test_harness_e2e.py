"""
Harness e2e smoke 测试(W2 D13)

跑通整套 Harness Engineering 工程化:
    Guides → Score → Events → Personas → Relationships
    Sensors(命中率/合规度/漂移) → evolve_thresholds → Dashboard

用法:
    cd backend
    python test_harness_e2e.py
    python test_harness_e2e.py --base-url http://127.0.0.1:8011

每条断言失败立即抛错 + 打印响应,方便定位。
通过则打印一行 ✓ <名字>。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import httpx


def _ok(name: str) -> None:
    print(f"  ✓ {name}")


def _fail(name: str, resp: httpx.Response | None = None, extra: str = "") -> None:
    print(f"  ✗ {name}")
    if resp is not None:
        print(f"    status={resp.status_code} body={resp.text[:300]}")
    if extra:
        print(f"    {extra}")
    sys.exit(1)


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def run(base_url: str) -> int:
    started = time.time()
    client = httpx.Client(base_url=base_url, timeout=30.0)

    # ============ 1. /api/harness/dashboard ============
    _section("1. Dashboard 七模块")
    r = client.get("/api/harness/dashboard")
    if r.status_code != 200:
        _fail("dashboard 返回 200", r)
    data = r.json()
    expected_modules = {
        "model_evaluation", "tool_invocation", "memory_management",
        "context_control", "state_persistence", "error_handling", "safety_protection",
    }
    if set(data.get("modules", {})) != expected_modules:
        _fail("七个模块都齐", r, f"got {list(data.get('modules', {}))}")
    _ok("七模块全齐")
    if "summary" not in data:
        _fail("summary 字段存在", r)
    _ok(f"summary 含事件 {data['summary'].get('total_events')} / 通过率 {data['summary'].get('sensors_pass_rate')}")

    # ============ 2. /api/harness/score 评分 ============
    _section("2. Importance Score 评分引擎")
    payload = {
        "content": "今天和老板谈下来,产品上线后日活突破 1 万,这是关键节点",
        "agent_id": "R01",
        "metadata": {"emotion_hint": "breakthrough"},
    }
    r = client.post("/api/harness/score", json=payload)
    if r.status_code != 200:
        _fail("score 返回 200", r)
    score = r.json()
    if not all(k in score for k in ["total_score", "emotion_score", "novelty_score", "relation_score", "emotion_tag"]):
        _fail("score 三维分量齐全", r)
    if score["total_score"] <= 0:
        _fail("total_score > 0", r)
    _ok(f"total={score['total_score']:.2f} (情={score['emotion_score']:.1f} 新={score['novelty_score']:.1f} 关={score['relation_score']:.1f}) tag={score['emotion_tag']}")

    # ============ 3. /api/harness/guides CRUD ============
    _section("3. Guides CRUD")
    create_payload = {
        "rule_type": "tone_constraint",
        "rule_name": "[E2E_SMOKE] 临时口语化护栏",
        "rule_content": "测试中,务必使用更口语化语言",
        "severity": "warn",
        "is_active": True,
    }
    r = client.post("/api/harness/guides", json=create_payload)
    if r.status_code not in (200, 201):
        _fail("guide 创建", r)
    guide = r.json()
    guide_id = guide.get("id")
    if not guide_id:
        _fail("guide 返回 id", r)
    _ok(f"创建 guide id={guide_id}")

    r = client.get("/api/harness/guides")
    if r.status_code != 200:
        _fail("guide list 200", r)
    guides = r.json()
    if not any(g["id"] == guide_id for g in guides):
        _fail("新 guide 出现在列表", r)
    _ok(f"列表含 {len(guides)} 条 guide")

    r = client.put(f"/api/harness/guides/{guide_id}", json={"severity": "block"})
    if r.status_code != 200:
        _fail("guide update", r)
    if r.json().get("severity") != "block":
        _fail("severity 更新成功", r)
    _ok("update severity=block")

    r = client.delete(f"/api/harness/guides/{guide_id}")
    if r.status_code not in (200, 204):
        _fail("guide delete", r)
    _ok("删除 guide")

    # ============ 4. /api/harness/events ============
    _section("4. Events 事件库")
    r = client.get("/api/harness/events")
    if r.status_code != 200:
        _fail("events list 200", r)
    events = r.json()
    if not isinstance(events, list):
        _fail("events 是数组", r)
    _ok(f"事件库 {len(events)} 条")
    if events:
        e0 = events[0]
        for k in ["importance_score", "decay_rate", "emotion_tag", "agent_id"]:
            if k not in e0:
                _fail(f"event 字段 {k}", r, f"got keys {list(e0)}")
        _ok("事件字段完整(importance / decay / emotion / agent)")

    # ============ 5. /api/harness/personas ============
    _section("5. Personas 角色认知")
    r = client.get("/api/harness/personas")
    if r.status_code != 200:
        _fail("personas 200", r)
    personas = r.json()
    _ok(f"认知 {len(personas)} 条")

    # ============ 6. /api/harness/relationships ============
    _section("6. Relationships 关系节点")
    r = client.get("/api/harness/relationships")
    if r.status_code != 200:
        _fail("relationships 200", r)
    rels = r.json()
    _ok(f"关系 {len(rels)} 条")

    # ============ 7. /api/harness/sensors ============
    _section("7. Sensors 各传感器")
    sensor_types = ["recall_hit_rate", "output_compliance", "persona_drift", "importance_calibration"]
    for st in sensor_types:
        r = client.get("/api/harness/sensors", params={"sensor_type": st, "limit": 50})
        if r.status_code != 200:
            _fail(f"sensors?type={st} 200", r)
        items = r.json()
        _ok(f"{st}: {len(items)} 条")

    # ============ 8. /api/harness/sensors/evolve ============
    _section("8. Evolve Thresholds 阈值自进化")
    r = client.post("/api/harness/sensors/evolve", json={"sample_size": 20})
    if r.status_code != 200:
        _fail("evolve 200", r)
    res = r.json()
    if "evolved" not in res:
        _fail("evolve 返回 evolved 字段", r)
    _ok(f"evolved={res['evolved']} actions={len(res.get('actions') or [])}")

    elapsed = time.time() - started
    print(f"\n✓ ALL PASS · {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    args = parser.parse_args()
    sys.exit(run(args.base_url))
