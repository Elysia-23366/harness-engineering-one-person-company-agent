# DESIGN.md

> 「墨道」**Ink Way** — 一个人 + 17 个 AI 岗位 = 一家会运转的公司。
> 用东方文房的精神骨架,撑起电影级 scroll-story 的 SaaS 工艺。

---

## 0. 设计宣言(为什么是它)

CEO 给的需求是「翻天覆地 / impeccable / 想抄袭别人一样」,**这不是颜值问题,是辨识度问题**。

国内 AI 产品 99% 在做 Linear 暗夜风(Vercel/Cursor/Resend 同款 Inter+Geist+紫蓝渐变),Western SaaS 全是 Stripe/Notion 暖白风。**两个池子都已经红海**。

「墨道」是**第三条路**:把中文文房的「墨色为主、朱砂为眼、大字直排」 × 顶级 SaaS 的工艺标准 × doubao/apple 级 scroll-story 三合一。这是给国际工程师社区也能秒懂"这是中国人做的 AI OS"的视觉护照,**给面试官见过的所有 demo 都加了一道光**。

| | 中文文房 | Linear Dark | 「墨道」 |
|---|---|---|---|
| 底色 | 米白宣纸 | 纯黑 | **墨蓝绀青**(`#0E1418`) |
| 强调色 | 单一赭石 | 紫蓝渐变 | **朱砂印章红**(`#C8473C`) |
| 字体 | 全中文衬线 | Inter+Geist | **LXGW 文楷 × Cormorant Garamond** |
| 排版 | 横排 | 横排 | **大字直排 + 横排混合** |
| 动效 | L1 静态 | L2 reveal | **L3 scroll-story + WebGL 墨水扩散球** |

---

## 1. Visual Theme & Atmosphere

**Style**: 墨道 / Ink Way · 东方文房 × 顶级 SaaS 工艺 × 电影级滚动叙事
**Keywords**: 墨色、朱砂、纸笺、雅、克制、文人、scroll-story、impeccable、辨识度
**Tone**: 含蓄、有骨、有气、慢拍 — **NOT** 紫蓝渐变 / Inter 黑体 / 圆胖卡通 / AI slop 默认搭配
**Feel**: **像在墨蓝绢布上看一部 4K 电影,旁边有人写楷书** — 静、深、有节奏的呼吸

**Interaction Tier**: **L3 沉浸体验**
**Dependencies**: GSAP 3.12 + ScrollTrigger + Lenis 1.0 + Three.js 0.160(WebGL 单实例)

**为什么 L3 而不是 L2**:
- 17 岗位 × 36 项目类型 × 4 闸 × 5 路径 — 这种**叙事密度**天然适合 scroll-story
- 求职面试场景 → 30 秒抓不住面试官 = 失败 → 必须有 signature moment
- 一人公司架构本身是「一个人撑起一家公司」的史诗叙事 → 配 L1/L2 是浪费

---

## 2. Color Palette & Roles

```css
:root {
  /* ---------- 墨色背景层(主体) ---------- */
  --bg:               #0E1418;   /* 绀青墨蓝 · 比纯黑暖,有文人气 */
  --bg-rgb:           14, 20, 24;
  --surface:          #141B20;   /* 主表面 · 卡片底 */
  --surface-alt:      #1A2228;   /* 次级表面 · 交替 section */
  --surface-hover:    #1F2830;   /* 悬停态 */
  --surface-paper:    #F5EFE0;   /* 纸笺色 · 高对比反白卡用 */
  --surface-paper-rgb: 245, 239, 224;

  /* ---------- 边线(几乎不用粗线) ---------- */
  --border:           rgba(245, 239, 224, 0.08);   /* 默认 · 极轻 */
  --border-strong:    rgba(245, 239, 224, 0.16);   /* 强调边 */
  --border-vermilion: rgba(200, 71, 60, 0.32);     /* 朱砂边 · CTA */

  /* ---------- 文字 ---------- */
  --text:             #F5EFE0;   /* 纸笺色 · 不是纯白,有暖调 */
  --text-secondary:   #A8A398;   /* 次文字 */
  --text-tertiary:    #6B6960;   /* 三级 · 标签/辅助 */
  --text-on-paper:    #1A1A1A;   /* 纸笺反白卡上的字 */

  /* ---------- 强调色(朱砂为眼) ---------- */
  --accent-vermilion:       #C8473C;   /* 朱砂红 · 主强调 · 印章/CTA/活跃态 */
  --accent-vermilion-rgb:   200, 71, 60;
  --accent-vermilion-hover: #D85447;
  --accent-vermilion-soft:  rgba(200, 71, 60, 0.12);
  --accent-vermilion-glow:  rgba(200, 71, 60, 0.32);

  /* ---------- 辅色(极少用) ---------- */
  --accent-jade:      #5E8B7E;   /* 玉石青 · 仅用于成功/已完成 */
  --accent-gold:      #B8956E;   /* 金彩色 · 仅用于精品档徽章 */

  /* ---------- 语义色 ---------- */
  --success:          #5E8B7E;   /* 玉石青 */
  --warning:          #B8956E;   /* 金彩色 */
  --error:            #C8473C;   /* 朱砂红(共用,因为本身就是预警色) */
  --info:             #6B8AA8;   /* 远山青 */

  /* ---------- 阴影 ---------- */
  --shadow-sm:        0 2px 8px rgba(0, 0, 0, 0.16);
  --shadow:           0 8px 24px rgba(0, 0, 0, 0.24);
  --shadow-lg:        0 24px 64px rgba(0, 0, 0, 0.40);
  --shadow-glow:      0 0 32px rgba(200, 71, 60, 0.24);   /* 朱砂光晕 · 仅 hero CTA */
  --shadow-paper:     0 16px 48px rgba(245, 239, 224, 0.08);

  /* ---------- 缓动函数(慢拍) ---------- */
  --ease-cinema:      cubic-bezier(0.65, 0, 0.35, 1);     /* 电影缓动 */
  --ease-out-expo:    cubic-bezier(0.19, 1, 0.22, 1);     /* 文人式收尾 */
  --ease-spring:      cubic-bezier(0.34, 1.56, 0.64, 1);  /* 极少用 · 弹簧 */
}
```

