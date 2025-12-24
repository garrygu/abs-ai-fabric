<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useModelsStore } from '@/stores/modelsStore'
import { useWorkloadsStore } from '@/stores/workloadsStore'
import { useDemoControlStore } from '@/stores/demoControlStore'

const modelsStore = useModelsStore()
const workloadsStore = useWorkloadsStore()
const demoControl = useDemoControlStore()

// Update flow animation based on demo control state
watch(() => demoControl.modelStatus, (status) => {
  if (status === 'warming') {
    // Highlight "Warming" step
    flowStep.value = 2 // Model Selection
  } else if (status === 'running') {
    // Highlight active model
    if (demoControl.activeModel === 'deepseek-r1-70b') {
      flowStep.value = 3 // DeepSeek
    } else if (demoControl.activeModel === 'llama3-70b') {
      flowStep.value = 4 // LLaMA-3
    } else if (demoControl.activeModel === 'dual') {
      // Alternate between both models
      flowStep.value = 3
    }
  } else {
    // Reset to beginning
    flowStep.value = 0
  }
})

// Detect the two 70B models
const deepseekModel = computed(() => 
  modelsStore.models.find(m => 
    m.model_id.toLowerCase().includes('deepseek') && 
    (m.model_id.toLowerCase().includes('70b') || m.model_id.toLowerCase().includes('r1'))
  )
)

const llamaModel = computed(() => 
  modelsStore.models.find(m => 
    m.model_id.toLowerCase().includes('llama') && 
    m.model_id.toLowerCase().includes('70b') &&
    !m.model_id.toLowerCase().includes('8b')
  )
)

// Deep dive section state
const isDeepDiveExpanded = ref(false)

// Live orchestration flow animation state
const flowStep = ref(0)
const flowSteps = [
  'User Task',
  'Task Classification',
  'Model Selection',
  'DeepSeek R1 70B',
  'LLaMA-3 70B',
  'Output'
]

// Animate flow (subtle, restrained)
let flowInterval: ReturnType<typeof setInterval> | null = null

function startFlowAnimation() {
  if (flowInterval) clearInterval(flowInterval)
  flowStep.value = 0
  flowInterval = setInterval(() => {
    flowStep.value = (flowStep.value + 1) % flowSteps.length
  }, 3000) // 3 seconds per step
}

function stopFlowAnimation() {
  if (flowInterval) {
    clearInterval(flowInterval)
    flowInterval = null
  }
}

// Start animation on mount, stop on unmount
onMounted(() => {
  startFlowAnimation()
})
onUnmounted(() => {
  stopFlowAnimation()
})
</script>

