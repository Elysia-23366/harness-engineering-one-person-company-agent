<script setup>
/**
 * SevenModuleDashboard · Harness 七模块仪表盘 hero(W2 D12)
 *
 * 七模块:
 *   1. 模型评判 model_evaluation
 *   2. 工具调用 tool_invocation
 *   3. 记忆管理 memory_management
 *   4. 上下文管控 context_control
 *   5. 状态持久化 state_persistence
 *   6. 错误处理 error_handling
 *   7. 安全防护 safety_protection
 *
 * 数据源:GET /api/harness/dashboard
 * 用作 HarnessPage 顶部 hero · 取代原来的简单 hero。
 */
import { computed, onMounted, ref } from "vue";
import {
  Brain,
  Wrench,
  Library,
  Target,
  HardDrive,
  Shield,
  ShieldCheck,
  RefreshCw,
} from "lucide-vue-next";

import { fetchHarnessDashboard } from "../../api";

const data = ref(null);
const loading = ref(false);
const error = ref("");

// 顺序固定 + 中文名 + icon · 给视觉一致性
const MODULE_ORDER = [
  { id: "model_evaluation",   icon: Brain,       title: "模型评判",     hint: "Sensors 通过率 · 度量 LLM 输出质量" },
  { id: "tool_invocation",    icon: Wrench,      title: "工具调用",     hint: "事件总数 · 每次调用都会留事件痕" },
  { id: "memory_management",  icon: Library,     title: "记忆管理",     hint: "三库平均重要性 · 衰减式存活" },
  { id: "context_control",    icon: Target,      title: "上下文管控",   hint: "Top-K 召回深度 · 精选 > 全量塞" },
  { id: "state_persistence",  icon: HardDrive,   title: "状态持久化",   hint: "Persona + Relationship 永久存活" },
  { id: "error_handling",     icon: Shield,      title: "错误处理",     hint: "近期警报数 · 越少越好" },
  { id: "safety_protection",  icon: ShieldCheck, title: "安全防护",     hint: "活跃 Guides · 前馈护栏数" },
];

const summary = computed(() => data.value?.summary || {});
const modules = computed(() => {
  const m = data.value?.modules || {};
  return MODULE_ORDER.map((spec) => ({
    ...spec,
    raw: m[spec.id] || { active: false, metric: 0, metric_label: "无数据" },
  }));
});

function fmt(v) {
  if (v === null || v === undefined) return "—";
  if (typeof v !== "number") return v;
  if (Number.isInteger(v)) return v;
  if (Math.abs(v) < 1) return Math.round(v * 1000) / 1000;
  if (Math.abs(v) < 100) return Math.round(v * 100) / 100;
  return Math.round(v);
}