**Color Rules:**
- 所有颜色**必须**通过 CSS 变量引用,组件文件中**禁止**硬编码 hex
- 同一 section 内**只用一个强调色**(朱砂红是唯一主调,玉石青/金彩色是配角)
- **禁止使用纯黑** `#000` 和**纯白** `#FFF` — 全用墨蓝 `#0E1418` 和纸笺 `#F5EFE0` 替代,这是「墨道」灵魂
- **禁止任何紫色渐变**(违反 CEO 反 AI slop 第一律)
- 朱砂红 hover 态用 `--accent-vermilion-hover`,**禁止用 opacity 来做 hover**

---

## 3. Typography Rules

### Font Stack

```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Serif+SC:wght@400;500;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap');

/* LXGW 文楷 · 字库自建(github.com/lxgw/LxgwWenKai) */
@font-face {
  font-family: 'LXGW WenKai';
  src: url('https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/lxgwwenkai-regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}
```

**Font Family 变量**:

```css
:root {
  /* 中文标题 · LXGW 文楷优先,Noto Serif SC 兜底 */
  --font-cn-display: 'LXGW WenKai', 'Noto Serif SC', 'Songti SC', serif;
  /* 中文正文 · 思源黑体 */
  --font-cn-body:    'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  /* 西文标题 · Cormorant Garamond 衬线大字(配 LXGW) */
  --font-en-display: 'Cormorant Garamond', 'Times New Roman', Georgia, serif;
  /* 西文正文 · Inter(克制) */
  --font-en-body:    'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  /* 等宽 */
  --font-mono:       'JetBrains Mono', 'SF Mono', Menlo, monospace;

  /* 复合默认(中英混排自动 fallback) */
  --font-display:    var(--font-en-display), var(--font-cn-display);
  --font-body:       var(--font-en-body), var(--font-cn-body);
}
```

### Size Scale

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| **Hero H1** | `var(--font-display)` | `clamp(56px, 9vw, 120px)` | 600 | 1.0 | -0.02em |
| **Hero Sub** | `var(--font-body)` | `clamp(18px, 2vw, 22px)` | 400 | 1.55 | 0 |
| **Section H2** | `var(--font-display)` | `clamp(40px, 5.5vw, 72px)` | 600 | 1.05 | -0.015em |
| **H3** | `var(--font-cn-display)` | 28px | 600 | 1.2 | 0 |
| **H4** | `var(--font-cn-body)` | 18px | 600 | 1.4 | 0 |
| **Body Lead** | `var(--font-body)` | 19px | 400 | 1.7 | 0 |
| **Body** | `var(--font-body)` | 16px | 400 | **1.75** | 0 |
| **Body 中文** | `var(--font-cn-body)` | 16px | 400 | **1.8** | **0.02em** |
| **Label / Eyebrow** | `var(--font-mono)` | 12px | 500 | 1.5 | **0.08em**(uppercase) |
| **Caption** | `var(--font-body)` | 13px | 400 | 1.55 | 0 |
| **Mono / Code** | `var(--font-mono)` | 14px | 500 | 1.6 | 0 |

### Typography Rules

- **中文标题永远用 LXGW WenKai**,英文/数字字符 fallback 到 Cormorant Garamond(自动靠 font-family 链接)
- **中文正文必须** `line-height: 1.8` + `letter-spacing: 0.02em`(中文优雅纪律)
- **中文长篇文字宽度**:`max-width: 32em`,容器宽度上限 800px(中文阅读舒适带)
- **Hero H1 必须用 SplitText 字粒度入场**,但**中文用词粒度**(中文字粒度太碎,违反阅读习惯)
- **NEVER use**: `font-family: Inter` 单独用作中文标题 / Roboto / Poppins / Lato / Open Sans / 任何"Google Fonts 默认五大件"
- **EM dash** 在中英之间用全角破折号 `——`,不是 `--` 或 `—`

### Text Decoration

按 `text-decoration-rules.md` 决策:

- **Hero H1**:**关键词**(如「墨道」「一人公司」)用 `var(--accent-vermilion)` 朱砂直填,**不用渐变**(中文配渐变会显廉价)
- **Section H2**:无装饰,但加一个 `::before` 朱砂"印章符号"作前缀(详见组件章节)
- **Body**:无装饰
- **Code inline**:`background: var(--surface-alt)`,圆角 4px,padding 2px 6px

---

## 4. Component Stylings

### 4.1 Buttons

