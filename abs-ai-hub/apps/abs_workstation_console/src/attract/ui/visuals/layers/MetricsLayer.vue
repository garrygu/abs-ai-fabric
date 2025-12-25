<script setup lang="ts">
import { computed } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useCESMode } from '@/composables/useCESMode'

const metricsStore = useMetricsStore()
const { isCESMode } = useCESMode()

const displayGpuUtil = computed(() => Math.round(metricsStore.gpuUtilization))
const displayVramUsed = computed(() => metricsStore.vramUsed.toFixed(1))
const displayVramTotal = computed(() => metricsStore.vramTotal.toFixed(0))
const displayCpuUtil = computed(() => Math.round(metricsStore.cpuUtilization))
const displayRamUsed = computed(() => metricsStore.memoryUsed.toFixed(0))
const displayRamTotal = computed(() => metricsStore.memoryTotal.toFixed(0))
</script>

<template>
  <div class="metrics-layer" :class="{ 'metrics-layer--ces': isCESMode }">
    <!-- GPU Utilization - Primary -->
    <div class="metric-block metric-block--gpu">
      <div class="metric-label">GPU UTIL</div>
      <div class="metric-value-row">
        <span class="metric-value">{{ displayGpuUtil }}</span>
        <span class="metric-unit">%</span>
      </div>
    </div>
    
    <!-- VRAM -->
    <div class="metric-block">
      <div class="metric-label">VRAM</div>
      <div class="metric-value-row">
        <span class="metric-value metric-value--sm">{{ displayVramUsed }}</span>
        <span class="metric-unit">/ {{ displayVramTotal }} GB</span>
      </div>
    </div>
    
    <!-- CPU -->
    <div class="metric-block">
      <div class="metric-label">CPU LOAD</div>
      <div class="metric-value-row">
        <span class="metric-value metric-value--sm">{{ displayCpuUtil }}</span>
        <span class="metric-unit">%</span>
      </div>
    </div>
    
    <!-- RAM -->
    <div class="metric-block">
      <div class="metric-label">RAM</div>
      <div class="metric-value-row">
        <span class="metric-value metric-value--sm">{{ displayRamUsed }}</span>
        <span class="metric-unit">/ {{ displayRamTotal }} GB</span>
      </div>
    </div>
    
    <!-- GPU Model + Uptime -->
    <div class="metric-footer">
      <span class="gpu-model">{{ metricsStore.gpuModel }}</span>
      <span class="divider">•</span>
      <span class="uptime">Uptime {{ metricsStore.uptimeFormatted }}</span>
    </div>
  </div>
</template>

<style scoped>
.metrics-layer {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 320px;
}

.metric-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-block--gpu {
  margin-bottom: 8px;
}

.metric-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
}

.metric-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.metric-value {
  font-family: var(--font-mono);
  font-size: 4rem;
  font-weight: 600;
  line-height: 1;
  color: var(--text-primary);
  transition: all var(--duration-normal) var(--ease-smooth);
}

.metric-value--sm {
  font-size: 2.5rem;
}

.metric-block--gpu .metric-value {
  color: var(--abs-orange);
  text-shadow: 0 0 30px var(--abs-orange-glow);
}

.metric-unit {
  font-family: var(--font-label);
  font-size: 1.25rem;
  color: var(--text-secondary);
}

.metric-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  font-family: var(--font-label);
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.divider {
  color: var(--text-muted);
}

.gpu-model {
  font-weight: 600;
}

.uptime {
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

/* CES Mode: Larger fonts */
.metrics-layer--ces .metric-value {
  font-size: 5rem;
}

.metrics-layer--ces .metric-value--sm {
  font-size: 3rem;
}
</style>

