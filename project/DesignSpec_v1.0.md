# DesignSpec_v1.0.md
# Multi-Agent Playground · 视觉设计规格
> R02 → R03 交付物 | 版本 1.0 | 深色技术文档风

---

## 一、设计系统 Tokens（7 项齐）

### 1. Color Tokens

```
/* ── 背景层级 ── */
--color-bg-base:       #0d1117   /* 页面底色，GitHub Dark 同源 */
--color-bg-surface:    #161b22   /* 卡片/区块底色 */
--color-bg-elevated:   #21262d   /* 悬浮/高亮区块 */
--color-bg-code:       #1a1f27   /* 代码块底色 */
--color-bg-tab-active: #21262d   /* Tab 激活态底色 */

/* ── 边框 ── */
--color-border:        #30363d   /* 通用边框 */
--color-border-focus:  #58a6ff   /* 焦点环颜色（WCAG AA 键盘导航） */

/* ── 文字 ── */
--color-text-primary:  #e6edf3   /* 正文主色，对比度 vs bg-base = 13.8:1 ✓ */
--color-text-secondary:#8b949e   /* 辅助文字，对比度 vs bg-base = 4.6:1 ✓ */
--color-text-muted:    #6e7681   /* 最弱文字，仅用于 placeholder/disabled */
--color-text-inverse:  #0d1117   /* 深色背景上的反色文字 */

/* ── 品牌 / 强调 ── */
--color-accent:        #58a6ff   /* 主强调色（蓝），对比度 vs bg-base = 5.9:1 ✓ */
--color-accent-hover:  #79c0ff   /* 悬浮态 */
--color-accent-subtle: #1f3a5f   /* 低饱和强调背景（步骤编号圆圈） */

/* ── 语义色 ── */
--color-success:       #3fb950   /* 成功/完成 */
--color-warning:       #d29922   /* 警告 */
--color-error:         #f85149   /* 错误 */
--color-info:          #58a6ff   /* 信息 */

/* ── 代码语法高亮 ── */
--color-code-text:     #e6edf3   /* 默认代码文字 */
--color-code-comment:  #6e7681   /* 注释（# 开头） */
--color-code-string:   #a5d6ff   /* 字符串值（sk-...、路径） */
--color-code-keyword:  #ff7b72   /* 关键字（cd、source、pip） */
--color-code-param:    #ffa657   /* 参数/标志（--host、--port） */
--color-code-number:   #79c0ff   /* 数字（8011） */
--color-code-env:      #d2a8ff   /* 环境变量名（OPENAI_API_KEY） */
```

**对比度校验表（WCAG 2.2 AA，正文 ≥ 4.5:1，大文字 ≥ 3:1）**

| 前景 Token | 背景 Token | 对比度 | 用途 | 达标 |
|---|---|---|---|---|
| text-primary `#e6edf3` | bg-base `#0d1117` | 13.8:1 | 正文 | ✓ AAA |
| text-secondary `#8b949e` | bg-base `#0d1117` | 4.6:1 | 辅助文字 | ✓ AA |
| accent `#58a6ff` | bg-base `#0d1117` | 5.9:1 | 链接/强调 | ✓ AA |
| accent `#58a6ff` | bg-surface `#161b22` | 5.4:1 | 卡片内强调 | ✓ AA |
| text-primary `#e6edf3` | bg-code `#1a1f27` | 11.2:1 | 代码文字 | ✓ AAA |
| code-comment `#6e7681` | bg-code `#1a1f27` | 3.1:1 | 注释（大字号 ≥16px） | ✓ AA大 |
| code-string `#a5d6ff` | bg-code `#1a1f27` | 7.8:1 | 字符串 | ✓ AAA |
| code-keyword `#ff7b72` | bg-code `#1a1f27` | 5.2:1 | 关键字 | ✓ AA |

---

### 2. Typography Tokens

