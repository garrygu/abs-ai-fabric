<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useDemoControlStore } from '@/stores/demoControlStore'
import { useBloomEffect } from '@/composables/useBloomEffect'

const metricsStore = useMetricsStore()
const demoControlStore = useDemoControlStore()
const containerRef = ref<HTMLElement | null>(null)
const { getElementGlow } = useBloomEffect()

// WebGPU particle field is rendered globally via AttractModeOverlay
// (removed legacy Canvas 2D fallback)


// GPU utilization animation: 8% → 45% → 72%
const animatedGpuUtil = ref(8)
let animationInterval: ReturnType<typeof setInterval> | null = null
const animationPhase = ref<'idle' | 'surge' | 'peak' | 'locked'>('idle')

// Screen shake (at ~80%)
const screenShake = ref({ x: 0, y: 0 })
let shakeTimer: ReturnType<typeof setTimeout> | null = null

// Lock-in flash (at 100%)
const showFlash = ref(false)

// VRAM counter (counts up in real-time)
const animatedVram = ref(0)
const vramTarget = computed(() => Math.round(metricsStore.vramUsed))

// Cold start time (simulated)
const coldStartTime = ref<number | null>(null)
const elapsedTime = ref(0)

onMounted(() => {
  // Simulate cold start time (randomized between 8-15 seconds)
  coldStartTime.value = Math.floor(Math.random() * 7) + 8
  
  // Start animation sequence
  setTimeout(() => {
    animationPhase.value = 'surge'
    animatedGpuUtil.value = 45
    
    setTimeout(() => {
      animationPhase.value = 'peak'
      animatedGpuUtil.value = 72
      
      // Screen shake at ~80%
      setTimeout(() => {
        triggerScreenShake()
      }, 500)
      
      // Continue to 100%
      setTimeout(() => {
        animatedGpuUtil.value = 100
        animationPhase.value = 'locked'
        triggerLockFlash()
      }, 1500)
    }, 2000)
  }, 1000)
  
  // Elapsed time counter
  const elapsedInterval = setInterval(() => {
    elapsedTime.value += 0.1
    if (elapsedTime.value >= (coldStartTime.value || 12)) {
      clearInterval(elapsedInterval)
    }
  }, 100)
  
  // VRAM counter animation
  const vramInterval = setInterval(() => {
    if (animatedVram.value < vramTarget.value) {
      animatedVram.value = Math.min(animatedVram.value + 0.5, vramTarget.value)
    }
  }, 50)
  
  // Subtle ongoing animation
  animationInterval = setInterval(() => {
    if (animationPhase.value === 'locked') {
      // Slight variation around peak
      animatedGpuUtil.value = 100 + (Math.random() * 2 - 1)
    }
  }, 500)
  
  return () => {
    clearInterval(elapsedInterval)
    clearInterval(vramInterval)
  }
})

function triggerScreenShake() {
  const shakeDuration = 300
  const shakeIntensity = 2
  let elapsed = 0
  
  const shake = () => {
    if (elapsed < shakeDuration) {
      screenShake.value = {
        x: (Math.random() - 0.5) * shakeIntensity,
        y: (Math.random() - 0.5) * shakeIntensity
      }
      elapsed += 16
      shakeTimer = setTimeout(shake, 16)
    } else {
      screenShake.value = { x: 0, y: 0 }
    }
  }
  shake()
}

function triggerLockFlash() {
  showFlash.value = true
  setTimeout(() => {
    showFlash.value = false
  }, 200)
}

onUnmounted(() => {
  if (animationInterval) {
    clearInterval(animationInterval)
    animationInterval = null
  }
  if (shakeTimer) {
    clearTimeout(shakeTimer)
    shakeTimer = null
  }
})

const displayGpuUtil = computed(() => Math.round(animatedGpuUtil.value))
const displayVramLocked = computed(() => {
  if (animationPhase.value === 'locked' || animationPhase.value === 'peak') {
    return `${Math.round(animatedVram.value)} / ${Math.round(metricsStore.vramTotal)} GB`
  }
  return null
})

const displayElapsedTime = computed(() => {
  return elapsedTime.value.toFixed(1)
})

// Container transform for screen shake
const containerTransform = computed(() => {
  return `translate(${screenShake.value.x}px, ${screenShake.value.y}px)`
})
</script>

