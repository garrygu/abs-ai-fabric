<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import SystemVisualization from './SystemVisualization.vue'

const props = defineProps<{
  visualType: 'system' | 'image' | 'llm'
}>()
</script>

<template>
  <div class="visual-demo-layer">
    <!-- System Visualization (WebGL/Canvas) -->
    <SystemVisualization v-if="visualType === 'system'" />
    
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
