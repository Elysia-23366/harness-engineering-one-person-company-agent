<script setup>
/**
 * GuidesPanel · 武艺《Harness Engineering》前馈控制面板(W2 D8)
 *
 * 设计意图:让 CEO 直接看到/编辑 17 岗位的"前馈规则",视觉沿用 Claude.ai 暖米白调性。
 * 数据源:GET/POST/PUT/DELETE /api/harness/guides
 * 规则按 agent 分组展示:全局规则 + 各岗位专属规则。
 */
import { computed, onMounted, ref, watch } from "vue";
import {
  AlertTriangle,
  CheckCircle2,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Shield,
  ShieldAlert,
  Trash2,
  X,
} from "lucide-vue-next";

import {
  createGuide,
  deleteGuide,
  fetchGuides,
  updateGuide,
} from "../../api";

const props = defineProps({
  agents: { type: Array, default: () => [] },
});

const guides = ref([]);
const loading = ref(false);
const error = ref("");
const editingId = ref("");
const isCreating = ref(false);

// 表单
const form = ref(emptyForm());

function emptyForm() {
  return {
    agent_id: "",   // 空字符串 = 全局
    rule_type: "output_schema",
    rule_name: "",
    rule_content: "",
    severity: "warn",
    is_active: true,
  };
}

const RULE_TYPES = [
  { value: "output_schema",       label: "output_schema · 字段/关键词必须出现" },
  { value: "forbidden_topic",     label: "forbidden_topic · 禁词" },
  { value: "tone_constraint",     label: "tone_constraint · 语气约束" },
  { value: "capability_boundary", label: "capability_boundary · 能力边界" },
  { value: "authority_min",       label: "authority_min · 最小权威级别" },
];

const agentNameById = computed(() => {
  const m = new Map();
  for (const a of props.agents) m.set(a.id, a.name);
  return m;
});

const grouped = computed(() => {
  const groups = new Map();
  groups.set("__global__", { label: "🌐 全局规则(对所有岗位生效)", items: [] });
  for (const g of guides.value) {
    if (!g.agent_id) {
      groups.get("__global__").items.push(g);
    } else {
      const key = g.agent_id;
      if (!groups.has(key)) {
        const name = agentNameById.value.get(key) || key;
        groups.set(key, { label: `👤 ${name}(本岗位专属)`, items: [] });
      }
      groups.get(key).items.push(g);
    }
  }
  // 全局排首位
  const ordered = [];
  if (groups.has("__global__")) ordered.push(["__global__", groups.get("__global__")]);
  for (const [k, v] of groups) if (k !== "__global__") ordered.push([k, v]);
  return ordered;
});

const totalActive = computed(() => guides.value.filter((g) => g.is_active).length);
const totalAll = computed(() => guides.value.length);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    guides.value = await fetchGuides({ activeOnly: false });
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

function startCreate() {
  isCreating.value = true;
  editingId.value = "";
  form.value = emptyForm();
}

function startEdit(g) {
  isCreating.value = false;
  editingId.value = g.id;
  form.value = {
    agent_id: g.agent_id || "",
    rule_type: g.rule_type,
    rule_name: g.rule_name,
    rule_content: g.rule_content,
    severity: g.severity,
    is_active: g.is_active,
  };
}

function cancelForm() {
  isCreating.value = false;
  editingId.value = "";
  form.value = emptyForm();
}

