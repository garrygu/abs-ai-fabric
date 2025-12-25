<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useCESMode } from '@/composables/useCESMode'
import { useBloomEffect } from '@/composables/useBloomEffect'
import { useDemoControlStore } from '@/stores/demoControlStore'
import { useSceneAController, type SceneATelemetry } from '@/attract/scene-a/sceneAState'

const metricsStore = useMetricsStore()
const demoControlStore = useDemoControlStore()
const { isCESMode } = useCESMode()
const containerRef = ref<HTMLElement | null>(null)
const { getElementGlow } = useBloomEffect()

// Scene A state controller
const sceneA = useSceneAController()
const { display, uniforms } = sceneA

// Feed telemetry to controller
let telemetryInterval: ReturnType<typeof setInterval> | null = null
let tickRaf: ReturnType<typeof requestAnimationFrame> | null = null

onMounted(() => {
  // Feed telemetry every 500ms
  telemetryInterval = setInterval(() => {
    const t: SceneATelemetry = {
      ts: Date.now(),
      gpuUtilPct: metricsStore.gpuUtilization,
      vramUsedGB: metricsStore.vramUsed,
      vramTotalGB: metricsStore.vramTotal,
      ramUsedGB: metricsStore.memoryUsed,
      ramTotalGB: metricsStore.memoryTotal,
      uptimeSec: metricsStore.metrics?.uptime_seconds ?? 0,
      // Map demo control state to loading/inference
      activeModel: demoControlStore.activeModel ?? undefined,
      tokPerSec: demoControlStore.isRunning ? 45 : undefined,  // Simulated
      loadProgress: demoControlStore.isWarming ? 0.5 : undefined  // Simulated
    }
    sceneA.onTelemetry(t)
  }, 500)
  
  // Tick animation loop
  const tick = () => {
    sceneA.tick(Date.now())
    tickRaf = requestAnimationFrame(tick)
  }
  tick()
})

onUnmounted(() => {
  if (telemetryInterval) {
    clearInterval(telemetryInterval)
    telemetryInterval = null
  }
  if (tickRaf !== null) {
    cancelAnimationFrame(tickRaf)
    tickRaf = null
  }
})

// 3D ring rotation (parallax)
const ringRotationY = ref(0)
const ringRotationX = ref(0)
let rotationAnimation: ReturnType<typeof requestAnimationFrame> | null = null

// Ring jitter (reacts to GPU temp/utilization changes)
const ringJitter = ref({ x: 0, y: 0 })
let jitterTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // Parallax rotation animation - speed varies by state
  const animateRotation = () => {
    const speedMult = uniforms.value.state === 'LIVE_INFERENCE' ? 1.5 
                    : uniforms.value.state === 'LOADING_70B' ? 0.8 
                    : 0.3
    ringRotationY.value += 0.2 * speedMult
    ringRotationX.value = Math.sin(Date.now() / 5000) * 5
    rotationAnimation = requestAnimationFrame(animateRotation)
  }
  animateRotation()
  
  // Ring jitter (reacts to state changes)
  let lastState = uniforms.value.state
  jitterTimer = setInterval(() => {
    if (uniforms.value.state !== lastState) {
      // Jitter on state change
      ringJitter.value = {
        x: (Math.random() - 0.5) * 3,
        y: (Math.random() - 0.5) * 3
      }
      setTimeout(() => {
        ringJitter.value = { x: 0, y: 0 }
      }, 300)
      lastState = uniforms.value.state
    }
  }, 100)
})

onUnmounted(() => {
  if (rotationAnimation !== null) {
    cancelAnimationFrame(rotationAnimation)
    rotationAnimation = null
  }
  if (jitterTimer) {
    clearInterval(jitterTimer)
    jitterTimer = null
  }
})

// Ring progress based on state
const ringProgress = computed(() => {
  if (uniforms.value.state === 'LOADING_70B') {
    return uniforms.value.progress01  // Loading progress
  }
  return uniforms.value.gpuUtil01  // GPU utilization
})

