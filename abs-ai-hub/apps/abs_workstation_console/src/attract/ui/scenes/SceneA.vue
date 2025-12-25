<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useCESMode } from '@/composables/useCESMode'
import { useBloomEffect } from '@/composables/useBloomEffect'

const metricsStore = useMetricsStore()
const { isCESMode } = useCESMode()
const containerRef = ref<HTMLElement | null>(null)
const { getElementGlow } = useBloomEffect()

// WebGPU particle field is rendered globally via AttractModeOverlay
// (removed legacy Canvas 2D fallback)

// Animated GPU utilization (starts at 8%, can spike)
const animatedGpuUtil = ref(8)
let gpuAnimationInterval: ReturnType<typeof setInterval> | null = null

// VRAM animation (brief tick upward)
const animatedVramUsed = ref(82)
const vramTotal = computed(() => metricsStore.vramTotal)
let vramTickTimer: ReturnType<typeof setTimeout> | null = null

// 3D ring rotation (parallax)
const ringRotationY = ref(0)
const ringRotationX = ref(0)
let rotationAnimation: ReturnType<typeof requestAnimationFrame> | null = null

// Ring jitter (reacts to GPU temp/utilization changes)
const ringJitter = ref({ x: 0, y: 0 })
let jitterTimer: ReturnType<typeof setInterval> | null = null

// Inner/outer ring separation
const innerRingProgress = computed(() => displayGpuUtil.value / 100)
const outerRingProgress = computed(() => (metricsStore.vramUsed / metricsStore.vramTotal) * 100 / 100)

onMounted(() => {
  // Start with base GPU utilization
  animatedGpuUtil.value = Math.max(8, metricsStore.gpuUtilization)
  
  // GPU utilization animation - subtle variations
  gpuAnimationInterval = setInterval(() => {
    const base = Math.max(8, metricsStore.gpuUtilization)
    animatedGpuUtil.value = base + (Math.random() * 2 - 1) // ±1% variation
  }, 2000)
  
  // VRAM tick animation - brief upward tick once per loop
  const triggerVramTick = () => {
    const base = metricsStore.vramUsed
    animatedVramUsed.value = base + 0.5
    setTimeout(() => {
      animatedVramUsed.value = base
    }, 500)
  }
  
  // Trigger VRAM tick once during scene (around 4-5 seconds in)
  vramTickTimer = setTimeout(triggerVramTick, 5000)
  
  // Parallax rotation animation
  const animateRotation = () => {
    ringRotationY.value += 0.2
    ringRotationX.value = Math.sin(Date.now() / 5000) * 5
    rotationAnimation = requestAnimationFrame(animateRotation)
  }
  animateRotation()
  
  // Ring jitter (reacts to GPU utilization changes)
  let lastGpuUtil = animatedGpuUtil.value
  jitterTimer = setInterval(() => {
    const currentUtil = animatedGpuUtil.value
    const delta = Math.abs(currentUtil - lastGpuUtil)
    if (delta > 1) {
      // Jitter when utilization changes significantly
      ringJitter.value = {
        x: (Math.random() - 0.5) * delta * 0.5,
        y: (Math.random() - 0.5) * delta * 0.5
      }
      setTimeout(() => {
        ringJitter.value = { x: 0, y: 0 }
      }, 300)
    }
    lastGpuUtil = currentUtil
  }, 500)
})

onUnmounted(() => {
  if (gpuAnimationInterval) {
    clearInterval(gpuAnimationInterval)
    gpuAnimationInterval = null
  }
  if (vramTickTimer) {
    clearTimeout(vramTickTimer)
    vramTickTimer = null
  }
  if (rotationAnimation !== null) {
    cancelAnimationFrame(rotationAnimation)
    rotationAnimation = null
  }
  if (jitterTimer) {
    clearInterval(jitterTimer)
    jitterTimer = null
  }
})

const displayGpuUtil = computed(() => Math.round(animatedGpuUtil.value))
const displayVramUsed = computed(() => animatedVramUsed.value.toFixed(0))
const displayVramTotal = computed(() => vramTotal.value.toFixed(0))
const displayRamUsed = computed(() => metricsStore.memoryUsed.toFixed(0))
const displayRamTotal = computed(() => metricsStore.memoryTotal.toFixed(0))

// GPU ring circumference calculation (for SVG)
const radius = 120
const innerRadius = 100
const circumference = 2 * Math.PI * radius
const innerCircumference = 2 * Math.PI * innerRadius
const gpuUtilOffset = computed(() => circumference * (1 - innerRingProgress.value))
const vramOffset = computed(() => innerCircumference * (1 - outerRingProgress.value))

// 3D transform for ring
const ringTransform = computed(() => {
  const jitterX = ringJitter.value.x
  const jitterY = ringJitter.value.y
  return `perspective(1000px) rotateY(${ringRotationY.value}deg) rotateX(${ringRotationX.value + jitterX}deg) translateZ(${jitterY}px)`
})

// Bloom glow styles
const ringGlow = computed(() => getElementGlow('var(--abs-orange)', 1.2))
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
      
      <div class="gpu-ring-value" :style="ringGlow">{{ displayGpuUtil }}%</div>
    </div>
    
    <!-- Left rail: Metrics -->
    <div class="scene-a__left-rail">
      <div class="metric-item">
        <div class="metric-label">GPU VRAM</div>
        <div class="metric-value-large" :style="getElementGlow('var(--text-primary)', 0.3)">
          {{ displayVramUsed }} / {{ displayVramTotal }} GB
        </div>
      </div>
      
      <div class="metric-item">
        <div class="metric-label">RAM</div>
        <div class="metric-value-large" :style="getElementGlow('var(--text-primary)', 0.3)">
          {{ displayRamUsed }} / {{ displayRamTotal }} GB
        </div>
      </div>
      
      <div class="metric-item">
        <div class="metric-label">UPTIME</div>
        <div class="metric-value-medium">
          {{ metricsStore.uptimeFormatted }}
        </div>
      </div>
    </div>
    
    <!-- Top-right: CES overlay -->
    <div v-if="isCESMode" class="scene-a__top-right">
      <div class="ces-badge" :style="getElementGlow('var(--abs-orange)', 0.5)">
        LIVE AI · NO CLOUD · RTX PRO 6000
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
  filter: drop-shadow(0 0 20px var(--abs-orange-glow)) drop-shadow(0 0 40px rgba(249, 115, 22, 0.4));
}

.gpu-ring-arc--inner {
  filter: drop-shadow(0 0 25px var(--abs-orange-glow)) drop-shadow(0 0 50px rgba(249, 115, 22, 0.5)) drop-shadow(0 0 15px var(--abs-orange-glow));
}

.gpu-ring-value {
  position: absolute;
  font-family: var(--font-mono);
  font-size: 10rem;
  font-weight: 700;
  color: var(--abs-orange);
  text-shadow: 
    0 0 30px var(--abs-orange-glow),
    0 0 60px var(--abs-orange-glow),
    0 0 90px rgba(249, 115, 22, 0.5);
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
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.5), 0 0 40px rgba(255, 255, 255, 0.2);
  transition: all 0.3s var(--ease-smooth);
  letter-spacing: 0.02em;
}

.metric-value-medium {
  font-family: var(--font-mono);
  font-size: 3rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.4);
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
    0 0 15px var(--abs-orange-glow),
    0 0 30px rgba(249, 115, 22, 0.6);
  transition: all 0.3s var(--ease-smooth);
  background: rgba(0, 0, 0, 0.3);
  padding: 12px 24px;
  border-radius: 8px;
  border: 1px solid rgba(249, 115, 22, 0.2);
}
</style>