<template>
  <div class="page page-orchestration">
    <!-- ① ORCHESTRATION HERO -->
    <div class="orchestration-hero">
      <h1 class="hero-title">MODEL ORCHESTRATION</h1>
      <p class="hero-subtitle">How the workstation selects and activates intelligence</p>
      
      <div class="hero-statement">
        <div class="statement-main">Multiple 70B Models.</div>
        <div class="statement-main">One Intelligent System.</div>
      </div>
      
      <p class="hero-supporting">
        Models are activated on demand, not left running.
      </p>
    </div>

    <!-- ② DUAL 70B MODELS — ROLES -->
    <div class="dual-models-section">
      <div class="models-container">
        <!-- DeepSeek R1 70B -->
        <div class="model-card model-card--deepseek">
          <div class="model-header">
            <div class="model-icon">🧠</div>
            <div class="model-name">{{ deepseekModel?.display_name || 'DeepSeek R1 70B' }}</div>
          </div>
          
          <div class="model-role">
            <span class="role-label">Role:</span>
            <span class="role-value">Reasoning / Analysis</span>
          </div>
          
          <div class="model-activations">
            <div class="activation-title">Activated for:</div>
            <ul class="activation-list">
              <li>Conflicting constraints</li>
              <li>Long-form judgment</li>
              <li>Risk analysis</li>
            </ul>
          </div>
        </div>

        <!-- Divider with key line -->
        <div class="models-divider">
          <div class="divider-line"></div>
          <div class="divider-text">Different minds. Same workstation.</div>
          <div class="divider-line"></div>
        </div>

        <!-- LLaMA-3 70B -->
        <div class="model-card model-card--llama">
          <div class="model-header">
            <div class="model-icon">💬</div>
            <div class="model-name">{{ llamaModel?.display_name || 'LLaMA-3 70B' }}</div>
          </div>
          
          <div class="model-role">
            <span class="role-label">Role:</span>
            <span class="role-value">Language / Explanation</span>
          </div>
          
          <div class="model-activations">
            <div class="activation-title">Activated for:</div>
            <ul class="activation-list">
              <li>Natural conversation</li>
              <li>Summaries</li>
              <li>Business communication</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- ③ LIVE ORCHESTRATION FLOW -->
    <div class="orchestration-flow-section">
      <h2 class="flow-title">Live Orchestration Flow</h2>
      
      <div class="flow-diagram">
        <div class="flow-step" :class="{ 'flow-step--active': flowStep === 0 || (demoControl.isActive && demoControl.modelStatus === 'idle') }">
          <div class="step-node">User Task</div>
        </div>
        
        <div class="flow-arrow" :class="{ 'flow-arrow--active': flowStep >= 1 || demoControl.isActive }">↓</div>
        
        <div class="flow-step" :class="{ 'flow-step--active': flowStep === 1 || (demoControl.isWarming && flowStep >= 1) }">
          <div class="step-node">Task Classification</div>
        </div>
        
        <div class="flow-arrow" :class="{ 'flow-arrow--active': flowStep >= 2 || demoControl.isWarming }">↓</div>
        
        <div class="flow-step" :class="{ 'flow-step--active': flowStep === 2 || demoControl.isWarming }">
          <div class="step-node">Model Selection</div>
          <div v-if="demoControl.isWarming" class="loading-indicator">
            {{ demoControl.loadingStage }}
          </div>
        </div>
        
        <div class="flow-branch">
          <div class="flow-path flow-path--deepseek">
            <div class="flow-arrow" :class="{ 'flow-arrow--active': (demoControl.activeModel === 'deepseek-r1-70b' || demoControl.activeModel === 'dual') && (demoControl.isWarming || demoControl.isRunning) }">↓</div>
            <div class="flow-step" :class="{ 
              'flow-step--active': flowStep === 3 || ((demoControl.activeModel === 'deepseek-r1-70b' || demoControl.activeModel === 'dual') && (demoControl.isWarming || demoControl.isRunning)),
              'flow-step--warming': (demoControl.activeModel === 'deepseek-r1-70b' || demoControl.activeModel === 'dual') && demoControl.isWarming,
              'flow-step--running': (demoControl.activeModel === 'deepseek-r1-70b' || demoControl.activeModel === 'dual') && demoControl.isRunning
            }">
              <div class="step-node step-node--model">DeepSeek R1 70B</div>
            </div>
            <div class="flow-arrow" :class="{ 'flow-arrow--active': (demoControl.activeModel === 'deepseek-r1-70b' || demoControl.activeModel === 'dual') && demoControl.isRunning }">→</div>
            <div class="flow-step" :class="{ 'flow-step--active': flowStep === 5 || ((demoControl.activeModel === 'deepseek-r1-70b' || demoControl.activeModel === 'dual') && demoControl.isRunning && demoControl.modelOutput?.reasoned) }">
              <div class="step-node step-node--output">Reasoned Output</div>
            </div>
          </div>
          
          <div class="flow-path flow-path--llama">
            <div class="flow-arrow" :class="{ 'flow-arrow--active': (demoControl.activeModel === 'llama3-70b' || demoControl.activeModel === 'dual') && (demoControl.isWarming || demoControl.isRunning) }">↓</div>
            <div class="flow-step" :class="{ 
              'flow-step--active': flowStep === 4 || ((demoControl.activeModel === 'llama3-70b' || demoControl.activeModel === 'dual') && (demoControl.isWarming || demoControl.isRunning)),
              'flow-step--warming': (demoControl.activeModel === 'llama3-70b' || demoControl.activeModel === 'dual') && demoControl.isWarming,
              'flow-step--running': (demoControl.activeModel === 'llama3-70b' || demoControl.activeModel === 'dual') && demoControl.isRunning
            }">
              <div class="step-node step-node--model">LLaMA-3 70B</div>
            </div>
            <div class="flow-arrow" :class="{ 'flow-arrow--active': (demoControl.activeModel === 'llama3-70b' || demoControl.activeModel === 'dual') && demoControl.isRunning }">→</div>
            <div class="flow-step" :class="{ 'flow-step--active': flowStep === 5 || ((demoControl.activeModel === 'llama3-70b' || demoControl.activeModel === 'dual') && demoControl.isRunning && demoControl.modelOutput?.explained) }">
              <div class="step-node step-node--output">Clear Explanation</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ④ OPTIONAL DEEP DIVE (EXPANDABLE) -->
    <div class="deep-dive-section">
      <button 
        class="deep-dive-toggle"
        @click="isDeepDiveExpanded = !isDeepDiveExpanded"
      >
        <span class="toggle-icon">{{ isDeepDiveExpanded ? '▾' : '▸' }}</span>
        <span class="toggle-text">How model selection works</span>
      </button>
      
      <Transition name="expand">
        <div v-if="isDeepDiveExpanded" class="deep-dive-content">
          <div class="deep-dive-item">
            <h3 class="deep-dive-title">Rule-based routing (for now)</h3>
            <p class="deep-dive-description">
              Task intent is analyzed to determine whether reasoning or language generation is required. 
              DeepSeek R1 is selected for complex reasoning tasks, while LLaMA-3 handles conversational and explanatory needs.
            </p>
          </div>
          
          <div class="deep-dive-item">
            <h3 class="deep-dive-title">Future auto-selection</h3>
            <p class="deep-dive-description">
              Planned enhancement: Machine learning-based model selection that learns from task outcomes 
              to optimize routing decisions automatically.
            </p>
          </div>
          
          <div class="deep-dive-item">
            <h3 class="deep-dive-title">Fallback logic</h3>
            <p class="deep-dive-description">
              If the primary model is unavailable or overloaded, the system automatically routes to the 
              secondary model with appropriate capability adjustments.
            </p>
          </div>
          
          <div class="deep-dive-item">
            <h3 class="deep-dive-title">Safety guarantees</h3>
            <p class="deep-dive-description">
              All model selections are logged and auditable. No model executes without explicit task 
              classification and resource availability checks.
            </p>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.page-orchestration {
  display: flex;
  flex-direction: column;
  gap: 48px;
  padding: 40px 24px;
  max-width: var(--container-max);
  margin: 0 auto;
  min-height: calc(100vh - 120px);
}

