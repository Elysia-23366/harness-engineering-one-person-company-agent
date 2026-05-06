<script setup>
/**
 * MemoryDashboard · 三库记忆面板(W2 D10)
 *
 * 三个 tab:
 *   - 事件库 Episodic     · 列表 + 衰减曲线 SVG
 *   - 角色认知 Persona    · 17 卡(perception_summary / traits / interaction / confidence)
 *   - 关系节点 Relationship · 17 卡(trust / familiarity / phase / collaboration_count)
 */
import { computed, onMounted, ref } from "vue";
import {
  Database,
  Heart,
  Library,
  RefreshCw,
  TrendingDown,
  UserCircle2,
  Users,
} from "lucide-vue-next";

import {
  fetchHarnessEvents,
  fetchHarnessPersonas,
  fetchHarnessRelationships,
} from "../../api";

const props = defineProps({
  agents: { type: Array, default: () => [] },
});

const events = ref([]);
const personas = ref([]);
const relationships = ref([]);
const loading = ref(false);
const error = ref("");
const selectedTab = ref("events");

const TABS = [
  { id: "events",        label: "事件库",   icon: Library,      brief: "Episodic · 衰减式 · 跨人物共享" },
  { id: "personas",      label: "角色认知", icon: UserCircle2,  brief: "Persona · 永久 · 累积印象,跨人物" },
  { id: "relationships", label: "关系节点", icon: Heart,        brief: "Relationship · 永久 · 每对独立" },
];

const agentNameById = computed(() => {
  const m = new Map();
  for (const a of props.agents) m.set(a.id, a.name);
  return m;
});

async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const [ev, pe, re] = await Promise.all([
      fetchHarnessEvents({ activeOnly: true, limit: 200 }),
      fetchHarnessPersonas(),
      fetchHarnessRelationships(),
    ]);
    events.value = ev;
    personas.value = pe;
    relationships.value = re;
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

// ---- 衰减曲线 ----
function daysSince(iso) {
  if (!iso) return 0;
  const ms = Date.now() - new Date(iso).getTime();
  return Math.max(0, ms / 86400000);
}

function decayedAt(score, decayRate, days) {
  return score * Math.exp(-decayRate * days);
}

// 取 active 事件中重要性 top 8 画衰减
const decayCurves = computed(() => {
  const top = [...events.value]
    .sort((a, b) => b.importance_score - a.importance_score)
    .slice(0, 8);
  // 在 0-30 天范围采样 31 个点
  return top.map((evt) => {
    const offsetDays = daysSince(evt.created_at);
    const points = [];
    for (let d = 0; d <= 30; d += 0.5) {
      const totalDays = offsetDays + d;
      const v = decayedAt(evt.importance_score, evt.decay_rate, totalDays);
      points.push({ d, v });
    }
    return {
      id: evt.id,
      content: evt.content.slice(0, 40) + (evt.content.length > 40 ? "…" : ""),
      emotion: evt.emotion_tag,
      decayRate: evt.decay_rate,
      score0: evt.importance_score,
      offsetDays,
      points,
    };
  });
});

// SVG 尺寸
const SVG_W = 560;
const SVG_H = 200;
const PAD_L = 36;
const PAD_R = 12;
const PAD_T = 16;
const PAD_B = 28;
const PLOT_W = SVG_W - PAD_L - PAD_R;
const PLOT_H = SVG_H - PAD_T - PAD_B;

