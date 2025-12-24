<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useModelsStore } from '@/stores/modelsStore'
import { useWorkloadsStore } from '@/stores/workloadsStore'
import { useCESMode } from '@/composables/useCESMode'
import { useAttractModeStore } from '@/stores/attractModeStore'
import { useDemoControlStore } from '@/stores/demoControlStore'

const modelsStore = useModelsStore()
const workloadsStore = useWorkloadsStore()
const demoControl = useDemoControlStore()
const { isCESMode } = useCESMode()
const attractStore = useAttractModeStore()

// Get model loading status from demo control
function getModelLoadingStatus(modelId: string) {
  if (!demoControl.activeModel || demoControl.modelStatus === 'idle') {
    return null
  }
  
  const modelIdLower = modelId.toLowerCase()
  const normalizedModelId = modelIdLower.replace(/[:_]/g, '-') // Normalize colons and underscores to dashes
  
  // Check DeepSeek R1 70B
  if (demoControl.activeModel === 'deepseek-r1-70b') {
    if (normalizedModelId.includes('deepseek') && (normalizedModelId.includes('r1') || normalizedModelId.includes('70b'))) {
      // If processing, show as running
      if (demoControl.isProcessing && demoControl.modelStatus === 'running') {
        return 'running'
      }
      return demoControl.modelStatus
    }
  }
  
  // Check LLaMA-3 70B (not 8B)
  if (demoControl.activeModel === 'llama3-70b') {
    if (normalizedModelId.includes('llama') && normalizedModelId.includes('70b') && !normalizedModelId.includes('8b')) {
      // If processing, show as running
      if (demoControl.isProcessing && demoControl.modelStatus === 'running') {
        return 'running'
      }
      return demoControl.modelStatus
    }
  }
  
  // Check dual mode
  if (demoControl.activeModel === 'dual') {
    if (normalizedModelId.includes('deepseek') && (normalizedModelId.includes('r1') || normalizedModelId.includes('70b'))) {
      // If processing, show as running
      if (demoControl.isProcessing && demoControl.modelStatus === 'running') {
        return 'running'
      }
      return demoControl.modelStatus
    }
    if (normalizedModelId.includes('llama') && normalizedModelId.includes('70b') && !normalizedModelId.includes('8b')) {
      // If processing, show as running
      if (demoControl.isProcessing && demoControl.modelStatus === 'running') {
        return 'running'
      }
      return demoControl.modelStatus
    }
  }
  
  return null
}

function getModelStatusLabel(modelId: string) {
  const status = getModelLoadingStatus(modelId)
  if (status === 'warming') return 'Warming'
  if (status === 'running') return 'Running'
  if (status === 'cooling') return 'Cooling'
  return null
}

// Check if a model is currently active (for processing status)
function isModelActive(modelId: string): boolean {
  if (!demoControl.activeModel) return false
  
  const modelIdLower = modelId.toLowerCase()
  const normalizedModelId = modelIdLower.replace(/[:_]/g, '-')
  
  if (demoControl.activeModel === 'deepseek-r1-70b') {
    return normalizedModelId.includes('deepseek') && (normalizedModelId.includes('r1') || normalizedModelId.includes('70b'))
  }
  
  if (demoControl.activeModel === 'llama3-70b') {
    return normalizedModelId.includes('llama') && normalizedModelId.includes('70b') && !normalizedModelId.includes('8b')
  }
  
  if (demoControl.activeModel === 'dual') {
    return (normalizedModelId.includes('deepseek') && (normalizedModelId.includes('r1') || normalizedModelId.includes('70b'))) ||
           (normalizedModelId.includes('llama') && normalizedModelId.includes('70b') && !normalizedModelId.includes('8b'))
  }
  
  return false
}

// Auto Highlight Tour state (CES-only)
const highlightedCardId = ref<string | null>(null)
const tourCaption = ref<string>('')
const isTourActive = ref(false)
const captionPosition = ref({ top: '0px', left: '0px', transform: 'translate(-50%, -100%)' })
let idleTimer: ReturnType<typeof setTimeout> | null = null
let tourInterval: ReturnType<typeof setInterval> | null = null
const lastActivityTime = ref(Date.now())
const IDLE_THRESHOLD_MS = 7000 // 7 seconds
const TOUR_CYCLE_MS = 7000 // 7 seconds per card