```css
/* 默认按钮 · 朱砂印章风 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.01em;
  border: 1px solid var(--border-strong);
  background: transparent;
  color: var(--text);
  border-radius: 4px;          /* 小圆角,文房不喜欢圆胖 */
  cursor: pointer;
  transition: all 280ms var(--ease-cinema);
  position: relative;
  overflow: hidden;
}
.btn:hover {
  background: var(--surface-hover);
  border-color: var(--text-secondary);
  transform: translateY(-1px);
}
.btn:active {
  transform: translateY(0);
}
.btn:focus-visible {
  outline: 2px solid var(--accent-vermilion);
  outline-offset: 3px;
}
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

/* Primary · 朱砂填充 + 印章感 */
.btn-primary {
  background: var(--accent-vermilion);
  border-color: var(--accent-vermilion);
  color: var(--surface-paper);
  font-weight: 600;
  box-shadow: var(--shadow-glow);
}
.btn-primary::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.18) 50%, transparent 70%);
  transform: translateX(-100%);
  transition: transform 600ms var(--ease-cinema);
}
.btn-primary:hover {
  background: var(--accent-vermilion-hover);
  border-color: var(--accent-vermilion-hover);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(200, 71, 60, 0.36);
}
.btn-primary:hover::after {
  transform: translateX(100%);
}

/* Ghost · 极简文人 */
.btn-ghost {
  border-color: transparent;
  background: transparent;
  padding: 14px 8px;
}
.btn-ghost:hover {
  border-color: transparent;
  background: transparent;
  transform: none;
  color: var(--accent-vermilion);
}
.btn-ghost::before {
  content: '→';
  margin-right: -4px;
  opacity: 0;
  transform: translateX(-8px);
  transition: all 280ms var(--ease-cinema);
}
.btn-ghost:hover::before {
  opacity: 1;
  transform: translateX(0);
}
```

### 4.2 Cards · 纸笺卡 / 墨色卡

```css
/* 默认卡片 · 墨色 */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 32px;
  position: relative;
  transition: all 320ms var(--ease-cinema);
}
.card:hover {
  background: var(--surface-hover);
  border-color: var(--border-strong);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* 卡片左上 + 右上 · 朱砂"角标"(铆钉风,doubao 同款) */
.card-rivets::before,
.card-rivets::after {
  content: '';
  position: absolute;
  top: 12px;
  width: 4px;
  height: 4px;
  background: var(--accent-vermilion);
  transform: rotate(45deg);
  opacity: 0.6;
}
.card-rivets::before { left: 12px; }
.card-rivets::after { right: 12px; }

/* SpotlightCard · 鼠标聚光灯(L3 必备) */
.spotlight-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 32px;
  position: relative;
  overflow: hidden;
  --mx: 50%;
  --my: 50%;
}
.spotlight-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(
    600px circle at var(--mx) var(--my),
    var(--accent-vermilion-soft) 0%,
    transparent 40%
  );
  opacity: 0;
  transition: opacity 400ms var(--ease-cinema);
  pointer-events: none;
}
.spotlight-card:hover::before {
  opacity: 1;
}

/* 纸笺反白卡 · 偶尔用作强调区 */
.card-paper {
  background: var(--surface-paper);
  color: var(--text-on-paper);
  border-radius: 4px;
  padding: 40px;
  box-shadow: var(--shadow-paper);
}
.card-paper h3,
.card-paper h4 { color: var(--text-on-paper); }
```

### 4.3 Navigation · 顶栏

```css
.topnav {
  position: sticky;
  top: 0;
  z-index: 50;
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 48px;
  background: rgba(14, 20, 24, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
  transition: all 320ms var(--ease-cinema);
}
.topnav.scrolled {
  height: 60px;
  background: rgba(14, 20, 24, 0.92);
}

.topnav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: var(--font-cn-display);
  font-weight: 600;
}
.topnav-mark {
  /* 朱砂印章 logo · SVG 见落地清单 */
  width: 36px;
  height: 36px;
}

.topnav-links {
  display: flex;
  gap: 8px;
  margin-left: 48px;
}
.topnav-link {
  padding: 8px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  border-radius: 4px;
  transition: all 200ms var(--ease-cinema);
}
.topnav-link:hover { color: var(--text); }
.topnav-link.active {
  color: var(--accent-vermilion);
  background: var(--accent-vermilion-soft);
}
```

### 4.4 Links · 文房链接

```css
.link {
  color: var(--text);
  text-decoration: none;
  background-image: linear-gradient(var(--accent-vermilion), var(--accent-vermilion));
  background-position: 0 100%;
  background-size: 0% 1px;
  background-repeat: no-repeat;
  transition: background-size 400ms var(--ease-cinema), color 200ms;
}
.link:hover {
  color: var(--accent-vermilion);
  background-size: 100% 1px;
}
```

### 4.5 Tags / Badges · 印章式

```css
.tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 2px;
  color: var(--text-secondary);
}
.tag-vermilion {
  background: var(--accent-vermilion-soft);
  color: var(--accent-vermilion);
  border-color: var(--border-vermilion);
}
.tag-jade {
  background: rgba(94, 139, 126, 0.12);
  color: var(--accent-jade);
  border-color: rgba(94, 139, 126, 0.32);
}

/* 档位徽章 · ⚡🚀🏆 */
.tier-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  border-radius: 999px;     /* 唯一允许的胶囊形状 · 因为档位是分类标签 */
  border: 1px solid;
}
.tier-badge.lightning { background: rgba(200, 71, 60, 0.08); border-color: var(--accent-vermilion); color: var(--accent-vermilion); }
.tier-badge.standard  { background: rgba(94, 139, 126, 0.08); border-color: var(--accent-jade);      color: var(--accent-jade); }
.tier-badge.premium   { background: rgba(184, 149, 110, 0.08); border-color: var(--accent-gold);    color: var(--accent-gold); }
```

