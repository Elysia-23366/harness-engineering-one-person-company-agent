import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";
import "./style.inkway.css"; // 「墨道」视觉系统 · 叠加在 style.css 之后,优先级更高

// 性能模式标记 · 给 CSS 选择器和动效用
const perfMode = {
  isMobile: matchMedia("(max-width: 640px)").matches,
  isLowCore: navigator.hardwareConcurrency < 4,
  reduceMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
  noHover: !matchMedia("(hover: hover)").matches,
};
document.documentElement.dataset.perf = JSON.stringify(perfMode);

createApp(App).mount("#app");
