<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useDemoControlStore, type ActiveModel } from '@/stores/demoControlStore'
import { useMetricsStore } from '@/stores/metricsStore'

const demoControl = useDemoControlStore()
const metricsStore = useMetricsStore()

// Panel state: 'collapsed' | 'compact' | 'expanded'
type PanelState = 'collapsed' | 'compact' | 'expanded'
const panelState = ref<PanelState>('expanded')
const showStateDropdown = ref(false)

// Panel is always visible, just in different states (collapsed/compact/expanded)

// Dragging state
const panelRef = ref<HTMLElement | null>(null)
const reopenButtonRef = ref<HTMLElement | null>(null)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const panelPosition = ref({ x: 0, y: 0 })
const dragOffset = ref({ x: 0, y: 0 })

// Load saved position from localStorage
function loadPosition() {
  const saved = localStorage.getItem('demoControlPanelPosition')
  if (saved) {
    try {
      const { x, y } = JSON.parse(saved)
      panelPosition.value = { x, y }
      return
    } catch (e) {
      console.warn('Failed to parse saved panel position', e)
    }
  }
  // Default position: bottom-right aligned to viewport
  // Will be calculated in onMounted based on actual panel width
  panelPosition.value = { x: 0, y: 0 }
}

// Calculate default right-aligned position
function calculateDefaultPosition() {
  if (!panelRef.value) return
  
  const rect = panelRef.value.getBoundingClientRect()
  const panelWidth = rect.width || getPanelWidth(panelState.value)
  const margin = 24
  
  panelPosition.value = {
    x: window.innerWidth - panelWidth - margin,
    y: window.innerHeight - (rect.height || 200) - margin
  }
  
  constrainPosition()
  savePosition()
}

// Save position to localStorage
function savePosition() {
  localStorage.setItem('demoControlPanelPosition', JSON.stringify(panelPosition.value))
}

// Load saved panel state from localStorage
function loadPanelState() {
  const saved = localStorage.getItem('demoControlPanelState')
  if (saved && ['collapsed', 'compact', 'expanded'].includes(saved)) {
    panelState.value = saved as PanelState
  } else {
    panelState.value = 'expanded' // Default to expanded
  }
}

// Save panel state to localStorage
function savePanelState() {
  localStorage.setItem('demoControlPanelState', panelState.value)
}

// Toggle panel state
function setPanelState(state: PanelState) {
  const oldState = panelState.value
  panelState.value = state
  savePanelState()
  showStateDropdown.value = false
  
  // Adjust position when switching to wider states
  adjustPositionForStateChange(state, oldState)
}

// Get state label for display
function getStateLabel(state: PanelState): string {
  switch (state) {
    case 'collapsed':
      return 'Collapsed'
    case 'compact':
      return 'Compact'
    case 'expanded':
      return 'Expanded'
  }
}

// Close dropdown when clicking outside
function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.state-dropdown')) {
    showStateDropdown.value = false
  }
}

// Cycle through states: collapsed -> compact -> expanded -> collapsed
function cyclePanelState() {
  const states: PanelState[] = ['collapsed', 'compact', 'expanded']
  const currentIndex = states.indexOf(panelState.value)
  const nextIndex = (currentIndex + 1) % states.length
  setPanelState(states[nextIndex])
}

// Constrain position to viewport
function constrainPosition() {
  if (!panelRef.value) return
  
  const rect = panelRef.value.getBoundingClientRect()
  const maxX = window.innerWidth - rect.width
  const maxY = window.innerHeight - rect.height
  
  panelPosition.value.x = Math.max(0, Math.min(panelPosition.value.x, maxX))
  panelPosition.value.y = Math.max(0, Math.min(panelPosition.value.y, maxY))
}

// Get expected panel width based on state
function getPanelWidth(state: PanelState): number {
  switch (state) {
    case 'collapsed':
      return 60
    case 'compact':
      return 240
    case 'expanded':
      return 280
  }
}

