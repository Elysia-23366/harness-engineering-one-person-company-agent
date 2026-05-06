<script setup>
/**
 * ArtifactCard · 从 agent 输出里抽出"📄 文件: xxx" 标记 + 紧跟代码块 → 给下载按钮
 * 兜底:即使没标记,也提取所有代码块,文件名按 language 自动推断
 */
import { computed } from "vue";
import { Download, FileText } from "lucide-vue-next";

const props = defineProps({
  content: { type: String, required: true },
});

// 后缀推断
const LANG_TO_EXT = {
  html: "html", htm: "html",
  css: "css",
  javascript: "js", js: "js", mjs: "mjs",
  typescript: "ts", ts: "ts", tsx: "tsx",
  python: "py", py: "py",
  json: "json",
  markdown: "md", md: "md",
  yaml: "yml", yml: "yml",
  bash: "sh", sh: "sh", shell: "sh",
  sql: "sql",
  vue: "vue",
  jsx: "jsx",
  xml: "xml",
  toml: "toml",
  dockerfile: "Dockerfile",
  text: "txt", plain: "txt", "": "txt",
};

const artifacts = computed(() => {
  const text = props.content || "";
  const out = [];

  // 匹配:可选的 "📄 文件: xxx" 标记 + 三反引号 + lang + 代码块
  // 优先匹配带标记的,再扫剩下没标记的代码块
  const FILE_TAG_RE = /(?:^|\n)\s*📄\s*文件\s*[：:]\s*([^\n]+?)\s*\n\s*```(\w+)?\s*\n([\s\S]*?)\n```/g;
  const matched = new Set();
  let m;
  while ((m = FILE_TAG_RE.exec(text)) !== null) {
    out.push({
      name: m[1].trim(),
      lang: (m[2] || "").trim().toLowerCase(),
      content: m[3],
      tagged: true,
    });
    matched.add(m.index);
  }

  // 兜底:扫所有 ``` 块,过滤已匹配的位置
  const CODE_BLOCK_RE = /```(\w+)?\s*\n([\s\S]*?)\n```/g;
  let i = 0;
  let cm;
  while ((cm = CODE_BLOCK_RE.exec(text)) !== null) {
    // 检查这个代码块是否已被 tagged 模式 capture
    const start = cm.index;
    let alreadyMatched = false;
    for (const tagPos of matched) {
      // tag 模式 match 范围比较宽,大致判断起点之前 200 字符内有 "📄 文件"
      if (Math.abs(start - tagPos) < 600) { alreadyMatched = true; break; }
    }
    if (alreadyMatched) continue;
    i++;
    const lang = (cm[1] || "").trim().toLowerCase();
    const ext = LANG_TO_EXT[lang] || "txt";
    out.push({
      name: `untitled-${i}.${ext}`,
      lang,
      content: cm[2],
      tagged: false,
    });
  }

  return out;
});

function downloadFile(file) {
  const blob = new Blob([file.content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function downloadAll() {
  artifacts.value.forEach((f, idx) => {
    // 错开下载防浏览器拦截
    setTimeout(() => downloadFile(f), idx * 250);
  });
}

function fmtBytes(s) {
  const b = new Blob([s]).size;
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(2)} MB`;
}
</script>

<template>
  <div v-if="artifacts.length" class="artifact-card">
    <header class="ac-head">
      <div class="ac-title">
        <span class="ac-emoji">📦</span>
        <span>产物文件 · {{ artifacts.length }}</span>
      </div>
      <button v-if="artifacts.length > 1" class="ac-btn-all" @click="downloadAll">
        <Download :size="13" />
        <span>全部下载</span>
      </button>
    </header>
    <ul class="ac-list">
      <li v-for="(f, i) in artifacts" :key="i" class="ac-item">
        <FileText :size="16" class="ac-icon" />
        <div class="ac-meta">
          <div class="ac-name">{{ f.name }}</div>
          <div class="ac-info">
            <span v-if="f.lang">{{ f.lang }}</span>
            <span class="ac-dot">·</span>
            <span>{{ fmtBytes(f.content) }}</span>
            <span v-if="!f.tagged" class="ac-untagged">推断文件名</span>
          </div>
        </div>
        <button class="ac-btn-dl" @click="downloadFile(f)">
          <Download :size="13" />
          <span>下载</span>
        </button>
      </li>
    </ul>
    <p class="ac-tip">浏览器会弹下载窗口,选「桌面」即可保存。</p>
  </div>
</template>

<style scoped>
.artifact-card {
  margin-top: 12px;
  background: var(--c-parchment, #f5f4ed);
  border: 1px solid var(--c-border-warm, #e8e6dc);
  border-radius: 12px;
  padding: 14px 16px;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
}
.ac-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 10px;
}
.ac-title {
  display: flex; align-items: center; gap: 6px;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 14px;
  font-weight: 600;
  color: var(--c-near-black, #141413);
  flex: 1;
}
.ac-emoji { font-size: 16px; }
.ac-btn-all {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 10px;
  border: 1px solid var(--c-border-warm);
  background: var(--c-ivory, #faf9f5);
  color: var(--c-charcoal, #4d4c48);
  border-radius: 7px;
  font-size: 12px;
  cursor: pointer;
}
.ac-btn-all:hover { background: var(--c-warm-sand); }
.ac-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.ac-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px;
  background: var(--c-ivory);
  border: 1px solid var(--c-border, #f0eee6);
  border-radius: 8px;
}
.ac-icon { color: var(--c-terracotta, #c96442); flex-shrink: 0; }
.ac-meta { flex: 1; min-width: 0; }
.ac-name {
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 13px;
  color: var(--c-near-black);
  font-weight: 500;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ac-info {
  display: flex; gap: 5px;
  font-size: 11px;
  color: var(--c-stone, #87867f);
  margin-top: 2px;
}
.ac-dot { opacity: 0.5; }
.ac-untagged {
  margin-left: auto;
  background: var(--c-warm-sand);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
}
.ac-btn-dl {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 12px;
  background: var(--c-terracotta, #c96442);
  color: var(--c-ivory);
  border: none;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
}
.ac-btn-dl:hover { background: var(--c-coral, #d97757); }
.ac-tip {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--c-stone);
  font-style: italic;
}
</style>