// GPU ring circumference calculation (for SVG)
const radius = 140
const innerRadius = 120
const circumference = 2 * Math.PI * radius
const innerCircumference = 2 * Math.PI * innerRadius
const gpuUtilOffset = computed(() => circumference * (1 - ringProgress.value))
const vramOffset = computed(() => {
  const vramRatio = metricsStore.vramUsed / metricsStore.vramTotal
  return innerCircumference * (1 - vramRatio)
})

// 3D transform for ring
const ringTransform = computed(() => {
  const jitterX = ringJitter.value.x
  const jitterY = ringJitter.value.y
  return `perspective(1000px) rotateY(${ringRotationY.value}deg) rotateX(${ringRotationX.value + jitterX}deg) translateZ(${jitterY}px)`
})

// State-aware bloom intensity
const bloomIntensity = computed(() => {
  switch (uniforms.value.state) {
    case 'LIVE_INFERENCE': return 1.5
    case 'LOADING_70B': return 1.2
    default: return 0.8
  }
})

// Bloom glow styles
const ringGlow = computed(() => getElementGlow('var(--abs-orange)', bloomIntensity.value))

// Format uptime
function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// ============================================================================
// CES Wow Enhancements
// ============================================================================

// Carousel cards for IDLE state (rotate every 8s)
const carouselCards = [
  { title: 'No Cloud', subtitle: '0 data leaves this device' },
  { title: '70B Ready', subtitle: '96GB VRAM · Instant inference' },
  { title: 'Apps', subtitle: 'Chat · RAG · Vision · Code' },
  { title: 'Live Demo', subtitle: 'One-click to try it yourself' }
]
const currentCardIndex = ref(0)
let carouselInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // Rotate carousel every 8 seconds
  carouselInterval = setInterval(() => {
    if (uniforms.value.state === 'IDLE_READY') {
      currentCardIndex.value = (currentCardIndex.value + 1) % carouselCards.length
    }
  }, 8000)
})

onUnmounted(() => {
  if (carouselInterval) {
    clearInterval(carouselInterval)
    carouselInterval = null
  }
})

const currentCard = computed(() => carouselCards[currentCardIndex.value])

// GPU model info (for hero bar) - extract short name
const gpuModelRaw = computed(() => metricsStore.gpuModel || 'RTX PRO 6000')
const gpuModelShort = computed(() => {
  // Extract just "RTX PRO 6000" from full model name
  const raw = gpuModelRaw.value
  const match = raw.match(/RTX\s*(?:PRO)?\s*\d+/i)
  return match ? match[0].toUpperCase() : 'RTX PRO 6000'
})
const vramTotal = computed(() => Math.round(metricsStore.vramTotal) || 96)

// WebGPU visual parameters by state
const webgpuParams = computed(() => {
  switch (uniforms.value.state) {
    case 'LIVE_INFERENCE':
      const utilNorm = uniforms.value.gpuUtil01
      return {
        energy: 0.80,
        flowSpeed: 0.45,
        particleSpeed: 0.55 + 0.60 * utilNorm,
        pulseFreq: 0.8 + 1.4 * Math.min(1, (display.value.tokPerSec ? parseFloat(display.value.tokPerSec) : 0) / 80),
        bloom: 0.65
      }
    case 'LOADING_70B':
      return {
        energy: 0.55,
        flowSpeed: 0.30,
        particleSpeed: 0.35,
        pulseFreq: 0,
        bloom: 0.55
      }
    default: // IDLE_READY
      return {
        energy: 0.25,
        flowSpeed: 0.12,
        particleSpeed: 0.18,
        pulseFreq: 0,
        bloom: 0.35
      }
  }
})

// Center ring label (contextual - never bare %)
const centerLabel = computed(() => {
  switch (display.value.state) {
    case 'LOADING_70B':
      return `${display.value.loadProgressPct}%`
    case 'LIVE_INFERENCE':
      return `GPU ${display.value.gpuUtilPct}%`
    default:
      // Trust rule: if VRAM high + GPU low = PRELOADED
      return display.value.statusLabel
  }
})

