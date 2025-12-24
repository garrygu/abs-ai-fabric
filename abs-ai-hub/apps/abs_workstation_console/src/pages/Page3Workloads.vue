<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWorkloadsStore } from '@/stores/workloadsStore'
import { useMetricsStore } from '@/stores/metricsStore'
import { useCESMode } from '@/composables/useCESMode'
import { useAttractModeStore } from '@/stores/attractModeStore'

const workloadsStore = useWorkloadsStore()
const metricsStore = useMetricsStore()
const { isCESMode } = useCESMode()
const attractStore = useAttractModeStore()

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

// Workload captions for tour (narrative, one sentence max)
const workloadCaptions: Record<string, string> = {
  'contract-reviewer': 'Live contract analysis powered by local LLM inference and semantic search.',
  'contract-reviewer-v2': 'Advanced contract review using local LLM + embeddings for real-time analysis.',
  'onyx-ai-assistant': 'Multiple AI assistants running simultaneously on enterprise-class hardware.',
  'onyx-suite': 'Integrated AI platform managing inference, embeddings, and model lifecycle.',
  'legal-assistant': 'Domain-specific AI assistant leveraging legal embeddings and LLM inference.',
  'model-management': 'Model management and inference orchestration on the same workstation.'
}

// Hero workloads (highlighted for CES)
const heroWorkloadIds = computed(() => {
  const heroIds: string[] = []
  
  // Find Contract Reviewer (primary demo workload)
  const contractReviewer = workloadsStore.workloads.find(w => 
    w.app_name.toLowerCase().includes('contract') && 
    w.status === 'running'
  )
  if (contractReviewer) {
    heroIds.push(contractReviewer.app_id)
  }
  
  // Find Onyx AI Assistant (secondary demo workload)
  const onyxAssistant = workloadsStore.workloads.find(w => 
    w.app_name.toLowerCase().includes('onyx') && 
    w.status === 'running'
  )
  if (onyxAssistant && !heroIds.includes(onyxAssistant.app_id)) {
    heroIds.push(onyxAssistant.app_id)
  }
  
  return heroIds
})

// Get GPU model for hardware attribution
const gpuModel = computed(() => {
  return metricsStore.metrics?.gpu?.model || 'NVIDIA RTX Pro 6000'
})

// Get workload categories (can have multiple)
function getWorkloadCategories(workload: any): string[] {
  const categories: string[] = []
  
  if (workload.workload_type === 'llm_inference') {
    categories.push('LLM Inference')
  } else if (workload.workload_type === 'rag') {
    categories.push('RAG / Search')
  } else if (workload.workload_type === 'embedding') {
    categories.push('Embeddings')
  } else if (workload.workload_type === 'model_management') {
    categories.push('Model Management')
  }
  
  // Additional categories based on app name
  const appNameLower = workload.app_name.toLowerCase()
  if (appNameLower.includes('contract') || appNameLower.includes('legal')) {
    if (!categories.includes('Summarization')) {
      categories.push('Summarization')
    }
  }
  
  return categories.length > 0 ? categories : ['AI Application']
}

// Sorted workloads: hero workloads first, then running, then idle
const sortedWorkloads = computed(() => {
  const workloads = [...workloadsStore.workloads]
  
  return workloads.sort((a, b) => {
    const aIsHero = heroWorkloadIds.value.includes(a.app_id)
    const bIsHero = heroWorkloadIds.value.includes(b.app_id)
    
    if (aIsHero && !bIsHero) return -1
    if (!aIsHero && bIsHero) return 1
    
    const aIsRunning = a.status === 'running'
    const bIsRunning = b.status === 'running'
    if (aIsRunning && !bIsRunning) return -1
    if (!aIsRunning && bIsRunning) return 1
    
    return 0
  })
})

function getWorkloadIcon(type: string): string {
  const icons: Record<string, string> = {
    'llm_inference': '🧠',
    'rag': '📚',
    'embedding': '🔗',
    'model_management': '⚙️'
  }
  return icons[type] || '📱'
}

function getWorkloadLabel(type: string): string {
  const labels: Record<string, string> = {
    'llm_inference': 'LLM Inference',
    'rag': 'RAG Pipeline',
    'embedding': 'Embeddings',
    'model_management': 'Model Management'
  }
  return labels[type] || type
}

// Auto Highlight Tour functions
function getCardCaption(appId: string, appName: string): string {
  // Try exact match first
  if (workloadCaptions[appId]) {
    return workloadCaptions[appId]
  }
  
  // Try fuzzy match by app name
  const appNameLower = appName.toLowerCase()
  for (const [key, caption] of Object.entries(workloadCaptions)) {
    if (appNameLower.includes(key.replace('-', ' '))) {
      return caption
    }
  }
  
  // Default caption
  return 'AI workload running locally on enterprise-class hardware.'
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
                      sortedWorkloads.value.length > 0
  
  if (shouldStart) {
    startTour()
  }
}

