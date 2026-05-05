<script setup>
/**
 * SensorsPanel · 武艺《Harness Engineering》反馈控制面板(W2 D9)
 *
 * 显示 sensor_event 时间线 + tab 切换:
 *   - 全部 / recall_hit_rate / output_compliance / persona_drift / importance_calibration
 * 每条事件:metric vs threshold 条 + passed/failed 图标 + remediation + raw_data 折叠
 */
import { computed, onMounted, ref } from "vue";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Target,
  TrendingUp,
  Wand2,
  XCircle,
} from "lucide-vue-next";

import { fetchHarnessSensors, runEvolveThresholds } from "../../api";

const props = defineProps({
  agents: { type: Array, default: () => [] },
});

const sensors = ref([]);
const loading = ref(false);
const error = ref("");
const expanded = ref(new Set());
const selectedTab = ref("all");
const evolving = ref(false);
const evolveResult = ref(null);

const TABS = [
  { id: "all",                     label: "全部",        icon: Activity, brief: "时间线总览" },
  { id: "recall_hit_rate",         label: "命中率",      icon: Target,   brief: "召回算法是否选对了真值得记的事件" },
  { id: "output_compliance",       label: "合规度",      icon: CheckCircle2, brief: "输出是否满足该岗位 active guides" },
  { id: "persona_drift",           label: "漂移度",      icon: TrendingUp, brief: "人格语言风格是否偏离历史" },
  { id: "importance_calibration",  label: "自进化建议",  icon: Wand2,    brief: "evolve_thresholds 出过的修正建议" },
];

const agentNameById = computed(() => {
  const m = new Map();
  for (const a of props.agents) m.set(a.id, a.name);
  return m;
});

const filteredSensors = computed(() => {
  if (selectedTab.value === "all") return sensors.value;
  return sensors.value.filter((s) => s.sensor_type === selectedTab.value);
});

