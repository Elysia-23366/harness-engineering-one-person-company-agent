<script setup>
/**
 * DriftRadar · 人格稳定性雷达(W2 D11)
 *
 * 数据源:GET /api/harness/sensors?sensor_type=persona_drift
 *
 * 视觉:
 *   - 顶部雷达图 · 每个 agent 一根径向轴,值 = 最近一次 drift metric(0-1)
 *   - 下方每个 agent 一张卡:大数字当前 metric + 历史 N 次 mini sparkline
 *   - drift metric 含义:相似度(高 = 风格稳定 = 好)· 阈值 0.35
 */
import { computed, onMounted, ref } from "vue";
import {
  AlertTriangle,
  RefreshCw,
  TrendingUp,
} from "lucide-vue-next";

import { fetchHarnessSensors } from "../../api";

const props = defineProps({
  agents: { type: Array, default: () => [] },
});

const driftEvents = ref([]);
const loading = ref(false);
const error = ref("");

const agentNameById = computed(() => {
  const m = new Map();
  for (const a of props.agents) m.set(a.id, a.name);
  return m;
});

// 按 agent 分组,取最近 N 次
const byAgent = computed(() => {
  const m = new Map();
  for (const e of driftEvents.value) {
    if (!e.agent_id) continue;
    if (!m.has(e.agent_id)) m.set(e.agent_id, []);
    m.get(e.agent_id).push(e);
  }
  // 每组按时间倒序(API 已 DESC)
  const arr = [];
  for (const [agentId, list] of m) {
    arr.push({
      agentId,
      agentName: agentNameById.value.get(agentId) || agentId,
      latest: list[0],
      history: list.slice(0, 10).reverse(), // 时序老→新,给 sparkline 用
      avg: list.reduce((s, e) => s + e.metric_value, 0) / list.length,
      passRate: list.filter((e) => e.passed).length / list.length,
    });
  }
  // 按 latest metric 降序
  arr.sort((a, b) => b.latest.metric_value - a.latest.metric_value);
  return arr;
});