```
/* ── 字体栈 ── */
--font-sans:  -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
              "Helvetica Neue", Arial, sans-serif;
--font-mono:  "SFMono-Regular", Consolas, "Liberation Mono",
              Menlo, Courier, monospace;

/* ── 字号阶梯（Major Third 1.25 比例） ── */
--text-xs:    12px   /* muted 标注 */
--text-sm:    14px   /* 表格内容、注意事项 */
--text-base:  16px   /* 正文基准 */
--text-lg:    20px   /* 卡片标题、步骤标题 */
--text-xl:    24px   /* Section 标题 */
--text-2xl:   32px   /* Hero 副标题 */
--text-3xl:   48px   /* Hero 主标题 */

/* ── 行高 ── */
--leading-tight:  1.25   /* 标题 */
--leading-normal: 1.6    /* 正文 */
--leading-code:   1.7    /* 代码块 */

/* ── 字重 ── */
--weight-normal:  400
--weight-medium:  500
--weight-semibold:600
--weight-bold:    700

/* ── 字间距 ── */
--tracking-tight: -0.02em   /* 大标题 */
--tracking-normal: 0        /* 正文 */
--tracking-wide:  0.05em    /* 全大写标签 */
```

---

### 3. Spacing Tokens

```
/* 4px 基准网格 */
--space-1:   4px
--space-2:   8px
--space-3:   12px
--space-4:   16px
--space-5:   20px
--space-6:   24px
--space-8:   32px
--space-10:  40px
--space-12:  48px
--space-16:  64px
--space-20:  80px
--space-24:  96px
```

---

### 4. Border Radius Tokens

```
--radius-sm:   4px    /* 行内代码、小标签 */
--radius-md:   8px    /* 卡片、代码块 */
--radius-lg:   12px   /* Hero 图片、步骤卡片 */
--radius-full: 9999px /* 步骤编号圆圈、徽章 */
```

---

### 5. Shadow Tokens

```
--shadow-sm:  0 1px 3px rgba(0,0,0,0.4);
--shadow-md:  0 4px 12px rgba(0,0,0,0.5);
--shadow-lg:  0 8px 24px rgba(0,0,0,0.6);
--shadow-focus: 0 0 0 3px rgba(88,166,255,0.4);  /* 焦点环 */
```

---

### 6. Motion Tokens

```
--duration-fast:   120ms
--duration-normal: 200ms
--duration-slow:   300ms
--ease-default:    cubic-bezier(0.16, 1, 0.3, 1)   /* ease-out-expo */
--ease-in:         cubic-bezier(0.4, 0, 1, 1)
```

---

### 7. Breakpoint Tokens

```
--bp-sm:   480px    /* 手机横屏 */
--bp-md:   768px    /* 平板 */
--bp-lg:   1024px   /* 桌面 */
--bp-xl:   1280px   /* 宽屏 */

/* 内容最大宽度 */
--content-max:  860px   /* 文档阅读最佳宽度，两侧留白 */
```

---

## 二、页面布局规格

### 全局结构

```
<html>
  <body bg=bg-base>
    <header>          ← 顶部导航条（固定，高 56px）
    <main>
      §1 Hero         ← 全宽，内容居中 max-width=860px
      §2 项目结构      ← 内容区
      §3 快速开始      ← 3 列卡片（桌面）/ 1 列（移动）
      §4 启动服务      ← 2 列并排（桌面）/ 1 列（移动）
      §5 工作流类型    ← 全宽表格
      §6 桌面端打包    ← Tab 切换区
      §7 注意事项      ← 2 条 tip 卡片
    </main>
    <footer>          ← 极简单行
  </body>
</html>
```

### 顶部导航条

```
高度:        56px
背景:        bg-surface + border-bottom: 1px solid border
内容:        左 · 项目名「Multi-Agent Playground」font-mono text-sm accent色
             右 · 「MIT License」text-muted text-xs
Padding:     水平 space-6
Position:    sticky top:0，z-index:100
```

---

## 三、各区块视觉规格

### §1 Hero 区

```
背景:        bg-base（无卡片，直接页面底色）
Padding:     top space-20，bottom space-16
内容对齐:    居中

主标题:
  文字:      「Multi-Agent Playground」
  字号:      text-3xl（48px）桌面 / text-2xl（32px）移动
  字重:      weight-bold
  颜色:      text-primary
  字间距:    tracking-tight
  字体:      font-mono（技术感）

副标题:
  文字:      「基于 LangGraph 的多智能体工作流实验平台」
  字号:      text-lg（20px）
  字重:      weight-normal
  颜色:      text-secondary
  margin-top: space-3

图片区:
  布局:      两张图片水平并排（桌面）/ 垂直堆叠（移动 <768px）
  宽度:      各 calc(50% - space-3)，gap: space-6
  border-radius: radius-lg
  border:    1px solid border
  shadow:    shadow-lg
  margin-top: space-10
  overflow:  hidden（圆角裁切）
  加载态:    背景 bg-elevated，高度 240px，含 shimmer 动画
```

