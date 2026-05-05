<script setup>
/**
 * HarnessPage · W2 Harness 双控台壳页面
 *
 * D8: GuidesPanel(前馈)
 * D9: SensorsPanel(反馈)
 * D10: MemoryDashboard(三库)
 * D11: DriftRadar
 * D13: EvolutionChart
 * 全部组件挂在这一页,D12 会再把核心摘要搬到 OverviewPage hero。
 */
import DriftRadar from "../components/harness/DriftRadar.vue";
import EvolutionChart from "../components/harness/EvolutionChart.vue";
import GuidesPanel from "../components/harness/GuidesPanel.vue";
import MemoryDashboard from "../components/harness/MemoryDashboard.vue";
import SensorsPanel from "../components/harness/SensorsPanel.vue";
import SevenModuleDashboard from "../components/harness/SevenModuleDashboard.vue";

defineProps({
  agents: { type: Array, default: () => [] },
});
</script>

<template>
  <div class="harness-page">
    <SevenModuleDashboard />

    <GuidesPanel :agents="agents" />

    <SensorsPanel :agents="agents" />

    <MemoryDashboard :agents="agents" />

    <DriftRadar :agents="agents" />

    <EvolutionChart />
  </div>
</template>

<style scoped>
.harness-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 24px 32px 48px;
  max-width: 1480px;
  margin: 0 auto;
  font-family: var(--ff-sans, "Source Sans 3", system-ui, sans-serif);
  color: var(--c-near-black, #141413);
}

/* Hero */
.hp-hero {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 30px 32px 32px;
  background:
    radial-gradient(80% 120% at 0% 0%, var(--c-terracotta-soft, rgba(201, 100, 66, 0.08)) 0%, transparent 50%),
    var(--c-ivory, #faf9f5);
  border: 1px solid var(--c-ring-warm, #d1cfc5);
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(20, 20, 19, 0.04);
}
.hp-hero-tag {
  display: inline-block;
  padding: 4px 10px;
  font-family: var(--ff-mono, "Source Code Pro", ui-monospace, monospace);
  font-size: 11px;
  letter-spacing: 0.06em;
  color: var(--c-terracotta, #c96442);
  background: var(--c-terracotta-soft, rgba(201, 100, 66, 0.10));
  border-radius: 6px;
  width: max-content;
}
.hp-hero-title {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 36px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.15;
}
.hp-hero-accent { color: var(--c-terracotta, #c96442); font-style: italic; }
.hp-hero-sub {
  margin: 0;
  font-size: 14px;
  color: var(--c-stone, #87867f);
  line-height: 1.6;
  max-width: 720px;
}

/* Coming-soon placeholders for D9-D11 */
.hp-coming {
  margin-top: 12px;
}
.hp-coming-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}
.hp-coming-card {
  background: var(--c-parchment, #f5f4ed);
  border: 1px dashed var(--c-border-warm, #e8e6dc);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.hp-coming-tag {
  font-family: var(--ff-mono, "Source Code Pro", monospace);
  font-size: 10px;
  letter-spacing: 0.06em;
  color: var(--c-stone);
}
.hp-coming-card h3 {
  margin: 0;
  font-family: var(--ff-serif, "Fraunces", serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--c-charcoal, #4d4c48);
}
.hp-coming-card p {
  margin: 0;
  font-size: 12px;
  color: var(--c-stone);
  line-height: 1.5;
}

@media (max-width: 720px) {
  .harness-page { padding: 16px 14px 36px; }
  .hp-hero { padding: 22px 18px; }
  .hp-hero-title { font-size: 26px; }
}
</style>
