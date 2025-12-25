<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useWorkloadsStore } from '@/stores/workloadsStore'
import { useModelsStore } from '@/stores/modelsStore'
import { useCESMode } from '@/composables/useCESMode'
import { useDemoControlStore } from '@/stores/demoControlStore'

const metricsStore = useMetricsStore()
const workloadsStore = useWorkloadsStore()
const modelsStore = useModelsStore()
const demoControlStore = useDemoControlStore()
const { isCESMode } = useCESMode()

// Enhanced GPU utilization when model is warming/running
const enhancedGpuUtilization = computed(() => {
  if (demoControlStore.isWarming) {
    // Simulate GPU surge during warming
    return Math.min(100, metricsStore.gpuUtilization + 45)
  }
  if (demoControlStore.isRunning) {
    // Simulate active inference
    return Math.min(100, metricsStore.gpuUtilization + 30)
  }
  return metricsStore.gpuUtilization
})

// Model loading overlay text
const modelLoadingText = computed(() => {
  if (demoControlStore.isWarming) {
    if (demoControlStore.activeModel === 'deepseek-r1-70b') {
      return 'DeepSeek R1 70B warming'
    } else if (demoControlStore.activeModel === 'llama3-70b') {
      return 'LLaMA-3 70B warming'
    } else if (demoControlStore.activeModel === 'dual') {
      return 'Dual 70B models warming'
    }
  }
  return null
})

// History for animated flowing lines
const historyLength = 60
const gpuHistory = ref<number[]>([])
const vramHistory = ref<number[]>([])
const ramHistory = ref<number[]>([])

// Lifecycle states for the strip
const lifecycleStates = ['Idle', 'Requested', 'Warming', 'Running', 'Sleeping']

// Active Intelligence cards (auto-generated from workloads)
const activeIntelligenceCards = computed(() => {
  const cards: Array<{ icon: string; title: string; subtitle: string; state?: string }> = []
  
  const hasActiveWorkloads = workloadsStore.activeWorkloads.length > 0
  
  workloadsStore.activeWorkloads.forEach(workload => {
    const modelName = workload.associated_models?.[0] || 'Local Model'
    const model = modelsStore.models.find(m => 
      m.model_id.toLowerCase().includes(modelName.toLowerCase()) ||
      modelName.toLowerCase().includes(m.model_id.toLowerCase())
    )
    
    if (workload.workload_type === 'llm_inference') {
      cards.push({
        icon: '🧠',
        title: 'Running Reasoning Model',
        subtitle: `${model?.display_name || modelName} · ${model?.size_gb ? Math.round(model.size_gb) + 'B' : 'Local'}`,
        state: 'Running'
      })
    } else if (workload.workload_type === 'rag') {
      cards.push({
        icon: '📄',
        title: 'Processing Document',
        subtitle: 'RAG Pipeline · Semantic Search',
        state: 'Running'
      })
    }
  })
  
  // Add asset state card - reactive based on workload state (only when no active workloads shown)
  const readyModels = modelsStore.readyModels
  
  // Check demoControlStore state for warming/running status
  if (demoControlStore.isWarming && cards.length === 0) {
    // Model is warming up
    let modelName = 'Model'
    if (demoControlStore.activeModel === 'deepseek-r1-70b') {
      modelName = 'DeepSeek R1 70B'
    } else if (demoControlStore.activeModel === 'llama3-70b') {
      modelName = 'LLaMA-3 70B'
    } else if (demoControlStore.activeModel === 'dual') {
      modelName = 'Dual 70B Models'
    }
    cards.push({
      icon: '⚡',
      title: `${modelName} Warming`,
      subtitle: `Loading into VRAM... ${Math.round(demoControlStore.loadingProgress)}%`,
      state: 'Warming'
    })
  } else if (demoControlStore.isRunning && cards.length === 0) {
    // Model is loaded and running (but no active workloads yet)
    let modelName = 'Model'
    if (demoControlStore.activeModel === 'deepseek-r1-70b') {
      modelName = 'DeepSeek R1 70B'
    } else if (demoControlStore.activeModel === 'llama3-70b') {
      modelName = 'LLaMA-3 70B'
    } else if (demoControlStore.activeModel === 'dual') {
      modelName = 'Dual 70B Models'
    }
    cards.push({
      icon: '⚡',
      title: 'Models Ready',
      subtitle: `${modelName} loaded · Waiting for Request`,
      state: 'Ready'
    })
  } else if (readyModels.length > 0 && cards.length === 0) {
    // Idle state - show asset state card
    cards.push({
      icon: '⚡',
      title: 'Models Ready',
      subtitle: 'Waiting for Request',
      state: undefined // No state badge when idle
    })
  } else if (hasActiveWorkloads && cards.length === 0) {
    // During demo but no workload cards created - show warming/running state
    const firstWorkload = workloadsStore.activeWorkloads[0]
    const modelName = firstWorkload.associated_models?.[0] || 'Model'
    const model = modelsStore.models.find(m => 
      m.model_id.toLowerCase().includes(modelName.toLowerCase()) ||
      modelName.toLowerCase().includes(m.model_id.toLowerCase())
    )
    const modelDisplay = model?.display_name || modelName
    const modelSize = model?.size_gb ? Math.round(model.size_gb) + 'B' : ''
    
    cards.push({
      icon: '🧠',
      title: modelDisplay + (modelSize ? ' ' + modelSize : ''),
      subtitle: firstWorkload.status === 'running' ? 'Warming → Running' : 'Warming',
      state: firstWorkload.status === 'running' ? 'Running' : 'Warming'
    })
  }
  
  return cards
})

