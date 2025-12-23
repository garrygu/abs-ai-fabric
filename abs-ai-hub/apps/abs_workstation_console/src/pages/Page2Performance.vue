<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'

const metricsStore = useMetricsStore()

// Store history for charts - longer history for smoother visualization
const historyLength = 60 // 60 data points = ~2 minutes at 2s intervals
const gpuHistory = ref<number[]>([])
const cpuHistory = ref<number[]>([])
const vramHistory = ref<number[]>([])
const ramHistory = ref<number[]>([])
const diskReadHistory = ref<number[]>([])
const diskWriteHistory = ref<number[]>([])

function updateHistory() {
  gpuHistory.value = [...gpuHistory.value.slice(-historyLength + 1), metricsStore.gpuUtilization]
  cpuHistory.value = [...cpuHistory.value.slice(-historyLength + 1), metricsStore.cpuUtilization]
  vramHistory.value = [...vramHistory.value.slice(-historyLength + 1), metricsStore.vramPercent]
  ramHistory.value = [...ramHistory.value.slice(-historyLength + 1), metricsStore.memoryPercent]
  diskReadHistory.value = [...diskReadHistory.value.slice(-historyLength + 1), metricsStore.diskRead]
  diskWriteHistory.value = [...diskWriteHistory.value.slice(-historyLength + 1), metricsStore.diskWrite]
}

let historyInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // Wait for initial metrics to load before initializing history
  // This prevents initializing with all zeros
  const initializeHistory = () => {
    const initialGpu = metricsStore.gpuUtilization || 0
    const initialCpu = metricsStore.cpuUtilization || 0
    const initialVram = metricsStore.vramPercent || 0
    const initialRam = metricsStore.memoryPercent || 0
    const initialDiskRead = metricsStore.diskRead || 0
    const initialDiskWrite = metricsStore.diskWrite || 0
    
    // Only initialize if we have at least some data, or after a short delay
    if (metricsStore.metrics || gpuHistory.value.length === 0) {
      for (let i = 0; i < historyLength; i++) {
        gpuHistory.value.push(initialGpu)
        cpuHistory.value.push(initialCpu)
        vramHistory.value.push(initialVram)
        ramHistory.value.push(initialRam)
        diskReadHistory.value.push(initialDiskRead)
        diskWriteHistory.value.push(initialDiskWrite)
      }
    }
  }
  
  // Initialize immediately if data exists, otherwise wait a bit
  if (metricsStore.metrics) {
    initializeHistory()
  } else {
    // Wait for first metrics fetch (max 3 seconds)
    const checkInterval = setInterval(() => {
      if (metricsStore.metrics || metricsStore.error) {
        initializeHistory()
        clearInterval(checkInterval)
      }
    }, 100)
    
    setTimeout(() => {
      clearInterval(checkInterval)
      initializeHistory() // Initialize anyway after timeout
    }, 3000)
  }
  
  historyInterval = setInterval(updateHistory, 2000)
})

onUnmounted(() => {
  if (historyInterval) clearInterval(historyInterval)
})

// Smooth chart path generation with better interpolation
function getChartPath(data: number[], height: number, smooth: boolean = true): string {
  if (data.length === 0) return ''
  const width = 100
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - (Math.max(0, Math.min(100, val)) / 100) * height
    return { x, y }
  })
  
  if (!smooth || points.length < 3) {
    return `M ${points.map(p => `${p.x},${p.y}`).join(' L ')}`
  }
  
  // Create smooth curve using quadratic bezier
  let path = `M ${points[0].x},${points[0].y}`
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const next = points[i + 1] || curr
    
    const cp1x = prev.x + (curr.x - prev.x) / 2
    const cp1y = prev.y
    const cp2x = curr.x - (next.x - curr.x) / 2
    const cp2y = curr.y
    
    path += ` Q ${cp1x},${cp1y} ${(prev.x + curr.x) / 2},${(prev.y + curr.y) / 2}`
    if (i < points.length - 1) {
      path += ` T ${curr.x},${curr.y}`
    } else {
      path += ` L ${curr.x},${curr.y}`
    }
  }
  
  return path
}