// Adjust position when switching states that increase panel width
function adjustPositionForStateChange(newState: PanelState, oldState: PanelState) {
  // Adjust when switching to a wider state (collapsed -> compact/expanded, or compact -> expanded)
  const oldWidth = getPanelWidth(oldState)
  const newWidth = getPanelWidth(newState)
  
  // Only adjust if new state is wider
  if (newWidth <= oldWidth) return
  
  nextTick(() => {
    if (!panelRef.value) return
    
    const viewportWidth = window.innerWidth
    const margin = 24
    
    // Calculate current right edge position
    const currentRight = panelPosition.value.x + oldWidth
    const maxRight = viewportWidth - margin
    
    // If panel would overflow viewport, reposition from right edge
    if (currentRight > maxRight || panelPosition.value.x + newWidth > viewportWidth - margin) {
      panelPosition.value.x = viewportWidth - newWidth - margin
    }
    
    // Ensure panel stays within bounds
    constrainPosition()
    savePosition()
  })
}

// Drag handlers - Mouse
function handleMouseDown(e: MouseEvent) {
  const target = e.target as HTMLElement
  
  // For collapsed state, allow dragging from anywhere except the button content
  if (panelState.value === 'collapsed') {
    if (target.closest('.collapsed-button-content')) {
      // Don't drag when clicking the button content directly
      return
    }
    startDrag(e.clientX, e.clientY)
    e.preventDefault()
    e.stopPropagation()
    return
  }
  
  // For compact/expanded states, only allow dragging from the header
  if (!target.closest('.panel-header')) return
  // Don't drag when clicking buttons (dropdown, state items, etc.)
  if (target.closest('button')) return
  
  startDrag(e.clientX, e.clientY)
  e.preventDefault()
  e.stopPropagation()
}

function handleMouseMove(e: MouseEvent) {
  if (!isDragging.value) return
  updateDragPosition(e.clientX, e.clientY)
  e.preventDefault()
}

function handleMouseUp() {
  endDrag()
}

// Drag handlers - Touch
function handleTouchStart(e: TouchEvent) {
  const target = e.target as HTMLElement
  
  // For collapsed state, allow dragging from anywhere except the button content
  if (panelState.value === 'collapsed') {
    if (target.closest('.collapsed-button-content')) {
      return
    }
    const touch = e.touches[0]
    if (touch) {
      startDrag(touch.clientX, touch.clientY)
      e.preventDefault()
    }
    return
  }
  
  // For compact/expanded states, only allow dragging from the header
  if (!target.closest('.panel-header')) return
  // Don't drag when clicking buttons (dropdown, state items, etc.)
  if (target.closest('button')) return
  
  const touch = e.touches[0]
  if (touch) {
    startDrag(touch.clientX, touch.clientY)
    e.preventDefault()
  }
}

function handleTouchMove(e: TouchEvent) {
  if (!isDragging.value) return
  const touch = e.touches[0]
  if (touch) {
    updateDragPosition(touch.clientX, touch.clientY)
    e.preventDefault()
  }
}

function handleTouchEnd() {
  endDrag()
}

// Common drag logic
function startDrag(clientX: number, clientY: number) {
  if (!panelRef.value) return
  
  isDragging.value = true
  const rect = panelRef.value.getBoundingClientRect()
  dragOffset.value = {
    x: clientX - rect.left,
    y: clientY - rect.top
  }
  
  // Prevent text selection during drag
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'grabbing'
}

function updateDragPosition(clientX: number, clientY: number) {
  panelPosition.value = {
    x: clientX - dragOffset.value.x,
    y: clientY - dragOffset.value.y
  }
  constrainPosition()
}

function endDrag() {
  if (isDragging.value) {
    isDragging.value = false
    savePosition()
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
  }
}

// Handle window resize
function handleResize() {
  constrainPosition()
}

onMounted(() => {
  loadPosition()
  loadPanelState()
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseup', handleMouseUp)
  window.addEventListener('touchmove', handleTouchMove, { passive: false })
  window.addEventListener('touchend', handleTouchEnd)
  window.addEventListener('resize', handleResize)
  window.addEventListener('click', handleClickOutside)
  
  // Check for already-loaded models on mount
  demoControl.checkLoadedModels()
  // Sync pull status when Admin is pulling a model (via gateway)
  demoControl.startPullStatusPolling()

  // Calculate initial position from bottom-right if not saved
  if (panelPosition.value.x === 0 && panelPosition.value.y === 0) {
    nextTick(() => {
      calculateDefaultPosition()
    })
  } else {
    nextTick(() => {
      if (panelRef.value) {
        // Ensure saved position aligns to right if it's too far left
        const panelWidth = panelRef.value.getBoundingClientRect().width || getPanelWidth(panelState.value)
        const minX = window.innerWidth - panelWidth - 24
        if (panelPosition.value.x < minX) {
          panelPosition.value.x = minX
          savePosition()
        }
        constrainPosition()
      }
    })
  }
})

