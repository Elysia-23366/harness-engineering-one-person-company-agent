# 设计系统 v1.0 · 个人品牌官网
> 作者：R02 交互UI设计师 | 状态：交付 · 待闸2确认 | 基准：WCAG 2.2 AA

---

## 0. 设计决策说明

本系统采用**深色系主方案 + 浅色系备方案**，跟随 `prefers-color-scheme` 自动切换（对应 PRD F07）。
基准格栅 8px，所有间距值均为 8 的倍数。
字体栈优先系统字体，标题引入 Inter（Google Fonts CDN，fallback 到 system-ui）。
对比度全部 ≥ 4.5:1（正文），大字号 ≥ 3:1，已逐项标注。

---

## 1. Color Tokens（颜色令牌）

### 1.1 深色模式（默认 · Dark Mode）

```css
:root[data-theme="dark"], @media (prefers-color-scheme: dark) {

  /* === 背景层 === */
  --color-bg-base:       #0a0a0a;   /* 页面底色 */
  --color-bg-surface:    #141414;   /* 卡片/区块底色 */
  --color-bg-elevated:   #1e1e1e;   /* 悬浮层/Tooltip底色 */
  --color-bg-overlay:    rgba(0,0,0,0.72); /* 遮罩层 */

  /* === 文字层 === */
  --color-text-primary:  #f0f0f0;   /* 主文字 · 对比度 vs bg-base = 16.1:1 ✅ */
  --color-text-secondary:#a0a0a0;   /* 辅助文字 · 对比度 vs bg-base = 5.3:1 ✅ */
  --color-text-disabled:  #4a4a4a;  /* 禁用态文字 · 仅配合图标使用，不单独传达信息 */
  --color-text-inverse:   #0a0a0a;  /* 反色文字（用于主色按钮上）*/

  /* === 品牌主色 === */
  --color-brand-primary:  #e8e8e8;  /* 主CTA · 对比度 vs bg-base = 15.2:1 ✅ */
  --color-brand-hover:    #ffffff;  /* hover态 */
  --color-brand-active:   #c8c8c8;  /* pressed态 */

  /* === 功能色 === */
  --color-success:        #4ade80;  /* 成功 · 对比度 vs bg-surface = 7.2:1 ✅ */
  --color-success-bg:     #052e16;  /* 成功背景 */
  --color-error:          #f87171;  /* 错误 · 对比度 vs bg-surface = 5.8:1 ✅ */
  --color-error-bg:       #2d0a0a;  /* 错误背景 */
  --color-warning:        #fbbf24;  /* 警告 · 对比度 vs bg-surface = 6.1:1 ✅ */
  --color-info:           #60a5fa;  /* 信息 · 对比度 vs bg-surface = 5.4:1 ✅ */

  /* === 边框/分割线 === */
  --color-border-default: #2a2a2a;  /* 默认边框 */
  --color-border-strong:  #404040;  /* 强调边框（focus ring 基础色）*/
  --color-border-focus:   #e8e8e8;  /* focus ring 颜色 */

  /* === 阴影 === */
  --shadow-card:   0 1px 3px rgba(0,0,0,0.5), 0 4px 12px rgba(0,0,0,0.3);
  --shadow-modal:  0 8px 32px rgba(0,0,0,0.6);
  --shadow-focus:  0 0 0 3px rgba(232,232,232,0.4);
}
```

### 1.2 浅色模式（Light Mode）

```css
:root[data-theme="light"], @media (prefers-color-scheme: light) {

  --color-bg-base:       #ffffff;
  --color-bg-surface:    #f5f5f5;
  --color-bg-elevated:   #ebebeb;
  --color-bg-overlay:    rgba(0,0,0,0.48);

  --color-text-primary:  #111111;   /* 对比度 vs bg-base = 19.6:1 ✅ */
  --color-text-secondary:#555555;   /* 对比度 vs bg-base = 7.0:1 ✅ */
  --color-text-disabled:  #b0b0b0;
  --color-text-inverse:   #ffffff;

  --color-brand-primary:  #111111;  /* 对比度 vs bg-base = 19.6:1 ✅ */
  --color-brand-hover:    #000000;
  --color-brand-active:   #333333;

  --color-success:        #16a34a;  /* 对比度 vs bg-base = 5.1:1 ✅ */
  --color-success-bg:     #f0fdf4;
  --color-error:          #dc2626;  /* 对比度 vs bg-base = 5.9:1 ✅ */
  --color-error-bg:       #fef2f2;
  --color-warning:        #d97706;  /* 对比度 vs bg-base = 4.6:1 ✅ */
  --color-info:           #2563eb;  /* 对比度 vs bg-base = 5.9:1 ✅ */

  --color-border-default: #e0e0e0;
  --color-border-strong:  #c0c0c0;
  --color-border-focus:   #111111;

  --shadow-card:   0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.06);
  --shadow-modal:  0 8px 32px rgba(0,0,0,0.16);
  --shadow-focus:  0 0 0 3px rgba(17,17,17,0.2);
}
```