const stats = computed(() => {
  const total = driftEvents.value.length;
  const failed = driftEvents.value.filter((e) => !e.passed).length;
  const avg = total > 0 ? driftEvents.value.reduce((s, e) => s + e.metric_value, 0) / total : 0;
  return { total, failed, avg };
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    driftEvents.value = await fetchHarnessSensors({
      sensorType: "persona_drift",
      limit: 200,
    });
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

// ---- Radar SVG ----
const RADAR_SIZE = 360;
const RADAR_CX = RADAR_SIZE / 2;
const RADAR_CY = RADAR_SIZE / 2;
const RADAR_R = 130;
const THRESHOLD = 0.35;

const radarPolygons = computed(() => {
  const items = byAgent.value;
  if (items.length < 1) return null;
  // 至少 3 个轴才好看,不够就重复填到 3 个
  const axes = items.length >= 3 ? items : [...items, ...items, ...items].slice(0, Math.max(3, items.length));

  function polarPoint(value, idx, n) {
    const angle = -Math.PI / 2 + (idx / n) * 2 * Math.PI;
    const r = Math.max(0, Math.min(1, value)) * RADAR_R;
    return {
      x: RADAR_CX + Math.cos(angle) * r,
      y: RADAR_CY + Math.sin(angle) * r,
      ax: RADAR_CX + Math.cos(angle) * RADAR_R,
      ay: RADAR_CY + Math.sin(angle) * RADAR_R,
      labelX: RADAR_CX + Math.cos(angle) * (RADAR_R + 18),
      labelY: RADAR_CY + Math.sin(angle) * (RADAR_R + 18),
    };
  }

  const n = axes.length;
  const currentPts = axes.map((a, i) => polarPoint(a.latest.metric_value, i, n));
  const avgPts = axes.map((a, i) => polarPoint(a.avg, i, n));
  const thresholdPts = Array.from({ length: n }, (_, i) => polarPoint(THRESHOLD, i, n));

  const labels = axes.map((a, i) => {
    const p = polarPoint(1, i, n);
    return { x: p.labelX, y: p.labelY, text: a.agentName };
  });

  const toPath = (pts) => pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ") + " Z";

  return {
    axes: axes.map((a, i) => ({ ax: currentPts[i].ax, ay: currentPts[i].ay })),
    currentPath: toPath(currentPts),
    avgPath: toPath(avgPts),
    thresholdPath: toPath(thresholdPts),
    currentDots: currentPts,
    labels,
    n,
  };
});

// Sparkline 渲染
function sparklinePath(history, w = 80, h = 24) {
  if (history.length < 2) return "";
  const xs = history.map((_, i) => (i / (history.length - 1)) * w);
  const ys = history.map((e) => h - Math.max(0, Math.min(1, e.metric_value)) * h);
  return xs.map((x, i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");
}

function fmtPct(v) {
  return Math.round(v * 100) + "%";
}

function fmtNum(v) {
  return Math.round(v * 1000) / 1000;
}

onMounted(load);
</script>

<template>
  <section class="drift-radar">
    <header class="dr-header">
      <div class="dr-title-block">
        <div class="dr-title-row">
          <TrendingUp :size="20" class="dr-title-icon" />
          <h2 class="dr-title">Drift Radar · 人格稳定性</h2>
        </div>
        <p class="dr-subtitle">
          余弦相似度衡量当前输出与历史 5 条事件的风格距离 · 越高越稳 · 阈值 {{ THRESHOLD }}
        </p>
      </div>
      <div class="dr-meta">
        <div class="dr-stat">
          <span class="dr-stat-num">{{ stats.total }}</span>
          <span class="dr-stat-label">检测次数</span>
        </div>
        <div class="dr-stat-divider"></div>
        <div class="dr-stat">
          <span class="dr-stat-num dr-stat-fail">{{ stats.failed }}</span>
          <span class="dr-stat-label">漂移警报</span>
        </div>
        <div class="dr-stat-divider"></div>
        <div class="dr-stat">
          <span class="dr-stat-num">{{ fmtPct(stats.avg) }}</span>
          <span class="dr-stat-label">平均稳定度</span>
        </div>
        <button class="dr-btn-icon" title="刷新" @click="load" :disabled="loading">
          <RefreshCw :size="16" :class="loading ? 'dr-spin' : ''" />
        </button>
      </div>
    </header>

    <div v-if="error" class="dr-error">
      <AlertTriangle :size="14" /> {{ error }}
    </div>

    <div class="dr-body">
      <!-- 雷达 -->
      <div class="dr-radar-wrap">
        <div v-if="!radarPolygons" class="dr-empty">
          还没有 persona_drift 检测数据 · 跑一次 workflow 触发 sensor
        </div>
        <svg v-else :viewBox="`0 0 ${RADAR_SIZE} ${RADAR_SIZE}`" class="dr-radar">
          <!-- 同心圆 grid -->
          <g fill="none" stroke="var(--c-border-warm, #e8e6dc)" stroke-width="1">
            <circle :cx="RADAR_CX" :cy="RADAR_CY" :r="RADAR_R * 0.25" />
            <circle :cx="RADAR_CX" :cy="RADAR_CY" :r="RADAR_R * 0.5" />
            <circle :cx="RADAR_CX" :cy="RADAR_CY" :r="RADAR_R * 0.75" />
            <circle :cx="RADAR_CX" :cy="RADAR_CY" :r="RADAR_R" />
          </g>
          <!-- 轴线 -->
          <g stroke="var(--c-border-warm, #e8e6dc)" stroke-width="1">
            <line v-for="(a, i) in radarPolygons.axes" :key="i"
              :x1="RADAR_CX" :y1="RADAR_CY" :x2="a.ax" :y2="a.ay"
            />
          </g>
          <!-- 阈值多边形(虚线) -->
          <path
            :d="radarPolygons.thresholdPath"
            fill="none"
            stroke="var(--c-terracotta, #c96442)"
            stroke-width="1.2"
            stroke-dasharray="4,4"
            opacity="0.6"
          />
          <!-- 历史平均 多边形(填充) -->
          <path
            :d="radarPolygons.avgPath"
            fill="rgba(184, 149, 110, 0.15)"
            stroke="var(--c-warning, #b8956e)"
            stroke-width="1.4"
            stroke-dasharray="2,3"
          />
          <!-- 当前 多边形(主) -->
          <path
            :d="radarPolygons.currentPath"
            fill="rgba(201, 100, 66, 0.18)"
            stroke="var(--c-terracotta, #c96442)"
            stroke-width="2"
          />
          <!-- 当前 dots -->
          <g fill="var(--c-terracotta, #c96442)">
            <circle v-for="(p, i) in radarPolygons.currentDots" :key="i" :cx="p.x" :cy="p.y" r="3" />
          </g>
          <!-- agent 名 label -->
          <g font-size="11" fill="var(--c-charcoal, #4d4c48)" font-family="var(--ff-sans, sans-serif)">
            <text v-for="(l, i) in radarPolygons.labels" :key="i"
              :x="l.x" :y="l.y" text-anchor="middle" dy="3"
            >{{ l.text }}</text>
          </g>
        </svg>
        <!-- legend -->
        <div class="dr-legend">
          <span class="dr-legend-item"><span class="dr-legend-swatch dr-legend-current"></span>当前</span>
          <span class="dr-legend-item"><span class="dr-legend-swatch dr-legend-avg"></span>历史平均</span>
          <span class="dr-legend-item"><span class="dr-legend-swatch dr-legend-threshold"></span>阈值 {{ THRESHOLD }}</span>
        </div>
      </div>

      <!-- 各 agent 卡列 -->
      <div class="dr-agent-list">
        <article v-for="a in byAgent" :key="a.agentId" class="dr-agent-card"
          :class="{ 'dr-agent-fail': !a.latest.passed }">
          <header class="dr-agent-head">
            <h4>{{ a.agentName }}</h4>
            <span class="dr-agent-tag" :class="a.latest.passed ? 'dr-tag-pass' : 'dr-tag-fail'">
              {{ a.latest.passed ? "稳定" : "漂移警报" }}
            </span>
          </header>
          <div class="dr-agent-body">
            <div class="dr-agent-num">
              <span class="dr-num">{{ fmtNum(a.latest.metric_value) }}</span>
              <span class="dr-num-label">当前相似度</span>
            </div>
            <svg viewBox="0 0 80 24" class="dr-spark" v-if="a.history.length >= 2">
              <!-- threshold line -->
              <line x1="0" :y1="24 - THRESHOLD * 24" x2="80" :y2="24 - THRESHOLD * 24"
                stroke="var(--c-terracotta, #c96442)" stroke-width="0.5" stroke-dasharray="2,2" opacity="0.6" />
              <path :d="sparklinePath(a.history)" fill="none"
                stroke="var(--c-terracotta, #c96442)" stroke-width="1.5" />
              <g fill="var(--c-terracotta, #c96442)">
                <circle v-for="(h, i) in a.history" :key="i"
                  :cx="(i / Math.max(1, a.history.length - 1)) * 80"
                  :cy="24 - h.metric_value * 24"
                  r="1.5"
                />
              </g>
            </svg>
            <div v-else class="dr-spark-empty">仅 {{ a.history.length }} 个数据点</div>
          </div>
          <footer class="dr-agent-foot">
            <span>历史均值 {{ fmtNum(a.avg) }}</span>
            <span>·</span>
            <span>{{ a.history.length }} 次</span>
            <span>·</span>
            <span>通过率 {{ fmtPct(a.passRate) }}</span>
          </footer>
          <p v-if="a.latest.remediation" class="dr-remediation">
            {{ a.latest.remediation }}
          </p>
        </article>
        <div v-if="!loading && byAgent.length === 0" class="dr-empty">
          没有任何 agent 触发过 persona_drift sensor
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.drift-radar {
  display: flex; flex-direction: column; gap: 16px;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
  color: var(--c-near-black, #141413);
}

/* Header */
.dr-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 16px;
  padding: 22px 24px;
  background: var(--c-ivory, #faf9f5);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 16px;
  box-shadow: 0 0 0 1px var(--c-ring-warm, #d1cfc5) inset, 0 1px 2px rgba(20, 20, 19, 0.04);
}
.dr-title-block { display: flex; flex-direction: column; gap: 6px; }
.dr-title-row { display: flex; align-items: center; gap: 10px; }
.dr-title-icon { color: var(--c-terracotta, #c96442); }
.dr-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 22px;
  font-weight: 600;
}
.dr-subtitle { margin: 0; color: var(--c-stone); font-size: 13px; line-height: 1.55; }
.dr-meta { display: flex; align-items: center; gap: 12px; }
.dr-stat { display: flex; flex-direction: column; align-items: center; min-width: 56px; }
.dr-stat-num { font-family: var(--ff-serif, "Fraunces", serif); font-size: 22px; font-weight: 600; line-height: 1; }
.dr-stat-fail { color: var(--c-terracotta, #c96442); }
.dr-stat-label { font-size: 11px; color: var(--c-stone); margin-top: 2px; letter-spacing: 0.04em; }
.dr-stat-divider { width: 1px; height: 28px; background: var(--c-border-warm); }

.dr-btn-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  border: 1px solid var(--c-border-warm);
  border-radius: 8px;
  background: var(--c-ivory);
  color: var(--c-charcoal);
  cursor: pointer;
}
.dr-btn-icon:hover:not(:disabled) { background: var(--c-warm-sand); color: var(--c-near-black); }
.dr-btn-icon:disabled { opacity: 0.5; cursor: not-allowed; }
.dr-spin { animation: dr-spin 1s linear infinite; }
@keyframes dr-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }

.dr-error {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  background: rgba(181, 51, 51, 0.06);
  color: var(--c-error, #b53333);
  border: 1px solid rgba(181, 51, 51, 0.2);
  border-radius: 10px;
  font-size: 13px;
}

/* Body two-column */
.dr-body {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) minmax(300px, 1fr);
  gap: 16px;
}

.dr-radar-wrap {
  background: var(--c-ivory);
  border: 1px solid var(--c-border);
  border-radius: 14px;
  padding: 18px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.dr-radar { width: 100%; height: auto; max-width: 380px; }
.dr-legend { display: flex; gap: 14px; flex-wrap: wrap; padding-top: 4px; font-size: 11px; color: var(--c-stone); }
.dr-legend-item { display: inline-flex; align-items: center; gap: 5px; }
.dr-legend-swatch { width: 12px; height: 4px; border-radius: 2px; display: inline-block; }
.dr-legend-current { background: var(--c-terracotta, #c96442); }
.dr-legend-avg { background: var(--c-warning, #b8956e); }
.dr-legend-threshold { background: transparent; border-top: 1px dashed var(--c-terracotta, #c96442); }

/* Agent list (right column) */
.dr-agent-list {
  display: flex; flex-direction: column; gap: 10px;
}
.dr-agent-card {
  background: var(--c-ivory);
  border: 1px solid var(--c-border);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.dr-agent-card:hover { border-color: var(--c-ring-warm); }
.dr-agent-fail { border-left: 3px solid var(--c-terracotta, #c96442); }

.dr-agent-head { display: flex; align-items: center; gap: 8px; }
.dr-agent-head h4 {
  margin: 0; flex: 1;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 14px; font-weight: 600;
}
.dr-agent-tag {
  font-size: 11px; padding: 2px 8px; border-radius: 5px;
}
.dr-tag-pass { background: rgba(111, 142, 95, 0.14); color: var(--c-success, #6f8e5f); }
.dr-tag-fail { background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.10)); color: var(--c-terracotta, #c96442); }

.dr-agent-body { display: flex; align-items: center; gap: 14px; }
.dr-agent-num { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-width: 80px; }
.dr-num { font-family: var(--ff-serif, "Fraunces", serif); font-size: 24px; font-weight: 600; color: var(--c-near-black); }
.dr-num-label { font-size: 10px; color: var(--c-stone); letter-spacing: 0.04em; }
.dr-spark { flex: 1; height: 32px; }
.dr-spark-empty { flex: 1; font-size: 11px; color: var(--c-stone); }

.dr-agent-foot {
  font-size: 11px;
  color: var(--c-stone);
  display: flex; gap: 6px; flex-wrap: wrap;
}
.dr-remediation {
  margin: 0;
  padding: 8px 12px;
  background: var(--c-parchment, #f5f4ed);
  color: var(--c-charcoal);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.55;
}

.dr-empty {
  text-align: center;
  padding: 32px;
  color: var(--c-stone);
  background: var(--c-ivory);
  border: 1px dashed var(--c-border-warm);
  border-radius: 12px;
}

@media (max-width: 1080px) {
  .dr-body { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .dr-meta { flex-wrap: wrap; }
}
</style>