### 4.6 Section H2 · 朱砂印章前缀

```css
.section-h2 {
  display: inline-flex;
  align-items: baseline;
  gap: 16px;
  font-family: var(--font-display);
  font-size: clamp(40px, 5.5vw, 72px);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: -0.015em;
  margin-bottom: 24px;
}
.section-h2::before {
  content: '';
  display: inline-block;
  width: 12px;
  height: 12px;
  background: var(--accent-vermilion);
  transform: rotate(45deg);
  margin-right: 8px;
  flex-shrink: 0;
  align-self: center;
}
```

### 4.7 Eyebrow · 章节小标(等宽朱砂)

```css
.eyebrow {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-vermilion);
  margin-bottom: 16px;
}
.eyebrow::before {
  content: '— ';
  opacity: 0.6;
}
```

### 4.8 17 岗位卡 · CardConstellation

```css
.role-card {
  position: absolute;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  width: 200px;
  transform-style: preserve-3d;
  will-change: transform, filter;
  transition: filter 400ms var(--ease-cinema), border-color 200ms;
  cursor: pointer;
}
.role-card:hover {
  border-color: var(--accent-vermilion);
  filter: blur(0) !important;       /* hover 时永远清晰 */
  z-index: 100;
}
.role-card .role-id {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent-vermilion);
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}
.role-card .role-name {
  font-family: var(--font-cn-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}
.role-card .role-mentor {
  font-family: var(--font-en-display);
  font-style: italic;
  font-size: 12px;
  color: var(--text-tertiary);
}
```

---

## 5. Layout Principles

### Container

```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 32px;
}
.container-narrow {
  max-width: 800px;     /* 中文阅读舒适带 */
  margin: 0 auto;
  padding: 0 32px;
}
.container-wide {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 48px;
}
```

### Spacing Scale (8 网格)

```css
:root {
  --s-1:   4px;
  --s-2:   8px;
  --s-3:   16px;
  --s-4:   24px;
  --s-5:   40px;
  --s-6:   64px;
  --s-7:   80px;     /* section 之间最小留白 */
  --s-8:   120px;    /* section padding 默认 */
  --s-9:   160px;    /* 重要 section 之间 */
}
```

**铁律**:
- Section vertical padding ≥ `var(--s-8)` (120px)
- 卡片内 padding ≥ `var(--s-4)` (24px),通常 32px
- 网格间距 ≥ `var(--s-3)` (16px)
- Hero section 高度 100vh,内部留白拉到极致

### Grid

```css
.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.grid-bento {
  /* MagicBento 不等大网格 · feature 区用 */
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 16px;
  /* 一个大卡 + 四个小卡的布局 */
}
.grid-bento > :first-child { grid-row: 1 / span 2; }
```

---

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| **Flat** | `box-shadow: none` | 默认所有元素 |
| **Subtle** | `var(--shadow-sm)` 2px 8px | 卡片 hover |
| **Elevated** | `var(--shadow)` 8px 24px | Modal 边缘 |
| **Cinema** | `var(--shadow-lg)` 24px 64px | Hero 卡片星座、CardSwap |
| **Glow** | `var(--shadow-glow)` 朱砂光晕 | **唯一一个** Hero CTA(全站只此一处) |
| **Paper** | `var(--shadow-paper)` 暖光 | 纸笺反白卡 |

**铁律**:
- 默认全部 `box-shadow: none`,**用对比度 + 留白做层次**,不靠阴影
- 朱砂光晕 `--shadow-glow` 全站只用 **1 处**(Hero 主 CTA),用多就廉价
- 移动端阴影减半(避免性能问题)

---

## 7. Animation & Interaction

### 7.1 Motion Philosophy

**慢拍、有呼吸、东方含蓄**。每个动效都问自己:**这是"惊艳"还是"花哨"?**惊艳留下,花哨删掉。

**Tier**: L3 沉浸体验
**FPS Budget**: 60fps 不可妥协 · 移动端必须降级
**核心缓动**: `--ease-cinema` (`cubic-bezier(0.65, 0, 0.35, 1)`) — 电影感
**辅助缓动**: `--ease-out-expo` 收尾时用 — 文人式

### 7.2 Dependencies

```html
<!-- 在 index.html 的 <head> 末尾追加 -->
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/lenis@1.0.45/dist/lenis.min.js"></script>
<!-- Three.js 仅在含 WebGL 签名的页面加载,不全站加 -->
```

### 7.3 Base Setup

```js
// app.js / main.js · 全站初始化
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

gsap.registerPlugin(ScrollTrigger);

// Lenis 平滑滚动 · 但移动端关闭(避免 iOS Safari bug)
const isMobile = matchMedia('(max-width: 640px)').matches;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

if (!isMobile && !reduceMotion) {
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
  });
  function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
  requestAnimationFrame(raf);
  lenis.on('scroll', ScrollTrigger.update);
}

// 性能模式标记 · CSS 可读
document.documentElement.dataset.perf = JSON.stringify({
  isMobile,
  isLowCore: navigator.hardwareConcurrency < 4,
  reduceMotion,
  noHover: !matchMedia('(hover: hover)').matches,
});
```