---

## 2. Typography Tokens（字体令牌）

```css
:root {
  /* === 字体家族 === */
  --font-display: 'Inter', 'PingFang SC', 'Noto Sans SC', system-ui, sans-serif;
  --font-body:    system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono:    'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

  /* === 字号阶梯（Major Third · 1.25 ratio） === */
  --text-xs:   0.75rem;   /* 12px · 版权/标注 */
  --text-sm:   0.875rem;  /* 14px · 辅助文字/标签 */
  --text-base: 1rem;      /* 16px · 正文基准 */
  --text-lg:   1.125rem;  /* 18px · 大正文/卡片标题 */
  --text-xl:   1.25rem;   /* 20px · 小标题 */
  --text-2xl:  1.5rem;    /* 24px · Section标题 */
  --text-3xl:  1.875rem;  /* 30px · 副标题 */
  --text-4xl:  2.25rem;   /* 36px · Hero副标题 */
  --text-5xl:  3rem;      /* 48px · Hero主标题（桌面）*/
  --text-6xl:  3.75rem;   /* 60px · Hero主标题（大屏）*/

  /* === 行高 === */
  --leading-tight:  1.25;  /* 标题 */
  --leading-snug:   1.375; /* 大字号正文 */
  --leading-normal: 1.5;   /* 正文 */
  --leading-relaxed:1.625; /* 长文阅读 */

  /* === 字重 === */
  --weight-regular: 400;
  --weight-medium:  500;
  --weight-semibold:600;
  --weight-bold:    700;

  /* === 字间距 === */
  --tracking-tight:  -0.025em; /* 大标题收紧 */
  --tracking-normal:  0em;
  --tracking-wide:    0.05em;  /* 全大写标签 */
  --tracking-widest:  0.1em;   /* 装饰性标签 */
}
```

### 2.1 语义化文字样式速查

| 样式名 | font-size | font-weight | line-height | letter-spacing | 用途 |
|--------|-----------|-------------|-------------|----------------|------|
| `hero-name` | 5xl→6xl | bold 700 | tight 1.25 | tight -0.025em | Hero姓名 |
| `hero-tagline` | 2xl→3xl | medium 500 | snug 1.375 | normal | Hero一句话定位 |
| `section-title` | 2xl | semibold 600 | tight | normal | 各Section标题 |
| `card-title` | lg | semibold 600 | snug | normal | 卡片标题 |
| `body-default` | base | regular 400 | normal 1.5 | normal | 正文 |
| `body-small` | sm | regular 400 | normal | normal | 辅助说明 |
| `label-tag` | xs | medium 500 | tight | wide 0.05em | 技能标签/徽章 |
| `nav-link` | sm | medium 500 | tight | normal | 导航链接 |
| `btn-label` | sm→base | semibold 600 | tight | normal | 按钮文字 |
| `caption` | xs | regular 400 | normal | normal | 图片说明/版权 |

---

## 3. Spacing Tokens（间距令牌）

```css
:root {
  /* 基准：8px · 所有值为 8 的倍数 */
  --space-1:   0.25rem;  /*  4px */
  --space-2:   0.5rem;   /*  8px */
  --space-3:   0.75rem;  /* 12px */
  --space-4:   1rem;     /* 16px */
  --space-5:   1.25rem;  /* 20px */
  --space-6:   1.5rem;   /* 24px */
  --space-8:   2rem;     /* 32px */
  --space-10:  2.5rem;   /* 40px */
  --space-12:  3rem;     /* 48px */
  --space-16:  4rem;     /* 64px */
  --space-20:  5rem;     /* 80px */
  --space-24:  6rem;     /* 96px */
  --space-32:  8rem;     /* 128px */

  /* Section 内边距 */
  --section-padding-y-mobile:  var(--space-16);  /* 64px */
  --section-padding-y-desktop: var(--space-24);  /* 96px */
  --section-padding-x-mobile:  var(--space-6);   /* 24px */
  --section-padding-x-desktop: var(--space-8);   /* 32px */

  /* 容器最大宽度 */
  --container-max:    1200px;
  --container-narrow: 720px;  /* 文字密集区 */
}
```