const centerSublabel = computed(() => {
  switch (display.value.state) {
    case 'LOADING_70B':
      return 'LOADING 70B'
    case 'LIVE_INFERENCE':
      return display.value.activeModel || 'INFERENCE'
    default:
      return 'LOCAL AI'
  }
})

// Inference load label (below ring)
const inferenceLoadLabel = computed(() => {
  if (display.value.state === 'LIVE_INFERENCE' || display.value.state === 'LOADING_70B') {
    return 'ACTIVE INFERENCE'
  }
  return 'INFERENCE LOAD'
})

// Active model name for VRAM allocation label
const activeModelForVram = computed(() => {
  if (display.value.state === 'LIVE_INFERENCE' && display.value.activeModel) {
    return display.value.activeModel
  }
  if (demoControlStore.activeModel === 'deepseek-r1-70b') return 'deepseek-r1-70b'
  if (demoControlStore.activeModel === 'llama3-70b') return 'llama3-70b'
  if (demoControlStore.activeModel === 'dual') return 'dual-70b'
  return null
})

// Performance metrics for right panel
const performanceMetrics = computed(() => {
  const metrics: {
    tokPerSec?: string
    ttft?: string
    lat?: string
    ctx?: string
    quant?: string
  } = {}
  
  if (display.value.state === 'LIVE_INFERENCE') {
    if (display.value.tokPerSec) {
      metrics.tokPerSec = display.value.tokPerSec
    }
    
    // TTFT
    if (display.value.ttftMs !== null && display.value.ttftMs !== undefined) {
      const ttftMs = display.value.ttftMs
      metrics.ttft = ttftMs < 1000 ? `${ttftMs}ms` : `${(ttftMs / 1000).toFixed(1)}s`
    } else if (demoControlStore.liveMetrics.timeToFirstToken !== undefined && demoControlStore.liveMetrics.timeToFirstToken > 0) {
      const ttftMs = demoControlStore.liveMetrics.timeToFirstToken
      metrics.ttft = ttftMs < 1000 ? `${ttftMs}ms` : `${(ttftMs / 1000).toFixed(1)}s`
    } else {
      metrics.ttft = '<1s'
    }
    
    // Latency
    if (demoControlStore.liveMetrics.latency !== undefined && demoControlStore.liveMetrics.latency > 0) {
      const lat = demoControlStore.liveMetrics.latency
      metrics.lat = lat < 1000 ? `${lat}ms` : `${(lat / 1000).toFixed(1)}s`
    } else {
      metrics.lat = '<1s'
    }
    
    // Context window
    metrics.ctx = demoControlStore.liveMetrics.contextWindow || '128k'
    
    // Quantization (default for 70B models)
    metrics.quant = 'Q4_K_M'
  }
  
  return metrics
})
</script>