// Model captions for tour (narrative, one sentence max)
const modelCaptions: Record<string, string> = {
  // LLM models
  'llama3:8b': 'Primary inference model powering live contract analysis and document processing.',
  'llama4:scout': 'Latest generation LLM optimized for enterprise workloads and local deployment.',
  'llama3:70b': 'Large-scale language model enabling advanced reasoning and complex task completion.',
  // Embedding models
  'bge-small-en-v1.5': 'Embedding model enabling fast local RAG and semantic search capabilities.',
  'all-minilm-l6-v2': 'Lightweight embedding model optimized for high-throughput document indexing.',
  'legal-bert': 'Domain-specific embedding model fine-tuned for legal document understanding.',
  'nomic-embed-text': 'General-purpose embedding model for cross-domain semantic search.',
  // System runtime
  'ollama': 'System runtime managing local LLM execution and model lifecycle.'
}

// Hero models (highlighted for CES) - Feature the 2 70B models
const heroModelIds = computed(() => {
  const heroIds: string[] = []
  
  // Find DeepSeek R1 70B
  const deepseek = modelsStore.models.find(m => 
    m.model_id.toLowerCase().includes('deepseek') && 
    (m.model_id.toLowerCase().includes('70b') || m.model_id.toLowerCase().includes('r1'))
  )
  if (deepseek) {
    heroIds.push(deepseek.model_id)
  }
  
  // Find LLaMA-3 70B (not 8B)
  const llama70b = modelsStore.models.find(m => 
    m.model_id.toLowerCase().includes('llama') && 
    m.model_id.toLowerCase().includes('70b') &&
    !m.model_id.toLowerCase().includes('8b')
  )
  if (llama70b) {
    heroIds.push(llama70b.model_id)
  }
  
  return heroIds
})

// Model role badges
function getModelRole(model: any): string {
  if (model.type === 'llm') {
    return 'Inference'
  } else if (model.type === 'embedding') {
    return 'RAG'
  } else if (model.type === 'image') {
    return 'Vision'
  } else if (model.model_id.toLowerCase().includes('ollama')) {
    return 'System Runtime'
  }
  return 'Inference' // Default
}

function getRoleBadgeColor(role: string): string {
  const colors: Record<string, string> = {
    'Inference': 'rgba(99, 102, 241, 0.15)',
    'RAG': 'rgba(34, 197, 94, 0.15)',
    'Embeddings': 'rgba(34, 197, 94, 0.15)',
    'Vision': 'rgba(251, 146, 60, 0.15)',
    'System Runtime': 'rgba(139, 92, 246, 0.15)'
  }
  return colors[role] || colors['Inference']
}

function getRoleBadgeBorderColor(role: string): string {
  const colors: Record<string, string> = {
    'Inference': 'rgba(99, 102, 241, 0.3)',
    'RAG': 'rgba(34, 197, 94, 0.3)',
    'Embeddings': 'rgba(34, 197, 94, 0.3)',
    'Vision': 'rgba(251, 146, 60, 0.3)',
    'System Runtime': 'rgba(139, 92, 246, 0.3)'
  }
  return colors[role] || colors['Inference']
}

// "Used By" mapping: which apps use which models
const modelUsageMap = computed(() => {
  const usage: Record<string, string[]> = {}
  
  workloadsStore.workloads.forEach(workload => {
    if (workload.associated_models && workload.associated_models.length > 0) {
      workload.associated_models.forEach(modelName => {
        // Match model name to model_id (fuzzy matching)
        const matchedModel = modelsStore.models.find(m => {
          const modelIdLower = m.model_id.toLowerCase()
          const modelNameLower = modelName.toLowerCase()
          const displayNameLower = m.display_name.toLowerCase()
          return modelIdLower.includes(modelNameLower) || 
                 modelNameLower.includes(modelIdLower) ||
                 displayNameLower.includes(modelNameLower) ||
                 modelNameLower.includes(displayNameLower)
        })
        
        if (matchedModel) {
          if (!usage[matchedModel.model_id]) {
            usage[matchedModel.model_id] = []
          }
          if (!usage[matchedModel.model_id].includes(workload.app_name)) {
            usage[matchedModel.model_id].push(workload.app_name)
          }
        }
      })
    }
  })
  
  return usage
})

