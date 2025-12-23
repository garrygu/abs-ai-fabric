<script setup lang="ts">
import { computed } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useCESMode } from '@/composables/useCESMode'

const metricsStore = useMetricsStore()
const { isCESMode } = useCESMode()

// Headroom-focused metrics (CES-friendly framing)
const gpuHeadroom = computed(() => 100 - Math.round(metricsStore.gpuUtilization))
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

    <!-- Hero GPU Tile -->
    <div class="hero-gpu-card">
      <div class="gpu-icon">⚡</div>
      <h2 class="gpu-model">{{ metricsStore.gpuModel }}</h2>
      
      <!-- Configuration Badge -->
      <div class="config-badge">
        <span class="config-tier">Enterprise Configuration</span>
        <span class="config-note">Multiple GPU & Memory options available</span>
      </div>
      
      <!-- Use Case Context -->
      <div class="use-cases">
        Designed for: Enterprise AI • On-Prem Inference • Regulated Environments
      </div>
      
      <div class="gpu-metrics">
        <div class="gpu-metric">
          <span class="metric-label">GPU Headroom</span>
          <span class="metric-value">{{ gpuHeadroom }}<span class="metric-unit">%</span></span>
        </div>
        <div class="gpu-divider"></div>
        <div class="gpu-metric">
          <span class="metric-label">VRAM Available</span>
          <span class="metric-value">{{ vramAvailable }}<span class="metric-unit"> GB</span></span>
        </div>
      </div>
      <div class="gpu-bar">
        <div class="gpu-bar__fill" :style="{ width: `${100 - gpuHeadroom}%` }"></div>
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
        <span class="teaser-title">AI Models Ready</span>
        <span class="teaser-badge">LOCAL</span>
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
      <p>"Everything you're seeing is running locally on this workstation, right now."</p>
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
  padding: 32px 24px;
  gap: 24px;
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

.hero-gpu-card {
  width: 100%;
  max-width: 600px;
  padding: 40px 36px;
  background: linear-gradient(135deg, var(--abs-card) 0%, var(--abs-elevated) 100%);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-lg), 0 0 60px rgba(249, 115, 22, 0.1);
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

/* CES Mode: Larger typography */
.ces-mode .gpu-model {
  font-size: 2.25rem;
}

.ces-mode .gpu-metric .metric-value {
  font-size: 3rem;
}

@media (max-width: 768px) {
  .capability-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .secondary-metrics {
    flex-direction: column;
  }
}
</style>