// Area fill path (for gradient fills)
function getAreaPath(data: number[], height: number): string {
  const linePath = getChartPath(data, height, true)
  return `${linePath} L 100,${height} L 0,${height} Z`
}

const gpuPath = computed(() => getChartPath(gpuHistory.value, 80, true))
const gpuAreaPath = computed(() => getAreaPath(gpuHistory.value, 80))
const cpuPath = computed(() => getChartPath(cpuHistory.value, 80, true))
const cpuAreaPath = computed(() => getAreaPath(cpuHistory.value, 80))
const vramPath = computed(() => getChartPath(vramHistory.value, 80, true))
const vramAreaPath = computed(() => getAreaPath(vramHistory.value, 80))
const ramPath = computed(() => getChartPath(ramHistory.value, 80, true))
const diskReadPath = computed(() => {
  // Normalize disk read to 0-100 scale (assuming max 500 MB/s for visualization)
  const normalized = diskReadHistory.value.map(v => Math.min(100, (v / 500) * 100))
  return getChartPath(normalized, 60, true)
})
const diskReadAreaPath = computed(() => {
  const normalized = diskReadHistory.value.map(v => Math.min(100, (v / 500) * 100))
  return getAreaPath(normalized, 60)
})
const diskWritePath = computed(() => {
  // Normalize disk write to 0-100 scale
  const normalized = diskWriteHistory.value.map(v => Math.min(100, (v / 500) * 100))
  return getChartPath(normalized, 60, true)
})
const diskWriteAreaPath = computed(() => {
  const normalized = diskWriteHistory.value.map(v => Math.min(100, (v / 500) * 100))
  return getAreaPath(normalized, 60)
})

// Headroom calculations
const gpuHeadroom = computed(() => 100 - metricsStore.gpuUtilization)
const vramHeadroom = computed(() => 100 - metricsStore.vramPercent)
const ramHeadroom = computed(() => 100 - metricsStore.memoryPercent)
</script>

