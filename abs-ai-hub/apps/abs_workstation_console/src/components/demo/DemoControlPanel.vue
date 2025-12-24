<script setup lang="ts">
import { computed } from 'vue'
import { useDemoControlStore, type ActiveModel } from '@/stores/demoControlStore'

const demoControl = useDemoControlStore()

function activateModel(model: ActiveModel) {
  demoControl.activateModel(model)
}

function getStatusColor() {
  switch (demoControl.modelStatus) {
    case 'warming':
      return 'var(--abs-orange)'
    case 'running':
      return 'var(--status-success)'
    case 'cooling':
      return 'var(--text-muted)'
    default:
      return 'var(--text-secondary)'
  }
}

const statusLabel = computed(() => {
  switch (demoControl.modelStatus) {
    case 'warming':
      return 'Warming'
    case 'running':
      return 'Running'
    case 'cooling':
      return 'Cooling'
    default:
      return 'Idle'
  }
})

function showPromptKiosk() {
  window.dispatchEvent(new CustomEvent('show-prompt-kiosk'))
}
</script>

<template>
  <div class="demo-control-panel">
    <div class="panel-header">
      <div class="panel-title">DEMO CONTROL</div>
      <div class="status-indicator" :style="{ color: getStatusColor() }">
        <span class="status-dot" :style="{ backgroundColor: getStatusColor() }"></span>
        {{ statusLabel }}
      </div>
    </div>
    
    <div class="panel-actions">
      <button
        class="demo-button"
        :class="{ 
          'demo-button--active': demoControl.activeModel === 'deepseek-r1-70b' && demoControl.isActive,
          'demo-button--pending': demoControl.pendingRequest === 'deepseek-r1-70b'
        }"
        :disabled="demoControl.isActive && demoControl.activeModel !== 'deepseek-r1-70b'"
        @click="activateModel('deepseek-r1-70b')"
      >
        <span v-if="demoControl.pendingRequest === 'deepseek-r1-70b'">⏳ </span>
        Activate DeepSeek R1 70B
      </button>
      
      <button
        class="demo-button"
        :class="{ 
          'demo-button--active': demoControl.activeModel === 'llama3-70b' && demoControl.isActive,
          'demo-button--pending': demoControl.pendingRequest === 'llama3-70b'
        }"
        :disabled="demoControl.isActive && demoControl.activeModel !== 'llama3-70b'"
        @click="activateModel('llama3-70b')"
      >
        <span v-if="demoControl.pendingRequest === 'llama3-70b'">⏳ </span>
        Activate LLaMA-3 70B
      </button>
      
      <button
        class="demo-button demo-button--dual"
        :class="{ 
          'demo-button--active': demoControl.activeModel === 'dual' && demoControl.isActive,
          'demo-button--pending': demoControl.pendingRequest === 'dual'
        }"
        :disabled="demoControl.isActive && demoControl.activeModel !== 'dual'"
        @click="activateModel('dual')"
      >
        <span v-if="demoControl.pendingRequest === 'dual'">⏳ </span>
        Dual 70B Showcase
      </button>
    </div>
    
    <!-- Loading Progress -->
    <div v-if="demoControl.isWarming" class="loading-section">
      <div class="loading-stage">{{ demoControl.loadingStage }}</div>
      <div class="loading-bar">
        <div class="loading-bar-fill" :style="{ width: `${demoControl.loadingProgress}%` }"></div>
      </div>
    </div>
    
    <!-- Loading Duration (when ready, auto-hides after 5s) -->
    <Transition name="fade">
      <div v-if="demoControl.isRunning && demoControl.loadingDuration !== null" class="loading-duration">
        <span class="duration-text">Loaded in {{ demoControl.loadingDuration }}s</span>
      </div>
    </Transition>
    
    <!-- Pending Request Status -->
    <div v-if="demoControl.pendingRequest" class="pending-request-status">
      <div class="pending-message">
        <span class="pending-icon">⏳</span>
        <span>Waiting for current session to end...</span>
      </div>
      <button 
        class="cancel-pending-button"
        @click="demoControl.cancelPendingRequest"
        title="Cancel pending request"
      >
        Cancel
      </button>
    </div>
    
    <!-- Try It Button -->
    <button
      v-if="demoControl.isRunning"
      class="try-it-button"
      @click="showPromptKiosk"
    >
      Try It Yourself
    </button>
    
    <!-- Safety Info -->
    <div class="safety-info">
      Auto-sleep: 2 min after idle
    </div>
    
    <!-- Session Timer -->
    <div v-if="demoControl.timeRemaining !== null && demoControl.timeRemaining > 0" class="session-timer">
      <span class="timer-label">Session ends in:</span>
      <span class="timer-countdown">{{ demoControl.timeRemaining }}s</span>
    </div>
  </div>
</template>

<style scoped>
.demo-control-panel {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 280px;
  padding: 20px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  z-index: 150;
  backdrop-filter: blur(10px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.panel-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.demo-button {
  width: 100%;
  padding: 12px 16px;
  background: var(--abs-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.demo-button:hover:not(:disabled) {
  background: var(--abs-card);
  border-color: var(--electric-indigo);
  transform: translateY(-1px);
}

.demo-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.demo-button--active {
  background: linear-gradient(135deg, var(--abs-orange), #ff9f43);
  border-color: var(--abs-orange);
  color: white;
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.3);
}

.demo-button--pending {
  border-color: var(--abs-orange);
  box-shadow: 0 0 10px rgba(249, 115, 22, 0.2);
  opacity: 0.8;
}

.demo-button--dual {
  background: linear-gradient(135deg, var(--electric-indigo), #6366f1);
  border-color: var(--electric-indigo);
  color: white;
}

.demo-button--dual:hover:not(:disabled) {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border-color: var(--electric-indigo);
}

.loading-section {
  margin-bottom: 12px;
}

.loading-stage {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-align: center;
}

.loading-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.loading-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--abs-orange), #ff9f43);
  border-radius: 2px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(249, 115, 22, 0.5);
}

.loading-duration {
  text-align: center;
  margin-top: 8px;
  font-family: var(--font-label);
  font-size: 0.7rem;
}

.duration-text {
  color: var(--text-muted);
  font-weight: 400;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.pending-request-status {
  margin-bottom: 12px;
  padding: 10px;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.3);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pending-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--abs-orange);
  text-align: center;
}

.pending-icon {
  font-size: 1rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.cancel-pending-button {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s ease;
  align-self: center;
}

.cancel-pending-button:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.safety-info {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-muted);
  text-align: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

.session-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: var(--font-label);
  font-size: 0.7rem;
  text-align: center;
  margin-top: 8px;
  padding: 6px;
  background: rgba(249, 115, 22, 0.05);
  border-radius: 6px;
}

.timer-label {
  color: var(--text-muted);
  font-weight: 400;
}

.timer-countdown {
  font-family: var(--font-mono);
  color: var(--abs-orange);
  font-weight: 600;
  font-size: 0.8rem;
}

.try-it-button {
  width: 100%;
  padding: 14px 16px;
  margin-top: 12px;
  background: linear-gradient(135deg, var(--abs-orange), #ff9f43);
  border: 1px solid var(--abs-orange);
  border-radius: 8px;
  color: white;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.3);
}

.try-it-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(249, 115, 22, 0.5);
}
</style>