<template>
  <div ref="containerRef" class="scene-a" :class="`scene-a--${display.state.toLowerCase()}`">
    <!-- GPU Particle Field Background -->
    <!-- Particle field is rendered via composable -->
    
    <!-- ============================================== -->
    <!-- HERO STATUS BAR (Top) -->
    <!-- ============================================== -->
    <div class="scene-a__hero-bar">
      <div class="hero-bar__content">
        <span class="hero-bar__tag">LOCAL AI</span>
        <span class="hero-bar__divider">·</span>
        <span class="hero-bar__tag">NO CLOUD</span>
        <span class="hero-bar__divider">·</span>
        <span class="hero-bar__gpu">{{ gpuModelShort }} · {{ vramTotal }}GB</span>
        <span v-if="!display.isFresh" class="hero-bar__stale">· DEMO</span>
      </div>
    </div>
    
    <!-- ============================================== -->
    <!-- CENTER: GPU RING + CONTEXTUAL LABELS -->
    <!-- ============================================== -->
    <div class="scene-a__gpu-ring-wrapper">
      <div class="scene-a__gpu-ring" :style="ringTransform">
      <!-- Outer ring: VRAM bandwidth -->
      <svg class="gpu-ring-svg gpu-ring-svg--outer" width="600" height="600" viewBox="0 0 300 300">
        <circle
          cx="150"
          cy="150"
          :r="radius"
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          stroke-width="6"
        />
        <circle
          cx="150"
          cy="150"
          :r="radius"
          fill="none"
          stroke="rgba(249, 115, 22, 0.4)"
          stroke-width="6"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="vramOffset"
          transform="rotate(-90 150 150)"
          class="gpu-ring-arc gpu-ring-arc--outer"
          :style="ringGlow"
        />
      </svg>
      
      <!-- Inner ring: GPU util / progress -->
      <svg class="gpu-ring-svg gpu-ring-svg--inner" width="600" height="600" viewBox="0 0 300 300">
        <circle
          cx="150"
          cy="150"
          :r="innerRadius"
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          stroke-width="8"
        />
        <circle
          cx="150"
          cy="150"
          :r="innerRadius"
          fill="none"
          stroke="var(--abs-orange)"
          stroke-width="8"
          stroke-linecap="round"
          :stroke-dasharray="innerCircumference"
          :stroke-dashoffset="gpuUtilOffset"
          transform="rotate(-90 150 150)"
          class="gpu-ring-arc gpu-ring-arc--inner"
          :style="ringGlow"
        />
      </svg>
      
      <!-- Center value (contextual) - value first (larger), label below (smaller) -->
      <div class="gpu-ring-center">
        <div class="gpu-ring-value" :style="ringGlow">{{ centerLabel }}</div>
        <div class="gpu-ring-sublabel">{{ centerSublabel }}</div>
      </div>
      </div>
      
      <!-- Inference Load Label (below ring) -->
      <div class="gpu-ring-inference-label">
        {{ inferenceLoadLabel }}
      </div>
    </div>
    
    <!-- ============================================== -->
    <!-- LEFT RAIL: METRICS -->
    <!-- ============================================== -->
    <div class="scene-a__left-rail">
      <div class="metric-item">
        <div class="metric-label">GPU VRAM</div>
        <div class="metric-value-large" :style="getElementGlow('var(--text-primary)', 0.3)">
          {{ display.vramUsed }} / {{ display.vramTotal }} GB
        </div>
        <div v-if="activeModelForVram" class="metric-allocated">
          ALLOCATED BY: <span class="model-name">{{ activeModelForVram }}</span>
        </div>
      </div>
      
      <div class="metric-item">
        <div class="metric-label">RAM</div>
        <div class="metric-value-large" :style="getElementGlow('var(--text-primary)', 0.3)">
          {{ display.ramUsed }} / {{ display.ramTotal }} GB
        </div>
      </div>
      
      <div class="metric-item">
        <div class="metric-label">UPTIME</div>
        <div class="metric-value-medium">
          {{ formatUptime(display.uptime) }}
        </div>
      </div>
    </div>
    
    <!-- ============================================== -->
    <!-- RIGHT PANEL: CAROUSEL / PHASE / PERFORMANCE -->
    <!-- ============================================== -->
    <div class="scene-a__right-panel">
      <!-- IDLE: Rotating carousel cards -->
      <Transition name="card-fade" mode="out-in">
        <div v-if="display.state === 'IDLE_READY'" :key="currentCardIndex" class="carousel-card">
          <div class="carousel-card__title">{{ currentCard.title }}</div>
          <div class="carousel-card__subtitle">{{ currentCard.subtitle }}</div>
        </div>
      </Transition>
      
      <!-- LOADING: Phase card -->
      <div v-if="display.state === 'LOADING_70B'" class="phase-card">
        <div class="phase-card__title">{{ display.loadPhase?.toUpperCase() || 'LOADING' }}</div>
        <div class="phase-card__subtitle">Preparing 70B for instant inference</div>
        <div class="phase-card__progress">
          <div class="phase-card__progress-bar" :style="{ width: `${display.loadProgressPct}%` }"></div>
        </div>
      </div>
      
      <!-- LIVE: Performance card -->
      <div v-if="display.state === 'LIVE_INFERENCE'" class="performance-card">
        <div class="performance-card__header">Running:</div>
        <div class="performance-card__model">{{ display.activeModel || 'Llama 70B' }}</div>
        <div class="performance-card__metrics">
          <div v-if="performanceMetrics.tokPerSec" class="perf-metric">
            <span class="perf-metric__value">{{ performanceMetrics.tokPerSec }}</span>
            <span class="perf-metric__label">tok/s</span>
          </div>
          <div v-if="performanceMetrics.ttft" class="perf-metric">
            <span class="perf-metric__value">{{ performanceMetrics.ttft }}</span>
            <span class="perf-metric__label">TTFT</span>
          </div>
          <div v-if="performanceMetrics.lat" class="perf-metric">
            <span class="perf-metric__value">{{ performanceMetrics.lat }}</span>
            <span class="perf-metric__label">LAT</span>
          </div>
        </div>
        <div v-if="performanceMetrics.ctx || performanceMetrics.quant" class="performance-card__meta">
          <span v-if="performanceMetrics.ctx" class="meta-item">CTX {{ performanceMetrics.ctx }}</span>
          <span v-if="performanceMetrics.quant" class="meta-item">{{ performanceMetrics.quant }}</span>
        </div>
      </div>
    </div>
    
    <!-- LIVE indicator (bottom-right) -->
    <div v-if="display.isFresh" class="scene-a__live-badge">
      <span class="live-badge__dot"></span>
      LIVE
    </div>
  </div>
