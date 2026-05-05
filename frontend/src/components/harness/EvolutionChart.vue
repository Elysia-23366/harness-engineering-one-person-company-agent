<script setup>
/**
 * EvolutionChart · 命中率自进化可视化(W2 D13)
 *
 * 上方:命中率折线图 + 阈值线 · 时间序列(老→新)
 * 下方:自进化建议时间线 · importance_calibration 每条记录展开
 *
 * 数据源:
 *   GET /api/harness/sensors?sensor_type=recall_hit_rate
 *   GET /api/harness/sensors?sensor_type=importance_calibration
 */
import { computed, onMounted, ref } from "vue";
import {
  Activity,
  RefreshCw,
  Sparkles,
  TrendingUp,
  Wand2,
} from "lucide-vue-next";

import { fetchHarnessSensors, runEvolveThresholds } from "../../api";

const hitRateEvents = ref([]);
const calibrations = ref([]);
const loading = ref(false);
const error = ref("");
const evolving = ref(false);
const lastEvolveResult = ref(null);

// 时序老→新
const hitRateSeries = computed(() => {
  const arr = [...hitRateEvents.value];
  arr.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  return arr;
});

const stats = computed(() => {
  const arr = hitRateSeries.value;
  if (!arr.length) return { count: 0, avg: 0, latest: null, threshold: 0.5 };
  return {
    count: arr.length,
    avg: arr.reduce((s, e) => s + e.metric_value, 0) / arr.length,
    latest: arr[arr.length - 1],
    threshold: arr[arr.length - 1].threshold,
  };
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [hits, calibs] = await Promise.all([
      fetchHarnessSensors({ sensorType: "recall_hit_rate", limit: 200 }),
      fetchHarnessSensors({ sensorType: "importance_calibration", limit: 50 }),
    ]);
    hitRateEvents.value = hits;
    calibrations.value = calibs;
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function triggerEvolve() {
  evolving.value = true;
  lastEvolveResult.value = null;
  try {
    lastEvolveResult.value = await runEvolveThresholds({ sampleSize: 20 });
    await load();
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    evolving.value = false;
  }
}

// ---- SVG 折线图 ----
const W = 720;
const H = 220;
const PAD_L = 40;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 32;

const linePath = computed(() => {
  const arr = hitRateSeries.value;
  if (arr.length < 1) return { d: "", points: [], thresholdY: H - PAD_B };
  const minMs = arr.length > 1 ? new Date(arr[0].created_at).getTime() : 0;
  const maxMs = arr.length > 1 ? new Date(arr[arr.length - 1].created_at).getTime() : 1;
  const span = Math.max(1, maxMs - minMs);

  const points = arr.map((e, i) => {
    const x = arr.length === 1
      ? PAD_L + (W - PAD_L - PAD_R) / 2
      : PAD_L + ((new Date(e.created_at).getTime() - minMs) / span) * (W - PAD_L - PAD_R);
    const y = PAD_T + (1 - Math.max(0, Math.min(1, e.metric_value))) * (H - PAD_T - PAD_B);
    return { x, y, raw: e };
  });
  const d = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");
  const thresholdY = PAD_T + (1 - (arr[arr.length - 1].threshold || 0.5)) * (H - PAD_T - PAD_B);
  return { d, points, thresholdY };
});

function fmtPct(v) {
  if (v === null || v === undefined) return "—";
  return Math.round(v * 100) + "%";
}

function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const ms = Date.now() - d.getTime();
  if (ms < 60000) return "刚刚";
  if (ms < 3600000) return `${Math.floor(ms / 60000)} 分钟前`;
  if (ms < 86400000) return `${Math.floor(ms / 3600000)} 小时前`;
  return d.toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

onMounted(load);
</script>

<template>
  <section class="evo-chart">
    <header class="ev-header">
      <div class="ev-title-block">
        <div class="ev-title-row">
          <TrendingUp :size="20" class="ev-title-icon" />
          <h2 class="ev-title">命中率 · 自进化时间线</h2>
        </div>
        <p class="ev-subtitle">
          系统每跑一次 workflow,recall_hit_rate sensor 记一笔 ·
          低于阈值时 evolve_thresholds 自动生成修正建议
        </p>
      </div>
      <div class="ev-meta">
        <div class="ev-stat">
          <span class="ev-stat-num">{{ fmtPct(stats.avg) }}</span>
          <span class="ev-stat-label">平均命中率</span>
        </div>
        <div class="ev-stat-divider"></div>
        <div class="ev-stat">
          <span class="ev-stat-num">{{ stats.count }}</span>
          <span class="ev-stat-label">采样次数</span>
        </div>
        <div class="ev-stat-divider"></div>
        <div class="ev-stat">
          <span class="ev-stat-num">{{ calibrations.length }}</span>
          <span class="ev-stat-label">建议数</span>
        </div>
        <button class="ev-btn-icon" title="刷新" @click="load" :disabled="loading">
          <RefreshCw :size="16" :class="loading ? 'ev-spin' : ''" />
        </button>
        <button class="ev-btn-primary" @click="triggerEvolve" :disabled="evolving">
          <Wand2 :size="16" />
          <span>{{ evolving ? "诊断中..." : "立刻诊断" }}</span>
        </button>
      </div>
    </header>

    <div v-if="lastEvolveResult" class="ev-evolve-banner" :class="{ 'ev-evolve-passed': !lastEvolveResult.evolved }">
      <Sparkles :size="14" />
      <span v-if="lastEvolveResult.evolved">
        诊断完成 · 触发 {{ lastEvolveResult.actions.length }} 条修正建议(已落库)
      </span>
      <span v-else>诊断完成 · 当前指标全部健康,无需调整</span>
    </div>

    <div v-if="error" class="ev-error">{{ error }}</div>

    <!-- 折线图 -->
    <div class="ev-chart-card">
      <div class="ev-chart-head">
        <Activity :size="14" />
        <h3>recall_hit_rate · 时间序列</h3>
        <span class="ev-chart-note" v-if="stats.latest">
          最近 {{ fmtTime(stats.latest.created_at) }} · 阈值 {{ fmtPct(stats.threshold) }}
        </span>
      </div>
      <svg :viewBox="`0 0 ${W} ${H}`" class="ev-chart" v-if="hitRateSeries.length > 0">
        <!-- y 轴 grid -->
        <g stroke="var(--c-border-warm, #e8e6dc)" stroke-width="1" stroke-dasharray="2,3">
          <line v-for="y in [0, 0.25, 0.5, 0.75, 1]" :key="y"
            :x1="PAD_L"
            :x2="W - PAD_R"
            :y1="PAD_T + (1 - y) * (H - PAD_T - PAD_B)"
            :y2="PAD_T + (1 - y) * (H - PAD_T - PAD_B)"
          />
        </g>
        <!-- y label -->
        <g fill="var(--c-stone, #87867f)" font-size="10" font-family="monospace">
          <text v-for="y in [0, 0.5, 1]" :key="y"
            :x="PAD_L - 6"
            :y="PAD_T + (1 - y) * (H - PAD_T - PAD_B) + 3"
            text-anchor="end"
          >{{ fmtPct(y) }}</text>
        </g>
        <!-- threshold dashed -->
        <line
          :x1="PAD_L"
          :x2="W - PAD_R"
          :y1="linePath.thresholdY"
          :y2="linePath.thresholdY"
          stroke="var(--c-terracotta, #c96442)"
          stroke-width="1"
          stroke-dasharray="4,4"
          opacity="0.6"
        />
        <text
          :x="W - PAD_R - 4"
          :y="linePath.thresholdY - 4"
          font-size="9"
          fill="var(--c-terracotta, #c96442)"
          text-anchor="end"
          font-family="monospace"
        >阈值 {{ fmtPct(stats.threshold) }}</text>
        <!-- area fill under curve -->
        <path
          v-if="linePath.points.length > 1"
          :d="`${linePath.d} L${linePath.points[linePath.points.length - 1].x},${H - PAD_B} L${linePath.points[0].x},${H - PAD_B} Z`"
          fill="rgba(201, 100, 66, 0.08)"
        />
        <!-- main line -->
        <path
          :d="linePath.d"
          fill="none"
          stroke="var(--c-terracotta, #c96442)"
          stroke-width="2"
        />
        <!-- dots · 通过=success 警报=terracotta -->
        <g>
          <circle
            v-for="(p, i) in linePath.points"
            :key="i"
            :cx="p.x"
            :cy="p.y"
            r="4"
            :fill="p.raw.passed ? 'var(--c-success, #6f8e5f)' : 'var(--c-terracotta, #c96442)'"
            :stroke="'var(--c-ivory, #faf9f5)'"
            stroke-width="2"
          >
            <title>{{ fmtPct(p.raw.metric_value) }} · {{ fmtTime(p.raw.created_at) }} · {{ p.raw.passed ? "通过" : "警报" }}</title>
          </circle>
        </g>
      </svg>
      <div v-else class="ev-chart-empty">还没有 recall_hit_rate 采样 · 跑一次 workflow 触发</div>
    </div>

    <!-- 自进化建议时间线 -->
    <div class="ev-calib">
      <div class="ev-calib-head">
        <Sparkles :size="14" />
        <h3>自进化建议时间线 · importance_calibration</h3>
      </div>
      <div class="ev-calib-list">
        <article v-for="c in calibrations" :key="c.id" class="ev-calib-card">
          <header class="ev-calib-card-head">
            <span class="ev-calib-tag">触发 {{ Math.round(c.metric_value) }} 条建议</span>
            <time class="ev-calib-time">{{ fmtTime(c.created_at) }}</time>
          </header>
          <div v-if="c.raw_data?.actions?.length" class="ev-calib-actions">
            <div v-for="a in c.raw_data.actions" :key="a.trigger" class="ev-calib-action">
              <div class="ev-calib-line">
                <code class="ev-calib-trigger">{{ a.trigger }}</code>
                <span class="ev-calib-metric">
                  实测 {{ a.metric_observed }} &lt; 目标 {{ a.target }}
                </span>
              </div>
              <p class="ev-calib-suggestion">→ {{ a.suggestion }}</p>
              <span class="ev-calib-scope" v-if="a.scope">作用域 · {{ a.scope }}</span>
            </div>
          </div>
          <div v-if="c.raw_data?.by_sensor_type" class="ev-calib-summary">
            <span v-for="(info, t) in c.raw_data.by_sensor_type" :key="t" class="ev-calib-summary-cell">
              <code>{{ t }}</code> 均值 {{ Math.round(info.avg_metric * 1000) / 1000 }} · 通过 {{ info.pass_count }}/{{ info.sample_size }}
            </span>
          </div>
        </article>
        <div v-if="!loading && calibrations.length === 0" class="ev-empty">
          还没有任何自进化建议落库 · 点击"立刻诊断"或继续跑 workflow 累积数据
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.evo-chart {
  display: flex; flex-direction: column; gap: 16px;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
  color: var(--c-near-black, #141413);
}

.ev-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 16px;
  padding: 22px 24px;
  background: var(--c-ivory, #faf9f5);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 16px;
  box-shadow: 0 0 0 1px var(--c-ring-warm, #d1cfc5) inset, 0 1px 2px rgba(20, 20, 19, 0.04);
}
.ev-title-block { display: flex; flex-direction: column; gap: 6px; }
.ev-title-row { display: flex; align-items: center; gap: 10px; }
.ev-title-icon { color: var(--c-terracotta, #c96442); }
.ev-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 22px;
  font-weight: 600;
}
.ev-subtitle { margin: 0; color: var(--c-stone); font-size: 13px; line-height: 1.55; }
.ev-meta { display: flex; align-items: center; gap: 12px; }
.ev-stat { display: flex; flex-direction: column; align-items: center; min-width: 56px; }
.ev-stat-num { font-family: var(--ff-serif, "Fraunces", serif); font-size: 22px; font-weight: 600; line-height: 1; }
.ev-stat-label { font-size: 11px; color: var(--c-stone); margin-top: 2px; letter-spacing: 0.04em; }
.ev-stat-divider { width: 1px; height: 28px; background: var(--c-border-warm); }

.ev-btn-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  border: 1px solid var(--c-border-warm);
  border-radius: 8px;
  background: var(--c-ivory);
  color: var(--c-charcoal);
  cursor: pointer;
}
.ev-btn-icon:hover:not(:disabled) { background: var(--c-warm-sand); color: var(--c-near-black); }
.ev-btn-icon:disabled { opacity: 0.5; cursor: not-allowed; }
.ev-btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--c-terracotta, #c96442);
  color: var(--c-ivory);
  border: none; border-radius: 10px;
  font-size: 13px; font-weight: 500;
  cursor: pointer;
}
.ev-btn-primary:hover:not(:disabled) { background: var(--c-coral, #d97757); }
.ev-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.ev-spin { animation: ev-spin 1s linear infinite; }
@keyframes ev-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }

.ev-evolve-banner {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.08));
  color: var(--c-terracotta, #c96442);
  border: 1px solid var(--c-terracotta-glow, rgba(201, 100, 66, 0.18));
  border-radius: 10px;
  font-size: 13px;
}
.ev-evolve-banner.ev-evolve-passed {
  background: rgba(111, 142, 95, 0.08);
  border-color: rgba(111, 142, 95, 0.18);
  color: var(--c-success, #6f8e5f);
}

.ev-error {
  padding: 10px 14px;
  background: rgba(181, 51, 51, 0.06);
  color: var(--c-error, #b53333);
  border: 1px solid rgba(181, 51, 51, 0.2);
  border-radius: 10px;
  font-size: 13px;
}

/* Chart */
.ev-chart-card {
  background: var(--c-ivory);
  border: 1px solid var(--c-border);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.ev-chart-head {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 8px;
  color: var(--c-charcoal);
}
.ev-chart-head h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--ff-serif, "Fraunces", serif);
}
.ev-chart-note { margin-left: auto; font-size: 11px; color: var(--c-stone); }
.ev-chart { width: 100%; height: auto; display: block; }
.ev-chart-empty {
  text-align: center;
  padding: 50px;
  color: var(--c-stone);
  font-size: 13px;
}

/* Calibration timeline */
.ev-calib {
  background: var(--c-ivory);
  border: 1px solid var(--c-border);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.ev-calib-head {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px;
  color: var(--c-charcoal);
}
.ev-calib-head h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--ff-serif, "Fraunces", serif);
}
.ev-calib-list { display: flex; flex-direction: column; gap: 10px; }
.ev-calib-card {
  background: var(--c-parchment, #f5f4ed);
  border: 1px solid var(--c-border-warm);
  border-radius: 10px;
  padding: 12px 14px;
  display: flex; flex-direction: column; gap: 8px;
}
.ev-calib-card-head { display: flex; align-items: center; gap: 8px; }
.ev-calib-tag {
  display: inline-flex;
  font-size: 11px;
  padding: 2px 8px;
  background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.10));
  color: var(--c-terracotta, #c96442);
  border-radius: 5px;
}
.ev-calib-time { margin-left: auto; font-size: 11px; color: var(--c-stone); font-family: var(--ff-mono, monospace); }
.ev-calib-actions { display: flex; flex-direction: column; gap: 8px; }
.ev-calib-action {
  padding: 10px 12px;
  background: var(--c-ivory);
  border: 1px solid var(--c-border-warm);
  border-radius: 8px;
  display: flex; flex-direction: column; gap: 4px;
}
.ev-calib-line { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.ev-calib-trigger {
  font-family: var(--ff-mono, monospace);
  font-size: 11px;
  background: var(--c-warm-sand);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--c-charcoal);
}
.ev-calib-metric { font-size: 11px; color: var(--c-stone); }
.ev-calib-suggestion { margin: 0; font-size: 13px; color: var(--c-near-black); line-height: 1.55; }
.ev-calib-scope { font-size: 11px; color: var(--c-stone); font-family: var(--ff-mono, monospace); }
.ev-calib-summary {
  display: flex; gap: 6px; flex-wrap: wrap;
  font-size: 11px; color: var(--c-stone);
  padding-top: 6px; border-top: 1px dashed var(--c-border-warm);
}
.ev-calib-summary-cell {
  background: var(--c-warm-sand);
  padding: 2px 8px;
  border-radius: 5px;
}
.ev-calib-summary-cell code { font-family: var(--ff-mono, monospace); margin-right: 4px; }

.ev-empty {
  text-align: center;
  padding: 28px;
  color: var(--c-stone);
}

@media (max-width: 720px) {
  .ev-meta { flex-wrap: wrap; }
}
</style>
