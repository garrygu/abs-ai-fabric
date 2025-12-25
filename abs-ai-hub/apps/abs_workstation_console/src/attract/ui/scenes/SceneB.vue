<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useModelsStore } from '@/stores/modelsStore'
import { useDemoControlStore } from '@/stores/demoControlStore'
import { useCESMode } from '@/composables/useCESMode'
import { useBloomEffect } from '@/composables/useBloomEffect'

const modelsStore = useModelsStore()
const demoControlStore = useDemoControlStore()
const { isCESMode } = useCESMode()
const containerRef = ref<HTMLElement | null>(null)
const { getElementGlow } = useBloomEffect()

// WebGPU particle field is rendered globally via AttractModeOverlay
// (removed legacy Canvas 2D fallback)


// Auto-expand right panel after a delay
const isRightPanelExpanded = ref(false)

// Highlighted card (for gravity effect)
const highlightedCardId = ref<string | null>(null)

// 3D card transforms (floating, breathing)
const cardTransforms = ref<Record<string, { x: number; y: number; z: number; rotation: number }>>({})
let cardAnimationFrame: ReturnType<typeof requestAnimationFrame> | null = null

// Digit-by-digit text animation for "70B"
const displayedSize = ref('')
const sizeAnimationComplete = ref(false)

onMounted(() => {
  // Expand panel after 2 seconds
  setTimeout(() => {
    isRightPanelExpanded.value = true
  }, 2000)
  
  // Initialize card transforms
  installedModels.value.forEach((model, index) => {
    cardTransforms.value[model.model_id] = {
      x: 0,
      y: Math.sin(index) * 5,
      z: 0,
      rotation: (index - 0.5) * 2
    }
  })
  
  // Animate cards (floating, breathing)
  const animateCards = () => {
    const time = Date.now() / 1000
    installedModels.value.forEach((model, index) => {
      const card = cardTransforms.value[model.model_id]
      if (card) {
        card.y = Math.sin(time * 0.5 + index) * 8
        card.z = Math.sin(time * 0.3 + index) * 3
        card.rotation = Math.sin(time * 0.2 + index) * 1
      }
    })
    cardAnimationFrame = requestAnimationFrame(animateCards)
  }
  animateCards()
  
  // Highlight first card after 1 second
  setTimeout(() => {
    if (installedModels.value.length > 0) {
      highlightedCardId.value = installedModels.value[0].model_id
    }
  }, 1000)
  
  // Digit-by-digit animation for "70B"
  setTimeout(() => {
    const digits = ['7', '0', 'B']
    let digitIndex = 0
    const digitInterval = setInterval(() => {
      if (digitIndex < digits.length) {
        displayedSize.value += digits[digitIndex]
        digitIndex++
      } else {
        clearInterval(digitInterval)
        sizeAnimationComplete.value = true
      }
    }, 300)
  }, 1500)
})

onUnmounted(() => {
  if (cardAnimationFrame !== null) {
    cancelAnimationFrame(cardAnimationFrame)
    cardAnimationFrame = null
  }
})

// Get installed models (focus on 70B models)
const installedModels = computed(() => {
  return modelsStore.models.filter(m => {
    const id = m.model_id.toLowerCase()
    // Focus on 70B models
    return (id.includes('deepseek') && (id.includes('70b') || id.includes('r1'))) ||
           (id.includes('llama') && id.includes('70b') && !id.includes('8b'))
  })
})

// Check if model is running
function isModelRunning(modelId: string): boolean {
  if (!demoControlStore.activeModel) return false
  
  const id = modelId.toLowerCase()
  const normalizedId = id.replace(/[:_]/g, '-')
  
  if (demoControlStore.activeModel === 'deepseek-r1-70b') {
    return normalizedId.includes('deepseek') && (normalizedId.includes('r1') || normalizedId.includes('70b'))
  }
  
  if (demoControlStore.activeModel === 'llama3-70b') {
    return normalizedId.includes('llama') && normalizedId.includes('70b') && !normalizedId.includes('8b')
  }
  
  if (demoControlStore.activeModel === 'dual') {
    return (normalizedId.includes('deepseek') && (normalizedId.includes('r1') || normalizedId.includes('70b'))) ||
           (normalizedId.includes('llama') && normalizedId.includes('70b') && !normalizedId.includes('8b'))
  }
  
  return false
}

function getModelStatus(modelId: string): 'RUNNING' | 'READY' | null {
  if (isModelRunning(modelId) && demoControlStore.modelStatus === 'running') {
    return 'RUNNING'
  }
  // Check if model is in ready state (simplified - would need to check actual lifecycle)
  return 'READY'
}

function getModelDisplayName(modelId: string): string {
  const model = modelsStore.models.find(m => m.model_id === modelId)
  return model?.display_name || modelId
}

// Get card transform style
function getCardTransform(modelId: string) {
  const transform = cardTransforms.value[modelId]
  if (!transform) return ''
  return `translate3d(${transform.x}px, ${transform.y}px, ${transform.z}px) rotateY(${transform.rotation}deg)`
}