// Track which asset the lifecycle strip represents
const lifecycleAsset = computed(() => {
  const activeWorkloads = workloadsStore.activeWorkloads
  if (activeWorkloads.length > 0) {
    const firstWorkload = activeWorkloads[0]
    const modelName = firstWorkload.associated_models?.[0]
    const model = modelName ? modelsStore.models.find(m => 
      m.model_id.toLowerCase().includes(modelName.toLowerCase()) ||
      modelName.toLowerCase().includes(m.model_id.toLowerCase())
    ) : null
    
    return {
      name: firstWorkload.app_name,
      type: 'app',
      model: model?.display_name || modelName
    }
  }
  
  // If no active workloads, show primary ready model
  const readyModels = modelsStore.readyModels
  if (readyModels.length > 0) {
    const primaryModel = readyModels[0]
    return {
      name: primaryModel.display_name,
      type: 'model',
      model: null
    }
  }
  
  return {
    name: 'System Assets',
    type: 'system',
    model: null
  }
})

const currentLifecycleState = computed(() => {
  const activeWorkloads = workloadsStore.activeWorkloads
  if (activeWorkloads.length > 0) {
    const firstWorkload = activeWorkloads[0]
    if (firstWorkload.status === 'running') {
      return 'Running'
    } else {
      return 'Warming'
    }
  }
  // Check if there are ready models waiting
  if (modelsStore.readyModels.length > 0) {
    return 'Idle'
  }
  return 'Idle'
})

// AI Outcomes metrics (capability-focused, not raw hardware)
const aiOutcomes = computed(() => {
  const activeModels = modelsStore.readyModels.length
  const activeWorkloads = workloadsStore.activeWorkloads.length
  const totalModels = modelsStore.models.length
  
  // Estimate tokens/sec based on GPU utilization (rough estimate)
  const estimatedTokensPerSec = Math.round(metricsStore.gpuUtilization * 0.5 + 10)
  
  // Estimate context length (assume 128k for large models)
  const contextLength = activeModels > 0 ? '128k' : 'N/A'
  
  // Concurrent sessions = active workloads
  const concurrentSessions = activeWorkloads
  
  return {
    activeModels,
    reasoningDepth: activeModels > 0 ? 'High' : 'Idle',
    contextLength,
    tokensPerSec: estimatedTokensPerSec,
    concurrentSessions,
    latency: 'Local (<1s)'
  }
})

