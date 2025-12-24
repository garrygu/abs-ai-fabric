<script setup lang="ts">
import { computed } from 'vue'
import { useAllInOneDemoStore } from '@/stores/allInOneDemoStore'

const demoStore = useAllInOneDemoStore()

// Step messages that explain what each step demonstrates
// Keyed by step index (0-based) to handle duplicate page names
const stepMessages: Record<number, { title: string; message: string }> = {
  0: { // Overview
    title: 'Identity',
    message: 'This is a single AI workstation — running enterprise-grade AI entirely locally. Not a dev box.'
  },
  1: { // Performance (first time)
    title: 'Power Without Waste',
    message: 'Nothing heavy is running. Power is reserved until it\'s actually needed. This AI workstation is disciplined, not brute-force.'
  },
  2: { // Orchestration
    title: 'Intelligence',
    message: 'Users have full control over which models and tools to use. Switch effortlessly between DeepSeek R1 for reasoning or LLaMA-3 for language tasks. This AI workstation gives you the power to choose.'
  },
  3: { // Models
    title: 'Proof of All-In-One',
    message: 'Users can install models locally or remove them easily. Every model runs on this workstation. No APIs. No cloud accounts. No external dependencies. This AI workstation replaces an entire AI stack.'
  },
  4: { // Performance (second time - closing)
    title: 'Close the Loop',
    message: 'That\'s an all-in-one AI workstation — not just hardware. GPU drops back to idle. Assets sleeping. Ready for the next task.'
  }
}

const currentStepInfo = computed(() => {
  if (!demoStore.isActive) return null
  const stepIndex = demoStore.currentStep
  const baseInfo = stepMessages[stepIndex]
  if (!baseInfo) return null
  
  const stepNumber = stepIndex + 1
  const totalSteps = demoStore.demoSequence.length
  
  return {
    title: `Step ${stepNumber} of ${totalSteps}: ${baseInfo.title}`,
    message: baseInfo.message
  }
})

const progress = computed(() => {
  if (!demoStore.isActive) return 0
  const currentStep = demoStore.currentStep
  const totalSteps = demoStore.demoSequence.length
  return ((currentStep + 1) / totalSteps) * 100
})

const currentStepNumber = computed(() => {
  if (!demoStore.isActive) return 0
  return demoStore.currentStep + 1
})

const totalSteps = computed(() => {
  return demoStore.demoSequence.length
})
</script>

<template>
  <Transition name="fade">
    <div v-if="demoStore.isActive && currentStepInfo" class="demo-overlay">
      <!-- Progress Bar -->
      <div class="demo-progress-container">
        <div class="demo-progress-bar">
          <div class="demo-progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <div class="demo-progress-text">
          Step {{ currentStepNumber }} of {{ totalSteps }}
        </div>
      </div>
      
      <!-- Step Message -->
      <div class="demo-message">
        <div class="demo-message-title">{{ currentStepInfo.title }}</div>
        <div class="demo-message-text">{{ currentStepInfo.message }}</div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.demo-overlay {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 200;
  pointer-events: none;
  max-width: 800px;
  width: calc(100% - 48px);
}

.demo-progress-container {
  margin-bottom: 16px;
  text-align: center;
}

.demo-progress-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.demo-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--abs-orange), #ff9f43);
  border-radius: 2px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(249, 115, 22, 0.5);
}

.demo-progress-text {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.demo-message {
  padding: 20px 28px;
  background: rgba(0, 0, 0, 0.9);
  border: 1px solid var(--abs-orange);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  box-shadow: 0 0 40px rgba(249, 115, 22, 0.3), 0 4px 20px rgba(0, 0, 0, 0.5);
}

.demo-message-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--abs-orange);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.demo-message-text {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--text-primary);
  line-height: 1.6;
  font-style: italic;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
</style>