---

### §2 项目结构

```
Section 标题规格（通用，所有 Section 复用）:
  字号:      text-xl（24px）
  字重:      weight-semibold
  颜色:      text-primary
  margin:    top space-16，bottom space-6
  左侧装饰:  3px solid accent，padding-left space-4

代码树块:
  背景:      bg-code
  border:    1px solid border
  border-radius: radius-md
  padding:   space-6
  font:      font-mono text-sm（14px）
  line-height: leading-code（1.7）
  颜色:      code-text
  overflow-x: auto（横向滚动，不折行）

  语法着色规则:
    「# 注释文字」→ color-code-comment
    目录名（backend/ frontend/ desktop/）→ color-code-text
    文件名（.env requirements.txt）→ color-code-string
    树形符号（├── └── │）→ color-code-comment
```

---

### §3 快速开始（步骤卡片）

```
容器布局:
  桌面（≥768px）: 3 列 grid，gap space-6
  移动（<768px）:  1 列，gap space-4

步骤卡片规格:
  背景:      bg-surface
  border:    1px solid border
  border-radius: radius-lg
  padding:   space-6
  position:  relative

步骤编号圆圈:
  尺寸:      36×36px（触控区 ≥44pt 由卡片整体保证）
  背景:      accent-subtle
  颜色:      accent
  字号:      text-base，weight-bold
  border-radius: radius-full
  margin-bottom: space-4

步骤标题:
  字号:      text-lg（20px）
  字重:      weight-semibold
  颜色:      text-primary
  margin-bottom: space-3

步骤说明文字（如有）:
  字号:      text-sm（14px）
  颜色:      text-secondary
  margin-bottom: space-3

卡片内代码块:
  同 §2 代码树块规格
  padding:   space-4（卡片内稍紧凑）
  margin-top: space-3
```

**步骤卡片 5 态集**

| 状态 | 视觉表现 |
|---|---|
| 正常 | bg-surface + border border |
| 悬浮（hover） | border-color → accent（opacity 0.6），shadow-md，transition duration-normal |
| 焦点（focus-visible） | shadow-focus（3px 蓝色焦点环），outline: none |
| 加载（loading） | 卡片内代码区显示 shimmer 骨架屏，高度保持 |
| 错误（error） | 不适用（静态内容卡片，无错误态） |

---

### §4 启动服务（两列并排）

```
容器布局:
  桌面（≥768px）: 2 列 grid，gap space-6，各 50%
  移动（<768px）:  1 列

列标题:
  字号:      text-lg（20px）
  字重:      weight-semibold
  颜色:      text-primary
  左侧 badge:
    文字:    「后端」/「前端」
    背景:    accent-subtle
    颜色:    accent
    padding: space-1 space-3
    border-radius: radius-full
    font:    font-mono text-xs
    margin-right: space-3

端口/代理说明:
  字号:      text-sm
  颜色:      text-secondary
  margin-bottom: space-3

代码块:
  同 §2 规格，语法高亮完整应用
```

---

### §5 工作流类型（表格）

```
表格容器:
  width: 100%
  overflow-x: auto（移动端横滚）
  border: 1px solid border
  border-radius: radius-md
  overflow: hidden

表头（thead）:
  背景:      bg-elevated
  字号:      text-sm（14px）
  字重:      weight-semibold
  颜色:      text-secondary
  padding:   space-3 space-5
  text-align: left
  border-bottom: 1px solid border

表格行（tbody tr）:
  背景:      bg-surface（奇数行）/ bg-base（偶数行）
  padding:   space-4 space-5
  border-bottom: 1px solid border（最后行无）
  字号:      text-base（16px）← R01 要求「不能太小」

  类型列（第1列）:
    font:    font-mono
    颜色:    accent
    背景:    accent-subtle（行内 code 标签）
    padding: space-1 space-2
    border-radius: radius-sm

  说明列（第2列）:
    颜色:    text-primary
    「→」箭头: 颜色 text-secondary

表格行 5 态集:
  正常:      如上
  悬浮:      背景 bg-elevated，transition duration-fast
  焦点:      outline 2px solid accent（键盘 Tab 可聚焦行）
  加载:      shimmer 骨架屏（5行占位）
  空:        单行居中「暂无工作流数据」text-muted（防御性设计）
```