function updateHistory() {
  gpuHistory.value = [...gpuHistory.value.slice(-historyLength + 1), metricsStore.gpuUtilization]
  vramHistory.value = [...vramHistory.value.slice(-historyLength + 1), metricsStore.vramPercent]
  ramHistory.value = [...ramHistory.value.slice(-historyLength + 1), metricsStore.memoryPercent]
}

// Generate flowing line paths for energy visualization
function getFlowingPath(data: number[], color: string, offset: number = 0): string {
  if (data.length === 0) return ''
  const width = 100
  const height = 100
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width
    const normalized = Math.max(0, Math.min(100, val)) / 100
    const y = height - (normalized * height * 0.6) - offset // Offset for layering
    return { x, y }
  })
  
  // Create smooth flowing curve
  let path = `M ${points[0].x},${points[0].y}`
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const cpX = (prev.x + curr.x) / 2
    path += ` Q ${cpX},${prev.y} ${curr.x},${curr.y}`
  }
  
  return path
}

const gpuFlowPath = computed(() => getFlowingPath(gpuHistory.value, '#3b82f6', 0))
const vramFlowPath = computed(() => getFlowingPath(vramHistory.value, '#a855f7', 20))
const ramFlowPath = computed(() => getFlowingPath(ramHistory.value, '#06b6d4', 40))

// Headroom calculations
const gpuHeadroom = computed(() => 100 - metricsStore.gpuUtilization)
const vramHeadroom = computed(() => 100 - metricsStore.vramPercent)
const ramHeadroom = computed(() => 100 - metricsStore.memoryPercent)

// Disk I/O formatted
const diskIOFormatted = computed(() => {
  const read = metricsStore.diskRead
  const write = metricsStore.diskWrite
  const total = read + write
  if (total >= 1000) {
    return `${(total / 1000).toFixed(1)} GB/s`
  }
  return `${total.toFixed(1)} MB/s`
})

let historyInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // Initialize history
  const initializeHistory = () => {
    const initialGpu = metricsStore.gpuUtilization || 0
    const initialVram = metricsStore.vramPercent || 0
    const initialRam = metricsStore.memoryPercent || 0
    
    for (let i = 0; i < historyLength; i++) {
      gpuHistory.value.push(initialGpu)
      vramHistory.value.push(initialVram)
      ramHistory.value.push(initialRam)
    }
  }
  
  if (metricsStore.metrics) {
    initializeHistory()
  } else {
    const checkInterval = setInterval(() => {
      if (metricsStore.metrics) {
        initializeHistory()
        clearInterval(checkInterval)
      }
    }, 100)
    setTimeout(() => {
      clearInterval(checkInterval)
      initializeHistory()
    }, 3000)
  }
  
  historyInterval = setInterval(updateHistory, 2000)
  
  // Fetch workloads and models if needed
  if (workloadsStore.workloads.length === 0) {
    workloadsStore.fetchWorkloads()
  }
  if (modelsStore.models.length === 0) {
    modelsStore.fetchModels()
  }
})

onUnmounted(() => {
  if (historyInterval) clearInterval(historyInterval)
})
</script>