onUnmounted(() => {
  demoControl.stopPullStatusPolling()
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
  window.removeEventListener('touchmove', handleTouchMove)
  window.removeEventListener('touchend', handleTouchEnd)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('click', handleClickOutside)
  // Clean up any lingering drag state
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
})

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

// Human-readable active model name
const activeModelDisplayName = computed(() => {
  switch (demoControl.activeModel) {
    case 'deepseek-r1-70b':
      return 'DeepSeek R1 70B'
    case 'llama3-70b':
      return 'LLaMA-3 70B'
    case 'dual':
      return 'Dual 70B Mode'
    default:
      return 'No Model'
  }
})

function showPromptKiosk() {
  window.dispatchEvent(new CustomEvent('show-prompt-kiosk'))
}

// Get GPU metric style based on utilization (for visual feedback)
function getGpuMetricStyle(utilization: number) {
  const intensity = Math.min(utilization / 100, 1)
  const glowIntensity = intensity > 0.1 ? intensity * 0.6 : 0
  
  return {
    color: `hsl(${15 + intensity * 15}, 100%, ${65 - intensity * 15}%)`, // Orange to brighter orange
    textShadow: glowIntensity > 0 
      ? `0 0 ${8 * glowIntensity}px rgba(249, 115, 22, ${0.4 * glowIntensity}), 0 0 ${16 * glowIntensity}px rgba(249, 115, 22, ${0.2 * glowIntensity})`
      : 'none',
    transition: 'color 0.3s ease, text-shadow 0.3s ease'
  }
}

</script>