// Sorted models: hero models first, then by type and status
const sortedModels = computed(() => {
  const models = [...modelsStore.models]
  
  // Sort: hero models first, then ready models, then by type
  return models.sort((a, b) => {
    const aIsHero = heroModelIds.value.includes(a.model_id)
    const bIsHero = heroModelIds.value.includes(b.model_id)
    
    if (aIsHero && !bIsHero) return -1
    if (!aIsHero && bIsHero) return 1
    
    const aIsReady = a.serving_status === 'ready'
    const bIsReady = b.serving_status === 'ready'
    if (aIsReady && !bIsReady) return -1
    if (!aIsReady && bIsReady) return 1
    
    // Then by type: llm, embedding, image
    const typeOrder: Record<string, number> = { 'llm': 0, 'embedding': 1, 'image': 2 }
    return (typeOrder[a.type] || 99) - (typeOrder[b.type] || 99)
  })
})

function getModelIcon(type: string): string {
  const icons: Record<string, string> = {
    'llm': '🧠',
    'embedding': '🔗',
    'image': '🖼️'
  }
  return icons[type] || '📦'
}

function getModelTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'llm': 'Large Language Model',
    'embedding': 'Embedding Model',
    'image': 'Image Generation'
  }
  return labels[type] || type
}

// Auto Highlight Tour functions
function getCardCaption(modelId: string): string {
  return modelCaptions[modelId] || 
         modelCaptions[modelId.toLowerCase()] ||
         'Enterprise-validated AI model running 100% locally on this workstation.'
}

function recordActivity() {
  lastActivityTime.value = Date.now()
  if (isTourActive.value) {
    stopTour()
  }
  if (idleTimer) {
    clearTimeout(idleTimer)
  }
  idleTimer = setTimeout(checkIdle, IDLE_THRESHOLD_MS)
}

function checkIdle() {
  if (attractStore.isActive) {
    stopTour()
    return
  }
  
  if (!isCESMode.value) {
    return
  }
  
  const idleTime = Date.now() - lastActivityTime.value
  const shouldStart = idleTime >= IDLE_THRESHOLD_MS && 
                      !isTourActive.value &&
                      !attractStore.isActive &&
                      sortedModels.value.length > 0
  
  if (shouldStart) {
    startTour()
  }
}

function startTour() {
  if (isTourActive.value || sortedModels.value.length === 0) {
    return
  }
  
  isTourActive.value = true
  highlightedCardId.value = null
  tourCaption.value = ''
  
  let currentIndex = 0
  
  function highlightNext() {
    if (!isTourActive.value || attractStore.isActive) {
      stopTour()
      return
    }
    
    highlightedCardId.value = null
    tourCaption.value = ''
    
    setTimeout(() => {
      if (!isTourActive.value || attractStore.isActive) {
        stopTour()
        return
      }
      
      if (currentIndex >= sortedModels.value.length) {
        currentIndex = 0
      }
      
      const model = sortedModels.value[currentIndex]
      highlightedCardId.value = model.model_id
      tourCaption.value = getCardCaption(model.model_id)
      
      // Position caption above card (with scroll and smart positioning)
      updateCaptionPosition(model.model_id)
      
      currentIndex++
    }, 300)
  }
  
  // Start immediately
  highlightNext()
  
  // Continue cycling
  tourInterval = setInterval(highlightNext, TOUR_CYCLE_MS)
}

function stopTour() {
  isTourActive.value = false
  highlightedCardId.value = null
  tourCaption.value = ''
  if (tourInterval) {
    clearInterval(tourInterval)
    tourInterval = null
  }
}