</template>

<style scoped>
.scene-a {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--abs-black);
  overflow: hidden;
  perspective: 2000px;
}

/* Ensure text is always readable - reduce particle field opacity if needed */
.scene-a::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, transparent 0%, rgba(0, 0, 0, 0.3) 100%);
  pointer-events: none;
  z-index: 0;
}

.scene-a__gpu-ring-wrapper {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, calc(-50% + 20px)); /* Offset down to avoid top overlap */
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 15; /* Center ring above side panels */
  width: 600px;
  pointer-events: none; /* Allow clicks to pass through */
}

.scene-a__gpu-ring-wrapper > * {
  pointer-events: auto; /* Re-enable for interactive elements */
}

.scene-a__gpu-ring {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transform-style: preserve-3d;
  transition: transform 0.1s linear;
}

.gpu-ring-svg {
  position: absolute;
  filter: drop-shadow(0 0 30px rgba(249, 115, 22, 0.4));
  transition: filter 0.3s var(--ease-smooth);
}

.gpu-ring-svg--outer {
  z-index: 1;
}

.gpu-ring-svg--inner {
  z-index: 2;
}

.gpu-ring-arc {
  transition: stroke-dashoffset 0.8s var(--ease-smooth);
  filter: drop-shadow(0 0 8px var(--abs-orange-glow)) drop-shadow(0 0 15px rgba(249, 115, 22, 0.3));
}

.gpu-ring-arc--inner {
  filter: drop-shadow(0 0 10px var(--abs-orange-glow)) drop-shadow(0 0 20px rgba(249, 115, 22, 0.4));
}

.gpu-ring-value {
  /* No position: absolute - let flex container handle layout */
  font-family: var(--font-mono);
  font-size: 7.5rem; /* Slightly smaller to fit better in larger ring */
  font-weight: 700;
  color: var(--abs-orange);
  text-shadow: 
    0 0 8px var(--abs-orange-glow),
    0 0 15px rgba(249, 115, 22, 0.4);
  transition: all 0.3s var(--ease-smooth);
  letter-spacing: -0.02em;
}