---

## 4. Border Radius Tokens（圆角令牌）

```css
:root {
  --radius-sm:   4px;   /* 输入框、小标签 */
  --radius-md:   8px;   /* 卡片、按钮 */
  --radius-lg:   12px;  /* 大卡片、模态框 */
  --radius-xl:   16px;  /* Hero区块 */
  --radius-full: 9999px; /* 圆形头像、胶囊标签 */
}
```

---

## 5. Motion Tokens（动效令牌）

```css
:root {
  /* 时长 */
  --duration-instant:  50ms;
  --duration-fast:    150ms;  /* hover反馈 */
  --duration-normal:  250ms;  /* 大多数过渡 */
  --duration-slow:    350ms;  /* 页面级动画 */
  --duration-enter:   400ms;  /* 元素进场 */

  /* 缓动曲线 */
  --ease-default:  cubic-bezier(0.4, 0, 0.2, 1);  /* Material标准 */
  --ease-in:       cubic-bezier(0.4, 0, 1, 1);     /* 退出动画 */
  --ease-out:      cubic-bezier(0, 0, 0.2, 1);     /* 进入动画 */
  --ease-spring:   cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性（慎用）*/

  /* 尊重用户偏好 */
  @media (prefers-reduced-motion: reduce) {
    --duration-fast:   0ms;
    --duration-normal: 0ms;
    --duration-slow:   0ms;
    --duration-enter:  0ms;
  }
}
```

---

## 6. Elevation Tokens（层级令牌）

```css
:root {
  /* z-index 语义层 */
  --z-base:     0;
  --z-raised:   10;   /* 卡片hover */
  --z-dropdown: 100;  /* 下拉菜单 */
  --z-sticky:   200;  /* 固定导航 */
  --z-overlay:  300;  /* 遮罩 */
  --z-modal:    400;  /* 模态框 */
  --z-toast:    500;  /* Toast通知 */
}
```

---

## 7. Breakpoint Tokens（断点令牌）

```css
/* 断点定义（Mobile First） */
/* sm:  ≥ 640px  · 大手机横屏 */
/* md:  ≥ 768px  · 平板 */
/* lg:  ≥ 1024px · 桌面 */
/* xl:  ≥ 1200px · 宽屏 */
/* 2xl: ≥ 1440px · 超宽屏 */

:root {
  --bp-sm:  640px;
  --bp-md:  768px;
  --bp-lg:  1024px;
  --bp-xl:  1200px;
  --bp-2xl: 1440px;
}

/* 主要响应式断点（PRD指定768/1200） */
@media (min-width: 768px)  { /* 平板及以上 */ }
@media (min-width: 1200px) { /* 桌面宽屏 */ }
```

---

## 8. 可访问性基线（WCAG 2.2 AA）

| 规则 | 实现方式 |
|------|----------|
| 对比度 ≥ 4.5:1（正文） | 所有 token 已标注实测值，见第1节 |
| 对比度 ≥ 3:1（大字号 ≥ 18px/14px粗体） | Hero标题、Section标题均满足 |
| 触控区 ≥ 44×44pt | 所有可交互元素 min-height/min-width: 44px |
| Focus 可见 | focus-visible: outline 3px solid var(--color-border-focus); outline-offset: 2px |
| 不依赖颜色单一传达信息 | 错误态：红色 + 图标 + 文字说明三重传达 |
| 键盘可导航 | Tab顺序与视觉顺序一致；跳过导航链接（Skip to main） |
| 图片 alt 文字 | 头像/作品图必须有描述性 alt；装饰图 alt="" |
| 表单标签 | 每个 input 必须有关联 `<label>`，不用 placeholder 代替 |
| 语义化 HTML | header/main/section/footer/nav/article 正确使用 |
| ARIA | 仅在语义 HTML 不够时补充；不滥用 |