<template>
  <div class="page page-performance">
    <div class="page-header">
      <h1 class="page-title">PERFORMANCE & TELEMETRY</h1>
      <p class="page-subtitle">Real-time system utilization</p>
      <div v-if="metricsStore.error" class="error-banner">
        <span class="error-icon">⚠️</span>
        <span class="error-text">{{ metricsStore.error }}</span>
        <span class="error-note">Using simulated data</span>
      </div>
      <div v-if="metricsStore.isLoading && !metricsStore.metrics" class="loading-indicator">
        Loading metrics...
      </div>
      <div v-if="metricsStore.metrics" class="status-indicator">
        <span class="status-dot status-dot--running"></span>
        <span class="status-text">Last updated: {{ metricsStore.timeSinceUpdate }}</span>
      </div>
    </div>

    <!-- GPU Utilization Timeline (Primary, Full Width) -->
    <div class="metric-section metric-section--primary">
      <div class="metric-card metric-card--gpu">
        <div class="metric-card__header">
          <div class="metric-card__title-group">
            <span class="metric-icon">⚡</span>
            <div class="metric-card__title-info">
              <h2 class="metric-card__title">GPU Utilization</h2>
              <span class="metric-card__subtitle">{{ metricsStore.gpuModel }}</span>
            </div>
          </div>
          <div class="metric-card__value-group">
            <span class="metric-value-large">{{ Math.round(metricsStore.gpuUtilization) }}</span>
            <span class="metric-unit">%</span>
            <div class="headroom-indicator">
              <span class="headroom-label">Headroom</span>
              <span class="headroom-value">{{ Math.round(gpuHeadroom) }}%</span>
            </div>
          </div>
        </div>
        <div class="chart-container chart-container--timeline">
          <svg viewBox="0 0 100 80" preserveAspectRatio="none" class="chart-svg chart-svg--timeline">
            <defs>
              <linearGradient id="gpuGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="var(--abs-orange)" stop-opacity="0.5"/>
                <stop offset="50%" stop-color="var(--abs-orange)" stop-opacity="0.2"/>
                <stop offset="100%" stop-color="var(--abs-orange)" stop-opacity="0"/>
              </linearGradient>
              <filter id="gpuGlow">
                <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            <!-- Grid lines for depth -->
            <line x1="0" y1="20" x2="100" y2="20" stroke="rgba(255,255,255,0.05)" stroke-width="0.3"/>
            <line x1="0" y1="40" x2="100" y2="40" stroke="rgba(255,255,255,0.05)" stroke-width="0.3"/>
            <line x1="0" y1="60" x2="100" y2="60" stroke="rgba(255,255,255,0.05)" stroke-width="0.3"/>
            <!-- Area fill -->
            <path :d="gpuAreaPath" fill="url(#gpuGradient)" class="chart-area"/>
            <!-- Line -->
            <path :d="gpuPath" fill="none" stroke="var(--abs-orange)" stroke-width="0.8" 
                  class="chart-line chart-line--gpu" filter="url(#gpuGlow)"/>
          </svg>
          <div class="chart-labels">
            <span class="chart-label">2 min ago</span>
            <span class="chart-label">Now</span>
          </div>
        </div>
      </div>
    </div>

    <!-- VRAM Usage & CPU/RAM (Side by Side) -->
    <div class="metric-section metric-section--dual">
      <!-- VRAM Usage -->
      <div class="metric-card">
        <div class="metric-card__header">
          <div class="metric-card__title-group">
            <span class="metric-icon">🎯</span>
            <h2 class="metric-card__title">VRAM Usage</h2>
          </div>
          <div class="metric-card__value-group">
            <span class="metric-value">{{ metricsStore.vramUsed.toFixed(1) }}</span>
            <span class="metric-unit">/ {{ metricsStore.vramTotal }} GB</span>
          </div>
        </div>
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-bar__fill progress-bar__fill--vram" 
                 :style="{ width: `${metricsStore.vramPercent}%` }">
              <div class="progress-bar__glow"></div>
            </div>
            <div class="progress-bar__headroom" 
                 :style="{ width: `${vramHeadroom}%` }"></div>
          </div>
          <div class="progress-info">
            <span class="progress-label">{{ Math.round(metricsStore.vramPercent) }}% Used</span>
            <span class="progress-label progress-label--headroom">{{ Math.round(vramHeadroom) }}% Available</span>
          </div>
        </div>
        <div class="chart-container chart-container--mini">
          <svg viewBox="0 0 100 80" preserveAspectRatio="none" class="chart-svg">
            <defs>
              <linearGradient id="vramGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#22c55e" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#22c55e" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path :d="vramAreaPath" fill="url(#vramGradient)" class="chart-area"/>
            <path :d="vramPath" fill="none" stroke="#22c55e" stroke-width="0.5" class="chart-line"/>
          </svg>
        </div>
      </div>

      <!-- CPU / RAM Combined -->
      <div class="metric-card">
        <div class="metric-card__header">
          <div class="metric-card__title-group">
            <span class="metric-icon">🔷</span>
            <h2 class="metric-card__title">CPU / RAM</h2>
          </div>
        </div>
        <div class="dual-metric-group">
          <!-- CPU -->
          <div class="dual-metric">
            <div class="dual-metric__header">
              <span class="dual-metric__label">CPU Load</span>
              <span class="dual-metric__value">{{ Math.round(metricsStore.cpuUtilization) }}%</span>
            </div>
            <div class="progress-bar progress-bar--small">
              <div class="progress-bar__fill progress-bar__fill--cpu" 
                   :style="{ width: `${metricsStore.cpuUtilization}%` }"></div>
            </div>
          </div>
          <!-- RAM -->
          <div class="dual-metric">
            <div class="dual-metric__header">
              <span class="dual-metric__label">RAM</span>
              <span class="dual-metric__value">{{ metricsStore.memoryUsed.toFixed(0) }} / {{ metricsStore.memoryTotal }} GB</span>
            </div>
            <div class="progress-bar progress-bar--small">
              <div class="progress-bar__fill progress-bar__fill--ram" 
                   :style="{ width: `${metricsStore.memoryPercent}%` }"></div>
            </div>
            <div class="progress-info progress-info--small">
              <span class="progress-label">{{ Math.round(metricsStore.memoryPercent) }}% Used</span>
              <span class="progress-label progress-label--headroom">{{ Math.round(ramHeadroom) }}% Free</span>
            </div>
          </div>
        </div>
        <div class="chart-container chart-container--mini">
          <svg viewBox="0 0 100 80" preserveAspectRatio="none" class="chart-svg">
            <defs>
              <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="var(--electric-indigo)" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="var(--electric-indigo)" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path :d="cpuAreaPath" fill="url(#cpuGradient)" class="chart-area"/>
            <path :d="cpuPath" fill="none" stroke="var(--electric-indigo)" stroke-width="0.5" class="chart-line"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- Disk IO (Optional) -->
    <div class="metric-section metric-section--disk">
      <div class="metric-card">
        <div class="metric-card__header">
          <div class="metric-card__title-group">
            <span class="metric-icon">💾</span>
            <h2 class="metric-card__title">Disk I/O</h2>
          </div>
          <div class="metric-card__value-group">
            <div class="disk-metric">
              <span class="disk-label">Read</span>
              <span class="disk-value">{{ metricsStore.diskRead.toFixed(0) }} MB/s</span>
            </div>
            <div class="disk-metric">
              <span class="disk-label">Write</span>
              <span class="disk-value">{{ metricsStore.diskWrite.toFixed(0) }} MB/s</span>
            </div>
          </div>
        </div>
        <div class="chart-container chart-container--disk">
          <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="chart-svg">
            <defs>
              <linearGradient id="diskReadGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
              </linearGradient>
              <linearGradient id="diskWriteGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <!-- Read -->
            <path :d="diskReadAreaPath" 
                  fill="url(#diskReadGradient)" class="chart-area"/>
            <path :d="diskReadPath" fill="none" stroke="#3b82f6" stroke-width="0.5" 
                  class="chart-line chart-line--read"/>
            <!-- Write -->
            <path :d="diskWriteAreaPath" 
                  fill="url(#diskWriteGradient)" class="chart-area"/>
            <path :d="diskWritePath" fill="none" stroke="#8b5cf6" stroke-width="0.5" 
                  class="chart-line chart-line--write"/>
          </svg>
          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-dot legend-dot--read"></span>
              <span class="legend-label">Read</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot legend-dot--write"></span>
              <span class="legend-label">Write</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-performance {
  padding: 40px 24px;
  max-width: var(--container-max);
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 48px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
}