<template>
  <!-- COLLAPSED STATE: Single vertical button -->
  <Transition name="fade">
    <div
      v-if="panelState === 'collapsed'"
      ref="panelRef"
      class="demo-control-panel demo-control-panel--collapsed"
      :class="{ 'is-running': demoControl.isRunning, 'is-dragging': isDragging }"
      :style="{
        left: `${panelPosition.x}px`,
        top: `${panelPosition.y}px`,
        right: 'auto',
        bottom: 'auto',
        transition: isDragging ? 'none' : 'transform 0.2s ease-out'
      }"
      @mousedown="handleMouseDown"
      @touchstart="handleTouchStart"
    >
      <button
        class="collapsed-button-content"
        @click.stop="setPanelState('compact')"
        title="Expand Playground"
      >
        <span class="collapsed-icon">⚡</span>
        <span class="collapsed-text">Playground</span>
        <span class="collapsed-arrow">▶</span>
      </button>
    </div>
  </Transition>

  <!-- COMPACT & EXPANDED STATES: Full panel -->
  <div 
    v-if="panelState === 'compact' || panelState === 'expanded'"
    ref="panelRef"
    class="demo-control-panel"
    :class="{ 
      'is-dragging': isDragging, 
      'is-running': demoControl.isRunning,
      'panel-state--compact': panelState === 'compact',
      'panel-state--expanded': panelState === 'expanded'
    }"
    :style="{
      left: `${panelPosition.x}px`,
      top: `${panelPosition.y}px`,
      right: 'auto',
      bottom: 'auto',
      transition: isDragging ? 'none' : 'transform 0.2s ease-out'
    }"
    @mousedown="handleMouseDown"
    @touchstart="handleTouchStart"
  >
    <div class="panel-header">
      <!-- Top row: Drag handle + Status/Controls -->
      <div class="header-top-row">
        <div class="drag-handle" :class="{ 'is-dragging': isDragging }">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="4" cy="4" r="1.5" fill="currentColor"/>
            <circle cx="12" cy="4" r="1.5" fill="currentColor"/>
            <circle cx="4" cy="8" r="1.5" fill="currentColor"/>
            <circle cx="12" cy="8" r="1.5" fill="currentColor"/>
            <circle cx="4" cy="12" r="1.5" fill="currentColor"/>
            <circle cx="12" cy="12" r="1.5" fill="currentColor"/>
          </svg>
        </div>
        <div class="header-right">
          <div class="status-indicator" :style="{ color: getStatusColor() }">
            <span class="status-dot" :style="{ backgroundColor: getStatusColor() }"></span>
            {{ statusLabel }}
          </div>
          
          <!-- Control buttons group - Top Right -->
          <div class="header-controls">
            <!-- State dropdown menu -->
            <div class="state-dropdown" v-if="(panelState as PanelState) !== 'collapsed'">
            <button 
              class="state-dropdown-trigger"
              @click.stop="showStateDropdown = !showStateDropdown"
              :title="`Current: ${getStateLabel(panelState)}`"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="2" y="2" width="10" height="10" stroke="currentColor" stroke-width="1.5" fill="none" rx="1"/>
                <rect v-if="panelState === 'expanded'" x="4" y="4" width="6" height="6" stroke="currentColor" stroke-width="1" fill="none" rx="0.5"/>
              </svg>
              <span class="state-dropdown-label">{{ getStateLabel(panelState) }}</span>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" class="dropdown-arrow" :class="{ 'is-open': showStateDropdown }">
                <path d="M2 3 L5 6 L8 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            
            <!-- Dropdown menu -->
            <Transition name="dropdown">
              <div v-if="showStateDropdown" class="state-dropdown-menu">
                <button
                  class="state-dropdown-item"
                  :class="{ 'active': panelState === 'expanded' }"
                  @click.stop="setPanelState('expanded')"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <rect x="1" y="1" width="12" height="12" stroke="currentColor" stroke-width="1.5" fill="none" rx="1"/>
                    <rect x="3" y="3" width="8" height="8" stroke="currentColor" stroke-width="1" fill="none" rx="0.5"/>
                  </svg>
                  <div class="state-dropdown-content">
                    <span class="state-name">Expanded</span>
                    <span class="state-description">Full console with all controls</span>
                  </div>
                </button>
                
                <button
                  class="state-dropdown-item"
                  :class="{ 'active': panelState === 'compact' }"
                  @click.stop="setPanelState('compact')"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <rect x="2" y="2" width="10" height="10" stroke="currentColor" stroke-width="1.5" fill="none" rx="1"/>
                  </svg>
                  <div class="state-dropdown-content">
                    <span class="state-name">Compact</span>
                    <span class="state-description">Active model + metrics</span>
                  </div>
                </button>
                
                <button
                  class="state-dropdown-item"
                  :class="{ 'active': (panelState as PanelState) === 'collapsed' }"
                  @click.stop="setPanelState('collapsed')"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M3 7 L11 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  <div class="state-dropdown-content">
                    <span class="state-name">Collapsed</span>
                    <span class="state-description">Minimal button only</span>
                  </div>
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
      </div>
      
      <!-- Bottom row: Title -->
      <div class="header-title-row">
        <div class="panel-title">LIVE PLAYGROUND</div>
      </div>
    </div>
    
    <!-- ============================================== -->
    <!-- COMPACT STATE: Active Model + Try It + Metrics -->
    <!-- ============================================== -->
    <template v-if="panelState === 'compact'">
      <!-- Active Model Section - Always shown in compact mode -->
      <div class="active-model-section active-model-section--compact">
        <div class="active-model-label">{{ demoControl.loadError ? 'ERROR' : demoControl.isWarming ? 'LOADING MODEL' : 'ACTIVE MODEL' }}</div>
        <div class="active-model-name" :class="{ 'no-model': !demoControl.activeModel && !demoControl.loadError, 'active-model-name--loading': demoControl.isWarming, 'active-model-name--error': demoControl.loadError }">
          {{ demoControl.loadError || (demoControl.isWarming ? `${activeModelDisplayName}...` : activeModelDisplayName) }}
        </div>
        
        <!-- Try It Button - Only shown when actually running (loaded), not while warming -->
        <button 
          v-if="demoControl.isRunning" 
          class="try-it-button try-it-button--compact"
          @click="showPromptKiosk"
        >
          ⚡ Try It Yourself
        </button>
        
        <!-- Quick activate button when idle or warming (so user can expand to see progress) -->
        <button 
          v-if="!demoControl.isRunning" 
          class="quick-activate-button"
          @click="setPanelState('expanded')"
          :title="demoControl.isWarming ? 'Model loading – expand for progress' : 'Select model to activate'"
        >
          {{ demoControl.isWarming ? 'Loading...' : 'Select Model →' }}
        </button>
      </div>
      
      <!-- Key Metrics (Compact) - Always shown -->
      <div class="compact-metrics">
        <div class="compact-metric">
          <div class="compact-metric-label">GPU</div>
          <div 
            class="compact-metric-value compact-metric-value--gpu"
            :style="getGpuMetricStyle(metricsStore.gpuUtilization)"
          >
            {{ Math.round(metricsStore.gpuUtilization) }}%
          </div>
        </div>
        <div class="compact-metric">
          <div class="compact-metric-label">VRAM</div>
          <div class="compact-metric-value">{{ metricsStore.vramUsed.toFixed(1) }} / {{ metricsStore.vramTotal.toFixed(0) }} GB</div>
        </div>
        <div class="compact-metric">
          <div class="compact-metric-label">CPU</div>
          <div class="compact-metric-value">{{ Math.round(metricsStore.cpuUtilization) }}%</div>
        </div>
      </div>
    </template>
    
    <!-- ============================================== -->
    <!-- EXPANDED STATE: Full Console -->
    <!-- ============================================== -->
    <template v-if="panelState === 'expanded'">
      <!-- Active Model Section -->
      <div v-if="demoControl.isRunning" class="active-model-section">
        <div class="active-model-label">ACTIVE MODEL</div>
        <div class="active-model-name">{{ activeModelDisplayName }}</div>
        
        <!-- Try It Button -->
        <button class="try-it-button" @click="showPromptKiosk">
          ⚡ Try It Yourself
        </button>
        
        <button
          class="deactivate-button"
          @click="demoControl.deactivateModelManually"
          title="Unload model and free VRAM"
        >
          Unload model
        </button>
      </div>
      
      <!-- Model Selector Section -->
      <div class="model-selector-section">
      <div v-if="demoControl.isRunning" class="section-label">SWITCH MODEL</div>
      <div v-else class="section-label">SELECT MODEL TO ACTIVATE</div>

      <!-- Load error: model not pulled -->
      <div v-if="demoControl.loadError" class="load-error-message">
        <span class="load-error-icon">📦</span>
        {{ demoControl.loadError }}
      </div>
      
      <div class="model-buttons">
        <button
          class="model-button"
          :class="{ 
            'model-button--active': demoControl.activeModel === 'deepseek-r1-70b' && demoControl.modelStatus === 'running',
            'model-button--warming': demoControl.activeModel === 'deepseek-r1-70b' && demoControl.modelStatus === 'warming',
            'model-button--pulling': demoControl.pullingModel === 'deepseek-r1-70b',
            'model-button--pending': demoControl.pendingRequest === 'deepseek-r1-70b'
          }"
          :disabled="demoControl.activeModel === 'deepseek-r1-70b'"
          @click="activateModel('deepseek-r1-70b')"
        >
          <span class="model-icon">🧠</span>
          <span class="model-name">DeepSeek R1 70B</span>
          <span v-if="demoControl.activeModel === 'deepseek-r1-70b' && demoControl.modelStatus === 'running'" class="active-badge">ACTIVE</span>
          <span v-else-if="demoControl.activeModel === 'deepseek-r1-70b' && demoControl.modelStatus === 'warming'" class="active-badge active-badge--loading">Loading...</span>
          <span v-else-if="demoControl.pullingModel === 'deepseek-r1-70b'" class="active-badge active-badge--pulling">Pulling...</span>
          <span v-else-if="demoControl.isRunning" class="switch-hint">SWITCH →</span>
        </button>
        
        <button
          class="model-button"
          :class="{ 
            'model-button--active': demoControl.activeModel === 'llama3-70b' && demoControl.modelStatus === 'running',
            'model-button--warming': demoControl.activeModel === 'llama3-70b' && demoControl.modelStatus === 'warming',
            'model-button--pulling': demoControl.pullingModel === 'llama3-70b',
            'model-button--pending': demoControl.pendingRequest === 'llama3-70b'
          }"
          :disabled="demoControl.activeModel === 'llama3-70b'"
          @click="activateModel('llama3-70b')"
        >
          <span class="model-icon">🦙</span>
          <span class="model-name">LLaMA-3 70B</span>
          <span v-if="demoControl.activeModel === 'llama3-70b' && demoControl.modelStatus === 'running'" class="active-badge">ACTIVE</span>
          <span v-else-if="demoControl.activeModel === 'llama3-70b' && demoControl.modelStatus === 'warming'" class="active-badge active-badge--loading">Loading...</span>
          <span v-else-if="demoControl.pullingModel === 'llama3-70b'" class="active-badge active-badge--pulling">Pulling...</span>
          <span v-else-if="demoControl.isRunning" class="switch-hint">SWITCH →</span>
        </button>
        
        <button
          class="model-button model-button--dual"
          :class="{ 
            'model-button--active': demoControl.activeModel === 'dual' && demoControl.modelStatus === 'running',
            'model-button--warming': demoControl.activeModel === 'dual' && demoControl.modelStatus === 'warming',
            'model-button--pending': demoControl.pendingRequest === 'dual'
          }"
          :disabled="demoControl.activeModel === 'dual'"
          @click="activateModel('dual')"
        >
          <span class="model-icon">⚡</span>
          <span class="model-name">Dual 70B Showcase</span>
          <span v-if="demoControl.activeModel === 'dual' && demoControl.modelStatus === 'running'" class="active-badge">ACTIVE</span>
          <span v-else-if="demoControl.activeModel === 'dual' && demoControl.modelStatus === 'warming'" class="active-badge active-badge--loading">Loading...</span>
          <span v-else-if="demoControl.isRunning" class="switch-hint">SWITCH →</span>
        </button>
      </div>
    </div>
    
      <!-- Loading Progress -->
      <div v-if="demoControl.isWarming" class="loading-section">
        <div class="loading-stage">
          <span>{{ demoControl.loadingStage }}</span>
          <span v-if="demoControl.loadingElapsedFormatted" class="loading-time">{{ demoControl.loadingElapsedFormatted }}</span>
        </div>
        <div class="loading-bar">
          <div class="loading-bar-fill" :style="{ width: `${demoControl.loadingProgress}%` }"></div>
        </div>
      </div>
      
      <!-- Pending Request Status -->
      <div v-if="demoControl.pendingRequest" class="pending-request-status">
        <div class="pending-message">
          <span class="pending-icon">⏳</span>
          <span>Switching model...</span>
        </div>
        <button 
          class="cancel-pending-button"
          @click="demoControl.cancelPendingRequest"
          title="Cancel pending request"
        >
          Cancel
        </button>
      </div>
    </template>
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
  border: 2px solid var(--border-subtle);
  border-radius: 12px;
  box-shadow: 
    var(--shadow-lg),
    0 0 0 1px rgba(249, 115, 22, 0.1),
    0 0 20px rgba(249, 115, 22, 0.05);
  z-index: 150;
  backdrop-filter: blur(10px);
  user-select: none;
  transition: width 0.3s ease, height 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
  overflow: visible;
  box-sizing: border-box;
  animation: subtleBorderPulse 4s ease-in-out infinite;
}

