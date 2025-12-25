<script setup lang="ts">
import { computed } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useDemoControlStore } from '@/stores/demoControlStore'
import { useCESMode } from '@/composables/useCESMode'

const metricsStore = useMetricsStore()
const demoControlStore = useDemoControlStore()
const { isCESMode } = useCESMode()

// GPU utilization (enhanced when model is running)
const gpuUtilization = computed(() => {
  if (demoControlStore.isWarming || demoControlStore.isRunning) {
    return Math.min(100, metricsStore.gpuUtilization + (demoControlStore.isRunning ? 30 : 45))
  }
  return metricsStore.gpuUtilization
})

// Active model name
const activeModelName = computed(() => {
  if (demoControlStore.activeModel === 'deepseek-r1-70b') return 'DeepSeek R1 70B'
  if (demoControlStore.activeModel === 'llama3-70b') return 'llama3-70b'
  if (demoControlStore.activeModel === 'dual') return 'Dual 70B'
  return null
})

// Performance metrics
const tokensPerSec = computed(() => {
  return demoControlStore.liveMetrics.tokensPerSec || (demoControlStore.isRunning ? Math.round(gpuUtilization.value * 0.5 + 10) : 0)
})

const ttft = computed(() => {
  const ttftMs = demoControlStore.liveMetrics.timeToFirstToken
  if (ttftMs > 0) {
    return ttftMs < 1000 ? `${ttftMs}ms` : `${(ttftMs / 1000).toFixed(1)}s`
  }
  return demoControlStore.isRunning ? '<1s' : '—'
})

const latency = computed(() => {
  const lat = demoControlStore.liveMetrics.latency
  if (lat > 0) {
    return lat < 1000 ? `${lat}ms` : `${(lat / 1000).toFixed(1)}s`
  }
  return demoControlStore.isRunning ? '<1s' : '—'
})

const contextWindow = computed(() => {
  return demoControlStore.liveMetrics.contextWindow || (demoControlStore.isRunning ? '128k' : '—')
})

// Headroom-focused metrics (CES-friendly framing)
const gpuHeadroom = computed(() => 100 - Math.round(gpuUtilization.value))
const ramAvailable = computed(() => 
  (metricsStore.memoryTotal - metricsStore.memoryUsed).toFixed(0)
)
const vramAvailable = computed(() => 
  (metricsStore.vramTotal - metricsStore.vramUsed).toFixed(0)
)

// Capability highlights (derived from config, not live)
const capabilities = [
  { icon: '🧠', label: '70B+ LLMs', detail: 'Local Inference' },
  { icon: '⚡', label: 'Multi-GPU Ready', detail: 'Scalable' },
  { icon: '💾', label: 'Up to 192GB+', detail: 'System RAM' },
  { icon: '🔒', label: 'No Cloud Required', detail: 'Air-Gap Ready' }
]

// Model categories teaser
const modelCategories = [
  'Large Language Models',
  'Image Generation', 
  'Embeddings / RAG'
]

function goToModels() {
  // Emit to parent to navigate to models page
  window.dispatchEvent(new CustomEvent('navigate-to-page', { detail: 3 }))
}
</script>