.scene-a__left-rail {
  position: absolute;
  left: 40px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 48px;
  z-index: 5; /* Side panels below center */
  background: rgba(0, 0, 0, 0.4);
  padding: 32px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  width: 360px;
  min-width: 320px;
  max-width: calc(50vw - 300px); /* Ensure it doesn't overlap center */
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-label {
  font-family: var(--font-label);
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.8);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

.metric-value-large {
  font-family: var(--font-mono);
  font-size: 3rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 0 6px rgba(255, 255, 255, 0.3);
  transition: all 0.3s var(--ease-smooth);
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.metric-value-medium {
  font-family: var(--font-mono);
  font-size: 2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.25);
}

.metric-allocated {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 4px;
}

.metric-allocated .model-name {
  color: var(--abs-orange);
  font-weight: 600;
}

.scene-a__top-right {
  position: absolute;
  top: 80px;
  right: 80px;
  z-index: 10;
}

.ces-badge {
  font-family: var(--font-label);
  font-size: 2.25rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--abs-orange);
  text-shadow: 
    0 0 8px var(--abs-orange-glow);
  transition: all 0.3s var(--ease-smooth);
  background: rgba(0, 0, 0, 0.3);
  padding: 12px 24px;
  border-radius: 8px;
  border: 1px solid rgba(249, 115, 22, 0.2);
  margin-bottom: 16px;
}

/* Status badge below ring */
.gpu-ring-status {
  position: absolute;
  bottom: -60px;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-label);
  font-size: 2rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  padding: 12px 28px;
  border-radius: 8px;
  transition: all 0.3s var(--ease-smooth);
  white-space: nowrap;
}

.gpu-ring-status--idle_ready {
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.gpu-ring-status--loading_70b {
  color: var(--abs-orange);
  background: rgba(249, 115, 22, 0.15);
  border: 1px solid var(--abs-orange);
  animation: pulse-status 1.5s ease-in-out infinite;
}

.gpu-ring-status--live_inference {
  color: var(--abs-orange);
  background: rgba(249, 115, 22, 0.2);
  border: 1px solid var(--abs-orange);
  text-shadow: 0 0 8px var(--abs-orange-glow);
}

@keyframes pulse-status {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

/* Live indicator */
.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-label);
  font-size: 1.25rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #4ade80;
  text-shadow: 0 0 6px rgba(74, 222, 128, 0.5);
}

.live-indicator__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 8px #4ade80;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.6; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.1); }
}

/* Metric highlight for live state */
.metric-item--highlight .metric-value-large {
  color: var(--abs-orange);
}

.scene-a__top-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

/* ============================================== */
/* HERO STATUS BAR */
/* ============================================== */

.scene-a__hero-bar {
  position: absolute;
  top: 40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  z-index: 20;
}

.hero-bar__content {
  display: flex;
  align-items: center;
  gap: 16px;
  font-family: var(--font-label);
  font-size: 2rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(0, 0, 0, 0.4);
  padding: 16px 32px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.hero-bar__tag {
  color: var(--abs-orange);
  text-shadow: 0 0 8px var(--abs-orange-glow);
}

.hero-bar__divider {
  color: rgba(255, 255, 255, 0.3);
}

.hero-bar__gpu {
  color: rgba(255, 255, 255, 0.8);
}

.hero-bar__status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-label);
  font-size: 1.25rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.hero-bar__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.hero-bar__dot--idle_ready {
  background: rgba(255, 255, 255, 0.6);
}

.hero-bar__dot--loading_70b {
  background: var(--abs-orange);
  animation: pulse-dot 1s ease-in-out infinite;
}

.hero-bar__dot--live_inference {
  background: #4ade80;
  box-shadow: 0 0 8px #4ade80;
  animation: pulse-dot 0.8s ease-in-out infinite;
}

.hero-bar__status-text {
  color: rgba(255, 255, 255, 0.7);
}

.hero-bar__stale {
  color: #fbbf24;
  font-size: 0.9rem;
}

/* ============================================== */
/* CENTER RING SUBLABEL */
/* ============================================== */

.gpu-ring-center {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px; /* Large gap between sublabel and value */
  z-index: 3;
}

.gpu-ring-sublabel {
  font-family: var(--font-label);
  font-size: 1.25rem; /* Slightly smaller */
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: rgba(255, 255, 255, 0.5);
  /* Sublabel now positioned above value */
}