### 7.4 6 类签名动效(L3 强制)

| 类别 | 落点 | 实现 |
|------|------|------|
| **Hero H1 — Text** | 「招齐 17 个岗位」 | **SplitText**(中文按词,英文按字)+ stagger 入场 |
| **Section H2 — Text** | 章节大标题 | **ScrollFloat** + 朱砂方块前缀 0.2s 延迟出现 |
| **Body — Text** | 正文段落 | **ScrollReveal**(中文行粒度 · 英文词粒度) |
| **Element — 元素级** | Hero CTA 「开始」 | **Magnet**(磁吸,半径 100px,强度 0.3) |
| **Component — 交互** | 17 岗位星座 / 6 种 workflow | **CardConstellation Hero** + **PinSwap** + **SpotlightCard** |
| **Background — 氛围** | Hero 底层 | **Aurora**(墨蓝紫流动,缓慢 30s 一周期) |

### 7.5 Entrance Animation

```css
/* 基础入场 · L1 兜底(JS 失败时) */
.fade-up {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 800ms var(--ease-cinema), transform 800ms var(--ease-cinema);
}
.fade-up.in {
  opacity: 1;
  transform: translateY(0);
}
```

```js
// SplitText Hero H1 · 中文词粒度
function splitHeroH1() {
  const h1 = document.querySelector('.hero-h1');
  if (!h1) return;
  const text = h1.textContent;
  const segmenter = new Intl.Segmenter('zh', { granularity: 'word' });
  const segments = [...segmenter.segment(text)].map(s => s.segment);
  h1.innerHTML = segments.map(s => `<span class="word">${s}</span>`).join('');
  gsap.from('.hero-h1 .word', {
    y: 80,
    opacity: 0,
    duration: 1.2,
    stagger: 0.06,
    ease: 'power3.out',
    delay: 0.3,
  });
}
splitHeroH1();
```

### 7.6 Scroll Behavior(L3 核心)

#### Pattern A · Card Constellation Hero(17 岗位星座)

```js
// 17 个岗位卡片在 3D 空间散布 + 鼠标视差
const stage = document.querySelector('.constellation-stage');
const cards = document.querySelectorAll('.role-card');

// 1. 每张卡 idle 浮动
cards.forEach((c) => {
  gsap.to(c, {
    y: `+=${gsap.utils.random(-12, 12)}`,
    rotate: `+=${gsap.utils.random(-3, 3)}`,
    duration: gsap.utils.random(5, 8),
    ease: 'sine.inOut',
    yoyo: true, repeat: -1,
  });
});

// 2. 鼠标视差(整个 stage 跟随)
stage.addEventListener('pointermove', (e) => {
  const cx = stage.clientWidth / 2;
  const cy = stage.clientHeight / 2;
  const dx = (e.clientX - cx) / cx;
  const dy = (e.clientY - cy) / cy;
  cards.forEach((c) => {
    const depth = parseFloat(c.style.getPropertyValue('--z') || 0) / 200;
    gsap.to(c, { x: dx * 24 * depth, y: dy * 24 * depth, duration: 0.8, ease: 'power3.out' });
  });
});

// 3. Scroll 离开时,17 张卡向中心汇聚 + 缩小 + fade(转场到下一 section)
gsap.timeline({
  scrollTrigger: {
    trigger: '.constellation-stage',
    start: 'bottom 80%',
    end: 'bottom top',
    scrub: 1,
  },
}).to('.role-card', {
  x: 0, y: 0, z: 0,
  rotateX: 0, rotateY: 0, rotateZ: 0,
  filter: 'blur(0px)',
  scale: 0.2,
  opacity: 0,
  stagger: { amount: 0.6, from: 'random' },
  ease: 'power2.in',
});
```

#### Pattern B · PinSwap(6 种 workflow type 横向切换)

```js
const scenes = gsap.utils.toArray('.workflow-scene');
const scenesData = [
  { title: 'Router · 路由专家', desc: '...', graphSvg: '...' },
  { title: 'Planner · 规划执行', desc: '...', graphSvg: '...' },
  { title: 'Supervisor · 动态监督', desc: '...', graphSvg: '...' },
  { title: 'Peer · 同伴交接', desc: '...', graphSvg: '...' },
  { title: 'Single · 单 Agent', desc: '...', graphSvg: '...' },
  { title: '★ 一人公司协作流(自创)', desc: '...', graphSvg: '...' },
];

ScrollTrigger.create({
  trigger: '.workflow-pin',
  start: 'top top',
  end: `+=${scenes.length * 100}%`,
  pin: true,
  scrub: 0.5,
  onUpdate: (self) => {
    const idx = Math.min(Math.floor(self.progress * scenes.length), scenes.length - 1);
    scenes.forEach((s, i) => {
      gsap.to(s, { opacity: i === idx ? 1 : 0, duration: 0.4 });
    });
    document.querySelector('.pin-title').textContent = scenesData[idx].title;
    document.querySelector('.pin-body').textContent = scenesData[idx].desc;
  },
});
```

#### Pattern C · ScrollStack(协作流程 7 步堆叠)

```js
gsap.utils.toArray('.sop-step-card').forEach((card, i) => {
  gsap.to(card, {
    scrollTrigger: {
      trigger: card,
      start: 'top 70%',
      end: 'top 20%',
      scrub: 1,
    },
    scale: 1 - (gsap.utils.toArray('.sop-step-card').length - i) * 0.02,
    y: i * 8,
    ease: 'none',
  });
});
```