<template>
  <div class="page page-overview">
    <!-- Badge -->
    <div class="live-badge">
      <span class="live-dot"></span>
      Live • Local • Enterprise
    </div>

    <!-- Three-Panel Connected Layout -->
    <div class="three-panel-layout">
      <!-- Left Panel: VRAM/RAM Usage -->
      <div class="panel panel-left">
        <div class="panel-header">
          <span class="panel-title">SYSTEM RESOURCES</span>
        </div>
        <div class="panel-content">
          <div class="resource-item">
            <div class="resource-header">
              <span class="resource-label">GPU VRAM</span>
            </div>
            <div class="resource-value">
              {{ metricsStore.vramUsed.toFixed(0) }}<span class="resource-unit"> GB</span>
              <span class="resource-total">/ {{ metricsStore.vramTotal }} GB</span>
            </div>
            <div v-if="activeModelName" class="resource-allocated">
              ALLOCATED BY: <span class="model-name">{{ activeModelName }}</span>
            </div>
            <div class="resource-bar">
              <div class="resource-bar-fill" :style="{ width: `${metricsStore.vramPercent}%` }"></div>
            </div>
          </div>
          
          <div class="resource-item">
            <div class="resource-header">
              <span class="resource-label">RAM</span>
            </div>
            <div class="resource-value">
              {{ metricsStore.memoryUsed.toFixed(0) }}<span class="resource-unit"> GB</span>
              <span class="resource-total">/ {{ metricsStore.memoryTotal }} GB</span>
            </div>
            <div class="resource-bar">
              <div class="resource-bar-fill resource-bar-fill--ram" :style="{ width: `${metricsStore.memoryPercent}%` }"></div>
            </div>
          </div>
          
          <div class="resource-item">
            <div class="resource-header">
              <span class="resource-label">UPTIME</span>
            </div>
            <div class="resource-value resource-value--mono">
              {{ metricsStore.uptimeFormatted }}
            </div>
          </div>
        </div>
      </div>

      <!-- Center Panel: GPU Ring -->
      <div class="panel panel-center">
        <div class="gpu-ring-container">
          <svg class="gpu-ring" width="200" height="200" viewBox="0 0 200 200">
            <circle
              cx="100"
              cy="100"
              r="85"
              fill="none"
              stroke="rgba(255, 255, 255, 0.1)"
              stroke-width="8"
            />
            <circle
              cx="100"
              cy="100"
              r="85"
              fill="none"
              stroke="var(--abs-orange)"
              stroke-width="8"
              stroke-linecap="round"
              :stroke-dasharray="534"
              :stroke-dashoffset="534 - (534 * gpuUtilization / 100)"
              transform="rotate(-90 100 100)"
              class="gpu-ring-fill"
            />
          </svg>
          <div class="gpu-ring-center">
            <div class="gpu-ring-value">{{ Math.round(gpuUtilization) }}<span class="gpu-ring-unit">%</span></div>
            <div class="gpu-ring-label">GPU</div>
          </div>
        </div>
        <div class="gpu-ring-subtitle">
          {{ demoControlStore.isRunning || demoControlStore.isWarming ? 'ACTIVE INFERENCE' : 'INFERENCE LOAD' }}
        </div>
        <div class="gpu-model-name">{{ metricsStore.gpuModel }}</div>
      </div>

      <!-- Right Panel: Model Status & Performance -->
      <div class="panel panel-right">
        <div class="panel-header">
          <span class="panel-title">PERFORMANCE</span>
        </div>
        <div class="panel-content">
          <div v-if="activeModelName || demoControlStore.isRunning" class="performance-item">
            <div class="performance-header">
              <span class="performance-status" :class="{ 'performance-status--active': demoControlStore.isRunning }">
                {{ demoControlStore.isRunning ? 'RUNNING' : 'READY' }}
              </span>
            </div>
            <div class="performance-model">{{ activeModelName || 'No Model Active' }}</div>
          </div>
          
          <div class="performance-metrics">
            <div class="performance-metric">
              <span class="performance-metric-label">Tokens/sec</span>
              <span class="performance-metric-value">{{ tokensPerSec }}</span>
            </div>
            
            <div class="performance-metric">
              <span class="performance-metric-label">TTFT</span>
              <span class="performance-metric-value">{{ ttft }}</span>
            </div>
            
            <div class="performance-metric">
              <span class="performance-metric-label">LAT</span>
              <span class="performance-metric-value">{{ latency }}</span>
            </div>
            
            <div class="performance-metric">
              <span class="performance-metric-label">CTX</span>
              <span class="performance-metric-value">{{ contextWindow }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Capability Highlights -->
    <div class="capability-row">
      <div 
        v-for="cap in capabilities" 
        :key="cap.label"
        class="capability-tile"
      >
        <span class="capability-icon">{{ cap.icon }}</span>
        <span class="capability-label">{{ cap.label }}</span>
        <span class="capability-detail">{{ cap.detail }}</span>
      </div>
    </div>

    <!-- Model Readiness Teaser -->
    <div class="model-teaser">
      <div class="teaser-header">
        <span class="teaser-icon">🎯</span>
        <span class="teaser-title">AI Models Ready (Local)</span>
        <span class="teaser-badge teaser-badge--pulse">LOCAL</span>
      </div>
      <div class="teaser-subtitle">Optimized for ABS-validated model stacks</div>
      <div class="teaser-categories">
        <span v-for="cat in modelCategories" :key="cat" class="teaser-category">
          • {{ cat }}
        </span>
      </div>
      <button class="teaser-cta" @click="goToModels">
        View Installed Models →
      </button>
    </div>

    <!-- Secondary Metrics (Headroom Focused) -->
    <div class="secondary-metrics">
      <div class="metric-card">
        <div class="metric-icon">💾</div>
        <div class="metric-content">
          <span class="metric-label">Memory Available</span>
          <span class="metric-value">{{ ramAvailable }}<span class="metric-unit"> GB</span></span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">⏱️</div>
        <div class="metric-content">
          <span class="metric-label">Uptime</span>
          <span class="metric-value metric-value--mono">{{ metricsStore.uptimeFormatted }}</span>
        </div>
      </div>
    </div>

    <!-- CES Script -->
    <div v-if="isCESMode" class="ces-script">
      <p>"Everything you're seeing is running locally — on this workstation — right now."</p>
    </div>
    
    <!-- Architectural Hint -->
    <div class="architectural-hint">
      Powered by an AI Operating Fabric with on-demand model orchestration
    </div>
  </div>
</template>

<style scoped>
.page-overview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 140px);
  padding: 40px 24px;
  gap: 32px;
}