function updateCaptionPosition(modelId: string) {
  // Wait for DOM update, then position caption
  setTimeout(() => {
    const cardElement = document.querySelector(`[data-model-id="${modelId}"]`) as HTMLElement
    if (cardElement) {
      // Scroll card into view smoothly, ensuring it's centered
      cardElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      
      // Calculate caption position after scroll animation completes
      setTimeout(() => {
        // Re-query to get updated position after scroll
        const updatedElement = document.querySelector(`[data-model-id="${modelId}"]`) as HTMLElement
        if (!updatedElement) return
        
        const rect = updatedElement.getBoundingClientRect()
        const viewportHeight = window.innerHeight
        const viewportWidth = window.innerWidth
        const captionHeight = 80 // Approximate caption height with padding
        const spacing = 20 // Spacing from card
        const minMargin = 10 // Minimum margin from viewport edges
        
        // Check available space above and below
        const spaceAbove = rect.top
        const spaceBelow = viewportHeight - rect.bottom
        
        // Determine best position: above, below, or overlay
        let top: number
        let transform: string
        let left: number
        
        // Calculate horizontal position (centered on card, but constrained to viewport)
        const cardCenterX = rect.left + rect.width / 2
        const captionWidth = 400 // max-width from CSS
        const halfCaptionWidth = captionWidth / 2
        const minLeft = minMargin + halfCaptionWidth
        const maxLeft = viewportWidth - minMargin - halfCaptionWidth
        
        // Center on card, but keep within viewport bounds
        left = Math.max(minLeft, Math.min(maxLeft, cardCenterX))
        
        if (spaceAbove >= captionHeight + spacing) {
          // Position above the card
          top = rect.top - spacing
          transform = 'translate(-50%, -100%)'
        } else if (spaceBelow >= captionHeight + spacing) {
          // Position below the card
          top = rect.bottom + spacing
          transform = 'translate(-50%, 0)'
        } else {
          // Not enough space above or below - position above but adjust to stay in viewport
          if (spaceAbove < minMargin + captionHeight) {
            // Very little space above - position at top of viewport
            top = minMargin
            transform = 'translate(-50%, 0)'
          } else {
            // Some space above - position above card but ensure it's visible
            top = Math.max(minMargin, rect.top - spacing)
            transform = 'translate(-50%, -100%)'
          }
        }
        
        // Ensure caption doesn't go below viewport
        if (top + captionHeight > viewportHeight - minMargin) {
          top = viewportHeight - captionHeight - minMargin
          transform = 'translate(-50%, 0)'
        }
        
        captionPosition.value = {
          top: `${top}px`,
          left: `${left}px`, // Left is already the center point (transform handles centering)
          transform: transform
        }
      }, 400) // Increased delay to ensure scroll animation completes
    }
  }, 100)
}

// Lifecycle
onMounted(() => {
  if (modelsStore.models.length === 0) {
    modelsStore.fetchModels()
  }
  if (workloadsStore.workloads.length === 0) {
    workloadsStore.fetchWorkloads()
  }
  
  // Start idle detection
  idleTimer = setTimeout(checkIdle, IDLE_THRESHOLD_MS)
  
  // Listen for user activity
  window.addEventListener('mousemove', recordActivity)
  window.addEventListener('click', recordActivity)
  window.addEventListener('keydown', recordActivity)
  window.addEventListener('scroll', recordActivity)
})

onUnmounted(() => {
  stopTour()
  if (idleTimer) {
    clearTimeout(idleTimer)
  }
  window.removeEventListener('mousemove', recordActivity)
  window.removeEventListener('click', recordActivity)
  window.removeEventListener('keydown', recordActivity)
  window.removeEventListener('scroll', recordActivity)
})

// Watch for Attract Mode changes
watch(() => attractStore.isActive, (isActive) => {
  if (isActive) {
    stopTour()
  }
})
</script>