<template>
  <div class="page page-performance-v2">
    <!-- Subtle labels for each line (positioned above chart) -->
    <div class="flow-labels">
      <div class="flow-label flow-label--gpu">GPU</div>
      <div class="flow-label flow-label--vram">VRAM</div>
      <div class="flow-label flow-label--ram">RAM</div>
    </div>
    <!-- ① HERO: LIVE SYSTEM PULSE -->
    <div class="hero-section">
      <div class="hero-background">
        <!-- Animated flowing lines -->
        <svg class="flowing-lines" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="gpuGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.8" />
              <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.2" />
            </linearGradient>
            <linearGradient id="vramGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#a855f7" stop-opacity="0.8" />
              <stop offset="100%" stop-color="#a855f7" stop-opacity="0.2" />
            </linearGradient>
            <linearGradient id="ramGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.8" />
              <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.2" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <!-- GPU Flow (Electric Blue) -->
          <path 
            :d="gpuFlowPath" 
            fill="none" 
            stroke="url(#gpuGradient)" 
            stroke-width="1.5"
            class="flow-line flow-line--gpu"
            filter="url(#glow)"
          />
          <!-- VRAM Flow (Violet) -->
          <path 
            :d="vramFlowPath" 
            fill="none" 
            stroke="url(#vramGradient)" 
            stroke-width="1.2"
            class="flow-line flow-line--vram"
            filter="url(#glow)"
          />
          <!-- RAM Flow (Cyan) -->
          <path 
            :d="ramFlowPath" 
            fill="none" 
            stroke="url(#ramGradient)" 
            stroke-width="1"
            class="flow-line flow-line--ram"
            filter="url(#glow)"
          />
        </svg>
      </div>
      
      <div class="hero-content">
        <div class="hero-centerpiece">
          <div class="hero-label">GPU UTILIZATION</div>
          <div class="hero-value hero-value--breathing" :class="{ 'hero-value--surge': demoControlStore.isWarming || demoControlStore.isRunning }">
            {{ Math.round(enhancedGpuUtilization) }}<span class="hero-unit">%</span>
          </div>
        </div>
        
        <div class="hero-caption">
          <Transition name="fade" mode="out-in">
            <span :key="enhancedGpuUtilization > 10 ? 'active' : 'idle'">
              {{ enhancedGpuUtilization > 10 ? 'Local AI Compute · Real Time · No Cloud' : 'Idle · Standing By · Local Execution' }}
            </span>
          </Transition>
        </div>
        <div class="hero-micro-subtitle">
          <Transition name="fade" mode="out-in">
            <span :key="enhancedGpuUtilization > 10 ? 'active' : 'idle'">
              {{ enhancedGpuUtilization > 10 ? 'Active compute in progress' : 'No heavy assets active' }}
            </span>
          </Transition>
        </div>

      </div>
    </div>

    <!-- ② ACTIVE INTELLIGENCE OVERLAY -->
    <div class="intelligence-overlay">
      <Transition name="intelligence-fade">
        <div 
          v-if="activeIntelligenceCards.length > 0"
          :key="activeIntelligenceCards[0].title + activeIntelligenceCards[0].state"
          class="intelligence-card"
          :class="{
            'intelligence-card--warming': activeIntelligenceCards[0].state === 'Warming',
            'intelligence-card--ready': activeIntelligenceCards[0].state === 'Ready',
            'intelligence-card--running': activeIntelligenceCards[0].state === 'Running'
          }"
        >
          <span class="intelligence-icon">{{ activeIntelligenceCards[0].icon }}</span>
          <div class="intelligence-content">
            <div class="intelligence-title">{{ activeIntelligenceCards[0].title }}</div>
            <div class="intelligence-subtitle">{{ activeIntelligenceCards[0].subtitle }}</div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- ③ & ④ DUAL PANEL: HARDWARE REALITY + AI OUTCOMES -->
    <div class="dual-panel-section">
      <!-- Left: Hardware Reality -->
      <div class="panel panel--hardware">
        <div class="panel-header">
          <div class="panel-title">HARDWARE</div>
          <div class="panel-divider"></div>
        </div>
        <div class="panel-content">
          <div class="hardware-item">
            <span class="hardware-label">GPU</span>
            <span class="hardware-value">{{ metricsStore.gpuModel }}</span>
          </div>
          <div class="hardware-item">
            <span class="hardware-label">VRAM</span>
            <div class="hardware-item-right">
              <span class="hardware-value">{{ metricsStore.vramUsed.toFixed(1) }} / {{ metricsStore.vramTotal }} GB</span>
              <div class="hardware-bar">
                <div class="hardware-bar-fill" :style="{ width: `${metricsStore.vramPercent}%` }"></div>
              </div>
            </div>
          </div>
          <div class="hardware-item">
            <span class="hardware-label">System RAM</span>
            <div class="hardware-item-right">
              <span class="hardware-value">{{ metricsStore.memoryUsed.toFixed(0) }} / {{ metricsStore.memoryTotal }} GB</span>
              <div class="hardware-bar">
                <div class="hardware-bar-fill hardware-bar-fill--ram" :style="{ width: `${metricsStore.memoryPercent}%` }"></div>
              </div>
            </div>
          </div>
          <div class="hardware-item">
            <span class="hardware-label">Disk I/O</span>
            <span class="hardware-value">{{ diskIOFormatted }}</span>
          </div>
          <div class="hardware-item">
            <span class="hardware-label">Thermal</span>
            <span class="hardware-value hardware-value--optimal">Optimal</span>
          </div>
        </div>
      </div>

      <!-- Right: AI Outcomes -->
      <div class="panel panel--intelligence">
        <div class="panel-header">
          <div class="panel-title">INTELLIGENCE</div>
          <div class="panel-divider"></div>
        </div>
        <div class="panel-content">
          <div class="outcome-item">
            <span class="outcome-label">Active Reasoning Models</span>
            <span class="outcome-value">{{ aiOutcomes.activeModels }}</span>
          </div>
          <div class="outcome-item">
            <span class="outcome-label">Reasoning Mode</span>
            <span class="outcome-value">{{ aiOutcomes.reasoningDepth }}</span>
          </div>
          <div class="outcome-item">
            <span class="outcome-label">Context Window</span>
            <span class="outcome-value">{{ aiOutcomes.contextLength }}</span>
          </div>
          <div class="outcome-item">
            <span class="outcome-label">Inference Rate</span>
            <span class="outcome-value">{{ aiOutcomes.tokensPerSec }}</span>
          </div>
          <div class="outcome-item">
            <span class="outcome-label">Concurrent Sessions</span>
            <span class="outcome-value">{{ aiOutcomes.concurrentSessions }}</span>
          </div>
          <div class="outcome-item">
            <span class="outcome-label">Response Latency</span>
            <span class="outcome-value">{{ aiOutcomes.latency }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Inference Metrics (when model is running) -->
    <Transition name="fade">
      <div v-if="demoControlStore.isRunning" class="live-inference-section">
        <div class="live-inference-header">
          <span class="live-badge">LIVE INFERENCE</span>
        </div>
        <div class="live-metrics-grid">
          <div class="live-metric">
            <span class="live-metric-label">Tokens/sec</span>
            <span class="live-metric-value">{{ demoControlStore.liveMetrics.tokensPerSec || aiOutcomes.tokensPerSec }}</span>
          </div>
          <div class="live-metric">
            <span class="live-metric-label">Time to first token</span>
            <span class="live-metric-value">{{ demoControlStore.liveMetrics.timeToFirstToken || '<1s' }}</span>
          </div>
          <div class="live-metric">
            <span class="live-metric-label">Active model</span>
            <span class="live-metric-value">{{ demoControlStore.liveMetrics.activeModel || (demoControlStore.activeModel === 'deepseek-r1-70b' ? 'DeepSeek R1 70B' : demoControlStore.activeModel === 'llama3-70b' ? 'LLaMA-3 70B' : 'Dual 70B') }}</span>
          </div>
          <div class="live-metric">
            <span class="live-metric-label">Context window</span>
            <span class="live-metric-value">{{ demoControlStore.liveMetrics.contextWindow || '128k' }}</span>
          </div>
          <div class="live-metric">
            <span class="live-metric-label">Latency (local)</span>
            <span class="live-metric-value">{{ demoControlStore.liveMetrics.latency || '<1s' }}</span>
          </div>
        </div>
        <!-- Annotation for why GPU spiked -->
        <div class="live-annotation">
          <span v-if="demoControlStore.isWarming">70B weights loaded · KV cache warming</span>
          <span v-else-if="demoControlStore.isRunning">Generating answer</span>
        </div>
      </div>
    </Transition>

    <!-- ⑤ LIFECYCLE STRIP -->
    <div class="lifecycle-section">
      <div class="lifecycle-header">
        <div class="lifecycle-asset-label">
          <span class="lifecycle-asset-name">{{ lifecycleAsset.name }}</span>
          <span v-if="lifecycleAsset.model" class="lifecycle-asset-model">· {{ lifecycleAsset.model }}</span>
        </div>
      </div>
      <div class="lifecycle-strip">
        <div 
          v-for="(state, index) in lifecycleStates" 
          :key="state"
          class="lifecycle-state"
          :class="{ 
            'lifecycle-state--active': state === currentLifecycleState,
            'lifecycle-state--past': lifecycleStates.indexOf(currentLifecycleState) > index,
            'lifecycle-state--future': lifecycleStates.indexOf(currentLifecycleState) < index
          }"
        >
          <div class="lifecycle-state-label">{{ state }}</div>
          <div class="lifecycle-state-indicator"></div>
          <div v-if="index < lifecycleStates.length - 1" class="lifecycle-connector"></div>
        </div>
      </div>
    </div>

    <!-- ⑥ FOOTER NARRATIVE -->
    <div class="footer-narrative">
      <div class="narrative-text narrative-text--shimmer">An AI Operating Fabric — Not Just a Workstation</div>
    </div>
  </div>