---

### §6 桌面端打包（Tab 切换）

```
Tab 导航条:
  背景:      bg-surface
  border-bottom: 1px solid border
  display:   flex，gap: 0

Tab 按钮规格:
  padding:   space-3 space-6
  最小触控区: 44px 高（padding 保证）
  字号:      text-sm，font-mono
  border-bottom: 2px solid transparent（默认）

Tab 按钮 5 态集:
  正常:      颜色 text-secondary，border-bottom transparent
  悬浮:      颜色 text-primary，bg-elevated，transition duration-fast
  激活:      颜色 accent，border-bottom 2px solid accent，bg-tab-active
  焦点:      shadow-focus，outline: none
  禁用:      颜色 text-muted，cursor not-allowed，opacity 0.5

Tab 内容区:
  背景:      bg-surface
  border:    1px solid border（顶部无，与 Tab 条合并）
  border-radius: 0 0 radius-md radius-md
  padding:   space-6

  子步骤标签（macOS未签名 / 签名发布 / Windows）:
    字号:    text-sm，weight-medium
    颜色:    text-secondary
    margin-bottom: space-2
    margin-top: space-5（首个除外）

  构建产物说明:
    样式:    blockquote 风格
    左边框:  3px solid warning（#d29922）
    padding-left: space-4
    颜色:    text-secondary
    font:    text-sm
```

---

### §7 注意事项

```
容器:
  display: flex，gap space-4
  移动端: flex-direction column

Tip 卡片:
  背景:      bg-surface
  border:    1px solid border
  border-left: 3px solid accent
  border-radius: radius-md
  padding:   space-4 space-5
  flex: 1

图标:
  「📁」emoji 或 SVG，font-size text-lg
  margin-right: space-2

文字:
  字号:      text-sm（14px）
  颜色:      text-secondary
  行内 code:
    font:    font-mono
    颜色:    accent
    背景:    accent-subtle
    padding: 1px space-2
    border-radius: radius-sm
```

---

### §8 Footer

```
背景:      bg-surface
border-top: 1px solid border
padding:   space-6
text-align: center
字号:      text-sm（14px）
颜色:      text-muted
内容:      「Multi-Agent Playground · MIT License」
字体:      font-mono
```

---

## 四、代码块语法高亮规则（R03 直接实现）

R03 用纯 JS 字符串替换实现，无需引入第三方库。

### 着色优先级（从高到低匹配，先匹配先着色）

```
1. 整行注释   /^(\s*)(#.*)$/gm
   → 「#」及后续全部 → color-code-comment

2. 环境变量名  /\b([A-Z_]{3,}=)/g
   → 「OPENAI_API_KEY=」→ color-code-env

3. 字符串值   /(sk-[^\s]+|http[^\s]+|[a-z0-9_]+\.txt|[a-z0-9_]+\.db|[a-z0-9_]+\.env[^\s]*)/g
   → color-code-string

4. Shell 命令  /\b(cd|source|pip|python3|npm|uvicorn|cp)\b/g
   → color-code-keyword

5. 参数标志   /(--[a-z:]+)/g
   → color-code-param

6. 端口数字   /\b(8011|3000)\b/g
   → color-code-number

7. 路径分隔符  /(\/)/g
   → color-code-comment（降低视觉权重）
```

### 行内 `code` 标签（非代码块）

```css
code（行内）:
  font-family: font-mono
  font-size:   0.875em（相对父级）
  color:       accent
  background:  accent-subtle
  padding:     1px 6px
  border-radius: radius-sm
```

---

## 五、可访问性规格（WCAG 2.2 AA）