#### Pattern D · WebGL 墨水扩散球(CKO 五路径回写签名时刻)

```js
import * as THREE from 'three';

const canvas = document.querySelector('.cko-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
camera.position.z = 5;

// 墨水球 · iridescent 玻璃材质(配朱砂光)
const geometry = new THREE.IcosahedronGeometry(1.4, 5);
const material = new THREE.MeshPhysicalMaterial({
  color: 0x141B20,           // 墨色
  transmission: 0.85,
  thickness: 1.6,
  roughness: 0.18,
  iridescence: 1,
  iridescenceIOR: 1.4,
  clearcoat: 1,
});
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

// 朱砂点光源
const lightVermilion = new THREE.PointLight(0xC8473C, 4, 18);
lightVermilion.position.set(3, 2, 3);
scene.add(lightVermilion);

// 玉石青反光
const lightJade = new THREE.PointLight(0x5E8B7E, 2, 20);
lightJade.position.set(-3, -2, 3);
scene.add(lightJade);

scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 0.6));

// ScrollTrigger 驱动 · 墨水球随滚动旋转 + 拉伸
gsap.to(mesh.rotation, {
  y: Math.PI * 1.5, x: Math.PI * 0.5,
  scrollTrigger: {
    trigger: '.cko-section',
    start: 'top bottom', end: 'bottom top',
    scrub: 1,
  },
});

// 渲染循环 · IntersectionObserver 不可见时暂停
let visible = true;
new IntersectionObserver(([e]) => visible = e.isIntersecting).observe(canvas);
function tick() {
  if (visible) {
    mesh.rotation.z += 0.002;
    renderer.render(scene, camera);
  }
  requestAnimationFrame(tick);
}
tick();
```

### 7.7 Hover & Focus States

所有可交互元素:
- **Hover**:`transform: translateY(-2px)` + `border-color: var(--border-strong)` + 加 hover 类
- **Focus**:`outline: 2px solid var(--accent-vermilion); outline-offset: 3px`
- **Active**:`transform: translateY(0)` 立即回弹
- **transition**:`all 280ms var(--ease-cinema)`

### 7.8 Special: Cursor Highlighter(可选 · 仅 desktop)

```css
.cursor-highlight {
  position: fixed;
  width: 28px; height: 28px;
  border: 1.5px solid var(--accent-vermilion);
  border-radius: 50%;
  pointer-events: none;
  mix-blend-mode: difference;
  transform: translate(-50%, -50%);
  transition: width 200ms var(--ease-cinema), height 200ms var(--ease-cinema);
  z-index: 9999;
}
.cursor-highlight.hovering {
  width: 60px; height: 60px;
}

@media (hover: none) { .cursor-highlight { display: none; } }
```