</template>

<style scoped>
.page-performance-v2 {
  position: relative;
  padding: 40px 24px;
  max-width: var(--container-max);
  margin: 0 auto;
  min-height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ① HERO SECTION */
.hero-section {
  position: relative;
  height: 40vh;
  min-height: 300px;
  max-height: 400px;
  background: var(--abs-black);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-subtle);
}

.hero-background {
  position: absolute;
  inset: 0;
  opacity: 0.6;
}

.flowing-lines {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.flow-line {
  animation: flow 8s ease-in-out infinite;
  transition: d 0.3s ease;
}

.flow-line--gpu {
  animation-duration: 6s;
  animation-delay: 0s;
}

.flow-line--vram {
  animation-duration: 8s;
  animation-delay: 1s;
}

.flow-line--ram {
  animation-duration: 10s;
  animation-delay: 2s;
}

.flow-labels {
  position: absolute;
  top: 20px;
  right: 24px;
  pointer-events: none;
  display: flex;
  flex-direction: row;
  gap: 28px;
  z-index: 1000;
  align-items: center;
}

.flow-label {
  font-family: var(--font-label, 'Rajdhani', sans-serif);
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.6;
  pointer-events: none;
  user-select: none;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  line-height: 1;
  white-space: nowrap;
  display: block;
  text-shadow: 0 0 8px currentColor;
}

.flow-label--gpu {
  color: #3b82f6;
}

.flow-label--vram {
  color: #a855f7;
}

.flow-label--ram {
  color: #06b6d4;
}

@keyframes flow {
  0%, 100% {
    opacity: 0.4;
    transform: translateX(0);
  }
  50% {
    opacity: 0.8;
    transform: translateX(2px);
  }
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-centerpiece {
  margin-bottom: 16px;
}

.hero-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}

.hero-value {
  font-family: var(--font-display);
  font-size: 6rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
  padding-bottom: 8px;
  transition: all 0.3s ease;
}

.hero-value--breathing {
  animation: breathing 4s ease-in-out infinite;
}

.hero-value--surge {
  animation: surge-pulse 2s ease-in-out infinite;
  color: var(--abs-orange);
}

@keyframes breathing {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.95;
    transform: scale(1.01);
  }
}

