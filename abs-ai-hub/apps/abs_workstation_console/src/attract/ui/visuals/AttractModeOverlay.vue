<script setup lang="ts">
import { onMounted, onUnmounted, watch, computed, ref } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useAttractModeStore } from '@/stores/attractModeStore'
import { useCESMode } from '@/composables/useCESMode'
import { useWebGPUAttractMode } from '@/composables/useWebGPUAttractMode'
import SceneA from '../scenes/SceneA.vue'
import SceneB from '../scenes/SceneB.vue'
import SceneC from '../scenes/SceneC.vue'
import SceneD from '../scenes/SceneD.vue'
import SceneE from '../scenes/SceneE.vue'

const metricsStore = useMetricsStore()
const attractStore = useAttractModeStore()
const { isCESMode } = useCESMode()
const containerRef = ref<HTMLElement | null>(null)

// Initialize WebGPU visual fabric layer
let webGPU: ReturnType<typeof useWebGPUAttractMode> | null = null

// Scene component mapping
const sceneComponents = {
  A: SceneA,
  B: SceneB,
  C: SceneC,
  D: SceneD,
  E: SceneE
}

const currentSceneComponent = computed(() => sceneComponents[attractStore.currentScene])

// Keyboard controls (hidden for staff)
function handleKeyDown(event: KeyboardEvent) {
  if (!attractStore.isActive) return
  
  switch (event.key) {
    case 'Escape':
      // ESC → Exit Attract Mode
      event.preventDefault()
      attractStore.deactivate()
      break
    case 'ArrowLeft':
      // ← → Previous scene
      event.preventDefault()
      attractStore.previousScene()
      break
    case 'ArrowRight':
      // → → Next scene
      event.preventDefault()
      attractStore.nextScene()
      break
    case 'Enter':
      // Enter → Jump to Guided Tour (exit attract mode and trigger tour)
      event.preventDefault()
      attractStore.deactivate()
      // Trigger guided tour - this would need to be connected to the tour system
      window.dispatchEvent(new CustomEvent('start-guided-tour'))
      break
  }
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
  
  // Set up keyboard controls
  window.addEventListener('keydown', handleKeyDown)
  
  // Initialize WebGPU visual fabric layer (wait for next tick to ensure containerRef is set)
  setTimeout(() => {
    if (containerRef.value) {
      try {
        webGPU = useWebGPUAttractMode(containerRef.value)
        watch(() => attractStore.isActive, (isActive) => {
          if (webGPU) {
            if (isActive && webGPU.isInitialized.value) {
              webGPU.start()
            } else {
              webGPU.stop()
            }
          }
        }, { immediate: true })
        
        // Log WebGPU status
        if (webGPU.isSupported.value) {
          console.log('[AttractMode] WebGPU visual fabric layer initialized')
        } else {
          console.warn('[AttractMode] WebGPU not supported:', webGPU.error.value)
        }
      } catch (err) {
        console.error('[AttractMode] Failed to initialize WebGPU:', err)
      }
    }
  }, 100)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div ref="containerRef" class="attract-overlay">
    <!-- Scene-based content -->
    <Transition name="scene-fade" mode="out-in">
      <component
        v-if="!attractStore.isPaused"
        :is="currentSceneComponent"
        :key="attractStore.currentScene"
      />
    </Transition>
    
    <!-- GPU Throttle indicator -->
    <div v-if="attractStore.shouldThrottle" class="throttle-indicator">
      <span class="throttle-text">GPU in use by workload</span>
    </div>
    
    <!-- Exit hint (subtle, bottom center) -->
    <div class="exit-hint">
      <span class="exit-text">Move mouse or press any key to exit</span>
    </div>
    
    <!-- Easter Egg Power Flex Overlay -->
    <Transition name="easter-egg-fade">
      <div v-if="attractStore.easterEggActive" class="easter-egg-overlay">
        <div class="easter-egg-text">LIVE MODEL TEST RUN</div>
      </div>
    </Transition>
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

.throttle-indicator {
  position: absolute;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  background: rgba(249, 115, 22, 0.2);
  border: 1px solid rgba(249, 115, 22, 0.4);
  border-radius: 6px;
  z-index: 100;
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
  z-index: 100;
}

.exit-text {
  font-family: var(--font-label);
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
  opacity: 0.7;
}

/* Scene transition */
.scene-fade-enter-active,
.scene-fade-leave-active {
  transition: opacity 800ms var(--ease-smooth);
}

.scene-fade-enter-from,
.scene-fade-leave-to {
  opacity: 0;
}

/* Easter Egg Power Flex */
.easter-egg-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 200;
  pointer-events: none;
}

.easter-egg-text {
  font-family: var(--font-label);
  font-size: 4.5rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--abs-orange);
  text-shadow: 0 0 60px var(--abs-orange-glow), 0 0 30px var(--abs-orange-glow);
  filter: drop-shadow(0 0 40px var(--abs-orange-glow));
  animation: easter-egg-pulse 0.5s ease-in-out;
}

@keyframes easter-egg-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.9;
  }
}

.easter-egg-fade-enter-active,
.easter-egg-fade-leave-active {
  transition: opacity 0.5s var(--ease-smooth);
}

.easter-egg-fade-enter-from,
.easter-egg-fade-leave-to {
  opacity: 0;
}
</style>