.error-icon {
  font-size: 1.25rem;
}

.error-text {
  flex: 1;
  color: var(--status-error);
}

.error-note {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.loading-indicator {
  margin-top: 16px;
  padding: 12px 16px;
  text-align: center;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--status-success);
}

.status-text {
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-section {
  margin-bottom: 32px;
}

.metric-section--primary {
  margin-bottom: 40px;
}

.metric-card {
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 32px;
  overflow: hidden;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.metric-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-md);
}

.metric-card--gpu {
  border-color: rgba(249, 115, 22, 0.3);
  background: linear-gradient(135deg, var(--abs-card) 0%, rgba(249, 115, 22, 0.05) 100%);
}

.metric-card--gpu:hover {
  border-color: var(--abs-orange);
  box-shadow: var(--shadow-glow-orange);
}

.metric-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 24px;
}

.metric-card__title-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.metric-icon {
  font-size: 2rem;
  line-height: 1;
}

.metric-card__title-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-card__title {
  font-family: var(--font-label);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0;
}

.metric-card__subtitle {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: none;
  letter-spacing: 0.04em;
}

.metric-card__value-group {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.metric-value-large {
  font-family: var(--font-mono);
  font-size: 4rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.metric-value {
  font-family: var(--font-mono);
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.metric-unit {
  font-family: var(--font-label);
  font-size: 1.25rem;
  color: var(--text-secondary);
}

.headroom-indicator {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: 16px;
  padding-left: 16px;
  border-left: 1px solid var(--border-subtle);
}

.headroom-label {
  font-family: var(--font-label);
  font-size: 0.625rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.headroom-value {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--status-success);
  line-height: 1;
}

.chart-container {
  position: relative;
  margin-top: 24px;
}

.chart-container--timeline {
  height: 200px;
}

.chart-container--mini {
  height: 80px;
  margin-top: 16px;
}

.chart-container--disk {
  height: 120px;
}

.chart-svg {
  width: 100%;
  height: 100%;
}

.chart-svg--timeline {
  filter: drop-shadow(0 0 2px rgba(249, 115, 22, 0.3));
}

.chart-area {
  transition: d 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-line {
  transition: d 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-line--gpu {
  filter: drop-shadow(0 0 3px rgba(249, 115, 22, 0.5));
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  padding: 0 4px;
}

.chart-label {
  font-family: var(--font-label);
  font-size: 0.625rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Progress Bars */
.progress-container {
  margin-top: 16px;
}

.progress-bar {
  position: relative;
  height: 12px;
  background: var(--abs-dark);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
}

.progress-bar--small {
  height: 8px;
  border-radius: 4px;
}

.progress-bar__fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  border-radius: 6px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 2;
}

.progress-bar__fill--vram {
  background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

.progress-bar__fill--cpu {
  background: linear-gradient(90deg, var(--electric-indigo) 0%, #4f46e5 100%);
  box-shadow: 0 0 6px rgba(99, 102, 241, 0.3);
}

.progress-bar__fill--ram {
  background: linear-gradient(90deg, #6366f1 0%, #818cf8 100%);
  box-shadow: 0 0 6px rgba(99, 102, 241, 0.3);
}

.progress-bar__glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 100%);
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

.progress-bar__headroom {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 0 6px 6px 0;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-family: var(--font-label);
  font-size: 0.75rem;
}

.progress-info--small {
  font-size: 0.625rem;
  margin-top: 4px;
}

.progress-label {
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.progress-label--headroom {
  color: var(--status-success);
}

/* Dual Metric Layout */
.metric-section--dual {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.dual-metric-group {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 16px;
}

.dual-metric {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dual-metric__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dual-metric__label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dual-metric__value {
  font-family: var(--font-mono);
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

/* Disk IO */
.metric-section--disk {
  margin-bottom: 0;
}

.disk-metric {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  margin-left: 24px;
}

.disk-label {
  font-family: var(--font-label);
  font-size: 0.625rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.disk-value {
  font-family: var(--font-mono);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.chart-legend {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  padding: 0 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot--read {
  background: #3b82f6;
  box-shadow: 0 0 4px rgba(59, 130, 246, 0.5);
}

.legend-dot--write {
  background: #8b5cf6;
  box-shadow: 0 0 4px rgba(139, 92, 246, 0.5);
}

.legend-label {
  font-family: var(--font-label);
  font-size: 0.625rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Responsive */
@media (min-width: 768px) {
  .metric-section--dual {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .metric-card__header {
    flex-wrap: wrap;
  }
}

@media (min-width: 1024px) {
  .page-performance {
    padding: 48px 32px;
  }
  
  .page-title {
    font-size: 2.5rem;
  }
  
  .metric-value-large {
    font-size: 5rem;
  }
  
  .chart-container--timeline {
    height: 240px;
  }
}
</style>