<template>
  <div class="page page-models" @mousemove="recordActivity" @click="recordActivity">
    <div class="page-header">
      <p class="capability-header">
        Enterprise-validated AI models running 100% locally on this workstation.
      </p>
      
      <!-- Model Status Summary -->
      <div class="model-status-summary">
        <div class="status-summary-item status-summary-item--ready">
          <span class="status-icon">●</span>
          <span class="status-label">Ready:</span>
          <span class="status-count">{{ modelsStore.readyModels.length }}</span>
          <span class="status-models">
            {{ modelsStore.readyModels.map(m => m.display_name).join(', ') || 'None' }}
          </span>
        </div>
        <div class="status-summary-item status-summary-item--idle">
          <span class="status-icon">○</span>
          <span class="status-label">Idle:</span>
          <span class="status-count">{{ modelsStore.models.length - modelsStore.readyModels.length }}</span>
        </div>
        <div class="status-summary-item status-summary-item--total">
          <span class="status-label">Total Models:</span>
          <span class="status-count">{{ modelsStore.models.length }}</span>
        </div>
      </div>
    </div>

    <div class="models-grid">
      <div 
        v-for="model in sortedModels" 
        :key="model.model_id"
        :data-model-id="model.model_id"
        class="model-card"
        :class="{ 
          'model-card--ready': model.serving_status === 'ready',
          'model-card--hero': heroModelIds.includes(model.model_id),
          'model-card--highlighted': isTourActive && highlightedCardId === model.model_id
        }"
      >
        <!-- Hero badge -->
        <div v-if="heroModelIds.includes(model.model_id)" class="hero-badge">
          <span class="hero-badge-text">Featured</span>
        </div>
        
        <div class="model-header">
          <span class="model-icon">{{ getModelIcon(model.type) }}</span>
          <div class="model-header-right">
            <span 
              class="model-status" 
              :class="[
                model.serving_status,
                { 
                  'model-status--warming': getModelLoadingStatus(model.model_id) === 'warming',
                  'model-status--running': getModelLoadingStatus(model.model_id) === 'running' || (demoControl.isProcessing && isModelActive(model.model_id)),
                  'model-status--cooling': getModelLoadingStatus(model.model_id) === 'cooling'
                }
              ]"
            >
              <span v-if="getModelLoadingStatus(model.model_id) === 'warming'">⚡ Warming</span>
              <span v-else-if="getModelLoadingStatus(model.model_id) === 'running' || (demoControl.isProcessing && isModelActive(model.model_id))">● Running</span>
              <span v-else-if="getModelLoadingStatus(model.model_id) === 'cooling'">❄ Cooling</span>
              <span v-else-if="model.serving_status === 'ready'">● Ready</span>
              <span v-else>○ Idle</span>
            </span>
          </div>
        </div>
        
        <!-- Loading Progress Bar (when warming) -->
        <div v-if="getModelLoadingStatus(model.model_id) === 'warming'" class="model-loading-bar">
          <div class="model-loading-bar-fill" :style="{ width: `${demoControl.loadingProgress}%` }"></div>
        </div>
        
        <!-- VRAM Allocated (when running) -->
        <div v-if="getModelLoadingStatus(model.model_id) === 'running'" class="model-vram-info">
          <span class="vram-label">VRAM allocated:</span>
          <span class="vram-value">{{ model.size_gb ? Math.round(model.size_gb * 0.6) : '~' }} GB</span>
        </div>
        
        <h3 class="model-name">{{ model.display_name }}</h3>
        
        <!-- Loading Duration (when running, shows how long it took to load, auto-hides after 5s) -->
        <Transition name="fade">
          <div v-if="getModelLoadingStatus(model.model_id) === 'running' && demoControl.loadingDuration !== null" class="model-load-time">
            <span class="load-time-text">Loaded in {{ demoControl.loadingDuration }}s</span>
          </div>
        </Transition>
        
        <!-- Role badge -->
        <div class="model-role-badge-container">
          <span 
            class="role-badge"
            :style="{
              backgroundColor: getRoleBadgeColor(getModelRole(model)),
              borderColor: getRoleBadgeBorderColor(getModelRole(model))
            }"
          >
            {{ getModelRole(model) }}
          </span>
        </div>
        
        <div class="model-meta">
          <span class="model-type">{{ getModelTypeLabel(model.type) }}</span>
          <span v-if="model.size_gb" class="model-size">{{ model.size_gb.toFixed(1) }} GB</span>
        </div>
        
        <!-- Used By section -->
        <div v-if="modelUsageMap[model.model_id] && modelUsageMap[model.model_id].length > 0" class="used-by-section">
          <span class="used-by-label">Used by:</span>
          <div class="used-by-apps">
            <span 
              v-for="appName in modelUsageMap[model.model_id]" 
              :key="appName"
              class="used-by-app"
            >
              • {{ appName }}
            </span>
          </div>
        </div>
        
        <div class="model-locality">
          <span class="locality-badge">🏠 LOCAL</span>
        </div>
      </div>

      <div v-if="modelsStore.models.length === 0" class="empty-state">
        <span class="empty-icon">📦</span>
        <p>No models installed</p>
      </div>
    </div>
    
    <!-- Auto Highlight Tour caption overlay -->
    <Transition name="fade-in">
      <div 
        v-if="isTourActive && tourCaption && highlightedCardId"
        class="tour-caption-overlay"
        :style="captionPosition"
      >
        <div class="tour-caption-text">{{ tourCaption }}</div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.page-models {
  padding: 40px 24px;
  max-width: var(--container-max);
  margin: 0 auto;
  position: relative;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.capability-header {
  font-family: var(--font-label);
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0 0 24px 0;
  font-weight: 500;
  line-height: 1.5;
}

.model-status-summary {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
  flex-wrap: wrap;
  padding: 16px 24px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  margin: 0 auto;
  max-width: 900px;
}

.status-summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
}