### 7.9 Reduced Motion 降级(必须)

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
  .role-card {
    animation: none !important;
  }
  .cko-canvas { display: none; }
  .cko-section::before {
    /* 静态大图替代 */
    content: '';
    display: block;
    width: 320px; height: 320px;
    margin: 0 auto;
    background: radial-gradient(circle, var(--accent-vermilion-soft), transparent 70%);
  }
}
```

```js
// 移动端自动降级
const perf = JSON.parse(document.documentElement.dataset.perf);
if (perf.isMobile || perf.isLowCore) {
  // 禁用 WebGL · 关闭视差 · 减少 stagger
  document.querySelectorAll('.cko-canvas').forEach(c => c.remove());
  document.querySelectorAll('.role-card').forEach(c => {
    c.style.transform = 'none';
    c.style.position = 'relative';   // 退化为静态网格
  });
}
```

---

## 8. Do's and Don'ts

### ✅ Do

1. **所有颜色用 CSS 变量**,组件文件零硬编码 hex
2. **中文标题永远配 LXGW WenKai**,英文跟随 Cormorant Garamond
3. **朱砂红是唯一主强调色**,玉石青和金彩色仅用于成功/精品档
4. **Section padding ≥ 120px**,留白即设计
5. **Hero H1 用 SplitText 入场**,中文按词粒度,英文按字粒度
6. **每个 section 必有 1 个 signature moment**(L3 至少 6 个)
7. **WebGL 全站只 1 个实例**(CKO 五路径回写),离开视窗暂停
8. **所有动效有 reduced-motion 降级路径**
9. **响应式从 desktop → tablet → mobile 全测**,移动端阴影减半
10. **圆角统一 4-8px**,极少用大圆角(文房不喜欢圆胖)

### ❌ Don't

1. ❌ **禁止用 Inter 当中文标题字体**(中文文房风灵魂破坏)
2. ❌ **禁止任何紫色渐变**(`linear-gradient(135deg, #667eea, #764ba2)` = AI slop 标志)
3. ❌ **禁止用纯黑 `#000` 和纯白 `#FFF`**(必须用墨蓝 `#0E1418` 和纸笺 `#F5EFE0`)
4. ❌ **禁止用 opacity 做 hover 状态**(必须用专门的 `--accent-vermilion-hover`)
5. ❌ **禁止 backdrop-filter blur > 14px** 在大面积滚动区(性能红线)
6. ❌ **禁止单页超过 1 个 WebGL scene**(GPU 内存爆)
7. ❌ **禁止全局 cursor 替换**(`cursor: none` 影响可访问性)
8. ❌ **禁止圆胖 button**(`border-radius: 16px+` 在 button 上 = 卡通感)
9. ❌ **禁止 emoji 装饰**(本架构是专业产品,emoji 仅用于档位 ⚡🚀🏆 这种语义标识)
10. ❌ **禁止"AI slop 默认五大件"组合**:Inter + Roboto + Poppins + Lato + Open Sans
11. ❌ **禁止用动效掩盖结构问题**(动效是放大器不是创可贴)
12. ❌ **禁止中文正文用 1.5 行高**(最低 1.7,推荐 1.8,加 0.02em 字距)

---

## 9. Responsive Behavior

### Breakpoints

| Name | Width | 关键变化 |
|------|-------|---------|
| **Desktop** | > 1024px | 三栏布局 / 完整 scroll-story / WebGL 全开 |
| **Tablet** | 640-1024px | 两栏 / pin-swap 简化为一次性入场 / WebGL 保留但分辨率降一半 |
| **Mobile** | < 640px | 单栏 / 关闭 pin / WebGL 替换为静态大图 / 阴影减半 |

```css
/* Mobile-first base */
.container { padding: 0 24px; }
.section-h2 { font-size: clamp(32px, 8vw, 56px); }
.hero-h1 { font-size: clamp(48px, 12vw, 88px); }

@media (min-width: 640px) {
  .container { padding: 0 32px; }
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
  .container { padding: 0 32px; }
  .grid-3 { grid-template-columns: repeat(3, 1fr); }
  .hero-h1 { font-size: clamp(64px, 9vw, 120px); }
}

@media (min-width: 1440px) {
  .container { max-width: 1280px; }
}
```

### Touch Targets

最小 `44 × 44px`(WCAG 2.5.8)

```css
@media (hover: none) {
  .btn, .topnav-link, .role-card {
    min-height: 44px;
  }
}
```

### Collapsing Strategy

- **Desktop**:三栏 `300px / 1fr / 360px`
- **Tablet**(< 1024px):右栏 trace 流变成底部抽屉
- **Mobile**(< 640px):左栏变 hamburger 抽屉,trace 流隐藏(可点按钮展开)

---

## 10. 关键页面草图(语义级,非 px-perfect)

### 10.1 总览页 Hero(首屏)

```
┌─────────────────────────────────────────────────────────────┐
│  [朱砂印章 logo] 一人公司 Agent      总览  岗位  协作  设置  │ ← topnav
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ── 一人公司架构 v1.8.0 · LIVE                                │ eyebrow
│                                                              │
│        招齐 17 个岗位。                                       │ Hero H1 LXGW
│        让公司自己跑起来。                                     │ (SplitText 词粒度入场)
│                                                              │
│        你 1 人 + 17 个 AI 岗位 = 一家会运转的公司。           │ lead
│        基于一人公司架构 v1.8.0 · CKO 自动分诊 → 岗位接力 →     │
│        4 道质量闸 → 五路径回写。                              │
│                                                              │
│        [开始一个项目 →]   [看 GitHub]                         │ CTA Magnet
│                                                              │
│  ─── 17 张岗位卡在 3D 空间浮动(CardConstellation)──────────  │
│      [R01]  [R02]                              [R03]         │ blur 远景
│         [R07]      [R20]    [R12]   [R11]                    │
│              [R04]    [R13]    [R22]                         │ 中景
│                  [R23]   [R21]                               │
│        [R05]  [R17]   [R18]  [R19]   [R06]                   │ 近景清晰
│                                                              │ + 鼠标视差
└─────────────────────────────────────────────────────────────┘
                Aurora 墨蓝紫极光底层(缓慢 30s)
```

### 10.2 6 种 workflow type 展示(PinSwap)

```
┌─────────────────────────────────────────────────────────────┐
│  ── PROVEN ARCHETYPES                                        │
│                                                              │
│  ◆ 6 种协作模式 · 5 种来自 LangGraph,1 种我自创             │ Section H2
│                                                              │
│  ┌──────────────┐  ┌──────────────────────────────┐          │
│  │ 1 / 6        │  │                              │          │
│  │              │  │   [Workflow Graph 可视化]    │          │ ← scrub 切换
│  │ Router       │  │                              │          │   1 → 2 → 3 → 4 → 5 → 6
│  │ 路由专家     │  │  ●→○○○                       │          │
│  │              │  │                              │          │
│  │ 单步分诊 ·   │  └──────────────────────────────┘          │
│  │ 客服级 FAQ   │                                            │
│  │              │  适合: 客服分诊 / FAQ 路由                 │
│  │ [滚动看下一种 ↓]                                          │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                  ↓ pin · 滚动驱动场景切换
```

### 10.3 一人公司协作流(自创范式 · highlight)

```
┌─────────────────────────────────────────────────────────────┐
│  ★  6 / 6 · ONE PERSON COMPANY                               │
│                                                              │
│  [WebGL 墨水球 · 中央居中 · 朱砂+玉石青双光]                 │
│   ◯ → 旋转 → 形变 → 五路径分裂                                │
│                                                              │
│      [A 岗位方法论]   [B 公司脑库]   [C 模板升级]            │
│           [D 失败案例]   [E 历史作品]                        │
│                                                              │
│  CKO 自动分诊 → 岗位接力 → 4 道质量闸 → 五路径回写            │
└─────────────────────────────────────────────────────────────┘
```

### 10.4 运行页 · Trace 流(右栏)

```
┌─────────────────────────────────────────────────┐
│ ●  TRACE STREAM                  47 events       │
├─────────────────────────────────────────────────┤
│ │ 04:23:12  run_started                          │
│ │   一人公司协作流启动 · 4 个岗位                 │
│ │                                                │
│ │ 04:23:13  node_entered                         │
│ ┃   📚 CKO 分诊员上场                             │ ← 朱砂色边
│ │   R07 视角 · 项目入口 SOP 第 1-3 步             │
│ │                                                │
│ │ 04:23:18  route_selected                       │
│ │   分诊提案已出 · 涉及 4 岗位                    │
│ ⊕ ── handoff ────────                            │
│ ┃ 04:23:19  node_entered                         │ ← 玉石青边
│ ┃   第 1 棒 · R01 AI 产品经理                     │
│ │   ...                                          │
└─────────────────────────────────────────────────┘
   等宽字体 + 时间戳 + 类型彩色边 · 实时滚动
```

---

## 11. Day 1 落地清单(精品档 2-3 天)

### Day 1 · 视觉骨架(8 小时)

**改动文件清单**(精确到行级):

| 优先级 | 文件 | 动作 | 说明 |
|---|---|---|---|
| P0 | `frontend/src/style.css` | **完全重写** | 73KB → 约 60KB,按本 DESIGN.md |
| P0 | `frontend/index.html` | 加 Google Fonts + GSAP/ScrollTrigger/Lenis CDN | head 末尾 |
| P0 | `frontend/src/App.vue` | logo SVG 换朱砂印章 | 替换 Building2 |
| P1 | `frontend/src/main.js` | 加 Lenis 初始化 + 性能检测 | 文件末尾 |
| P1 | `frontend/src/i18n.js` | 文案微调("一人公司 Agent" 加 LXGW 字体感词汇) | 已经做过一轮,微调 |

### Day 2 · Hero + 主页改造(8 小时)

**关键组件**(新建/改造):
- `components/CardConstellation.vue` — 17 岗位 3D 卡片星座(新建,~200 行)
- `components/AuroraBackground.vue` — Aurora 极光底层(新建,~80 行)
- `pages/OverviewPage.vue` — 改 Hero 区 + 引入 CardConstellation
- `components/SpotlightCard.vue` — 鼠标聚光灯卡片(新建,~50 行)

### Day 3 · scroll-story + 长尾(8 小时)

**新建**:
- `components/WorkflowPinSwap.vue` — 6 种 workflow 横向切换(L3 PinSwap)
- `components/CKODistillCanvas.vue` — WebGL 墨水球(Three.js)
- `components/SOPScrollStack.vue` — 7 步 SOP 滚动堆叠

**改造**:
- 现有 `GraphViewer.vue` / `TraceViewer.vue` — 只改色板和字体,不动逻辑
- 现有 `AgentManager.vue` / `WorkflowManager.vue` — CRUD 表单按新组件样式

### Day 3 末 · 自检 + 部署(2 小时)

按 `quality-checklist.md` 逐项过:
- [ ] 9 章节全 ✅
- [ ] 所有颜色 CSS 变量
- [ ] 字体 @import 完整
- [ ] L3 6 类动效齐
- [ ] reduced-motion 降级
- [ ] 移动端横向溢出 ✅
- [ ] WebGL 移动端降级到静态图
- [ ] FPS desktop ≥ 60 / mobile ≥ 30
- [ ] WCAG 2.2 AA 对比度

---

## 12. 给 CEO 的「面试故事」(配本设计)

> "我做的不是又一个 Linear 风的 SaaS,我做的是 **第三条路 · 墨道**:
>
> 国内 99% AI 产品在抄 Linear/Vercel 暗夜风,Western SaaS 全是 Stripe 暖白风。两个池子都是红海。
>
> 我用东方文房的精神骨架(墨蓝、朱砂、纸笺、LXGW 文楷大字),撑起 doubao/apple 级的 scroll-story 工艺(CardConstellation、PinSwap、WebGL 签名),做出一个**国际工程师社区也能秒懂'这是中国人做的 AI OS'** 的视觉护照。
>
> 17 张岗位卡在 3D 空间漂浮 → 鼠标视差 → 滚动汇聚 → 进入 6 种 workflow PinSwap → 最后到 CKO 五路径回写的 WebGL 墨水球。
>
> 这不是颜值,是**辨识度差异化**。给面试官见过的所有 demo 都加了一道光。"

---

## 13. 致谢

- 视觉灵感:Apple 中国官网 / doubao.com/about / minimax / igloo.inc
- 字体:[LXGW WenKai](https://github.com/lxgw/LxgwWenKai) by 落霞孤鹜(MIT)
- 动效组件库:[vue-bits](https://github.com/DavidHDev/vue-bits) by DavidHDev(MIT)
- 设计系统参考:[awesome-design-md](https://github.com/VoltAgent/awesome-design-md)(MIT)
- 方法论本体:[一人公司架构 v1.8.0](https://github.com/itawjh-lgtm/one-person-company)(CC-BY 4.0)

---

> **设计稿版本**: v1.0
> **创建日期**: 2026-05-05
> **下次迭代触发**: CEO 拍板后立刻进 Phase C(代码落地)
> **可逆性**: DESIGN.md 是文档,不影响线上;style.css 重写前 git commit 一次,可秒回滚
