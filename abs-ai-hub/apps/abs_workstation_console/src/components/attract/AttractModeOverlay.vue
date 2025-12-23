<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useAttractModeStore } from '@/stores/attractModeStore'
import { useCESMode } from '@/composables/useCESMode'
import MetricsLayer from './MetricsLayer.vue'
import VisualDemoLayer from './VisualDemoLayer.vue'
import BrandingLayer from './BrandingLayer.vue'

const metricsStore = useMetricsStore()
const attractStore = useAttractModeStore()
const { isCESMode, cesOverlayText } = useCESMode()

// Visual scheduler
let visualInterval: ReturnType<typeof setInterval> | null = null
const visuals: Array<'system' | 'image' | 'llm'> = ['system'] // Only system for now

function cycleVisual() {
  const currentIndex = visuals.indexOf(attractStore.currentVisual)
  const nextIndex = (currentIndex + 1) % visuals.length
  attractStore.setVisual(visuals[nextIndex])
}

// Watch for GPU budget and throttle visuals
watch(() => attractStore.shouldPause, (shouldPause) => {
  if (shouldPause) {
    attractStore.isPaused = true
    console.log('[AttractMode] Paused due to GPU hard cap')
  } else if (attractStore.isPaused) {
    attractStore.isPaused = false
    console.log('[AttractMode] Resumed')
  }
})

onMounted(() => {
  // Ensure metrics are polling
  metricsStore.startPolling(2000)
  
  // Start visual rotation every 45 seconds
  visualInterval = setInterval(cycleVisual, 45000)
})

onUnmounted(() => {
  if (visualInterval) {
    clearInterval(visualInterval)
    visualInterval = null
  }
})
</script>

<template>
  <div class="attract-overlay">
    <!-- Layer A: Live System Metrics (Always On) -->
    <div class="attract-overlay__metrics">
      <MetricsLayer />
    </div>
    
    <!-- Layer B: AI Visual Demo (Center Stage) -->
    <div class="attract-overlay__visual">
      <Transition name="fade-slow" mode="out-in">
        <VisualDemoLayer 
          v-if="!attractStore.isPaused"
          :key="attractStore.currentVisual"
          :visual-type="attractStore.currentVisual"
        />
      </Transition>
      
      <!-- GPU Throttle indicator -->
      <div v-if="attractStore.shouldThrottle" class="throttle-indicator">
        <span class="throttle-text">GPU in use by workload</span>
      </div>
    </div>
    
    <!-- Layer C: Branding & Messaging -->
    <div class="attract-overlay__branding">
      <BrandingLayer />
    </div>
    
    <!-- CES Mode Overlay Text -->
    <div v-if="isCESMode && cesOverlayText" class="ces-overlay">
      <span class="ces-overlay-text">{{ cesOverlayText }}</span>
    </div>
    
    <!-- Exit hint -->
    <div class="exit-hint">
      <span class="exit-text">Move mouse or press any key to exit</span>
    </div>
  </div>
</template>

<style scoped>
.attract-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: var(--abs-black);
  overflow: hidden;
}

.attract-overlay__metrics {
  position: absolute;
  top: 40px;
  left: 40px;
  z-index: 10;
}

.attract-overlay__visual {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attract-overlay__branding {
  position: absolute;
  bottom: 40px;
  right: 40px;
  z-index: 10;
}

.ces-overlay {
  position: absolute;
  top: 40px;
  right: 40px;
  z-index: 10;
}

.throttle-indicator {
  position: absolute;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  background: rgba(249, 115, 22, 0.2);
  border: 1px solid rgba(249, 115, 22, 0.4);
  border-radius: 6px;
}

.throttle-text {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--abs-orange);
}

.exit-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.exit-text {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  opacity: 0.5;
}

/* Slow fade for visual transitions */
.fade-slow-enter-active,
.fade-slow-leave-active {
  transition: opacity 600ms var(--ease-smooth);
}

.fade-slow-enter-from,
.fade-slow-leave-to {
  opacity: 0;
}
</style>