// Check if card is highlighted
function isCardHighlighted(modelId: string): boolean {
  return highlightedCardId.value === modelId
}
</script>

<template>
  <div ref="containerRef" class="scene-b">
    <!-- GPU Particle Field Background (particles bend toward highlighted cards) -->
    
    <!-- Installed Models Grid -->
    <div class="scene-b__grid">
      <div
        v-for="model in installedModels"
        :key="model.model_id"
        class="model-card"
        :class="{ 
          'model-card--running': getModelStatus(model.model_id) === 'RUNNING',
          'model-card--highlighted': isCardHighlighted(model.model_id)
        }"
        :style="{ 
          transform: getCardTransform(model.model_id),
          ...(isCardHighlighted(model.model_id) ? getElementGlow('var(--abs-orange)', 0.8) : {})
        }"
      >
        <!-- Volumetric light effect -->
        <div v-if="isCardHighlighted(model.model_id)" class="model-card__volumetric-light"></div>
        
        <div class="model-card__badge" 
             v-if="getModelStatus(model.model_id)"
             :class="{ 'model-card__badge--running': getModelStatus(model.model_id) === 'RUNNING' }"
             :style="getModelStatus(model.model_id) === 'RUNNING' ? { ...getElementGlow('var(--status-success)', 1), background: 'var(--status-success)' } : {}">
          {{ getModelStatus(model.model_id) }}
        </div>
        <div class="model-card__name">{{ getModelDisplayName(model.model_id) }}</div>
        <div class="model-card__size">
          {{ isCardHighlighted(model.model_id) && !sizeAnimationComplete ? displayedSize : '70B' }}
        </div>
      </div>
    </div>
    
    <!-- Right-side panel (auto-expands) -->
    <div class="scene-b__right-panel" :class="{ 'scene-b__right-panel--expanded': isRightPanelExpanded }">
      <div class="panel-content">
        <div class="panel-title">Dual 70B Showcase</div>
        <div class="panel-subtitle">Try It Yourself</div>
        <div class="panel-note">(Disabled in attract mode)</div>
      </div>
    </div>
    
    <!-- Animated callouts -->
    <div class="scene-b__callouts">
      <div class="callout callout--primary">70B Models · Fully Local</div>
      <div class="callout callout--secondary">Enterprise-Validated</div>
    </div>
  </div>
</template>

<style scoped>
.scene-b {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--abs-black);
  padding: 100px;
}

.scene-b__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
  max-width: 800px;
}

.model-card {
  position: relative;
  padding: 48px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  transition: all 0.4s var(--ease-smooth);
  transform-style: preserve-3d;
  perspective: 1000px;
  backface-visibility: hidden;
}

.model-card--running {
  border-color: var(--abs-orange);
  background: rgba(249, 115, 22, 0.1);
}

.model-card--highlighted {
  border-color: var(--abs-orange);
  background: rgba(249, 115, 22, 0.15);
}

.model-card__volumetric-light {
  position: absolute;
  inset: -20px;
  background: radial-gradient(circle at center, rgba(249, 115, 22, 0.2) 0%, transparent 70%);
  border-radius: 16px;
  pointer-events: none;
  z-index: -1;
  animation: volumetric-pulse 2s ease-in-out infinite;
}

@keyframes volumetric-pulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
}

.model-card__badge {
  position: absolute;
  top: 20px;
  right: 20px;
  padding: 8px 20px;
  background: var(--abs-orange);
  color: var(--abs-black);
  font-family: var(--font-label);
  font-size: 1.25rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 6px;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 10px rgba(249, 115, 22, 0.5);
  }
  50% {
    box-shadow: 0 0 20px rgba(249, 115, 22, 0.8);
  }
}

.model-card__name {
  font-family: var(--font-label);
  font-size: 3rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.model-card__size {
  font-family: var(--font-mono);
  font-size: 2.5rem;
  color: var(--text-secondary);
}

.scene-b__right-panel {
  position: absolute;
  right: 80px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  overflow: hidden;
  transition: width 0.6s var(--ease-smooth);
}

.scene-b__right-panel--expanded {
  width: 300px;
}

.panel-content {
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.panel-title {
  font-family: var(--font-label);
  font-size: 2.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.panel-subtitle {
  font-family: var(--font-label);
  font-size: 1.75rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.panel-note {
  font-family: var(--font-label);
  font-size: 1rem;
  color: var(--text-muted);
  font-style: italic;
}

.scene-b__callouts {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.callout {
  font-family: var(--font-label);
  font-size: 2rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  animation: fade-in-up 0.6s var(--ease-smooth);
}

.callout--primary {
  color: var(--abs-orange);
  border-color: var(--abs-orange);
  animation-delay: 0.2s;
  animation-fill-mode: both;
}

.callout--secondary {
  color: var(--text-secondary);
  animation-delay: 0.4s;
  animation-fill-mode: both;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