/* Three-Panel Layout */
.three-panel-layout {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 32px;
  width: 100%;
  max-width: 1400px;
  align-items: start;
}

.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 24px;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--status-success);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.live-dot {
  width: 8px;
  height: 8px;
  background: var(--status-success);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Panel Styles */
.panel {
  background: var(--abs-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
}

.panel-left {
  min-width: 280px;
}

.panel-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px;
  min-width: 240px;
}

.panel-right {
  min-width: 280px;
}

.panel-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
}

.panel-title {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Left Panel: Resources */
.resource-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-label {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.resource-value {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.resource-value--mono {
  font-family: var(--font-mono);
  font-size: 1.25rem;
  letter-spacing: 0.02em;
}

.resource-unit {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.resource-total {
  font-size: 0.875rem;
  color: var(--text-muted);
  font-weight: 400;
}

.resource-allocated {
  font-family: var(--font-label);
  font-size: 0.6rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-top: -4px;
}

.resource-allocated .model-name {
  color: var(--abs-orange);
  font-weight: 600;
}

.resource-bar {
  height: 4px;
  background: var(--border-subtle);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.resource-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--abs-orange), #ff9f43);
  transition: width var(--duration-slow) var(--ease-smooth);
}

.resource-bar-fill--ram {
  background: linear-gradient(90deg, var(--electric-indigo), #818cf8);
}

/* Center Panel: GPU Ring */
.gpu-ring-container {
  position: relative;
  width: 200px;
  height: 200px;
}

.gpu-ring {
  width: 100%;
  height: 100%;
}

.gpu-ring-fill {
  transition: stroke-dashoffset var(--duration-slow) var(--ease-smooth);
  filter: drop-shadow(0 0 8px var(--abs-orange-glow));
}

.gpu-ring-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.gpu-ring-value {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--abs-orange);
  line-height: 1;
}

.gpu-ring-unit {
  font-size: 1.25rem;
  color: var(--text-secondary);
}

.gpu-ring-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 4px;
}

.gpu-ring-subtitle {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--abs-orange);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 8px;
}

.gpu-model-name {
  font-family: var(--font-label);
  font-size: 0.65rem;
  color: var(--text-muted);
  text-align: center;
  margin-top: 4px;
  line-height: 1.4;
}

/* Right Panel: Performance */
.performance-item {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.performance-header {
  margin-bottom: 8px;
}

.performance-status {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 6px;
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.performance-status--active {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
  color: var(--status-success);
}

.performance-model {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.performance-metric {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.performance-metric-label {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}

.performance-metric-value {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  text-align: right;
  flex-shrink: 0;
}

.gpu-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
}

.gpu-model {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--abs-orange);
  margin: 0 0 12px;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.config-badge {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 20px;
}

.config-tier {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.config-note {
  font-family: var(--font-body);
  font-size: 0.7rem;
  color: var(--text-muted);
  font-style: italic;
}

.use-cases {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 16px;
  padding: 8px 16px;
  background: rgba(99, 102, 241, 0.06);
  border-radius: 6px;
}

.gpu-metrics {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 28px;
}

.gpu-divider {
  width: 1px;
  height: 40px;
  background: var(--border-color);
}

.gpu-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.gpu-metric .metric-label {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.gpu-metric .metric-value {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
}

.gpu-metric .metric-unit {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.gpu-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 5px;
  background: var(--border-subtle);
}

.gpu-bar__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--abs-orange), #ff9f43);
  box-shadow: 0 0 20px var(--abs-orange-glow);
  transition: width var(--duration-slow) var(--ease-smooth);
}

.current-state {
  font-family: var(--font-label);
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-top: 12px;
  opacity: 0.8;
}

/* Capability Highlights */
.capability-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  width: 100%;
  max-width: 700px;
}

.capability-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 12px;
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 10px;
}

.capability-icon {
  font-size: 1.25rem;
}

.capability-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
}

.capability-detail {
  font-family: var(--font-label);
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Model Teaser */
.model-teaser {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px 28px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  max-width: 400px;
}

.teaser-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.teaser-icon {
  font-size: 1.25rem;
}

.teaser-title {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.teaser-badge {
  padding: 2px 8px;
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 10px;
  font-family: var(--font-label);
  font-size: 0.6rem;
  font-weight: 700;
  color: var(--status-success);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.teaser-badge--pulse {
  animation: badge-pulse 3s ease-in-out infinite;
}

@keyframes badge-pulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.3);
  }
  50% {
    opacity: 0.9;
    box-shadow: 0 0 16px rgba(34, 197, 94, 0.5);
  }
}

.teaser-subtitle {
  font-family: var(--font-body);
  font-size: 0.75rem;
  color: var(--text-muted);
  font-style: italic;
}

.teaser-categories {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px 16px;
}

.teaser-category {
  font-family: var(--font-body);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.teaser-cta {
  background: transparent;
  border: none;
  color: var(--electric-indigo);
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 4px;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.teaser-cta:hover {
  background: rgba(99, 102, 241, 0.1);
}

/* Secondary Metrics */
.secondary-metrics {
  display: flex;
  gap: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
}

.metric-icon {
  font-size: 1.25rem;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.metric-content .metric-label {
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.metric-content .metric-value {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value--mono {
  font-family: var(--font-mono);
  letter-spacing: 0.02em;
}

.ces-script {
  max-width: 500px;
  padding: 16px 24px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 10px;
  text-align: center;
}

.ces-script p {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-style: italic;
  color: var(--text-secondary);
  margin: 0;
}

.architectural-hint {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-muted);
  text-align: center;
  opacity: 0.6;
  font-style: italic;
  margin-top: 8px;
}

/* CES Mode: Larger typography */
.ces-mode .gpu-model {
  font-size: 2.25rem;
}

.ces-mode .gpu-metric .metric-value {
  font-size: 3rem;
}

/* Visual Connections (Arrows) */
.three-panel-layout::before,
.three-panel-layout::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 24px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--abs-orange));
  opacity: 0.3;
  pointer-events: none;
}

.three-panel-layout {
  position: relative;
}

.three-panel-layout::before {
  left: calc(33.33% - 12px);
  transform: translateY(-50%);
}

.three-panel-layout::after {
  right: calc(33.33% - 12px);
  transform: translateY(-50%);
}

/* Responsive */
@media (max-width: 1200px) {
  .three-panel-layout {
    grid-template-columns: 1fr;
    gap: 24px;
    max-width: 600px;
  }
  
  .panel-center {
    order: -1;
  }
  
  .three-panel-layout::before,
  .three-panel-layout::after {
    display: none;
  }
}

@media (max-width: 768px) {
  .capability-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .panel-left,
  .panel-right {
    min-width: auto;
  }
  
  .gpu-ring-container {
    width: 160px;
    height: 160px;
  }
  
  .gpu-ring-value {
    font-size: 2rem;
  }
}
</style>