/* Enhanced border visual effects - subtle animated glow when idle */

@keyframes subtleBorderPulse {
  0%, 100% {
    box-shadow: 
      var(--shadow-lg),
      0 0 0 1px rgba(249, 115, 22, 0.1),
      0 0 20px rgba(249, 115, 22, 0.05);
  }
  50% {
    box-shadow: 
      var(--shadow-lg),
      0 0 0 1px rgba(249, 115, 22, 0.2),
      0 0 30px rgba(249, 115, 22, 0.1);
  }
}

/* Collapsed state */
.demo-control-panel--collapsed {
  width: 60px;
  height: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.demo-control-panel--collapsed:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.3);
}

.collapsed-icon {
  font-size: 24px;
  line-height: 1;
}

.collapsed-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-family: var(--font-display);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-primary);
}

.collapsed-arrow {
  font-size: 12px;
  color: var(--abs-orange);
  line-height: 1;
}

.collapsed-button-content {
  width: 100%;
  height: 100%;
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 0;
  color: inherit;
  font-family: inherit;
}

.demo-control-panel--collapsed {
  cursor: grab;
}

.demo-control-panel--collapsed.is-dragging {
  cursor: grabbing;
}

/* Compact state */
.panel-state--compact {
  width: 240px;
  min-width: 240px;
  max-width: 240px;
}