@keyframes surge-pulse {
  0%, 100% {
    text-shadow: 0 0 30px rgba(249, 115, 22, 0.6);
  }
  50% {
    text-shadow: 0 0 50px rgba(249, 115, 22, 0.9);
  }
}

.model-loading-overlay {
  display: inline-block;
  margin-top: 32px;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid var(--abs-orange);
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--abs-orange);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  z-index: 10;
  box-shadow: 0 0 30px rgba(249, 115, 22, 0.4);
  backdrop-filter: blur(10px);
}

.hero-unit {
  font-size: 3rem;
  opacity: 0.7;
}

.hero-caption {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 8px;
}

.hero-micro-subtitle {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 400;
  opacity: 0.7;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ② ACTIVE INTELLIGENCE OVERLAY */
.intelligence-overlay {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60px;
  width: 100%;
}

.intelligence-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(15, 15, 24, 0.8);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  position: relative;
  transition: border-color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
}

.intelligence-card--warming {
  border-color: var(--abs-orange);
  border-width: 2px;
  box-shadow: 
    0 0 20px rgba(249, 115, 22, 0.4),
    0 0 40px rgba(249, 115, 22, 0.2),
    inset 0 0 20px rgba(249, 115, 22, 0.1);
  background: rgba(15, 15, 24, 0.95);
  animation: warmingPulse 2s ease-in-out infinite;
}