async function submitForm() {
  if (!form.value.rule_name.trim() || !form.value.rule_content.trim()) {
    error.value = "rule_name / rule_content 都要填";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    const payload = {
      agent_id: form.value.agent_id || null,
      rule_type: form.value.rule_type,
      rule_name: form.value.rule_name.trim(),
      rule_content: form.value.rule_content.trim(),
      severity: form.value.severity,
      is_active: form.value.is_active,
    };
    if (editingId.value) {
      // 后端 update 不接受 agent_id / rule_type 切换,只允许改 name/content/severity/is_active
      await updateGuide(editingId.value, {
        rule_name: payload.rule_name,
        rule_content: payload.rule_content,
        severity: payload.severity,
        is_active: payload.is_active,
      });
    } else {
      await createGuide(payload);
    }
    cancelForm();
    await load();
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function toggleActive(g) {
  try {
    await updateGuide(g.id, { is_active: !g.is_active });
    await load();
  } catch (e) {
    error.value = e.message || String(e);
  }
}

async function removeGuide(g) {
  if (!confirm(`删除规则「${g.rule_name}」?`)) return;
  try {
    await deleteGuide(g.id);
    await load();
  } catch (e) {
    error.value = e.message || String(e);
  }
}

function severityColor(severity) {
  return severity === "block" ? "block" : "warn";
}

function ruleTypeLabel(t) {
  return RULE_TYPES.find((it) => it.value === t)?.label.split(" · ")[0] || t;
}

onMounted(load);
</script>

<template>
  <section class="guides-panel">
    <!-- 顶部 -->
    <header class="gp-header">
      <div class="gp-title-block">
        <div class="gp-title-row">
          <Shield :size="20" class="gp-title-icon" />
          <h2 class="gp-title">Guides · 前馈控制</h2>
        </div>
        <p class="gp-subtitle">
          行动之前的护栏 · 设规则、边界、能干啥不能干啥
        </p>
      </div>
      <div class="gp-meta">
        <div class="gp-stat">
          <span class="gp-stat-num">{{ totalActive }}</span>
          <span class="gp-stat-label">激活</span>
        </div>
        <div class="gp-stat-divider"></div>
        <div class="gp-stat">
          <span class="gp-stat-num">{{ totalAll }}</span>
          <span class="gp-stat-label">总数</span>
        </div>
        <button class="gp-btn-icon" :title="'刷新'" @click="load" :disabled="loading">
          <RefreshCw :size="16" :class="loading ? 'gp-spin' : ''" />
        </button>
        <button class="gp-btn-primary" @click="startCreate" v-if="!isCreating && !editingId">
          <Plus :size="16" />
          <span>新增规则</span>
        </button>
      </div>
    </header>

    <!-- 错误提示 -->
    <div v-if="error" class="gp-error">
      <AlertTriangle :size="14" /> {{ error }}
    </div>

    <!-- 编辑 / 新建表单 -->
    <div v-if="isCreating || editingId" class="gp-form">
      <div class="gp-form-title">
        {{ editingId ? "编辑规则" : "新建规则" }}
      </div>
      <div class="gp-form-grid">
        <label class="gp-field">
          <span class="gp-label">作用范围</span>
          <select v-model="form.agent_id" :disabled="!!editingId" class="gp-input">
            <option value="">🌐 全局(所有岗位)</option>
            <option v-for="a in agents" :key="a.id" :value="a.id">
              👤 {{ a.name }}
            </option>
          </select>
        </label>

        <label class="gp-field">
          <span class="gp-label">类型</span>
          <select v-model="form.rule_type" :disabled="!!editingId" class="gp-input">
            <option v-for="t in RULE_TYPES" :key="t.value" :value="t.value">
              {{ t.label }}
            </option>
          </select>
        </label>

        <label class="gp-field">
          <span class="gp-label">严重度</span>
          <select v-model="form.severity" class="gp-input">
            <option value="warn">warn · 警告但可继续</option>
            <option value="block">block · 不通过则 stop-the-line</option>
          </select>
        </label>

        <label class="gp-field gp-field-toggle">
          <span class="gp-label">激活</span>
          <input type="checkbox" v-model="form.is_active" />
          <span class="gp-toggle-text">{{ form.is_active ? "已启用" : "已停用" }}</span>
        </label>

        <label class="gp-field gp-field-full">
          <span class="gp-label">规则名称</span>
          <input v-model="form.rule_name" placeholder="给 CEO 看的名字" class="gp-input" />
        </label>

        <label class="gp-field gp-field-full">
          <span class="gp-label">规则内容</span>
          <textarea
            v-model="form.rule_content"
            placeholder='JSON 或自然语言。例如:{"required_fields":["北极星","JTBD"],"min_count":2}'
            class="gp-textarea"
            rows="4"
          />
        </label>
      </div>
      <div class="gp-form-actions">
        <button class="gp-btn-secondary" @click="cancelForm">
          <X :size="14" /> 取消
        </button>
        <button class="gp-btn-primary" @click="submitForm" :disabled="loading">
          <Save :size="14" /> {{ editingId ? "保存" : "新建" }}
        </button>
      </div>
    </div>

    <!-- 规则列表(按 agent 分组) -->
    <div class="gp-groups">
      <div v-if="!loading && guides.length === 0" class="gp-empty">
        还没有任何规则 · 点右上角"新增规则"开始
      </div>

      <div v-for="[key, group] in grouped" :key="key" class="gp-group">
        <div class="gp-group-title">{{ group.label }}</div>
        <div class="gp-cards">
          <article
            v-for="g in group.items"
            :key="g.id"
            class="gp-card"
            :class="{
              'gp-card-inactive': !g.is_active,
              'gp-card-block': g.severity === 'block',
            }"
          >
            <div class="gp-card-head">
              <div class="gp-card-titles">
                <h3 class="gp-card-name">{{ g.rule_name }}</h3>
                <div class="gp-card-tags">
                  <span class="gp-tag gp-tag-type">{{ ruleTypeLabel(g.rule_type) }}</span>
                  <span class="gp-tag" :class="`gp-tag-${severityColor(g.severity)}`">
                    <ShieldAlert v-if="g.severity === 'block'" :size="11" />
                    <CheckCircle2 v-else :size="11" />
                    {{ g.severity }}
                  </span>
                  <span v-if="!g.is_active" class="gp-tag gp-tag-mute">已停用</span>
                </div>
              </div>
              <div class="gp-card-actions">
                <button class="gp-btn-icon" :title="g.is_active ? '停用' : '启用'" @click="toggleActive(g)">
                  <CheckCircle2 v-if="g.is_active" :size="14" />
                  <X v-else :size="14" />
                </button>
                <button class="gp-btn-icon" title="编辑" @click="startEdit(g)">
                  <Pencil :size="14" />
                </button>
                <button class="gp-btn-icon gp-btn-danger" title="删除" @click="removeGuide(g)">
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
            <pre class="gp-card-body">{{ g.rule_content }}</pre>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.guides-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
  color: var(--c-near-black, #141413);
}

/* ---------- Header ---------- */
.gp-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px;
  background: var(--c-ivory, #faf9f5);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 16px;
  box-shadow: 0 0 0 1px var(--c-ring-warm, #d1cfc5) inset, 0 1px 2px rgba(20, 20, 19, 0.04);
}
.gp-title-block { display: flex; flex-direction: column; gap: 6px; }
.gp-title-row { display: flex; align-items: center; gap: 10px; }
.gp-title-icon { color: var(--c-terracotta, #c96442); }
.gp-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.gp-subtitle {
  margin: 0;
  color: var(--c-stone, #87867f);
  font-size: 13px;
  line-height: 1.55;
}
.gp-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}
.gp-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}
.gp-stat-num {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 22px;
  font-weight: 600;
  color: var(--c-near-black);
  line-height: 1;
}
.gp-stat-label {
  font-size: 11px;
  color: var(--c-stone);
  margin-top: 2px;
  letter-spacing: 0.04em;
}
.gp-stat-divider {
  width: 1px;
  height: 28px;
  background: var(--c-border-warm, #e8e6dc);
}

/* ---------- Buttons ---------- */
.gp-btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--c-border-warm, #e8e6dc);
  border-radius: 8px;
  background: var(--c-ivory);
  color: var(--c-charcoal, #4d4c48);
  cursor: pointer;
  transition: all 0.15s ease;
}
.gp-btn-icon:hover:not(:disabled) {
  background: var(--c-warm-sand, #e8e6dc);
  color: var(--c-near-black);
}
.gp-btn-icon:disabled { opacity: 0.5; cursor: not-allowed; }
.gp-btn-danger:hover:not(:disabled) {
  background: rgba(181, 51, 51, 0.08);
  color: var(--c-error, #b53333);
  border-color: rgba(181, 51, 51, 0.3);
}
.gp-btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--c-terracotta, #c96442);
  color: var(--c-ivory, #faf9f5);
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}
.gp-btn-primary:hover:not(:disabled) { background: var(--c-coral, #d97757); }
.gp-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.gp-btn-secondary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--c-ivory);
  color: var(--c-charcoal);
  border: 1px solid var(--c-border-warm, #e8e6dc);
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
}
.gp-btn-secondary:hover { background: var(--c-warm-sand); }

.gp-spin { animation: gp-spin 1s linear infinite; }
@keyframes gp-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }

/* ---------- Error ---------- */
.gp-error {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  background: rgba(181, 51, 51, 0.06);
  color: var(--c-error, #b53333);
  border: 1px solid rgba(181, 51, 51, 0.2);
  border-radius: 10px;
  font-size: 13px;
}

/* ---------- Form ---------- */
.gp-form {
  background: var(--c-ivory);
  border: 1px solid var(--c-ring-warm, #d1cfc5);
  border-radius: 14px;
  padding: 18px 22px;
  box-shadow: 0 0 0 4px var(--c-terracotta-soft, rgba(201, 100, 66, 0.08));
}
.gp-form-title {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 14px;
  color: var(--c-near-black);
}
.gp-form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 18px;
}
.gp-field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.gp-field-full { grid-column: 1 / -1; }
.gp-field-toggle { flex-direction: row; align-items: center; gap: 10px; }
.gp-field-toggle .gp-label { min-width: 56px; }
.gp-toggle-text { font-size: 13px; color: var(--c-charcoal); }
.gp-label {
  font-size: 12px;
  color: var(--c-stone);
  letter-spacing: 0.02em;
}
.gp-input, .gp-textarea {
  padding: 8px 12px;
  background: var(--c-white, #fff);
  color: var(--c-near-black);
  border: 1px solid var(--c-border-warm, #e8e6dc);
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.gp-input:focus, .gp-textarea:focus {
  border-color: var(--c-terracotta);
  box-shadow: 0 0 0 3px var(--c-terracotta-soft, rgba(201, 100, 66, 0.12));
}
.gp-textarea {
  resize: vertical;
  font-family: var(--ff-mono, "Source Code Pro", ui-monospace, monospace);
  font-size: 12px;
  line-height: 1.5;
}
.gp-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

/* ---------- Groups & Cards ---------- */
.gp-groups { display: flex; flex-direction: column; gap: 24px; }
.gp-empty {
  text-align: center;
  padding: 40px;
  color: var(--c-stone);
  background: var(--c-ivory);
  border: 1px dashed var(--c-border-warm);
  border-radius: 14px;
}
.gp-group-title {
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 14px;
  font-weight: 600;
  color: var(--c-charcoal);
  margin-bottom: 10px;
  padding-left: 4px;
}
.gp-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 12px;
}
.gp-card {
  background: var(--c-ivory);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all 0.18s ease;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.03);
}
.gp-card:hover {
  border-color: var(--c-ring-warm, #d1cfc5);
  box-shadow: 0 4px 12px rgba(20, 20, 19, 0.06);
  transform: translateY(-1px);
}
.gp-card-inactive { opacity: 0.55; }
.gp-card-block {
  border-left: 3px solid var(--c-terracotta);
}
.gp-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.gp-card-titles { display: flex; flex-direction: column; gap: 6px; min-width: 0; flex: 1; }
.gp-card-name {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--c-near-black);
  font-family: var(--ff-serif, "Fraunces", serif);
}
.gp-card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.gp-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.02em;
  background: var(--c-warm-sand);
  color: var(--c-charcoal);
}
.gp-tag-type {
  background: var(--c-warm-sand);
  color: var(--c-olive, #5e5d59);
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 10px;
}
.gp-tag-warn { background: rgba(184, 149, 110, 0.15); color: var(--c-warning, #b8956e); }
.gp-tag-block {
  background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.10));
  color: var(--c-terracotta, #c96442);
}
.gp-tag-mute { background: rgba(135, 134, 127, 0.12); color: var(--c-stone); }
.gp-card-actions { display: flex; gap: 4px; }
.gp-card-body {
  margin: 0;
  padding: 10px 12px;
  background: var(--c-parchment, #f5f4ed);
  border: 1px solid var(--c-border-warm, #e8e6dc);
  border-radius: 8px;
  font-family: var(--ff-mono, "Source Code Pro", ui-monospace, monospace);
  font-size: 11px;
  line-height: 1.55;
  color: var(--c-charcoal);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 140px;
  overflow-y: auto;
}

@media (max-width: 720px) {
  .gp-form-grid { grid-template-columns: 1fr; }
  .gp-cards { grid-template-columns: 1fr; }
  .gp-meta { flex-wrap: wrap; }
}
</style>
