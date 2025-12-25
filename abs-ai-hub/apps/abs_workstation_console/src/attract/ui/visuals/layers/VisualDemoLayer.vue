<script setup lang="ts">
/**
 * VisualDemoLayer.vue
 * 
 * ⚠️ DEMO-ONLY / FALLBACK PATH ⚠️
 * 
 * This component provides a simple Canvas 2D-based visualization layer
 * for demo/interactive pages. It is NOT used by the primary CES Attract Mode.
 * 
 * PRIMARY CES PATH:
 * - WebGPU-based scenes (SceneA-E) via AttractModeOverlay
 * - High-performance particle field with bloom effects
 * - Real-time telemetry-driven visuals
 * 
 * THIS COMPONENT:
 * - Canvas 2D fallback (150 particles max)
 * - Used only for demo/interactive pages
 * - Safe fallback if WebGPU unavailable
 * 
 * DO NOT USE IN SCENEA-E:
 * SceneA-E scenes use WebGPU directly and should never depend on
 * SystemVisualization2D or this layer component.
 */

import { ref, onMounted, onUnmounted, watch } from 'vue'
import SystemVisualization2D from '../visualizations/SystemVisualization2D.vue'

const props = defineProps<{
  /**
   * Visualization type for demo/fallback path
   * - 'system2d': Canvas 2D fallback visualization (SystemVisualization2D)
   * - 'image': Image generation placeholder (future)
   * - 'llm': LLM thought stream placeholder (future)
   */
  visualType: 'system2d' | 'image' | 'llm'
  /**
   * Visual quality mode for demo/fallback path
   * - 'lite': Reduced particle count, simpler effects (for low-end machines)
   * - 'pro': Full Canvas 2D effects (still fallback, but best quality)
   * 
   * Note: This only affects the Canvas 2D fallback path.
   * WebGPU scenes (SceneA-E) have their own quality controls.
   */
  demoVisualQuality?: 'lite' | 'pro'
}>()

// Default to 'pro' for demo pages, but can be forced to 'lite' for low-end machines
const visualQuality = props.demoVisualQuality || 'pro'
</script>

<template>
  <div class="visual-demo-layer">
    <!-- 
      System Visualization (Canvas 2D Fallback)
      ⚠️ This is the fallback path - WebGPU scenes (SceneA-E) do NOT use this component
    -->
    <SystemVisualization2D 
      v-if="visualType === 'system2d'" 
      :quality="visualQuality"
    />
    
    <!-- Placeholder for future Image Generation -->
    <div v-else-if="visualType === 'image'" class="visual-placeholder">
      <p class="placeholder-text">Image Generation</p>
      <p class="placeholder-sub">SDXL integration coming soon</p>
    </div>
    
    <!-- Placeholder for future LLM Stream -->
    <div v-else-if="visualType === 'llm'" class="visual-placeholder">
      <p class="placeholder-text">LLM Thought Stream</p>
      <p class="placeholder-sub">Coming soon</p>
    </div>
  </div>
</template>

<style scoped>
.visual-demo-layer {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-placeholder {
  text-align: center;
  padding: 40px;
}

.placeholder-text {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
}

.placeholder-sub {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
}
</style>

