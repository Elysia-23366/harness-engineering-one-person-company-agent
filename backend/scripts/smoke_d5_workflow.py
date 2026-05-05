"""
W1 D5 smoke test · one_person_company workflow Harness 集成(HTTP 版)

验证点:
  1. trace 流里有 harness_prompt_assembled 事件(每个 worker 1 个)
  2. trace 流里有 harness_post_hook 事件(每个 worker 1 个)
  3. harness_prompt_assembled payload 含 recalled_count / guides_count
  4. harness_post_hook payload 含 score / event_id / trust_delta
  5. Persona interaction_count 比跑前 +1
  6. Relationship collaboration_count 比跑前 +1
  7. event_memory 新增(若 score >= 3)

走 HTTP 复用 8011 backend 的热 LLM gateway。
为控制时长:1 个 worker(R01) + finalizer_enabled=False(跳 distill)。
"""
from __future__ import annotations

import json
import sys
import time

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "http://127.0.0.1:8011"
R01 = "agent_464094c7"


def get_persona(agent_id: str) -> dict | None:
    r = requests.get(f"{BASE}/api/harness/personas/{agent_id}", timeout=5)
    return r.json() if r.status_code == 200 else None


def get_relationship(agent_id: str) -> dict | None:
    r = requests.get(f"{BASE}/api/harness/relationships/{agent_id}", timeout=5)
    return r.json() if r.status_code == 200 else None