function fmtMetric(mod) {
  // metric_label 包含"率"的值 → 转成百分比格式
  const label = mod.raw.metric_label || "";
  if (/率/.test(label) && typeof mod.raw.metric === "number") {
    return Math.round(mod.raw.metric * 100) + "%";
  }
  return fmt(mod.raw.metric);
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await fetchHarnessDashboard();
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="seven-mod">
    <!-- Hero 标题 -->
    <header class="sm-hero">
      <div class="sm-hero-left">
        <div class="sm-tag">Harness Engineering · 七模块</div>
        <h1 class="sm-title">
          Agent = Model + <span class="sm-accent">Harness</span>
        </h1>
        <p class="sm-sub">
          核心机制全部工程化嵌入,
          每个模块都有真实数据驱动 · 跑过的 workflow 越多,数据越厚。
        </p>
      </div>
      <div class="sm-hero-right">
        <div class="sm-stat-tile">
          <span class="sm-stat-label">事件库</span>
          <span class="sm-stat-num">{{ summary.total_events ?? "—" }}</span>
        </div>
        <div class="sm-stat-tile">
          <span class="sm-stat-label">Sensors 通过率</span>
          <span class="sm-stat-num">{{ summary.sensors_pass_rate !== undefined ? Math.round(summary.sensors_pass_rate * 100) + "%" : "—" }}</span>
        </div>
        <div class="sm-stat-tile">
          <span class="sm-stat-label">活跃 Guides</span>
          <span class="sm-stat-num">{{ summary.active_guides ?? "—" }}</span>
        </div>
        <button class="sm-refresh" title="刷新" @click="load" :disabled="loading">
          <RefreshCw :size="14" :class="loading ? 'sm-spin' : ''" />
        </button>
      </div>
    </header>

    <div v-if="error" class="sm-error">{{ error }}</div>

    <!-- 七模块网格 -->
    <div class="sm-grid">
      <article
        v-for="(mod, idx) in modules"
        :key="mod.id"
        class="sm-mod"
        :class="{ 'sm-mod-active': mod.raw.active, 'sm-mod-spotlight': idx === 0 }"
      >
        <div class="sm-mod-head">
          <component :is="mod.icon" :size="18" class="sm-mod-icon" />
          <span class="sm-mod-num">0{{ idx + 1 }}</span>
        </div>
        <h3 class="sm-mod-title">{{ mod.title }}</h3>
        <div class="sm-mod-metric">
          <span class="sm-mod-value">{{ fmtMetric(mod) }}</span>
          <span class="sm-mod-label">{{ mod.raw.metric_label }}</span>
        </div>
        <p class="sm-mod-hint">{{ mod.hint }}</p>
        <div class="sm-mod-state" :class="mod.raw.active ? 'sm-state-on' : 'sm-state-off'">
          <span class="sm-dot"></span>
          {{ mod.raw.active ? "在线" : "离线" }}
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.seven-mod {
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
  color: var(--c-near-black, #141413);
}

/* Hero */
.sm-hero {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 24px;
  padding: 32px 32px;
  background:
    radial-gradient(70% 110% at 100% 0%, var(--c-terracotta-soft, rgba(201, 100, 66, 0.10)) 0%, transparent 50%),
    radial-gradient(50% 80% at 0% 100%, rgba(184, 149, 110, 0.06) 0%, transparent 60%),
    var(--c-ivory, #faf9f5);
  border: 1px solid var(--c-ring-warm, #d1cfc5);
  border-radius: 22px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.04);
  align-items: start;
}
.sm-hero-left { display: flex; flex-direction: column; gap: 12px; }
.sm-tag {
  display: inline-block;
  padding: 4px 10px;
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 11px;
  letter-spacing: 0.06em;
  color: var(--c-terracotta, #c96442);
  background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.10));
  border-radius: 6px;
  width: max-content;
}
.sm-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 38px;
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.sm-accent { color: var(--c-terracotta, #c96442); font-style: italic; }
.sm-sub {
  margin: 0;
  font-size: 14px;
  color: var(--c-stone, #87867f);
  line-height: 1.6;
  max-width: 640px;
}

.sm-hero-right {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  align-items: stretch;
  position: relative;
}
.sm-stat-tile {
  background: var(--c-parchment, #f5f4ed);
  border: 1px solid var(--c-border-warm, #e8e6dc);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.sm-stat-label {
  font-size: 11px;
  color: var(--c-stone);
  letter-spacing: 0.04em;
}
.sm-stat-num {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 26px;
  font-weight: 600;
  color: var(--c-near-black);
  line-height: 1;
}
.sm-refresh {
  position: absolute;
  top: -8px; right: -8px;
  width: 28px; height: 28px;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid var(--c-border-warm);
  border-radius: 50%;
  background: var(--c-ivory);
  color: var(--c-charcoal);
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(20, 20, 19, 0.06);
}
.sm-refresh:hover:not(:disabled) { background: var(--c-warm-sand); color: var(--c-near-black); }
.sm-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.sm-spin { animation: sm-spin 1s linear infinite; }
@keyframes sm-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }

/* Error */
.sm-error {
  padding: 10px 14px;
  background: rgba(181, 51, 51, 0.06);
  color: var(--c-error, #b53333);
  border: 1px solid rgba(181, 51, 51, 0.2);
  border-radius: 10px;
  font-size: 13px;
}

/* 7-module grid */
.sm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.sm-mod {
  background: var(--c-ivory);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
  transition: all 0.18s ease;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.sm-mod:hover {
  transform: translateY(-2px);
  border-color: var(--c-ring-warm, #d1cfc5);
  box-shadow: 0 6px 18px rgba(20, 20, 19, 0.08);
}
.sm-mod-spotlight {
  border-color: var(--c-terracotta, #c96442);
  box-shadow: 0 0 0 4px var(--c-terracotta-soft, rgba(201, 100, 66, 0.10));
}
.sm-mod-active::before {
  content: "";
  position: absolute;
  top: 14px; right: 14px;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--c-success, #6f8e5f);
  box-shadow: 0 0 0 4px rgba(111, 142, 95, 0.18);
}
.sm-mod-head {
  display: flex; align-items: center; justify-content: space-between;
  color: var(--c-charcoal);
}
.sm-mod-icon { color: var(--c-terracotta, #c96442); }
.sm-mod-num {
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 11px;
  color: var(--c-warm-silver, #b0aea5);
  letter-spacing: 0.06em;
}
.sm-mod-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--c-near-black);
}
.sm-mod-metric { display: flex; flex-direction: column; gap: 2px; }
.sm-mod-value {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 30px;
  font-weight: 600;
  color: var(--c-near-black);
  line-height: 1;
}
.sm-mod-label {
  font-size: 11px;
  color: var(--c-stone);
  letter-spacing: 0.04em;
}
.sm-mod-hint {
  margin: 0;
  font-size: 12px;
  color: var(--c-stone);
  line-height: 1.55;
  flex: 1;
}
.sm-mod-state {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px;
  letter-spacing: 0.04em;
}
.sm-dot { width: 6px; height: 6px; border-radius: 50%; }
.sm-state-on  { color: var(--c-success, #6f8e5f); }
.sm-state-on .sm-dot { background: var(--c-success, #6f8e5f); }
.sm-state-off { color: var(--c-stone); }
.sm-state-off .sm-dot { background: var(--c-warm-silver, #b0aea5); }

@media (max-width: 980px) {
  .sm-hero { grid-template-columns: 1fr; }
  .sm-hero-right { grid-template-columns: repeat(3, 1fr); }
  .sm-title { font-size: 30px; }
}
@media (max-width: 720px) {
  .sm-hero-right { grid-template-columns: 1fr; }
  .sm-grid { grid-template-columns: 1fr 1fr; }
}
</style>