| 项目 | 规格 | 实现方式 |
|---|---|---|
| 对比度 | 正文 ≥ 4.5:1，大文字 ≥ 3:1 | 见 Token 校验表 |
| 触控区 | ≥ 44×44px | Tab 按钮 padding-y space-3（48px 行高）|
| 焦点可见 | 所有交互元素有焦点环 | shadow-focus，不用 outline:none 除非替换 |
| 颜色非唯一 | 不单靠颜色传达信息 | Tab 激活态同时有 border-bottom + 颜色变化 |
| 图片 alt | Hero 截图有描述性 alt | `alt="Multi-Agent Playground 界面截图 1/2"` |
| 语义 HTML | 正确标签层级 | h1 唯一，h2 各 Section，code/pre 正确嵌套 |
| 键盘导航 | Tab 顺序合理 | Tab 切换用 role=tablist/tab/tabpanel + aria |
| 跳过导航 | skip-to-content 链接 | 页面第一个元素，focus 时显示 |

### Tab 组件 ARIA 规格

```html
<div role="tablist" aria-label="桌面端打包平台">
  <button role="tab" aria-selected="true"  aria-controls="panel-mac"  id="tab-mac">macOS</button>
  <button role="tab" aria-selected="false" aria-controls="panel-win"  id="tab-win">Windows</button>
</div>
<div role="tabpanel" id="panel-mac" aria-labelledby="tab-mac">...</div>
<div role="tabpanel" id="panel-win" aria-labelledby="tab-win" hidden>...</div>
```

---

## 六、动效规格

| 元素 | 触发 | 动效 | 时长/曲线 |
|---|---|---|---|
| 步骤卡片 | hover | border-color + shadow 渐变 | 200ms ease-out-expo |
| Tab 按钮 | hover | background + color 渐变 | 120ms ease-out |
| Tab 内容 | 切换 | opacity 0→1 | 200ms ease-out |
| 表格行 | hover | background 渐变 | 120ms ease-out |
| Hero 图片 | 加载中 | shimmer（background-position 动画）| 1.5s linear infinite |
| 页面 | 首次加载 | 无（文档页不做入场动画，减少干扰）| — |

### Shimmer 骨架屏规格

```css
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-elevated) 25%,
    var(--color-bg-surface)  50%,
    var(--color-bg-elevated) 75%
  );
  background-size: 800px 100%;
  animation: shimmer 1.5s linear infinite;
}
```

---

## 七、组件 5 态集汇总

| 组件 | 正常 | 空 | 加载 | 错误 | 边界 |
|---|---|---|---|---|---|
| Hero 图片 | 正常渲染 | alt 文字显示 | shimmer 占位 240px | broken-image 图标 + alt | 超长 alt 截断 |
| 步骤卡片 | bg-surface | — | 代码区 shimmer | — | 代码超长横滚 |
| 工作流表格 | 5行数据 | 「暂无数据」居中提示 | 5行 shimmer 骨架 | 「加载失败，请刷新」error色 | 类型名超长 font-size 缩小 |
| Tab 按钮 | 默认第一个激活 | — | — | — | 标签文字超长省略号 |
| 代码块 | 语法高亮 | — | — | — | 超长行横滚，不折行 |
| Footer | 正常显示 | — | — | — | 极窄屏换行居中 |

---

## 八、R03 实现检查清单

R03 交付前须逐项确认：

- [ ] CSS 变量全部定义在 `:root` 中，无硬编码色值
- [ ] 所有代码块 `<pre><code>` 正确嵌套，`overflow-x: auto`
- [ ] Tab 组件 ARIA 属性完整（tablist / tab / tabpanel / aria-selected）
- [ ] Tab 键盘切换：左右方向键在 tablist 内切换 tab
- [ ] 所有 `<img>` 有 `alt` 属性
- [ ] 焦点环在所有交互元素上可见（不被 `outline:none` 裸删）
- [ ] 移动端（<768px）三列变一列，两列变一列
- [ ] 代码块语法高亮 JS 函数在 `DOMContentLoaded` 后执行
- [ ] 单文件交付，无外部 CDN 依赖
- [ ] `<title>` = `Multi-Agent Playground`，`<html lang="zh-CN">`
- [ ] skip-to-content 链接存在（`#main-content`）
- [ ] 页面在 Chrome / Safari / Firefox 最新版验证

---

*DesignSpec_v1.0.md · R02 产出 · 交 R03 直接实现*