def list_events(agent_id: str) -> list[dict]:
    r = requests.get(
        f"{BASE}/api/harness/events",
        params={"agent_id": agent_id, "limit": 200},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def main() -> int:
    # ---- 健康检查 ----
    h = requests.get(f"{BASE}/api/harness/health", timeout=5).json()
    assert h["status"] == "ok"
    print(f"backend 健康 · guides={h['guides_count']}\n")

    # ---- 跑前快照 ----
    persona_b = get_persona(R01)
    rel_b = get_relationship(R01)
    events_b = list_events(R01)

    p_b_count = persona_b["interaction_count"] if persona_b else 0
    p_b_conf = persona_b["confidence_level"] if persona_b else 0.0
    r_b_count = rel_b["collaboration_count"] if rel_b else 0
    r_b_trust = rel_b["trust_level"] if rel_b else 0.0
    r_b_phase = rel_b["current_phase"] if rel_b else "(none)"

    print("=" * 60)
    print("【跑前快照 · R01】")
    print(f"  persona.interaction_count = {p_b_count}")
    print(f"  persona.confidence_level  = {p_b_conf:.3f}")
    print(f"  relationship.collaboration_count = {r_b_count}")
    print(f"  relationship.trust_level         = {r_b_trust:.3f}")
    print(f"  relationship.current_phase       = {r_b_phase}")
    print(f"  event_memory(R01) 总数 = {len(events_b)}")
    print()

    # ---- 创建临时 workflow ----
    print("=" * 60)
    print("【创建临时 workflow · 1 R01 棒,跳 distill】")
    wf_payload = {
        "name": "D5 smoke · R01 单棒",
        "type": "one_person_company",
        "specialist_agent_ids": [R01],
        "finalizer_enabled": False,
    }
    r = requests.post(f"{BASE}/api/workflows", json=wf_payload, timeout=10)
    r.raise_for_status()
    wf = r.json()
    print(f"  workflow_id = {wf['id']}\n")

    # ---- 跑 ----
    print("=" * 60)
    print("【启动 workflow · 等 LLM 跑(triage + worker + post-hook 各 1 次,~60-90s)】\n")
    t0 = time.time()
    r = requests.post(
        f"{BASE}/api/runs",
        json={"workflow_id": wf["id"], "user_input": "给我做一份 ADHD 待办 APP 的最简版 PRD,3 天 MVP"},
        timeout=300,
    )
    r.raise_for_status()
    elapsed = time.time() - t0
    response = r.json()

    print(f"  耗时 {elapsed:.1f}s")
    print(">>> assistant_message preview:")
    print(response["assistant_message"][:400])
    print("...\n")

    # ---- 分析 trace ----
    trace = response["trace"]
    print("=" * 60)
    print("【trace 流 · 全部 event 类型】")
    for e in trace:
        marker = "🧠" if e["type"].startswith("harness_") else "  "
        print(f"  {marker} {e['type']:32s} | {e['title']}")
    print()

    pre_hooks = [e for e in trace if e["type"] == "harness_prompt_assembled"]
    post_hooks = [e for e in trace if e["type"] == "harness_post_hook"]
    pre_failed = [e for e in trace if e["type"] == "harness_prompt_failed"]
    post_failed = [e for e in trace if e["type"] == "harness_post_hook_failed"]

    print("=" * 60)
    print("【Harness trace 计数】")
    print(f"  harness_prompt_assembled:  {len(pre_hooks)}")
    print(f"  harness_post_hook:         {len(post_hooks)}")
    print(f"  harness_prompt_failed:     {len(pre_failed)}")
    print(f"  harness_post_hook_failed:  {len(post_failed)}\n")

    # ---- 断言 ----
    print("=" * 60)
    print("【断言验证】")

    expected = 1
    assert len(pre_hooks) == expected, \
        f"期待 {expected} 条 harness_prompt_assembled,实际 {len(pre_hooks)}"
    print(f"  [PASS] harness_prompt_assembled × {expected} 触发")

    assert len(post_hooks) == expected, \
        f"期待 {expected} 条 harness_post_hook,实际 {len(post_hooks)}"
    print(f"  [PASS] harness_post_hook × {expected} 触发")

    assert len(pre_failed) == 0, f"pre-hook 不应失败 {len(pre_failed)} 次"
    assert len(post_failed) == 0, f"post-hook 不应失败 {len(post_failed)} 次"
    print("  [PASS] 无 hook 异常事件")

    # pre-hook payload
    pre = pre_hooks[0]["payload"]
    assert "recalled_count" in pre
    assert "guides_count" in pre
    print(
        f"  [PASS] pre-hook payload · recalled={pre['recalled_count']} "
        f"guides={pre['guides_count']} top_score={pre.get('top_recall_score')}"
    )

    # post-hook payload
    post = post_hooks[0]["payload"]
    assert "score" in post
    assert "trust_delta" in post
    assert "wrote_event" in post
    sc = post["score"]
    print(
        f"  [PASS] post-hook payload · score={sc['total_score']:.1f}/{sc['emotion_tag']} "
        f"· wrote={post['wrote_event']} · trust Δ{post['trust_delta']:+.2f} → {post['trust_level']:.2f}"
    )

    # ---- 跑后快照 ----
    persona_a = get_persona(R01)
    rel_a = get_relationship(R01)
    events_a = list_events(R01)

    p_a_count = persona_a["interaction_count"] if persona_a else 0
    p_a_conf = persona_a["confidence_level"] if persona_a else 0.0
    r_a_count = rel_a["collaboration_count"] if rel_a else 0
    r_a_trust = rel_a["trust_level"] if rel_a else 0.0
    r_a_phase = rel_a["current_phase"] if rel_a else "(none)"

    print()
    print("=" * 60)
    print("【跑后快照 · R01】")
    print(f"  persona.interaction_count = {p_b_count} → {p_a_count}")
    print(f"  persona.confidence_level  = {p_b_conf:.3f} → {p_a_conf:.3f}")
    print(f"  relationship.collaboration_count = {r_b_count} → {r_a_count}")
    print(f"  relationship.trust_level         = {r_b_trust:.3f} → {r_a_trust:.3f}")
    print(f"  relationship.current_phase       = {r_b_phase} → {r_a_phase}")
    print(f"  event_memory(R01) 总数 = {len(events_b)} → {len(events_a)}")
    print()

    assert p_a_count == p_b_count + 1, \
        f"interaction_count 应 +1,实际 {p_b_count} → {p_a_count}"
    print("  [PASS] persona.interaction_count +1")

    assert r_a_count == r_b_count + 1, \
        f"collaboration_count 应 +1,实际 {r_b_count} → {r_a_count}"
    print("  [PASS] relationship.collaboration_count +1")

    if post["wrote_event"]:
        assert len(events_a) == len(events_b) + 1, \
            f"事件应 +1,实际 {len(events_b)} → {len(events_a)}"
        print(f"  [PASS] event_memory +1(score={sc['total_score']:.1f} 达阈值)")
    else:
        assert len(events_a) == len(events_b)
        print(f"  [PASS] event_memory 未变(score={sc['total_score']:.1f} < 3 未达阈值)")

    # ---- 清理临时 workflow ----
    try:
        requests.delete(f"{BASE}/api/workflows/{wf['id']}", timeout=5)
        print(f"  [INFO] 临时 workflow {wf['id']} 已清理")
    except Exception:
        print(f"  [INFO] 临时 workflow {wf['id']} 留底,可手动清")

    print("\n[D5 SMOKE TEST 全部通过]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