/* ① ORCHESTRATION HERO */
.orchestration-hero {
  text-align: center;
  padding: 40px 0;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.hero-subtitle {
  font-family: var(--font-label);
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.hero-statement {
  margin: 32px 0;
}

.statement-main {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--abs-orange);
  line-height: 1.3;
  margin-bottom: 8px;
}

.hero-supporting {
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: var(--text-secondary);
  font-style: italic;
  margin-top: 24px;
}

/* ② DUAL 70B MODELS */
.dual-models-section {
  margin: 32px 0;
}

.models-container {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 32px;
  align-items: center;
  max-width: 1000px;
  margin: 0 auto;
}

.model-card {
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.model-card--deepseek {
  border-left: 3px solid var(--electric-blue);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.1);
}

.model-card--llama {
  border-left: 3px solid var(--abs-orange);
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.1);
}

.model-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-icon {
  font-size: 2rem;
}

.model-name {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.model-role {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
}

.role-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.role-value {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--electric-indigo);
}

.model-activations {
  margin-top: 8px;
}

.activation-title {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.activation-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activation-list li {
  font-family: var(--font-body);
  font-size: 0.875rem;
  color: var(--text-secondary);
  padding-left: 16px;
  position: relative;
}

.activation-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--abs-orange);
  font-weight: 700;
}