function pointPath(points) {
  if (!points.length) return "";
  return points
    .map((p, i) => {
      const x = PAD_L + (p.d / 30) * PLOT_W;
      const y = PAD_T + (1 - Math.min(1, p.v / 9)) * PLOT_H;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function curveColor(emotion, idx) {
  // emotion 决定基础色调,idx 微调透明度让 8 条线区分得开
  const tag = (emotion || "neutral").toLowerCase();
  if (tag === "breakthrough") return `rgba(201, 100, 66, ${0.55 + (idx % 4) * 0.1})`;
  if (tag === "positive")     return `rgba(111, 142, 95, ${0.55 + (idx % 4) * 0.1})`;
  if (tag === "negative")     return `rgba(181, 51, 51, ${0.55 + (idx % 4) * 0.1})`;
  if (tag === "urgent")       return `rgba(184, 149, 110, ${0.55 + (idx % 4) * 0.1})`;
  return `rgba(135, 134, 127, ${0.55 + (idx % 4) * 0.1})`;
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

function emotionTagClass(tag) {
  return `mb-emotion mb-emotion-${tag || "neutral"}`;
}

function phaseLabel(p) {
  return ({
    cold_start: "冷启动",
    warming: "升温中",
    established: "稳定协作",
    deep: "深度信任",
  })[p] || p;
}

function phaseClass(p) {
  return ({
    cold_start:  "mb-phase-cold",
    warming:     "mb-phase-warm",
    established: "mb-phase-strong",
    deep:        "mb-phase-deep",
  })[p] || "mb-phase-cold";
}

onMounted(loadAll);
</script>

<template>
  <section class="memory-dashboard">
    <header class="mb-header">
      <div class="mb-title-block">
        <div class="mb-title-row">
          <Database :size="20" class="mb-title-icon" />
          <h2 class="mb-title">Memory · 三库记忆架构</h2>
        </div>
        <p class="mb-subtitle">
          角色漂移 OOC 工程解 · 事件库(衰减) ⊕ 角色认知(永久) ⊕ 关系节点(永久 · 每对独立)
        </p>
      </div>
      <div class="mb-meta">
        <div class="mb-stat">
          <span class="mb-stat-num">{{ events.length }}</span>
          <span class="mb-stat-label">事件</span>
        </div>
        <div class="mb-stat-divider"></div>
        <div class="mb-stat">
          <span class="mb-stat-num">{{ personas.length }}</span>
          <span class="mb-stat-label">认知</span>
        </div>
        <div class="mb-stat-divider"></div>
        <div class="mb-stat">
          <span class="mb-stat-num">{{ relationships.length }}</span>
          <span class="mb-stat-label">关系</span>
        </div>
        <button class="mb-btn-icon" title="刷新" @click="loadAll" :disabled="loading">
          <RefreshCw :size="16" :class="loading ? 'mb-spin' : ''" />
        </button>
      </div>
    </header>

    <div v-if="error" class="mb-error">{{ error }}</div>

    <!-- Tabs -->
    <nav class="mb-tabs">
      <button
        v-for="t in TABS"
        :key="t.id"
        class="mb-tab"
        :class="{ 'mb-tab-active': selectedTab === t.id }"
        @click="selectedTab = t.id"
      >
        <component :is="t.icon" :size="14" />
        <span>{{ t.label }}</span>
      </button>
    </nav>
    <p class="mb-tab-hint">{{ TABS.find(t => t.id === selectedTab)?.brief }}</p>

    <!-- ============ 事件库 ============ -->
    <div v-if="selectedTab === 'events'" class="mb-events">
      <!-- 衰减曲线图 -->
      <div class="mb-chart-card">
        <div class="mb-chart-head">
          <TrendingDown :size="14" />
          <h3>衰减曲线 · 重要性 top 8 事件</h3>
          <span class="mb-chart-note">x = 自此刻起未来天数 · y = 衰减后重要性(0-9)</span>
        </div>
        <svg :viewBox="`0 0 ${SVG_W} ${SVG_H}`" class="mb-chart">
          <!-- y 轴刻度线 -->
          <g stroke="var(--c-border-warm, #e8e6dc)" stroke-width="1" stroke-dasharray="2,3">
            <line v-for="y in [0, 3, 6, 9]" :key="y"
              :x1="PAD_L"
              :x2="SVG_W - PAD_R"
              :y1="PAD_T + (1 - y / 9) * PLOT_H"
              :y2="PAD_T + (1 - y / 9) * PLOT_H"
            />
          </g>
          <!-- y 轴 label -->
          <g fill="var(--c-stone, #87867f)" font-size="10" font-family="monospace">
            <text v-for="y in [0, 3, 6, 9]" :key="y"
              :x="PAD_L - 6"
              :y="PAD_T + (1 - y / 9) * PLOT_H + 3"
              text-anchor="end"
            >{{ y }}</text>
          </g>
          <!-- x 轴 label -->
          <g fill="var(--c-stone, #87867f)" font-size="10" font-family="monospace">
            <text v-for="d in [0, 7, 14, 21, 30]" :key="d"
              :x="PAD_L + (d / 30) * PLOT_W"
              :y="SVG_H - PAD_B + 14"
              text-anchor="middle"
            >{{ d === 0 ? "今天" : d + "d" }}</text>
          </g>
          <!-- 阈值 2.0 红线 -->
          <line
            :x1="PAD_L"
            :x2="SVG_W - PAD_R"
            :y1="PAD_T + (1 - 2 / 9) * PLOT_H"
            :y2="PAD_T + (1 - 2 / 9) * PLOT_H"
            stroke="var(--c-terracotta, #c96442)"
            stroke-width="1"
            stroke-dasharray="4,4"
            opacity="0.5"
          />
          <text
            :x="SVG_W - PAD_R - 4"
            :y="PAD_T + (1 - 2 / 9) * PLOT_H - 4"
            font-size="9"
            fill="var(--c-terracotta, #c96442)"
            text-anchor="end"
            font-family="monospace"
          >淘汰阈值 2.0</text>
          <!-- 衰减曲线 -->
          <g fill="none" stroke-width="1.6">
            <path
              v-for="(c, idx) in decayCurves"
              :key="c.id"
              :d="pointPath(c.points)"
              :stroke="curveColor(c.emotion, idx)"
            >
              <title>{{ c.content }} · imp0={{ c.score0 }} · decay={{ c.decayRate }}</title>
            </path>
          </g>
        </svg>
      </div>

      <!-- 事件列表 -->
      <div class="mb-events-list">
        <article v-for="e in events" :key="e.id" class="mb-event-card">
          <div class="mb-event-head">
            <span class="mb-event-imp">{{ e.importance_score.toFixed(1) }}</span>
            <span :class="emotionTagClass(e.emotion_tag)">{{ e.emotion_tag }}</span>
            <span class="mb-event-agent">{{ agentNameById.get(e.agent_id) || e.agent_id }}</span>
            <span class="mb-event-time">{{ fmtTime(e.created_at) }}</span>
            <span class="mb-event-decay">decay {{ e.decay_rate }} · access {{ e.access_count }}</span>
          </div>
          <p class="mb-event-content">{{ e.content }}</p>
          <div class="mb-event-bars">
            <div class="mb-event-bar"><label>情</label><div class="mb-bar"><div class="mb-bar-fill" :style="{width: (e.importance_emotion/3*100)+'%'}"></div></div><span>{{ e.importance_emotion.toFixed(1) }}</span></div>
            <div class="mb-event-bar"><label>新</label><div class="mb-bar"><div class="mb-bar-fill" :style="{width: (e.importance_novelty/3*100)+'%'}"></div></div><span>{{ e.importance_novelty.toFixed(1) }}</span></div>
            <div class="mb-event-bar"><label>关</label><div class="mb-bar"><div class="mb-bar-fill" :style="{width: (e.importance_relation/3*100)+'%'}"></div></div><span>{{ e.importance_relation.toFixed(1) }}</span></div>
          </div>
        </article>
        <div v-if="!loading && events.length === 0" class="mb-empty">没有 active 事件 · 跑一次 workflow 触发 auto_route_event</div>
      </div>
    </div>

    <!-- ============ 角色认知 ============ -->
    <div v-else-if="selectedTab === 'personas'" class="mb-cards-grid">
      <article v-for="p in personas" :key="p.id" class="mb-pcard">
        <header class="mb-pcard-head">
          <UserCircle2 :size="16" class="mb-pcard-icon" />
          <h4>{{ agentNameById.get(p.agent_id) || p.agent_id }}</h4>
          <span class="mb-pcard-count">交互 {{ p.interaction_count }}</span>
        </header>
        <p class="mb-pcard-summary" v-if="p.perception_summary">{{ p.perception_summary }}</p>
        <p class="mb-pcard-summary mb-pcard-empty" v-else>(等待累积印象)</p>
        <div class="mb-traits" v-if="p.trait_keywords?.length">
          <span class="mb-trait" v-for="kw in p.trait_keywords" :key="kw">{{ kw }}</span>
        </div>
        <footer class="mb-pcard-foot">
          <span class="mb-pcard-label">认知信度</span>
          <div class="mb-bar"><div class="mb-bar-fill" :style="{width: (p.confidence_level*100)+'%'}"></div></div>
          <span class="mb-pcard-value">{{ (p.confidence_level*100).toFixed(0) }}%</span>
        </footer>
      </article>
      <div v-if="!loading && personas.length === 0" class="mb-empty">尚无认知数据 · workflow 跑过后会自动建立</div>
    </div>

    <!-- ============ 关系节点 ============ -->
    <div v-else-if="selectedTab === 'relationships'" class="mb-cards-grid">
      <article v-for="r in relationships" :key="r.id" class="mb-rcard">
        <header class="mb-rcard-head">
          <Heart :size="16" class="mb-rcard-icon" />
          <h4>{{ agentNameById.get(r.agent_id) || r.agent_id }}</h4>
          <span :class="['mb-phase', phaseClass(r.current_phase)]">{{ phaseLabel(r.current_phase) }}</span>
        </header>
        <div class="mb-rcard-stats">
          <div class="mb-rstat">
            <label>信任度</label>
            <div class="mb-bar"><div class="mb-bar-fill mb-bar-trust" :style="{width: (r.trust_level*100)+'%'}"></div></div>
            <span>{{ (r.trust_level*100).toFixed(0) }}%</span>
          </div>
          <div class="mb-rstat">
            <label>熟悉度</label>
            <div class="mb-bar"><div class="mb-bar-fill mb-bar-fam" :style="{width: (r.familiarity*100)+'%'}"></div></div>
            <span>{{ (r.familiarity*100).toFixed(0) }}%</span>
          </div>
          <div class="mb-rstat">
            <label>对齐度</label>
            <div class="mb-bar"><div class="mb-bar-fill mb-bar-align" :style="{width: (r.alignment_score*100)+'%'}"></div></div>
            <span>{{ (r.alignment_score*100).toFixed(0) }}%</span>
          </div>
        </div>
        <footer class="mb-rcard-foot">
          <span>协作 {{ r.collaboration_count }} 次</span>
          <span v-if="r.milestones?.length">里程碑 {{ r.milestones.length }}</span>
        </footer>
      </article>
      <div v-if="!loading && relationships.length === 0" class="mb-empty">尚无关系数据</div>
    </div>
  </section>
</template>

<style scoped>
.memory-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
  color: var(--c-near-black, #141413);
}

/* Header */
.mb-header {
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
.mb-title-block { display: flex; flex-direction: column; gap: 6px; }
.mb-title-row { display: flex; align-items: center; gap: 10px; }
.mb-title-icon { color: var(--c-terracotta, #c96442); }
.mb-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 22px;
  font-weight: 600;
}
.mb-subtitle { margin: 0; color: var(--c-stone); font-size: 13px; line-height: 1.55; }
.mb-meta { display: flex; align-items: center; gap: 12px; }
.mb-stat { display: flex; flex-direction: column; align-items: center; min-width: 48px; }
.mb-stat-num { font-family: var(--ff-serif, "Fraunces", serif); font-size: 22px; font-weight: 600; line-height: 1; }
.mb-stat-label { font-size: 11px; color: var(--c-stone); margin-top: 2px; letter-spacing: 0.04em; }
.mb-stat-divider { width: 1px; height: 28px; background: var(--c-border-warm); }

.mb-btn-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  border: 1px solid var(--c-border-warm);
  border-radius: 8px;
  background: var(--c-ivory);
  color: var(--c-charcoal);
  cursor: pointer;
}
.mb-btn-icon:hover:not(:disabled) { background: var(--c-warm-sand); color: var(--c-near-black); }
.mb-btn-icon:disabled { opacity: 0.5; cursor: not-allowed; }
.mb-spin { animation: mb-spin 1s linear infinite; }
@keyframes mb-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }

.mb-error {
  padding: 10px 14px;
  background: rgba(181, 51, 51, 0.06);
  color: var(--c-error, #b53333);
  border: 1px solid rgba(181, 51, 51, 0.2);
  border-radius: 10px;
  font-size: 13px;
}

/* Tabs */
.mb-tabs {
  display: flex; gap: 4px; padding: 4px;
  background: var(--c-warm-sand);
  border-radius: 10px;
  width: max-content;
}
.mb-tab {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px;
  background: transparent;
  border: none; border-radius: 7px;
  cursor: pointer;
  color: var(--c-charcoal);
  font-size: 13px;
  font-family: inherit;
  transition: all 0.15s;
}
.mb-tab:hover { color: var(--c-near-black); }
.mb-tab-active {
  background: var(--c-ivory);
  color: var(--c-near-black);
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.06);
}
.mb-tab-hint { margin: 0; font-size: 12px; color: var(--c-stone); padding-left: 4px; }

/* Events tab */
.mb-events { display: flex; flex-direction: column; gap: 16px; }
.mb-chart-card {
  background: var(--c-ivory);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.mb-chart-head {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 8px;
  color: var(--c-charcoal);
}
.mb-chart-head h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--ff-serif, "Fraunces", serif);
}
.mb-chart-note { margin-left: auto; font-size: 11px; color: var(--c-stone); }
.mb-chart {
  width: 100%;
  height: auto;
  display: block;
}

.mb-events-list { display: flex; flex-direction: column; gap: 10px; }
.mb-event-card {
  background: var(--c-ivory);
  border: 1px solid var(--c-border);
  border-radius: 12px;
  padding: 12px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.mb-event-card:hover { border-color: var(--c-ring-warm); }
.mb-event-head {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  font-size: 11px;
}
.mb-event-imp {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 18px; font-weight: 600;
  color: var(--c-near-black);
  min-width: 28px;
}
.mb-emotion {
  display: inline-flex;
  padding: 2px 7px;
  border-radius: 5px;
  font-size: 10px;
  letter-spacing: 0.02em;
  font-family: var(--ff-mono, monospace);
}
.mb-emotion-breakthrough { background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.12)); color: var(--c-terracotta, #c96442); }
.mb-emotion-positive     { background: rgba(111, 142, 95, 0.14); color: var(--c-success, #6f8e5f); }
.mb-emotion-negative     { background: rgba(181, 51, 51, 0.10); color: var(--c-error, #b53333); }
.mb-emotion-urgent       { background: rgba(184, 149, 110, 0.16); color: var(--c-warning, #b8956e); }
.mb-emotion-neutral      { background: var(--c-warm-sand); color: var(--c-stone); }
.mb-event-agent { color: var(--c-charcoal); }
.mb-event-time { color: var(--c-stone); margin-left: auto; }
.mb-event-decay { color: var(--c-stone); font-family: var(--ff-mono, monospace); }
.mb-event-content {
  margin: 0;
  font-size: 13px;
  color: var(--c-near-black);
  line-height: 1.6;
}
.mb-event-bars { display: flex; gap: 12px; }
.mb-event-bar { display: flex; align-items: center; gap: 6px; flex: 1; font-size: 11px; color: var(--c-stone); }
.mb-event-bar label { width: 14px; }

.mb-bar {
  flex: 1;
  height: 5px;
  background: var(--c-warm-sand);
  border-radius: 3px;
  overflow: hidden;
}
.mb-bar-fill {
  height: 100%;
  background: var(--c-terracotta, #c96442);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.mb-bar-trust { background: var(--c-terracotta, #c96442); }
.mb-bar-fam   { background: var(--c-warning, #b8956e); }
.mb-bar-align { background: var(--c-success, #6f8e5f); }

/* Personas + Relationships grid */
.mb-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
}
.mb-pcard, .mb-rcard {
  background: var(--c-ivory);
  border: 1px solid var(--c-border);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.mb-pcard:hover, .mb-rcard:hover { border-color: var(--c-ring-warm); }
.mb-pcard-head, .mb-rcard-head {
  display: flex; align-items: center; gap: 8px;
}
.mb-pcard-icon, .mb-rcard-icon { color: var(--c-terracotta, #c96442); }
.mb-pcard-head h4, .mb-rcard-head h4 {
  margin: 0; flex: 1;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 14px;
  font-weight: 600;
}
.mb-pcard-count {
  font-size: 11px;
  color: var(--c-stone);
  background: var(--c-warm-sand);
  padding: 2px 8px;
  border-radius: 5px;
  font-family: var(--ff-mono, monospace);
}
.mb-pcard-summary {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--c-charcoal);
}
.mb-pcard-empty { color: var(--c-stone); font-style: italic; }
.mb-traits { display: flex; gap: 5px; flex-wrap: wrap; }
.mb-trait {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--c-parchment);
  border: 1px solid var(--c-border-warm);
  border-radius: 5px;
  color: var(--c-charcoal);
}
.mb-pcard-foot, .mb-rcard-foot {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px;
  color: var(--c-stone);
}
.mb-pcard-label { min-width: 60px; }
.mb-pcard-value { min-width: 40px; text-align: right; font-family: var(--ff-mono, monospace); }

.mb-rcard-stats { display: flex; flex-direction: column; gap: 6px; }
.mb-rstat { display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--c-stone); }
.mb-rstat label { min-width: 50px; }
.mb-rstat span { min-width: 36px; text-align: right; font-family: var(--ff-mono, monospace); color: var(--c-charcoal); }
.mb-rcard-foot { padding-top: 4px; border-top: 1px dashed var(--c-border-warm); display: flex; gap: 12px; }

.mb-phase {
  margin-left: auto;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 5px;
  letter-spacing: 0.02em;
}
.mb-phase-cold   { background: var(--c-warm-sand);                          color: var(--c-stone); }
.mb-phase-warm   { background: rgba(184, 149, 110, 0.15);                   color: var(--c-warning, #b8956e); }
.mb-phase-strong { background: rgba(111, 142, 95, 0.16);                    color: var(--c-success, #6f8e5f); }
.mb-phase-deep   { background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.14)); color: var(--c-terracotta, #c96442); }

.mb-empty {
  text-align: center;
  padding: 32px;
  color: var(--c-stone);
  background: var(--c-ivory);
  border: 1px dashed var(--c-border-warm);
  border-radius: 12px;
  grid-column: 1 / -1;
}

@media (max-width: 720px) {
  .mb-meta { flex-wrap: wrap; }
  .mb-cards-grid { grid-template-columns: 1fr; }
}
</style>
