<script setup lang="ts">
import { computed } from 'vue'
import { useDemoControlStore } from '@/stores/demoControlStore'

const demoControl = useDemoControlStore()

const showOutput = computed(() => {
  return demoControl.isRunning && demoControl.activeModel === 'dual' && demoControl.modelOutput !== null
})
</script>

<template>
  <Transition name="fade">
    <div v-if="showOutput" class="dual-output-display">
      <div class="dual-output-header">
        <div class="output-title">Decide + Explain</div>
        <div class="output-subtitle">Two AI minds working together</div>
      </div>
      
      <div class="dual-output-columns">
        <!-- Left: Reasoned Output (DeepSeek R1) -->
        <div class="output-column output-column--reasoned">
          <div class="output-column-header">
            <div class="output-model-badge output-model-badge--deepseek">
              DeepSeek R1 70B
            </div>
            <div class="output-label">Reasoned Output</div>
          </div>
          <div class="output-content">
            <div v-if="demoControl.modelOutput?.reasoned" class="output-text">
              {{ demoControl.modelOutput.reasoned }}
            </div>
            <div v-else class="output-placeholder">
              Analyzing constraints and generating recommendation...
            </div>
          </div>
        </div>
        
        <!-- Right: Clear Explanation (LLaMA-3) -->
        <div class="output-column output-column--explained">
          <div class="output-column-header">
            <div class="output-model-badge output-model-badge--llama">
              LLaMA-3 70B
            </div>
            <div class="output-label">Executive Explanation</div>
          </div>
          <div class="output-content">
            <div v-if="demoControl.modelOutput?.explained" class="output-text">
              {{ demoControl.modelOutput.explained }}
            </div>
            <div v-else class="output-placeholder">
              Preparing business-friendly explanation...
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.dual-output-display {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 1200px;
  max-height: 80vh;
  padding: 32px;
  background: var(--abs-card);
  border: 1px solid var(--abs-orange);
  border-radius: 16px;
  box-shadow: 0 0 60px rgba(249, 115, 22, 0.4), 0 8px 40px rgba(0, 0, 0, 0.5);
  z-index: 200;
  backdrop-filter: blur(20px);
  overflow-y: auto;
}

.dual-output-header {
  text-align: center;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.output-title {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--abs-orange);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.output-subtitle {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.dual-output-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.output-column {
  padding: 24px;
  background: var(--abs-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
}

.output-column--reasoned {
  border-left: 3px solid var(--electric-blue);
}

.output-column--explained {
  border-left: 3px solid var(--abs-orange);
}

.output-column-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
}

.output-model-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 6px;
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.output-model-badge--deepseek {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--electric-blue);
}

.output-model-badge--llama {
  background: rgba(249, 115, 22, 0.15);
  border: 1px solid rgba(249, 115, 22, 0.3);
  color: var(--abs-orange);
}

.output-label {
  font-family: var(--font-label);
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.output-content {
  flex: 1;
  min-height: 200px;
}

.output-text {
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: var(--text-primary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.output-placeholder {
  font-family: var(--font-body);
  font-size: 0.875rem;
  color: var(--text-muted);
  font-style: italic;
  text-align: center;
  padding: 40px 20px;
  opacity: 0.6;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.95);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
}

@media (max-width: 768px) {
  .dual-output-columns {
    grid-template-columns: 1fr;
  }
}
</style>