/* Inference Load Label (below ring) */
.gpu-ring-inference-label {
  margin-top: 32px;
  font-family: var(--font-label);
  font-size: 1.5rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--abs-orange);
  text-shadow: 0 0 8px var(--abs-orange-glow);
  white-space: nowrap;
  transition: all 0.3s var(--ease-smooth);
  position: relative;
  z-index: 16;
}

/* ============================================== */
/* RIGHT PANEL */
/* ============================================== */

.scene-a__right-panel {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 5; /* Side panels below center */
  width: 280px;
  max-width: calc(50vw - 300px); /* Ensure it doesn't overlap center */
}

/* Carousel Card */
.carousel-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 32px;
  backdrop-filter: blur(10px);
}

.carousel-card__title {
  font-family: var(--font-label);
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--abs-orange);
  margin-bottom: 12px;
  text-shadow: 0 0 8px var(--abs-orange-glow);
}

.carousel-card__subtitle {
  font-family: var(--font-label);
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
}

/* Card fade transition */
.card-fade-enter-active,
.card-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.card-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.card-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Phase Card (Loading) */
.phase-card {
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid var(--abs-orange);
  border-radius: 16px;
  padding: 32px;
}

.phase-card__title {
  font-family: var(--font-label);
  font-size: 2rem;
  font-weight: 700;
  color: var(--abs-orange);
  margin-bottom: 8px;
  text-shadow: 0 0 8px var(--abs-orange-glow);
}

.phase-card__subtitle {
  font-family: var(--font-label);
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 20px;
}

.phase-card__progress {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.phase-card__progress-bar {
  height: 100%;
  background: var(--abs-orange);
  border-radius: 3px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px var(--abs-orange-glow);
}

/* Performance Card (Live) */
.performance-card {
  background: rgba(74, 222, 128, 0.08);
  border: 1px solid rgba(74, 222, 128, 0.3);
  border-radius: 16px;
  padding: 32px;
}

.performance-card__header {
  font-family: var(--font-label);
  font-size: 1.25rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #4ade80;
  margin-bottom: 8px;
}

.performance-card__model {
  font-family: var(--font-label);
  font-size: 2rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 20px;
}

.performance-card__metrics {
  display: flex;
  gap: 24px;
}

.perf-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.perf-metric__value {
  font-family: var(--font-mono);
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--abs-orange);
  text-shadow: 0 0 8px var(--abs-orange-glow);
}

.perf-metric__label {
  font-family: var(--font-label);
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.5);
}

.performance-card__meta {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-family: var(--font-label);
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.performance-card__meta .meta-item {
  font-weight: 500;
}

/* ============================================== */
/* LIVE BADGE (Bottom-right) */
/* ============================================== */

.scene-a__live-badge {
  position: absolute;
  bottom: 40px;
  right: 80px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-label);
  font-size: 1.5rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #4ade80;
  text-shadow: 0 0 8px rgba(74, 222, 128, 0.6);
  z-index: 20;
}

.live-badge__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 12px #4ade80;
  animation: pulse-dot 1s ease-in-out infinite;
}

/* Responsive adjustments to prevent overlap */
@media (max-width: 1600px) {
  .scene-a__left-rail {
    left: 40px;
    max-width: 340px;
    width: 340px;
  }
  
  .scene-a__gpu-ring-wrapper {
    width: 550px;
  }
  
  .gpu-ring-svg {
    width: 550px;
    height: 550px;
  }
  
  .gpu-ring-value {
    font-size: 7rem;
  }
  
  .scene-a__right-panel {
    right: 40px;
    width: 280px;
  }
}

@media (max-width: 1200px) {
  .scene-a__left-rail {
    left: 20px;
    max-width: 300px;
    width: 300px;
    padding: 24px;
  }
  
  .scene-a__gpu-ring-wrapper {
    width: 450px;
    padding-bottom: 100px;
  }
  
  .gpu-ring-svg {
    width: 450px;
    height: 450px;
  }
  
  .gpu-ring-value {
    font-size: 6rem;
  }
  
  .scene-a__right-panel {
    right: 20px;
    width: 250px;
  }
  
  .gpu-ring-inference-label {
    font-size: 1.25rem;
  }
}
</style>