const stats = computed(() => {
  const total = sensors.value.length;
  const passed = sensors.value.filter((s) => s.passed).length;
  const failed = total - passed;
  return {
    total,
    passed,
    failed,
    passRate: total > 0 ? passed / total : 0,
  };
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    sensors.value = await fetchHarnessSensors({ limit: 200 });
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function triggerEvolve() {
  evolving.value = true;
  evolveResult.value = null;
  error.value = "";
  try {
    const res = await runEvolveThresholds({ sampleSize: 20 });
    evolveResult.value = res;
    await load();
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    evolving.value = false;
  }
}

function toggle(id) {
  if (expanded.value.has(id)) expanded.value.delete(id);
  else expanded.value.add(id);
  // trigger reactivity
  expanded.value = new Set(expanded.value);
}

function fmt(num) {
  if (num === null || num === undefined) return "—";
  if (Math.abs(num) >= 100) return Math.round(num);
  return Math.round(num * 1000) / 1000;
}

function fmtPct(num) {
  if (num === null || num === undefined) return "—";
  return Math.round(num * 100) + "%";
}

function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diffSec = (now - d) / 1000;
  if (diffSec < 60) return "刚刚";
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} 分钟前`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} 小时前`;
  return d.toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function sensorTypeLabel(t) {
  return TABS.find((tt) => tt.id === t)?.label || t;
}

function metricBarStyle(metric, threshold, passed) {
  const pct = Math.max(0, Math.min(100, metric * 100));
  return {
    width: `${pct}%`,
    background: passed ? "var(--c-success, #6f8e5f)" : "var(--c-terracotta, #c96442)",
  };
}

function thresholdMarkerStyle(threshold) {
  const pct = Math.max(0, Math.min(100, threshold * 100));
  return { left: `${pct}%` };
}

onMounted(load);
</script>

<template>
  <section class="sensors-panel">
    <!-- 顶部 -->
    <header class="sp-header">
      <div class="sp-title-block">
        <div class="sp-title-row">
          <Activity :size="20" class="sp-title-icon" />
          <h2 class="sp-title">Sensors · 反馈控制</h2>
        </div>
        <p class="sp-subtitle">
          行动之后的检测 · 自动度量 / 命中率 / 漂移 / 合规 + 自纠错闭环
        </p>
      </div>
      <div class="sp-meta">
        <div class="sp-stat">
          <span class="sp-stat-num">{{ stats.passed }}</span>
          <span class="sp-stat-label">通过</span>
        </div>
        <div class="sp-stat-divider"></div>
        <div class="sp-stat">
          <span class="sp-stat-num sp-stat-fail">{{ stats.failed }}</span>
          <span class="sp-stat-label">警报</span>
        </div>
        <div class="sp-stat-divider"></div>
        <div class="sp-stat">
          <span class="sp-stat-num">{{ fmtPct(stats.passRate) }}</span>
          <span class="sp-stat-label">通过率</span>
        </div>
        <button class="sp-btn-icon" title="刷新" @click="load" :disabled="loading">
          <RefreshCw :size="16" :class="loading ? 'sp-spin' : ''" />
        </button>
        <button class="sp-btn-primary" @click="triggerEvolve" :disabled="evolving" title="跑一次 evolve_thresholds 自进化">
          <Wand2 :size="16" />
          <span>{{ evolving ? "诊断中..." : "自进化诊断" }}</span>
        </button>
      </div>
    </header>

    <!-- evolve 结果(命令式提示) -->
    <div v-if="evolveResult" class="sp-evolve-banner" :class="{ 'sp-evolve-passed': !evolveResult.evolved }">
      <Wand2 :size="16" />
      <div class="sp-evolve-text">
        <strong v-if="evolveResult.evolved">
          自进化引擎触发了 {{ evolveResult.actions.length }} 条修正建议(已落库)
        </strong>
        <strong v-else>当前无需调整 · sample={{ evolveResult.sample_size }}</strong>
        <ul v-if="evolveResult.actions?.length" class="sp-evolve-list">
          <li v-for="a in evolveResult.actions" :key="a.trigger">
            <code>{{ a.trigger }}</code> 实际 {{ fmt(a.metric_observed) }}
            &lt; 目标 {{ fmt(a.target) }} → {{ a.suggestion }}
          </li>
        </ul>
      </div>
    </div>

    <!-- 错误 -->
    <div v-if="error" class="sp-error">
      <AlertTriangle :size="14" /> {{ error }}
    </div>

    <!-- Tabs -->
    <nav class="sp-tabs">
      <button
        v-for="t in TABS"
        :key="t.id"
        class="sp-tab"
        :class="{ 'sp-tab-active': selectedTab === t.id }"
        @click="selectedTab = t.id"
      >
        <component :is="t.icon" :size="14" />
        <span>{{ t.label }}</span>
        <span class="sp-tab-count" v-if="t.id !== 'all'">
          {{ sensors.filter(s => s.sensor_type === t.id).length }}
        </span>
      </button>
    </nav>

    <p class="sp-tab-hint">
      {{ TABS.find(t => t.id === selectedTab)?.brief || "" }}
    </p>

    <!-- 时间线列表 -->
    <div class="sp-list">
      <div v-if="!loading && filteredSensors.length === 0" class="sp-empty">
        没有这个类型的 sensor 记录 · 跑一次 workflow 就会有数据
      </div>

      <article
        v-for="s in filteredSensors"
        :key="s.id"
        class="sp-card"
        :class="{ 'sp-card-fail': !s.passed, 'sp-card-pass': s.passed }"
      >
        <header class="sp-card-head">
          <div class="sp-card-titles">
            <div class="sp-card-tags">
              <span class="sp-tag sp-tag-type">{{ sensorTypeLabel(s.sensor_type) }}</span>
              <span class="sp-tag" :class="s.passed ? 'sp-tag-pass' : 'sp-tag-fail'">
                <CheckCircle2 v-if="s.passed" :size="11" />
                <XCircle v-else :size="11" />
                {{ s.passed ? "passed" : "failed" }}
              </span>
              <span class="sp-tag-agent" v-if="s.agent_id">
                {{ agentNameById.get(s.agent_id) || s.agent_id }}
              </span>
            </div>
            <time class="sp-card-time">{{ fmtTime(s.created_at) }}</time>
          </div>
          <button class="sp-btn-icon" :title="expanded.has(s.id) ? '收起 raw' : '展开 raw'" @click="toggle(s.id)">
            <ChevronDown v-if="expanded.has(s.id)" :size="14" />
            <ChevronRight v-else :size="14" />
          </button>
        </header>

        <!-- metric 进度条 -->
        <div class="sp-metric">
          <div class="sp-metric-numbers">
            <span class="sp-metric-value">
              {{ s.sensor_type === "importance_calibration" ? `${fmt(s.metric_value)} 条建议` : fmt(s.metric_value) }}
            </span>
            <span class="sp-metric-vs" v-if="s.sensor_type !== 'importance_calibration'">
              · 阈值 {{ fmt(s.threshold) }}
            </span>
          </div>
          <div class="sp-metric-bar" v-if="s.sensor_type !== 'importance_calibration'">
            <div class="sp-metric-fill" :style="metricBarStyle(s.metric_value, s.threshold, s.passed)"></div>
            <div class="sp-metric-threshold" :style="thresholdMarkerStyle(s.threshold)" :title="`阈值 ${s.threshold}`"></div>
          </div>
        </div>

        <p v-if="s.remediation" class="sp-remediation">
          <AlertTriangle :size="12" /> {{ s.remediation }}
        </p>

        <!-- raw_data 折叠 -->
        <pre v-if="expanded.has(s.id) && s.raw_data" class="sp-raw">{{
          JSON.stringify(s.raw_data, null, 2)
        }}</pre>
      </article>
    </div>
  </section>
</template>

<style scoped>
.sensors-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
  color: var(--c-near-black, #141413);
}

/* Header */
.sp-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 22px 24px;
  background: var(--c-ivory, #faf9f5);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 16px;
  box-shadow: 0 0 0 1px var(--c-ring-warm, #d1cfc5) inset, 0 1px 2px rgba(20, 20, 19, 0.04);
}
.sp-title-block { display: flex; flex-direction: column; gap: 6px; }
.sp-title-row { display: flex; align-items: center; gap: 10px; }
.sp-title-icon { color: var(--c-terracotta, #c96442); }
.sp-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.sp-subtitle {
  margin: 0;
  color: var(--c-stone, #87867f);
  font-size: 13px;
  line-height: 1.55;
}
.sp-meta { display: flex; align-items: center; gap: 12px; }
.sp-stat { display: flex; flex-direction: column; align-items: center; min-width: 48px; }
.sp-stat-num {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 22px;
  font-weight: 600;
  color: var(--c-near-black);
  line-height: 1;
}
.sp-stat-fail { color: var(--c-terracotta, #c96442); }
.sp-stat-label { font-size: 11px; color: var(--c-stone); margin-top: 2px; letter-spacing: 0.04em; }
.sp-stat-divider { width: 1px; height: 28px; background: var(--c-border-warm, #e8e6dc); }

/* Buttons */
.sp-btn-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  border: 1px solid var(--c-border-warm, #e8e6dc);
  border-radius: 8px;
  background: var(--c-ivory);
  color: var(--c-charcoal, #4d4c48);
  cursor: pointer;
  transition: all 0.15s ease;
}
.sp-btn-icon:hover:not(:disabled) { background: var(--c-warm-sand, #e8e6dc); color: var(--c-near-black); }
.sp-btn-icon:disabled { opacity: 0.5; cursor: not-allowed; }
.sp-btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--c-terracotta, #c96442);
  color: var(--c-ivory, #faf9f5);
  border: none; border-radius: 10px;
  font-size: 13px; font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}
.sp-btn-primary:hover:not(:disabled) { background: var(--c-coral, #d97757); }
.sp-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.sp-spin { animation: sp-spin 1s linear infinite; }
@keyframes sp-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }

/* Evolve banner */
.sp-evolve-banner {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px 18px;
  background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.08));
  border: 1px solid var(--c-terracotta-glow, rgba(201, 100, 66, 0.18));
  border-radius: 12px;
  color: var(--c-terracotta, #c96442);
  font-size: 13px;
}
.sp-evolve-banner.sp-evolve-passed {
  background: rgba(111, 142, 95, 0.08);
  border-color: rgba(111, 142, 95, 0.18);
  color: var(--c-success, #6f8e5f);
}
.sp-evolve-text { flex: 1; line-height: 1.55; }
.sp-evolve-list {
  margin: 8px 0 0 16px;
  padding: 0;
  list-style: disc;
  color: var(--c-charcoal);
}
.sp-evolve-list li { margin: 4px 0; }
.sp-evolve-list code {
  background: var(--c-warm-sand);
  padding: 1px 6px; border-radius: 4px;
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 11px;
}

/* Error */
.sp-error {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  background: rgba(181, 51, 51, 0.06);
  color: var(--c-error, #b53333);
  border: 1px solid rgba(181, 51, 51, 0.2);
  border-radius: 10px;
  font-size: 13px;
}

/* Tabs */
.sp-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--c-warm-sand, #e8e6dc);
  border-radius: 10px;
  width: max-content;
  flex-wrap: wrap;
}
.sp-tab {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 7px;
  cursor: pointer;
  color: var(--c-charcoal);
  font-size: 13px;
  font-family: inherit;
  transition: all 0.15s ease;
}
.sp-tab:hover { color: var(--c-near-black); }
.sp-tab-active {
  background: var(--c-ivory);
  color: var(--c-near-black);
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.06);
}
.sp-tab-count {
  font-size: 10px;
  background: var(--c-warm-sand);
  color: var(--c-stone);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 2px;
}
.sp-tab-active .sp-tab-count {
  background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.10));
  color: var(--c-terracotta, #c96442);
}
.sp-tab-hint {
  margin: 0;
  font-size: 12px;
  color: var(--c-stone);
  padding-left: 4px;
}

/* List & cards */
.sp-list { display: flex; flex-direction: column; gap: 10px; }
.sp-empty {
  text-align: center;
  padding: 40px;
  color: var(--c-stone);
  background: var(--c-ivory);
  border: 1px dashed var(--c-border-warm);
  border-radius: 12px;
}
.sp-card {
  background: var(--c-ivory);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
  transition: all 0.18s ease;
}
.sp-card:hover {
  border-color: var(--c-ring-warm, #d1cfc5);
  box-shadow: 0 4px 12px rgba(20, 20, 19, 0.06);
}
.sp-card-fail { border-left: 3px solid var(--c-terracotta, #c96442); }
.sp-card-pass { border-left: 3px solid var(--c-success, #6f8e5f); }

.sp-card-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.sp-card-titles { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 0; }
.sp-card-tags { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.sp-card-time { font-size: 11px; color: var(--c-stone); font-family: var(--ff-mono, monospace); }

.sp-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 6px;
  font-size: 11px; font-weight: 500; letter-spacing: 0.02em;
}
.sp-tag-type {
  background: var(--c-warm-sand);
  color: var(--c-olive, #5e5d59);
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 10px;
}
.sp-tag-pass { background: rgba(111, 142, 95, 0.14); color: var(--c-success, #6f8e5f); }
.sp-tag-fail { background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.10)); color: var(--c-terracotta, #c96442); }
.sp-tag-agent {
  font-size: 11px;
  color: var(--c-stone);
  background: var(--c-parchment, #f5f4ed);
  padding: 2px 8px; border-radius: 6px;
}

/* Metric bar */
.sp-metric { display: flex; flex-direction: column; gap: 5px; }
.sp-metric-numbers {
  font-size: 12px;
  color: var(--c-charcoal);
  display: flex; gap: 6px; align-items: baseline;
}
.sp-metric-value {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--c-near-black);
}
.sp-metric-vs { font-size: 11px; color: var(--c-stone); }
.sp-metric-bar {
  position: relative;
  height: 6px;
  background: var(--c-warm-sand, #e8e6dc);
  border-radius: 3px;
  overflow: visible;
}
.sp-metric-fill {
  position: absolute;
  top: 0; left: 0;
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}
.sp-metric-threshold {
  position: absolute;
  top: -2px; bottom: -2px;
  width: 2px;
  background: var(--c-charcoal);
  border-radius: 1px;
}

.sp-remediation {
  margin: 0;
  display: flex; align-items: flex-start; gap: 6px;
  padding: 8px 12px;
  background: var(--c-parchment, #f5f4ed);
  color: var(--c-charcoal);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.55;
}

.sp-raw {
  margin: 0;
  padding: 10px 12px;
  background: var(--c-parchment, #f5f4ed);
  border: 1px solid var(--c-border-warm);
  border-radius: 8px;
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 11px;
  line-height: 1.5;
  color: var(--c-charcoal);
  max-height: 280px;
  overflow: auto;
  white-space: pre-wrap;
}

@media (max-width: 720px) {
  .sp-meta { flex-wrap: wrap; }
  .sp-tabs { width: 100%; }
}
</style>