.intelligence-card--ready {
  border-color: var(--status-success);
  border-width: 2px;
  box-shadow: 
    0 0 20px rgba(34, 197, 94, 0.3),
    0 0 40px rgba(34, 197, 94, 0.15);
  background: rgba(15, 15, 24, 0.95);
}

.intelligence-card--running {
  border-color: var(--electric-indigo);
  border-width: 2px;
  box-shadow: 
    0 0 20px rgba(99, 102, 241, 0.4),
    0 0 40px rgba(99, 102, 241, 0.2);
  background: rgba(15, 15, 24, 0.95);
}

@keyframes warmingPulse {
  0%, 100% {
    box-shadow: 
      0 0 20px rgba(249, 115, 22, 0.4),
      0 0 40px rgba(249, 115, 22, 0.2),
      inset 0 0 20px rgba(249, 115, 22, 0.1);
  }
  50% {
    box-shadow: 
      0 0 30px rgba(249, 115, 22, 0.6),
      0 0 60px rgba(249, 115, 22, 0.3),
      inset 0 0 30px rgba(249, 115, 22, 0.15);
  }
}

@keyframes float-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.intelligence-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.intelligence-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.intelligence-title {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.intelligence-subtitle {
  font-family: var(--font-body);
  font-size: 0.8rem;
  color: var(--text-secondary);
}


.intelligence-fade-enter-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.intelligence-fade-leave-active {
  transition: opacity 0.15s ease;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.intelligence-fade-enter-from {
  opacity: 0;
  transform: translateY(5px);
}

.intelligence-fade-leave-to {
  opacity: 0;
}

/* ③ & ④ DUAL PANEL */
.dual-panel-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.panel {
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 24px;
}

.panel-header {
  margin-bottom: 20px;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.panel-divider {
  height: 1px;
  background: var(--border-subtle);
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Hardware Panel */
.hardware-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  gap: 12px;
}

.hardware-item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.hardware-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.hardware-value {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
}

.hardware-value--optimal {
  color: var(--status-success);
}

.hardware-bar {
  width: 100%;
  height: 3px;
  background: var(--border-subtle);
  border-radius: 2px;
  overflow: hidden;
  max-width: 120px;
}

.hardware-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--electric-indigo), var(--abs-orange));
  border-radius: 2px;
  transition: width 0.5s ease;
}

.hardware-bar-fill--ram {
  background: linear-gradient(90deg, #06b6d4, #3b82f6);
}

/* Intelligence Panel */
.outcome-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.outcome-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.outcome-value {
  font-family: var(--font-display);
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 600;
}

/* ⑤ LIFECYCLE STRIP */
.lifecycle-section {
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 24px;
}

.lifecycle-header {
  margin-bottom: 16px;
  text-align: center;
}

.lifecycle-asset-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.lifecycle-asset-name {
  color: var(--text-primary);
  font-weight: 600;
}

.lifecycle-asset-model {
  color: var(--text-secondary);
  font-weight: 400;
}

.lifecycle-strip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.lifecycle-state {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.lifecycle-state-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  transition: color 0.3s ease;
  white-space: nowrap;
}

.lifecycle-state-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border-subtle);
  border: 2px solid var(--border-subtle);
  transition: all 0.3s ease;
}