.models-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 200px;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, transparent, var(--border-subtle), transparent);
}

.divider-text {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  text-align: center;
}

/* ③ LIVE ORCHESTRATION FLOW */
.orchestration-flow-section {
  margin: 48px 0;
}

.flow-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 40px;
}

.flow-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  max-width: 600px;
  margin: 0 auto;
}

.flow-step {
  opacity: 0.4;
  transition: all 0.5s ease;
}

.flow-step--active {
  opacity: 1;
}

.flow-step--warming {
  opacity: 1;
  animation: pulse-warming 2s ease-in-out infinite;
}

.flow-step--running {
  opacity: 1;
  animation: pulse-running 2s ease-in-out infinite;
}

@keyframes pulse-warming {
  0%, 100% {
    opacity: 0.8;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
}

@keyframes pulse-running {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba(34, 197, 94, 0.5);
  }
}

.loading-indicator {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--abs-orange);
  margin-top: 8px;
  text-align: center;
  font-style: italic;
}

.flow-arrow--active {
  opacity: 1;
  color: var(--abs-orange);
  animation: arrow-pulse 1.5s ease-in-out infinite;
}

@keyframes arrow-pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.step-node {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  padding: 12px 20px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  text-align: center;
  min-width: 150px;
  transition: all 0.5s ease;
}

.flow-step--active .step-node {
  background: linear-gradient(135deg, var(--abs-card), var(--abs-elevated));
  border-color: var(--abs-orange);
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.2);
  transform: scale(1.05);
}

.step-node--model {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
  border-color: var(--electric-indigo);
}

.step-node--output {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));
  border-color: var(--status-success);
}

.flow-arrow {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  color: var(--text-muted);
  opacity: 0.5;
  transition: all 0.5s ease;
}

.flow-step--active + .flow-arrow,
.flow-arrow + .flow-step--active {
  opacity: 1;
  color: var(--abs-orange);
}

.flow-branch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  width: 100%;
  margin-top: 16px;
}

.flow-path {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.flow-path--deepseek .step-node--model {
  border-color: var(--electric-blue);
}

.flow-path--llama .step-node--model {
  border-color: var(--abs-orange);
}

/* ④ DEEP DIVE */
.deep-dive-section {
  margin-top: 48px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.deep-dive-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  text-align: left;
}

.deep-dive-toggle:hover {
  background: var(--abs-elevated);
  border-color: var(--electric-indigo);
}

.toggle-icon {
  font-size: 1rem;
  color: var(--electric-indigo);
  transition: transform 0.3s ease;
}

.deep-dive-toggle:hover .toggle-icon {
  transform: translateX(4px);
}

.toggle-text {
  flex: 1;
}

.deep-dive-content {
  margin-top: 16px;
  padding: 24px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.deep-dive-item {
  padding-bottom: 24px;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
}

.deep-dive-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.deep-dive-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.deep-dive-description {
  font-family: var(--font-body);
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.expand-enter-to {
  opacity: 1;
  max-height: 1000px;
}

.expand-leave-from {
  opacity: 1;
  max-height: 1000px;
}

.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

@media (max-width: 768px) {
  .models-container {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .models-divider {
    flex-direction: column;
    min-width: auto;
  }
  
  .divider-line {
    width: 100%;
    height: 1px;
  }
  
  .flow-branch {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .hero-title {
    font-size: 2rem;
  }
  
  .statement-main {
    font-size: 1.5rem;
  }
}
</style>

