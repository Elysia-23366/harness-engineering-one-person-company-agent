"""
W1 D6 smoke test · Sensors 反馈控制器(输出合规度 + 召回命中率)

验证点:
  1. POST /sensors/run/output_compliance · 不合规输出 → passed=False
  2. POST /sensors/run/output_compliance · 合规输出(含 PRD 5 字段) → passed=True
  3. POST /sensors/run/recall_hit_rate · 返回当前 R01 命中率
  4. 跑一次 workflow → trace post-hook payload.sensors 有 2 条记录
  5. sensor_event 表新增条目
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


def post(path: str, body: dict, timeout: int = 30) -> dict:
    r = requests.post(f"{BASE}{path}", json=body, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get(path: str, params: dict | None = None, timeout: int = 10) -> object:
    r = requests.get(f"{BASE}{path}", params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def main() -> int:
    # ---- 健康检查 ----
    h = get("/api/harness/health")
    print(f"backend 健康 · guides={h['guides_count']}\n")

    sensors_before = get("/api/harness/sensors", {"limit": 500})
    print(f"sensor_event 跑前总数: {len(sensors_before)}\n")

    # ============================================================
    # Case 1 · 不合规输出 → 应当 failed
    # ============================================================
    print("=" * 60)
    print("【Case 1 · 不合规输出(纯英文 + 不含 PRD 字段)】")
    bad_output = "Hi CEO, here's a quick note: the project looks fine."
    r1 = post("/api/harness/sensors/run/output_compliance", {
        "agent_id": R01,
        "output": bad_output,
    })
    print(f"  metric={r1['metric_value']:.2f} · threshold={r1['threshold']} · passed={r1['passed']}")
    print(f"  remediation: {r1['remediation']}")
    raw = r1.get("raw_data") or {}
    for res in raw.get("results", []):
        flag = "✓" if res["passed"] else "✗"
        print(f"   {flag} [{res['rule_type']}|{res['severity']}] {res['rule_name']}: {res['detail']}")

    assert r1["passed"] is False, f"期待 passed=False,实际 {r1['passed']}"
    print("  [PASS] 不合规输出正确判 failed\n")

    # ============================================================
    # Case 2 · 合规输出(含 PRD 5 字段中文 + 中文比例足够)
    # ============================================================
    print("=" * 60)
    print("【Case 2 · 合规输出(含北极星指标/用户画像/JTBD/功能清单/PRD 路线图)】")
    good_output = """
# ADHD 待办 APP · MVP 版 PRD

## 北极星指标
- 日均启动任务数(用户每天点开多少件待办)

## 用户画像
- 25-40 岁 ADHD 群体,事多但启动难

## JTBD
- 当我面对一堆事情时,我希望能立刻被推到一件事上,这样我就能开始行动

## 功能清单
1. 任务录入(语音 / 文字)
2. 自动按"启动成本"排序
3. 推一件事,只显示一件事
4. 完成动效奖励

## PRD 路线图
- D1: 任务录入 + 排序算法
- D2: 单聚焦 UI
- D3: 反馈动效 + 上线
"""
    r2 = post("/api/harness/sensors/run/output_compliance", {
        "agent_id": R01,
        "output": good_output,
    })
    print(f"  metric={r2['metric_value']:.2f} · threshold={r2['threshold']} · passed={r2['passed']}")
    raw = r2.get("raw_data") or {}
    for res in raw.get("results", []):
        flag = "✓" if res["passed"] else "✗"
        print(f"   {flag} [{res['rule_type']}|{res['severity']}] {res['rule_name']}: {res['detail']}")

    assert r2["passed"] is True, f"期待 passed=True,实际 {r2['passed']}"
    print("  [PASS] 合规输出正确判 passed\n")

    # ============================================================
    # Case 3 · 召回命中率 sensor
    # ============================================================
    print("=" * 60)
    print("【Case 3 · 召回命中率 sensor】")
    r3 = post("/api/harness/sensors/run/recall_hit_rate", {
        "agent_id": R01,
    })
    raw = r3.get("raw_data") or {}
    print(f"  metric(命中率) = {r3['metric_value']:.0%} · threshold={r3['threshold']:.0%} · passed={r3['passed']}")
    print(f"  事件总数: {raw.get('event_count')} · 被召回过: {raw.get('hit_count')}")
    print(f"  remediation: {r3['remediation']}")
    for sample in (raw.get("events_sampled") or [])[:5]:
        print(f"    · {sample['id']} | imp={sample['imp']:.2f} | access={sample['access_count']}")

    assert r3["sensor_type"] == "recall_hit_rate"
    assert "metric_value" in r3
    print("  [PASS] recall_hit_rate sensor 落库成功\n")

    # ============================================================
    # Case 4 · 跑一次完整 workflow,检查 post-hook 含 sensors 字段
    # ============================================================
    print("=" * 60)
    print("【Case 4 · 完整 workflow(单 R01 棒) → post-hook 应自动跑 2 个 sensor】")
    wf = post("/api/workflows", {
        "name": "D6 smoke · R01 单棒 sensors",
        "type": "one_person_company",
        "specialist_agent_ids": [R01],
        "finalizer_enabled": False,
    })
    print(f"  临时 workflow_id = {wf['id']}")

    t0 = time.time()
    run = post("/api/runs", {
        "workflow_id": wf["id"],
        "user_input": "做 ADHD 待办 APP 的 PRD 简化版,3 天 MVP",
    }, timeout=300)
    elapsed = time.time() - t0
    print(f"  耗时 {elapsed:.1f}s\n")

    post_hook_evts = [e for e in run["trace"] if e["type"] == "harness_post_hook"]
    assert len(post_hook_evts) == 1, f"期待 1 条 post-hook,实际 {len(post_hook_evts)}"
    payload = post_hook_evts[0]["payload"]

    sensors_in_trace = payload.get("sensors") or []
    print(f"  trace post-hook payload.sensors = {len(sensors_in_trace)} 条")
    for s in sensors_in_trace:
        flag = "✓" if s["passed"] else "✗"
        print(f"   {flag} {s['type']}: metric={s['metric']:.2f}/{s['threshold']:.2f}")
    assert any(s["type"] == "output_compliance" for s in sensors_in_trace)
    assert any(s["type"] == "recall_hit_rate" for s in sensors_in_trace)
    print("  [PASS] post-hook 自动跑了 output_compliance + recall_hit_rate 两个 sensor")

    # ---- 验证 sensor_event 表新增条目 ----
    sensors_after = get("/api/harness/sensors", {"limit": 500})
    delta = len(sensors_after) - len(sensors_before)
    # Case 1/2/3 各产 1 条,workflow 跑产 2 条 → 至少 +5
    print(f"\n  sensor_event 跑后总数: {len(sensors_after)} (Δ +{delta})")
    assert delta >= 5, f"期待至少 +5 条 sensor_event,实际 +{delta}"
    print(f"  [PASS] sensor_event 表新增 {delta} 条")

    # ---- 清理 ----
    try:
        requests.delete(f"{BASE}/api/workflows/{wf['id']}", timeout=5)
        print(f"  [INFO] 临时 workflow {wf['id']} 已清理")
    except Exception:
        pass

    print("\n[D6 SMOKE TEST 全部通过]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