.lifecycle-connector {
  width: 40px;
  height: 2px;
  background: var(--border-subtle);
  margin: 0 4px;
  transition: background 0.3s ease;
}

.lifecycle-state--active .lifecycle-state-label {
  color: var(--text-primary);
  font-weight: 600;
}

.lifecycle-state--active .lifecycle-state-indicator {
  background: var(--abs-orange);
  border-color: var(--abs-orange);
  box-shadow: 0 0 12px rgba(251, 146, 60, 0.5);
  transform: scale(1.2);
}

.lifecycle-state--past .lifecycle-state-label {
  color: var(--text-secondary);
}

.lifecycle-state--past .lifecycle-state-indicator {
  background: var(--status-success);
  border-color: var(--status-success);
  opacity: 0.6;
}

.lifecycle-state--past .lifecycle-connector {
  background: var(--status-success);
  opacity: 0.3;
}

.lifecycle-state--future .lifecycle-state-label {
  color: var(--text-muted);
  opacity: 0.5;
}

.lifecycle-state--future .lifecycle-state-indicator {
  opacity: 0.3;
}

.lifecycle-state--future .lifecycle-connector {
  opacity: 0.2;
}

/* ⑥ FOOTER NARRATIVE */
.footer-narrative {
  text-align: center;
  padding: 24px 0;
}

.narrative-text {
  font-family: var(--font-display);
  font-size: 1.125rem;
  color: var(--text-primary);
  font-weight: 600;
  letter-spacing: 0.02em;
  text-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}

.narrative-text--shimmer {
  position: relative;
  overflow: hidden;
}

.narrative-text--shimmer::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  animation: shimmer 8s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  50% {
    left: 100%;
  }
  100% {
    left: 100%;
  }
}

/* Model Loading Overlay - positioned below GPU value, not covering it */
.model-loading-overlay {
  position: absolute;
  top: auto;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.9);
  border: 1px solid var(--abs-orange);
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--abs-orange);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  z-index: 10;
  box-shadow: 0 0 30px rgba(249, 115, 22, 0.4);
  backdrop-filter: blur(10px);
  white-space: nowrap;
}

.hero-value--surge {
  animation: surge-pulse 2s ease-in-out infinite;
  color: var(--abs-orange);
}

@keyframes surge-pulse {
  0%, 100% {
    text-shadow: 0 0 30px rgba(249, 115, 22, 0.6);
  }
  50% {
    text-shadow: 0 0 50px rgba(249, 115, 22, 0.9);
  }
}

/* Live Inference Metrics */
.live-inference-section {
  margin-top: 32px;
  padding: 24px;
  background: var(--abs-card);
  border: 1px solid var(--abs-orange);
  border-radius: 12px;
  box-shadow: 0 0 30px rgba(249, 115, 22, 0.2);
}

.live-inference-header {
  margin-bottom: 16px;
  text-align: center;
}

.live-badge {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(249, 115, 22, 0.15);
  border: 1px solid var(--abs-orange);
  border-radius: 20px;
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--abs-orange);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.live-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.live-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.live-metric-label {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.live-metric-value {
  font-family: var(--font-mono);
  font-size: 1rem;
  font-weight: 600;
  color: var(--abs-orange);
}

.live-annotation {
  text-align: center;
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-style: italic;
  padding-top: 12px;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
}

/* Responsive */
@media (max-width: 768px) {
  .dual-panel-section {
    grid-template-columns: 1fr;
  }
  
  .hero-value {
    font-size: 4rem;
  }
  
  .hero-unit {
    font-size: 2rem;
  }
}
</style>