/* Expanded state */
.panel-state--expanded {
  width: 280px;
  min-width: 280px;
  max-width: 280px;
}

.demo-control-panel.is-dragging {
  cursor: grabbing;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  transform: scale(1.02);
  z-index: 200;
}

.panel-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
  width: 100%;
}

.panel-header:active {
  cursor: grabbing;
}

.header-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.header-title-row {
  display: flex;
  align-items: center;
  width: 100%;
  padding-left: 0;
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: grab;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 0.8;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  min-width: 24px;
  min-height: 24px;
}

.drag-handle:hover {
  color: var(--text-primary);
  opacity: 1;
  background: rgba(255, 255, 255, 0.05);
}

.drag-handle.is-dragging {
  color: var(--abs-orange);
  opacity: 1;
  cursor: grabbing;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  margin-left: auto;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  max-width: 100%;
  overflow: visible;
}

/* State Dropdown */
.state-dropdown {
  position: relative;
  z-index: 10;
}

.state-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  max-width: fit-content;
}

.state-dropdown-trigger:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.state-dropdown-label {
  color: var(--text-primary);
  white-space: nowrap;
}

.dropdown-arrow {
  transition: transform 0.2s ease, opacity 0.2s ease;
  opacity: 0.7;
}

.dropdown-arrow.is-open {
  transform: rotate(180deg);
}

