"""
W1 D3 smoke test · 重要性 3 维评分引擎

跑 4 个测试用例,验证:
  1. 高分突破事件 → total >= 6 + emotion_tag in {breakthrough, positive}
  2. 低分琐碎事件 → total < 4
  3. 中分关系事件 → 3 <= total < 6
  4. auto_route 真写入 DB(高分)+ 真丢弃(低分)
"""
from __future__ import annotations

import json
import sys

import requests

# Force UTF-8 on Windows console
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "http://127.0.0.1:8011"


def post_score(content: str, agent_id: str, prior: str = "") -> dict:
    r = requests.post(
        f"{BASE}/api/harness/score",
        json={"content": content, "agent_id": agent_id, "prior_context": prior},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()


def post_auto_route(content: str, agent_id: str, workflow_id: str, prior: str = "") -> dict:
    r = requests.post(
        f"{BASE}/api/harness/auto_route",
        json={
            "content": content,
            "agent_id": agent_id,
            "workflow_id": workflow_id,
            "prior_context": prior,
        },
        timeout=90,
    )
    r.raise_for_status()
    return r.json()


def line(label: str, data: dict) -> None:
    print(f"--- {label} ---")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()


def main() -> int:
    # 0. health
    h = requests.get(f"{BASE}/api/harness/health", timeout=5).json()
    line("0. health", h)

    # 1. 高分:R03 端到端造 APP 突破事件
    s1 = post_score(
        content=(
            "R03 全栈工程师拿到 PRD 后,30 分钟内通过 fs_write_file 工具真的把 "
            "Next.js 22 个文件的 ADHD 待办 APP 全写出来了,跑在 :3000 上可以真用,"
            "CEO 激动得说卧槽这真能跑。这是产品从概念走到可运行的关键转折。"
        ),
        agent_id="agent_f1077f1d",
        prior="之前一直以为 R03 只能写代码片段,从未端到端造过完整可运行的 APP",
    )
    line("1. 高分 · R03 突破事件", s1)
    assert s1["total_score"] >= 6.0, f"期待 total>=6,实际 {s1['total_score']}"
    assert s1["emotion_tag"] in ("breakthrough", "positive", "urgent"), \
        f"期待 breakthrough|positive|urgent,实际 {s1['emotion_tag']}"
    print("  [PASS] 高分用例 emotion_tag + total 都符合预期")

    # 2. 低分:琐碎陈述
    s2 = post_score(
        content="Agent 收到任务,准备开始",
        agent_id="agent_464094c7",
        prior="",
    )
    line("2. 低分 · 琐碎陈述", s2)
    assert s2["total_score"] < 4.0, f"期待 total<4,实际 {s2['total_score']}"
    print("  [PASS] 低分用例 total < 4")

    # 3. 中分:关系受损但非突破
    s3 = post_score(
        content="CEO 评审中第三次否决了候选方案,要求改回 Claude.ai 暖米白调性",
        agent_id="agent_464094c7",
        prior="前两版墨道风和深色 SaaS 都被否决过",
    )
    line("3. 中分 · 关系受损", s3)
    print("  [INFO] 中分用例 total =", s3["total_score"])

    # 4. auto_route · 高分应写入
    r1 = post_auto_route(
        content=(
            "CEO 拍板决定把整站视觉锁定为 Claude.ai 暖米白 "
            "(Parchment + Terracotta + Fraunces serif),"
            "并明确否决了所有深色 / 墨道 / 紫色渐变方向。这是关键设计语言决策。"
        ),
        agent_id="agent_464094c7",
        workflow_id="workflow_f66d5cfb",
        prior="此前墨道风和深色 SaaS 已被两次否决",
    )
    line("4. auto_route · 关键决策(应写入)", r1)
    assert r1["wrote"] is True, "期待 wrote=true"
    assert r1["decision"] in ("kept_low_decay", "kept_high_decay"), \
        f"期待 kept_*,实际 {r1['decision']}"
    assert r1["event"] is not None
    print(f"  [PASS] auto_route 写入成功 · event_id={r1['event']['id']} · decision={r1['decision']}")

    # 5. auto_route · 低分应丢弃
    r2 = post_auto_route(
        content="ok 收到",
        agent_id="agent_464094c7",
        workflow_id="workflow_f66d5cfb",
    )
    line("5. auto_route · 极简回复(应丢弃)", r2)
    if r2["wrote"]:
        print(f"  [WARN] 期待丢弃但写入了,total={r2['score']['total_score']}")
    else:
        print(f"  [PASS] auto_route 正确丢弃 · total={r2['score']['total_score']}")

    # 6. 验证 DB 中真有新事件
    events = requests.get(
        f"{BASE}/api/harness/events",
        params={"agent_id": "agent_464094c7", "limit": 20},
        timeout=10,
    ).json()
    print(f"--- 6. R01 名下事件总数: {len(events)} ---")
    for e in events[:5]:
        print(
            f"  · {e['id']} | imp={e['importance_score']:.2f} | "
            f"tag={e['emotion_tag']} | decay={e['decay_rate']} | "
            f"{e['content'][:50]}..."
        )

    print("\n[D3 SMOKE TEST 全部通过]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
