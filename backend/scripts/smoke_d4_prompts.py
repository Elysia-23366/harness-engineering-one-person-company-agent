"""
W1 D4 smoke test · Persona Core 三层 prompt 拼装器

验证:
  1. system_prompt 包含 agent 原始 §0 对标 + 信条
  2. system_prompt 注入 persona_perception 和 relationship 块
  3. system_prompt 注入 active guides
  4. user_prompt 注入 top-K 召回 + workflow_context + handoff
  5. HarnessContext 字段完整
  6. 不存在的 agent_id 返回 404
"""
from __future__ import annotations

import json
import sys

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "http://127.0.0.1:8011"
R01 = "agent_464094c7"  # PM,handoff §3.2 提到三库都有数据


def post_assemble(payload: dict) -> dict:
    r = requests.post(f"{BASE}/api/harness/assemble_prompt", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def main() -> int:
    # === Case 1 · 完整三层拼装 ===
    payload = {
        "agent_id": R01,
        "user_input": "ADHD 待办 APP 的 PRD,要 5 个核心字段",
        "workflow_context": "一人公司协作流 · APP 类经典 4 棒 · 当前在 R01 PM 棒",
        "handoff_inputs": [
            {"agent_name": "CEO", "output": "想要 3 天 MVP,标准档"},
        ],
        "current_emotion": "positive",
        "recall_limit": 5,
    }
    res = post_assemble(payload)

    # 必有的几把锁
    sp = res["system_prompt"]
    up = res["user_prompt"]
    hc = res["harness_context"]

    print("=" * 60)
    print("【system_prompt】")
    print(sp)
    print()
    print("=" * 60)
    print("【user_prompt】")
    print(up)
    print()
    print("=" * 60)
    print("【harness_context summary】")
    print(json.dumps({
        "agent_id": hc["agent_id"],
        "persona_present": hc.get("persona_perception") is not None,
        "relationship_phase": (hc.get("relationship") or {}).get("current_phase"),
        "trust_level": (hc.get("relationship") or {}).get("trust_level"),
        "active_guides_count": len(hc["active_guides"]),
        "recalled_events_count": len(hc["recalled_events"]),
        "recalled_top_score": hc["recalled_events"][0]["final_score"] if hc["recalled_events"] else None,
    }, ensure_ascii=False, indent=2))

    # === 断言 ===
    print()
    print("=" * 60)
    print("【断言验证】")

    # 1. system_prompt 包含原始 system_prompt 关键标记(§0 对标 / 精英 / 你是)
    assert any(k in sp for k in ("§0", "对标", "精英", "你是")), \
        "system_prompt 应包含 agent 原始内容(§0/对标/精英/你是 任一)"
    print("  [PASS] system_prompt 包含 agent 原始 §0/信条内容")

    # 2. persona 块
    assert "Persona" in sp or "累积认知" in sp, \
        "system_prompt 应包含 persona 累积认知块"
    print("  [PASS] system_prompt 注入 Persona 累积认知")

    # 3. relationship 块
    assert "关系坐标" in sp, "system_prompt 应包含关系坐标块"
    print("  [PASS] system_prompt 注入关系坐标")

    # 4. guides 块(R01 有 PRD 5 字段规则 + 全局中文规则)
    assert "Active Guides" in sp, "system_prompt 应包含 Active Guides"
    assert hc["active_guides"], "active_guides 不应为空(R01 至少有 1 条专属 + 1 条全局)"
    print(f"  [PASS] system_prompt 注入 {len(hc['active_guides'])} 条 Active Guides")

    # 5. user_prompt 包含 workflow_context + handoff + 召回 + 本次请求
    assert "当前任务上下文" in up
    assert "上一棒交接" in up
    assert "本次请求" in up
    print("  [PASS] user_prompt 含 workflow_context + handoff + 本次请求")

    # 6. 召回 top-K(R01 有 4 条事件,应该召回出来)
    assert hc["recalled_events"], "应有召回事件(R01 名下有 4 条 active)"
    assert "相关历史召回" in up
    print(f"  [PASS] 召回了 {len(hc['recalled_events'])} 条相关历史 · top score={hc['recalled_events'][0]['final_score']:.3f}")

    # 7. messages 数组形状对
    assert len(res["messages"]) == 2
    assert res["messages"][0]["role"] == "system"
    assert res["messages"][1]["role"] == "user"
    print("  [PASS] messages 数组 system/user 双段结构正确")

    # === Case 2 · 不存在的 agent ===
    r = requests.post(
        f"{BASE}/api/harness/assemble_prompt",
        json={"agent_id": "agent_does_not_exist", "user_input": "x"},
        timeout=10,
    )
    assert r.status_code == 404, f"期待 404,实际 {r.status_code}"
    print("  [PASS] 不存在的 agent_id 正确返回 404")

    # === Case 3 · 空 handoff / 空 workflow context ===
    res_min = post_assemble({"agent_id": R01, "user_input": "测试 PRD 召回"})
    assert "上一棒交接" not in res_min["user_prompt"], "无 handoff 时不应出现该段"
    assert "当前任务上下文" not in res_min["user_prompt"], "无 workflow_context 时不应出现该段"
    print("  [PASS] 无 handoff / 无 workflow_context 时正确省略对应段")

    print("\n[D4 SMOKE TEST 全部通过]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
