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
const radius = 120
const innerRadius = 100
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
</script>

<template>
  <div ref="containerRef" class="scene-a">
    <!-- GPU Particle Field Background -->
    <!-- Particle field is rendered via composable -->
    
    <!-- Full-screen GPU ring (center, 3D) -->
    <div class="scene-a__gpu-ring" :style="ringTransform">
      <!-- Outer ring: VRAM bandwidth -->
      <svg class="gpu-ring-svg gpu-ring-svg--outer" width="500" height="500" viewBox="0 0 300 300">
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
      
      <!-- Inner ring: CUDA cores -->
      <svg class="gpu-ring-svg gpu-ring-svg--inner" width="500" height="500" viewBox="0 0 300 300">
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
      
      <div class="gpu-ring-value" :style="ringGlow">
        <template v-if="display.state === 'LOADING_70B'">
          {{ display.loadProgressPct }}%
        </template>
        <template v-else>
          {{ display.gpuUtilPct }}%
        </template>
      </div>
      
      <!-- Status badge below ring -->
      <div class="gpu-ring-status" :class="`gpu-ring-status--${display.state.toLowerCase()}`">
        {{ display.statusLabel }}
      </div>
    </div>
    
    <!-- Left rail: Metrics -->
    <div class="scene-a__left-rail">
      <!-- State-specific content -->
      <template v-if="display.state === 'IDLE_READY' || display.state === 'LIVE_INFERENCE'">
        <div class="metric-item">
          <div class="metric-label">GPU VRAM</div>
          <div class="metric-value-large" :style="getElementGlow('var(--text-primary)', 0.3)">
            {{ display.vramUsed }} / {{ display.vramTotal }} GB
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
      </template>
      
      <!-- Loading state: show phase -->
      <template v-if="display.state === 'LOADING_70B'">
        <div class="metric-item">
          <div class="metric-label">LOADING</div>
          <div class="metric-value-large" :style="getElementGlow('var(--abs-orange)', 0.4)">
            {{ display.activeModel || '70B MODEL' }}
          </div>
        </div>
        <div class="metric-item">
          <div class="metric-label">PHASE</div>
          <div class="metric-value-medium">
            {{ display.loadPhase?.toUpperCase() || 'LOADING' }}
          </div>
        </div>
      </template>
      
      <!-- Live state: show performance -->
      <template v-if="display.state === 'LIVE_INFERENCE'">
        <div class="metric-item metric-item--highlight">
          <div class="metric-label">TOKENS/SEC</div>
          <div class="metric-value-large" :style="getElementGlow('var(--abs-orange)', 0.5)">
            {{ display.tokPerSec }}
          </div>
        </div>
      </template>
    </div>
    
    <!-- Top-right: CES overlay + live indicator -->
    <div class="scene-a__top-right">
      <div v-if="isCESMode" class="ces-badge" :style="getElementGlow('var(--abs-orange)', 0.5)">
        LIVE AI · NO CLOUD · RTX PRO 6000
      </div>
      <div v-if="display.isFresh" class="live-indicator">
        <span class="live-indicator__dot"></span>
        LIVE
      </div>
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

.scene-a__gpu-ring {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transform-style: preserve-3d;
  transition: transform 0.1s linear;
  z-index: 10;
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
  position: absolute;
  font-family: var(--font-mono);
  font-size: 10rem;
  font-weight: 700;
  color: var(--abs-orange);
  text-shadow: 
    0 0 8px var(--abs-orange-glow),
    0 0 15px rgba(249, 115, 22, 0.4);
  z-index: 3;
  transition: all 0.3s var(--ease-smooth);
  letter-spacing: -0.02em;
}

.scene-a__left-rail {
  position: absolute;
  left: 80px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 48px;
  z-index: 10;
  background: rgba(0, 0, 0, 0.4);
  padding: 32px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-label {
  font-family: var(--font-label);
  font-size: 1.5rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.8);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

.metric-value-large {
  font-family: var(--font-mono);
  font-size: 5.5rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 0 6px rgba(255, 255, 255, 0.3);
  transition: all 0.3s var(--ease-smooth);
  letter-spacing: 0.02em;
}

.metric-value-medium {
  font-family: var(--font-mono);
  font-size: 3rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.25);
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
</style>