.state-dropdown-trigger:hover .dropdown-arrow {
  opacity: 1;
}

.state-dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 200px;
  min-width: 180px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

/* For compact mode, make dropdown narrower to fit within panel */
.panel-state--compact .state-dropdown-menu {
  width: 180px;
  min-width: 160px;
}

.state-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.state-dropdown-item:last-child {
  border-bottom: none;
}

.state-dropdown-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.state-dropdown-item.active {
  background: rgba(249, 115, 22, 0.1);
  color: var(--abs-orange);
}

.state-dropdown-item.active svg {
  color: var(--abs-orange);
}

.state-dropdown-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  text-align: left;
}

.state-name {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.state-description {
  font-family: var(--font-label);
  font-size: 0.7rem;
  color: var(--text-muted);
  opacity: 0.7;
}

.state-dropdown-item.active .state-name {
  color: var(--abs-orange);
}

.state-dropdown-item.active .state-description {
  color: var(--abs-orange);
  opacity: 0.9;
}

/* Dropdown animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}


.header-title-row {
  display: flex;
  align-items: center;
  width: 100%;
  padding-left: 0;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  overflow: visible;
  flex-shrink: 0;
  width: 100%;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  padding-right: 12px;
  border-right: 1px solid var(--border-subtle);
  margin-right: 0;
  margin-left: auto;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.loading-time {
  font-family: var(--font-mono);
  color: var(--abs-orange);
  font-weight: 600;
  font-size: 0.8rem;
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

.deactivate-button {
  width: 100%;
  padding: 10px 16px;
  margin-top: 8px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.deactivate-button:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--text-muted);
  color: var(--text-primary);
}

/* ============================================== */
/* NEW LAYOUT STYLES */
/* ============================================== */

.demo-control-panel.is-running {
  border-color: var(--abs-orange);
  border-width: 2px;
  animation: runningBorderGlow 2s ease-in-out infinite;
  /* Override subtle pulse when running */
}

@keyframes runningBorderGlow {
  0%, 100% {
    box-shadow: 
      var(--shadow-lg),
      0 0 0 2px rgba(249, 115, 22, 0.4),
      0 0 20px rgba(249, 115, 22, 0.3),
      0 0 40px rgba(249, 115, 22, 0.15);
  }
  50% {
    box-shadow: 
      var(--shadow-lg),
      0 0 0 2px rgba(249, 115, 22, 0.6),
      0 0 30px rgba(249, 115, 22, 0.5),
      0 0 60px rgba(249, 115, 22, 0.25);
  }
}

/* Active Model Section */
.active-model-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
  text-align: center;
}

