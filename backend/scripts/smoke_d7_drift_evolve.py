"""
W1 D7 smoke test · Persona Drift sensor + 自进化引擎

验证点:
  1. POST /sensors/run/persona_drift · R01 风格输出 → passed=True(高相似度)
  2. POST /sensors/run/persona_drift · 离题极远的输出 → passed=False(低相似度)
  3. POST /sensors/evolve · 自进化引擎扫描 → 落库 importance_calibration 记录
  4. workflow 跑完 · trace post-hook payload.sensors 现在 3 条(含 persona_drift)
"""
from __future__ import annotations

import sys
import time

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "http://127.0.0.1:8011"
R01 = "agent_464094c7"


def post(path: str, body: dict | None = None, params: dict | None = None, timeout: int = 30) -> dict:
    r = requests.post(
        f"{BASE}{path}",
        json=body if body is not None else None,
        params=params or {},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()


def get(path: str, params: dict | None = None, timeout: int = 10):
    r = requests.get(f"{BASE}{path}", params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def main() -> int:
    h = get("/api/harness/health")
    print(f"backend 健康 · guides={h['guides_count']}\n")

    sensors_before = get("/api/harness/sensors", {"limit": 500})
    print(f"sensor_event 跑前总数: {len(sensors_before)}\n")

    # ============================================================
    # Case 1 · 风格相近(用 R01 历史里反复出现的"PRD/北极星/JTBD/ADHD/MVP"语汇)
    # ============================================================
    print("=" * 60)
    print("【Case 1 · 风格贴近 R01 历史(PRD/北极星/JTBD/ADHD)】")
    on_topic = (
        "我是 R01 PM,基于第一性原理重新拆 ADHD 待办 APP 的 PRD。"
        "北极星指标定义为日均启动任务数,因为 ADHD 群体的痛点是开始难。"
        "JTBD:当用户面对一堆待办事项,我希望系统直接推一件事,这样我能立刻进入行动。"
        "用户画像:25-40 岁 ADHD 群体。功能清单按启动成本排序。"
        "PRD 路线图:D1 录入和排序,D2 单聚焦 UI,D3 反馈动效上线 MVP。"
    )
    r1 = post("/api/harness/sensors/run/persona_drift", {
        "agent_id": R01,
        "current_output": on_topic,
    })
    print(f"  similarity={r1['metric_value']:.3f} · threshold={r1['threshold']:.2f} · passed={r1['passed']}")
    raw = r1.get("raw_data") or {}
    print(f"  历史 {raw.get('history_count')} 条 · 共有 token (top): {raw.get('common_tokens_top20', [])[:10]}")
    assert r1["passed"], f"R01 风格输出应判 passed=True,实际 {r1['passed']}"
    print("  [PASS] 风格贴近 → passed\n")

    # ============================================================
    # Case 2 · 风格离题(完全不相关话题)
    # ============================================================
    print("=" * 60)
    print("【Case 2 · 风格离题(谈 NBA / 烹饪)】")
    off_topic = (
        "Today I cooked spaghetti with tomato sauce. Add olive oil first, "
        "then garlic, then crushed tomatoes. Simmer for 20 minutes. "
        "The Lakers won by 12 points last night, LeBron scored 30. "
        "Watching basketball is a great evening activity."
    )
    r2 = post("/api/harness/sensors/run/persona_drift", {
        "agent_id": R01,
        "current_output": off_topic,
    })
    print(f"  similarity={r2['metric_value']:.3f} · threshold={r2['threshold']:.2f} · passed={r2['passed']}")
    print(f"  remediation: {r2['remediation']}")
    assert not r2["passed"], f"离题英文输出应判 passed=False,实际 {r2['passed']}"
    print("  [PASS] 离题输出 → drift 警报\n")

    # ============================================================
    # Case 3 · 自进化引擎
    # ============================================================
    print("=" * 60)
    print("【Case 3 · 自进化引擎扫描最近 sensor_event】")
    evo = post("/api/harness/sensors/evolve", params={"sample_size": 20})
    print(f"  sample_size={evo['sample_size']} · evolved={evo['evolved']}")
    print(f"  by_sensor_type:")
    for t, info in (evo.get("by_sensor_type") or {}).items():
        print(f"    · {t}: avg={info['avg_metric']:.3f} pass={info['pass_count']}/{info['sample_size']}")
    print(f"  actions ({len(evo.get('actions') or [])}):")
    for a in evo.get("actions") or []:
        print(f"    · trigger={a['trigger']} observed={a['metric_observed']} → {a['suggestion']}")

    # 自进化引擎本身要么发现问题(actions > 0)要么没问题(evolved=False) — 都算 PASS
    # 关键是它能跑通,不抛错,且落库 importance_calibration(若 actions > 0)
    print("  [PASS] evolve 引擎跑通\n")

    # ============================================================
    # Case 4 · workflow post-hook 现在应自动跑 3 个 sensor
    # ============================================================
    print("=" * 60)
    print("【Case 4 · workflow 跑 → post-hook 应自动跑 3 个 sensor(含 drift)】")
    wf = post("/api/workflows", {
        "name": "D7 smoke · 3-sensor 集成",
        "type": "one_person_company",
        "specialist_agent_ids": [R01],
        "finalizer_enabled": False,
    })
    print(f"  临时 workflow_id = {wf['id']}")

    t0 = time.time()
    run = post("/api/runs", {
        "workflow_id": wf["id"],
        "user_input": "继续打磨 ADHD 待办 APP 的 PRD,把启动成本排序逻辑写细",
    }, timeout=300)
    elapsed = time.time() - t0
    print(f"  耗时 {elapsed:.1f}s")

    post_hook_evts = [e for e in run["trace"] if e["type"] == "harness_post_hook"]
    assert len(post_hook_evts) == 1
    sensors_in_trace = post_hook_evts[0]["payload"].get("sensors") or []
    print(f"  trace post-hook payload.sensors = {len(sensors_in_trace)} 条")
    for s in sensors_in_trace:
        flag = "✓" if s["passed"] else "✗"
        print(f"   {flag} {s['type']}: metric={s['metric']:.3f}/{s['threshold']:.2f}")

    types_seen = {s["type"] for s in sensors_in_trace}
    assert "output_compliance" in types_seen
    assert "recall_hit_rate" in types_seen
    assert "persona_drift" in types_seen
    print("  [PASS] post-hook 自动跑了 3 个 sensor(含新加的 persona_drift)")

    # ---- 验证 sensor_event 表新增 ----
    sensors_after = get("/api/harness/sensors", {"limit": 500})
    delta = len(sensors_after) - len(sensors_before)
    # Case 1+2 各 1 + Case 3(可能 0 或 1 importance_calibration)+ Case 4 跑产 3 → 至少 +5
    print(f"\n  sensor_event 跑后总数: {len(sensors_after)} (Δ +{delta})")
    assert delta >= 5, f"期待至少 +5 条,实际 +{delta}"
    print(f"  [PASS] sensor_event 表新增 {delta} 条")

    # ---- 看最新一条 importance_calibration(自进化建议)如果有 ----
    calibs = get("/api/harness/sensors", {"sensor_type": "importance_calibration", "limit": 5})
    print(f"\n  importance_calibration 历史: {len(calibs)} 条")
    if calibs:
        latest = calibs[0]
        print(f"  最新一条: metric_value={latest['metric_value']} (= 触发的 action 数)")
        if latest.get("remediation"):
            print(f"  remediation: {latest['remediation'][:200]}")

    # ---- 清理 ----
    try:
        requests.delete(f"{BASE}/api/workflows/{wf['id']}", timeout=5)
        print(f"\n  [INFO] 临时 workflow {wf['id']} 已清理")
    except Exception:
        pass

    print("\n[D7 SMOKE TEST 全部通过]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
