<script setup lang="ts">
import { computed } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useCESMode } from '@/composables/useCESMode'

const metricsStore = useMetricsStore()
const { isCESMode } = useCESMode()

// Animated number display with interpolation
const displayGpuUtil = computed(() => Math.round(metricsStore.gpuUtilization))
const displayCpuUtil = computed(() => Math.round(metricsStore.cpuUtilization))
const displayVramUsed = computed(() => metricsStore.vramUsed.toFixed(1))
const displayVramTotal = computed(() => metricsStore.vramTotal.toFixed(0))
const displayRamUsed = computed(() => metricsStore.memoryUsed.toFixed(0))
const displayRamTotal = computed(() => metricsStore.memoryTotal.toFixed(0))
</script>

<template>
  <div class="metrics-panel">
    <div class="section-header">
      <h2 class="section-title">Live System Metrics</h2>
      <span class="last-updated text-muted">Updated {{ metricsStore.timeSinceUpdate }}</span>
    </div>
    
    <div class="metrics-grid">
      <!-- GPU Utilization - HERO TILE -->
      <div class="metric-tile metric-tile--hero card card--gpu">
        <div class="metric-tile__header">
          <span class="metric-tile__icon">⚡</span>
          <span class="metric-tile__label">GPU Utilization</span>
        </div>
        <div class="metric-tile__body">
          <span class="metric-tile__value metric-value">{{ displayGpuUtil }}</span>
          <span class="metric-tile__unit">%</span>
        </div>
        <div class="metric-tile__footer">
          <span class="gpu-model text-secondary">{{ metricsStore.gpuModel }}</span>
        </div>
        <div class="metric-bar">
          <div class="metric-bar__fill metric-bar__fill--gpu" :style="{ width: `${displayGpuUtil}%` }"></div>
        </div>
      </div>
      
      <!-- VRAM Usage -->
      <div class="metric-tile card">
        <div class="metric-tile__header">
          <span class="metric-tile__icon">🎯</span>
          <span class="metric-tile__label">VRAM</span>
        </div>
        <div class="metric-tile__body">
          <span class="metric-tile__value metric-value">{{ displayVramUsed }}</span>
          <span class="metric-tile__unit">/ {{ displayVramTotal }} GB</span>
        </div>
        <div class="metric-bar">
          <div class="metric-bar__fill" :style="{ width: `${metricsStore.vramPercent}%` }"></div>
        </div>
      </div>
      
      <!-- CPU Utilization -->
      <div class="metric-tile card">
        <div class="metric-tile__header">
          <span class="metric-tile__icon">🔷</span>
          <span class="metric-tile__label">CPU Load</span>
        </div>
        <div class="metric-tile__body">
          <span class="metric-tile__value metric-value">{{ displayCpuUtil }}</span>
          <span class="metric-tile__unit">%</span>
        </div>
        <div class="metric-bar">
          <div class="metric-bar__fill" :style="{ width: `${displayCpuUtil}%` }"></div>
        </div>
      </div>
      
      <!-- RAM Usage -->
      <div class="metric-tile card">
        <div class="metric-tile__header">
          <span class="metric-tile__icon">💾</span>
          <span class="metric-tile__label">System Memory</span>
        </div>
        <div class="metric-tile__body">
          <span class="metric-tile__value metric-value">{{ displayRamUsed }}</span>
          <span class="metric-tile__unit">/ {{ displayRamTotal }} GB</span>
        </div>
        <div class="metric-bar">
          <div class="metric-bar__fill" :style="{ width: `${metricsStore.memoryPercent}%` }"></div>
        </div>
      </div>
      
      <!-- Uptime -->
      <div class="metric-tile metric-tile--compact card">
        <div class="metric-tile__header">
          <span class="metric-tile__icon">⏱️</span>
          <span class="metric-tile__label">Uptime</span>
        </div>
        <div class="metric-tile__body">
          <span class="metric-tile__value metric-value metric-value--mono">{{ metricsStore.uptimeFormatted }}</span>
        </div>
      </div>
    </div>
    
    <!-- CES Mode: Script line -->
    <div v-if="isCESMode" class="ces-script">
      <p>"Everything you're seeing is running locally on this workstation, right now."</p>
    </div>
  </div>
</template>

<style scoped>
.metrics-panel {
  width: 100%;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}

.section-title {
  font-size: 1.375rem;
  margin: 0;
}

.last-updated {
  font-size: 0.75rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.metric-tile {
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.metric-tile--hero {
  grid-column: span 2;
  padding: 32px;
}

.metric-tile--compact {
  grid-column: span 2;
}

.metric-tile__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.metric-tile__icon {
  font-size: 1.25rem;
}

.metric-tile__label {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
}

.metric-tile__body {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.metric-tile__value {
  font-size: 3rem;
  line-height: 1;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.metric-tile--hero .metric-tile__value {
  font-size: 4.5rem;
}

.metric-tile__unit {
  font-family: var(--font-label);
  font-size: 1.25rem;
  color: var(--text-secondary);
}

.metric-tile--hero .metric-tile__unit {
  font-size: 1.75rem;
}

.metric-tile__footer {
  margin-top: 12px;
}

.gpu-model {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 500;
}

.metric-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--border-subtle);
}

.metric-bar__fill {
  height: 100%;
  background: var(--electric-indigo);
  transition: width var(--duration-normal) var(--ease-smooth);
}

.metric-bar__fill--gpu {
  background: var(--abs-orange);
  box-shadow: 0 0 10px var(--abs-orange-glow);
}

.metric-value--mono {
  letter-spacing: 0.02em;
}

.ces-script {
  margin-top: 32px;
  padding: 20px 24px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 8px;
}

.ces-script p {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-style: italic;
  color: var(--text-secondary);
  margin: 0;
}

/* CES Mode: Larger metrics */
.ces-mode .metric-tile__value {
  font-size: 3.5rem;
}

.ces-mode .metric-tile--hero .metric-tile__value {
  font-size: 5.5rem;
}

@media (min-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .metric-tile--hero {
    grid-column: span 2;
    grid-row: span 2;
  }
  
  .metric-tile--compact {
    grid-column: span 2;
  }
}
</style>