.active-model-label {
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--status-success);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 4px;
}

.active-model-name {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.active-model-name.no-model {
  color: var(--text-muted);
  font-size: 1rem;
}

.active-model-name.active-model-name--error {
  color: var(--abs-warning, #e67e22);
  font-size: 0.9rem;
}

.active-model-section--compact {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.try-it-button--compact {
  margin-top: 12px;
  padding: 12px 16px;
  font-size: 0.8rem;
}

.quick-activate-button {
  width: 100%;
  padding: 10px 16px;
  margin-top: 12px;
  background: transparent;
  border: 1px solid var(--abs-orange);
  border-radius: 8px;
  color: var(--abs-orange);
  font-family: var(--font-label);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.quick-activate-button:hover {
  background: rgba(249, 115, 22, 0.1);
  border-color: var(--abs-orange);
  color: var(--abs-orange);
  transform: translateY(-1px);
}

/* Model Selector Section */
.model-selector-section {
  margin-bottom: 16px;
}

.load-error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  font-size: 0.8rem;
  color: var(--abs-warning, #e67e22);
  background: rgba(230, 126, 34, 0.1);
  border: 1px solid rgba(230, 126, 34, 0.3);
  border-radius: 8px;
}
.load-error-icon {
  flex-shrink: 0;
}

.section-label {
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}

.model-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.model-button {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: var(--abs-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-label);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.model-button:hover {
  background: var(--abs-card);
  border-color: var(--electric-indigo);
}

.model-button--active {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(249, 115, 22, 0.05));
  border-color: var(--abs-orange);
}

.model-button--pending {
  opacity: 0.7;
  border-color: var(--abs-orange);
}

.model-button--dual {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(99, 102, 241, 0.05));
  border-color: var(--electric-indigo);
}

.model-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.model-name {
  flex: 1;
}

.active-badge {
  font-size: 0.6rem;
  padding: 2px 6px;
  background: var(--abs-orange);
  color: white;
  border-radius: 4px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.active-badge--loading {
  background: var(--text-muted);
  animation: pulse-loading 1.2s ease-in-out infinite;
}

@keyframes pulse-loading {
  50% { opacity: 0.7; }
}

.model-button--warming {
  border-color: var(--text-muted);
}

.model-button--pulling {
  border-color: var(--abs-warning, #e67e22);
}

.active-badge--pulling {
  background: var(--abs-warning, #e67e22);
  color: #fff;
}

.switch-hint {
  font-size: 0.6rem;
  padding: 2px 6px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  border-radius: 4px;
  font-weight: 600;
  letter-spacing: 0.05em;
  transition: all 0.2s ease;
}

.model-button:hover .switch-hint {
  background: var(--electric-indigo);
  border-color: var(--electric-indigo);
  color: white;
}

.model-button:disabled {
  cursor: default;
  opacity: 1;
}

.model-button:disabled:hover {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(249, 115, 22, 0.05));
  border-color: var(--abs-orange);
  transform: none;
}

/* Compact state styles */
.compact-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
  margin-bottom: 12px;
}

.compact-metric {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-subtle);
  gap: 12px;
  min-width: 0;
}

.compact-metric:last-child {
  border-bottom: none;
}

.compact-metric-label {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.compact-metric-label {
  flex-shrink: 0;
  min-width: fit-content;
}

.compact-metric-value {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  flex-shrink: 0;
  white-space: nowrap;
  overflow: visible;
  text-align: right;
  min-width: fit-content;
}

.compact-metric-value--gpu {
  /* Base color - will be enhanced by inline style based on utilization */
  color: var(--abs-orange);
}

.collapse-button {
  width: 100%;
  padding: 8px 12px;
  margin-top: 12px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.collapse-button:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--text-muted);
  color: var(--text-primary);
}
</style>