<template>
  <div ref="containerRef" class="scene-c" :style="{ transform: containerTransform }">
    <!-- GPU Particle Field Background (collapses inward) -->
    <!-- Particle field is rendered via composable -->
    
    <!-- Lock-in flash overlay -->
    <Transition name="flash">
      <div v-if="showFlash" class="flash-overlay"></div>
    </Transition>
    
    <!-- GPU utilization visualization (multi-layer) -->
    <div class="scene-c__gpu-visual">
      <!-- Progress bar layer -->
      <div class="gpu-bar-container">
        <div 
          class="gpu-bar"
          :style="{ width: `${displayGpuUtil}%` }"
        >
          <div class="gpu-bar__glow"></div>
          <div class="gpu-bar__particles"></div>
        </div>
      </div>
      
      <!-- GPU ring (accelerates) -->
      <div class="gpu-ring-wrapper">
        <svg class="gpu-ring-svg" width="350" height="350" viewBox="0 0 200 200">
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            stroke-width="4"
          />
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="var(--abs-orange)"
            stroke-width="4"
            stroke-linecap="round"
            :stroke-dasharray="502"
            :stroke-dashoffset="502 * (1 - displayGpuUtil / 100)"
            transform="rotate(-90 100 100)"
            class="gpu-ring-arc"
            :style="getElementGlow('var(--abs-orange)', 1)"
          />
        </svg>
      </div>
      
      <!-- GPU value (with bloom) -->
      <div class="gpu-value" :style="getElementGlow('var(--abs-orange)', 1.5)">
        {{ displayGpuUtil }}%
      </div>
    </div>
    
    <!-- Overlay text (big, minimal) -->
    <div class="scene-c__overlay-text">
      <div class="overlay-line overlay-line--primary" :style="getElementGlow('var(--text-primary)', 0.3)">
        SPINNING UP 70B MODEL
      </div>
      <div class="overlay-line overlay-line--secondary">
        COLD START · {{ displayElapsedTime }}s
      </div>
      <div v-if="displayVramLocked" class="overlay-line overlay-line--tertiary">
        VRAM LOCKED · NO SWAPPING
      </div>
      <div v-if="animationPhase === 'locked'" class="overlay-line overlay-line--success">
        FULLY LOCAL
      </div>
    </div>
  </div>
</template>

<style scoped>
.scene-c {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--abs-black);
  gap: 60px;
  overflow: hidden;
  transition: transform 0.05s linear;
}

.flash-overlay {
  position: absolute;
  inset: 0;
  background: rgba(249, 115, 22, 0.3);
  z-index: 100;
  pointer-events: none;
}

.flash-enter-active,
.flash-leave-active {
  transition: opacity 0.2s ease-out;
}

.flash-enter-from,
.flash-leave-to {
  opacity: 0;
}

.scene-c__gpu-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  width: 80%;
  max-width: 800px;
  position: relative;
}

.gpu-bar-container {
  width: 100%;
  height: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.gpu-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--abs-orange), #ff8c42, #ffaa66);
  border-radius: 8px;
  transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.gpu-bar__glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 1.5s ease-in-out infinite;
}

.gpu-bar__particles {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--x, 50%), rgba(255, 255, 255, 0.3) 0%, transparent 50%);
  animation: particle-flow 2s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes particle-flow {
  0% {
    --x: 0%;
  }
  100% {
    --x: 100%;
  }
}

.gpu-ring-wrapper {
  position: relative;
  animation: ring-rotate 3s linear infinite;
  filter: drop-shadow(0 0 20px rgba(249, 115, 22, 0.5));
}

@keyframes ring-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.gpu-ring-svg {
  transition: filter 0.3s var(--ease-smooth);
}

.gpu-ring-arc {
  transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.gpu-value {
  font-family: var(--font-mono);
  font-size: 9rem;
  font-weight: 600;
  color: var(--abs-orange);
  transition: all 0.3s var(--ease-smooth);
}

.scene-c__overlay-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.overlay-line {
  font-family: var(--font-label);
  font-weight: 600;
  text-align: center;
  animation: fade-in-up 0.6s var(--ease-smooth);
}

.overlay-line--primary {
  font-size: 5rem;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  animation-delay: 0.2s;
  animation-fill-mode: both;
}

.overlay-line--secondary {
  font-size: 3rem;
  color: var(--text-secondary);
  animation-delay: 0.4s;
  animation-fill-mode: both;
}

.overlay-line--tertiary {
  font-size: 2rem;
  color: var(--text-muted);
  animation-delay: 0.8s;
  animation-fill-mode: both;
}

.overlay-line--success {
  font-size: 2.5rem;
  color: var(--abs-orange);
  animation-delay: 1.2s;
  animation-fill-mode: both;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