.status-icon {
  font-size: 1rem;
  line-height: 1;
}

.status-summary-item--ready .status-icon {
  color: var(--status-success);
}

.status-summary-item--idle .status-icon {
  color: var(--text-muted);
  opacity: 0.6;
}

.status-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.status-count {
  color: var(--text-primary);
  font-weight: 700;
  font-family: var(--font-mono);
}

.status-models {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-left: 8px;
  font-style: italic;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-summary-item--total {
  padding-left: 16px;
  border-left: 1px solid var(--border-subtle);
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.model-card {
  padding: 24px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  transition: all var(--duration-normal) var(--ease-smooth);
  position: relative;
  overflow: visible;
}

.model-card--ready {
  border-color: rgba(34, 197, 94, 0.3);
}

.model-card--hero {
  border-color: rgba(251, 146, 60, 0.4);
  box-shadow: 0 0 20px rgba(251, 146, 60, 0.1);
}

.model-card--highlighted {
  border-color: rgba(251, 146, 60, 0.6);
  box-shadow: 0 0 30px rgba(251, 146, 60, 0.2);
  transform: scale(1.02);
  animation: pulse-glow 7s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 30px rgba(251, 146, 60, 0.2);
  }
  50% {
    box-shadow: 0 0 40px rgba(251, 146, 60, 0.35);
  }
}

.hero-badge {
  position: absolute;
  top: -8px;
  right: 16px;
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.95), rgba(251, 146, 60, 0.85));
  border: 1px solid rgba(251, 146, 60, 0.5);
  border-radius: 12px;
  padding: 4px 12px;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(251, 146, 60, 0.3);
}

.hero-badge-text {
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 700;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.model-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-icon {
  font-size: 1.5rem;
}

.model-status {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.model-status.ready {
  color: var(--status-success);
}

.model-status.idle {
  color: var(--text-muted);
}

.model-status--warming {
  color: var(--abs-orange);
  animation: pulse 1.5s ease-in-out infinite;
}

.model-status--running {
  color: var(--status-success);
  animation: pulse 2s ease-in-out infinite;
}

.model-status--cooling {
  color: var(--text-muted);
  opacity: 0.7;
}

.model-loading-bar {
  width: 100%;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin: 8px 0;
}

.model-loading-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--abs-orange), #ff9f43);
  border-radius: 2px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(249, 115, 22, 0.5);
}

.model-vram-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 6px;
  margin-top: 8px;
}

.model-load-time {
  margin-top: 8px;
  text-align: left;
  font-family: var(--font-label);
  font-size: 0.7rem;
}

.load-time-text {
  color: var(--text-muted);
  font-weight: 400;
}

.vram-label {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.vram-value {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--status-success);
  font-weight: 600;
}

.model-name {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}

.model-role-badge-container {
  margin-bottom: 12px;
}

.role-badge {
  display: inline-block;
  padding: 4px 10px;
  border: 1px solid;
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.model-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.model-type {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.model-size {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.used-by-section {
  margin-bottom: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

.used-by-label {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  display: block;
  margin-bottom: 6px;
}

.used-by-apps {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.used-by-app {
  font-family: var(--font-body);
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.model-locality {
  margin-top: 8px;
}

.locality-badge {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 24px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 16px;
}

/* Auto Highlight Tour caption */
.tour-caption-overlay {
  position: fixed;
  z-index: 100;
  pointer-events: none;
  max-width: 400px;
}

.tour-caption-text {
  background: rgba(15, 15, 20, 0.95);
  border: 1px solid rgba(251, 146, 60, 0.4);
  border-radius: 8px;
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 0.875rem;
  color: var(--text-primary);
  line-height: 1.5;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.fade-in-enter-active,
.fade-in-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-in-enter-from {
  opacity: 0;
  transform: translate(-50%, -100%) translateY(-10px);
}

.fade-in-leave-to {
  opacity: 0;
  transform: translate(-50%, -100%) translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