function startTour() {
  if (isTourActive.value || sortedWorkloads.value.length === 0) {
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
      
      if (currentIndex >= sortedWorkloads.value.length) {
        currentIndex = 0
      }
      
      const workload = sortedWorkloads.value[currentIndex]
      highlightedCardId.value = workload.app_id
      tourCaption.value = getCardCaption(workload.app_id, workload.app_name)
      
      // Position caption above card (with scroll and smart positioning)
      updateCaptionPosition(workload.app_id)
      
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

function updateCaptionPosition(appId: string) {
  // Wait for DOM update, then position caption
  setTimeout(() => {
    const cardElement = document.querySelector(`[data-workload-id="${appId}"]`) as HTMLElement
    if (cardElement) {
      // Scroll card into view smoothly, ensuring it's centered
      cardElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      
      // Calculate caption position after scroll animation completes
      setTimeout(() => {
        // Re-query to get updated position after scroll
        const updatedElement = document.querySelector(`[data-workload-id="${appId}"]`) as HTMLElement
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
  <div class="page page-workloads" @mousemove="recordActivity" @click="recordActivity">
    <div class="page-header">
      <p class="capability-header">
        Parallel AI workloads executing locally on enterprise-class hardware.
      </p>
    </div>

    <div class="workloads-list">
      <div 
        v-for="workload in sortedWorkloads" 
        :key="workload.app_id"
        :data-workload-id="workload.app_id"
        class="workload-card"
        :class="{ 
          'workload-card--active': workload.status === 'running',
          'workload-card--hero': heroWorkloadIds.includes(workload.app_id),
          'workload-card--highlighted': isTourActive && highlightedCardId === workload.app_id
        }"
      >
        <!-- Hero/Demo badge -->
        <div v-if="heroWorkloadIds.includes(workload.app_id)" class="hero-badge">
          <span class="hero-badge-text">{{ workload.status === 'running' ? 'Live' : 'Demo' }}</span>
        </div>
        
        <div class="workload-icon">{{ getWorkloadIcon(workload.workload_type) }}</div>
        <div class="workload-content">
          <h3 class="workload-name">{{ workload.app_name }}</h3>
          
          <!-- Workload Categories -->
          <div class="workload-categories">
            <span 
              v-for="category in getWorkloadCategories(workload)" 
              :key="category"
              class="category-badge"
            >
              {{ category }}
            </span>
          </div>
          
          <div class="workload-meta">
            <span class="workload-type">{{ getWorkloadLabel(workload.workload_type) }}</span>
            <span class="workload-status" :class="workload.status">
              {{ workload.status === 'running' ? '● Running' : '○ Idle' }}
            </span>
          </div>
          
          <div v-if="workload.associated_models?.length" class="workload-models">
            <span class="models-label">Models:</span>
            <span 
              v-for="model in workload.associated_models" 
              :key="model" 
              class="model-badge"
            >
              {{ model }}
            </span>
          </div>
          
          <!-- Hardware Attribution -->
          <div class="hardware-attribution">
            <span class="hardware-icon">⚡</span>
            <span class="hardware-text">Accelerated by: {{ gpuModel }}</span>
          </div>
        </div>
      </div>

      <div v-if="workloadsStore.workloads.length === 0" class="empty-state">
        <span class="empty-icon">💤</span>
        <p>No active workloads</p>
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
.page-workloads {
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
  margin: 0;
  font-weight: 500;
  line-height: 1.5;
}

.workloads-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.workload-card {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 24px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  transition: all var(--duration-normal) var(--ease-smooth);
  position: relative;
  overflow: visible;
}

.workload-card--active {
  border-color: rgba(34, 197, 94, 0.3);
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.05);
}

.workload-card--hero {
  border-color: rgba(251, 146, 60, 0.4);
  box-shadow: 0 0 20px rgba(251, 146, 60, 0.1);
}

.workload-card--highlighted {
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

.workload-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.workload-content {
  flex: 1;
  min-width: 0;
}

.workload-name {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}

.workload-categories {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.category-badge {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.workload-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.workload-type {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.workload-status {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
}

.workload-status.running {
  color: var(--status-success);
}

.workload-status.idle {
  color: var(--text-muted);
}

.workload-models {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.models-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
}

.model-badge {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--electric-indigo);
}

.hardware-attribution {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
  margin-top: 8px;
}

.hardware-icon {
  font-size: 0.875rem;
  opacity: 0.7;
}

.hardware-text {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 500;
}

.empty-state {
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
</style>
