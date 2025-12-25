<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import HeroContextLayer from '@/components/explore/HeroContextLayer.vue'
import { useCESMode } from '@/composables/useCESMode'
import { useAttractModeStore } from '@/stores/attractModeStore'
import { useWorkloadsStore } from '@/stores/workloadsStore'
import { useModelsStore } from '@/stores/modelsStore'

const { isCESMode } = useCESMode()
const attractStore = useAttractModeStore()
const workloadsStore = useWorkloadsStore()
const modelsStore = useModelsStore()

const activeTab = ref<'models' | 'solutions'>('models')

// "Why this matters" expansion state
const expandedWhyId = ref<string | null>(null)

// Auto Highlight Tour state
// CES-only enhancement: runs in Regular Mode when someone is nearby but not interacting
// Stops when Showcase Mode activates (full-screen) or user interacts
const highlightedCardId = ref<string | null>(null)
const tourCaption = ref<string>('')
const isTourActive = ref(false)
const captionPosition = ref({ top: '0px', left: '0px', transform: 'translate(-50%, -100%)' })
let idleTimer: ReturnType<typeof setTimeout> | null = null
let tourInterval: ReturnType<typeof setInterval> | null = null
const lastActivityTime = ref(Date.now())
const IDLE_THRESHOLD_MS = 7000 // 7 seconds (6-8 seconds for passive attention)
const TOUR_CYCLE_MS = 7000 // 7 seconds per card (6-8 seconds range, as per spec)

// Model captions for tour - narrative story-driven (one sentence max)
const modelCaptions: Record<string, string> = {
  'zaurion-aqua': 'Designed for local 70B-parameter LLM inference — no cloud required.',
  'zaurion-duo-aqua': 'Multi-GPU systems optimized for parallel AI training workloads.',
  'zaurion-ruby': 'Enterprise air-gapped deployments for secure, offline AI processing.',
  'zaurion-duo-ruby': 'Dual-GPU architecture for high-throughput secure AI workloads.',
  'zaurion-pro': 'Enterprise AI at scale with quad-GPU configuration and 512GB ECC memory.'
}

// Solution captions for tour - narrative story-driven (one sentence max)
const solutionCaptions: Record<string, string> = {
  'ai-deep-learning': 'Train and deploy large language models locally with multi-GPU acceleration.',
  'engineering-cad': 'Professional CAD workflows and engineering simulation with GPU acceleration.',
  'content-creation': 'VFX and media production pipelines with real-time rendering capabilities.',
  'scientific-research': 'High-performance computing for big data analytics and scientific research.'
}

// "Why this matters" explanations (hidden by default, revealed on demand)
const whyThisMatters: Record<string, string> = {
  // Models
  'zaurion-aqua': 'Local LLM inference eliminates cloud dependency, reduces latency, and ensures data privacy. Perfect for enterprises that need AI capabilities without sending sensitive data to external services.',
  'zaurion-duo-aqua': 'Dual-GPU configuration enables parallel training workflows, cutting model training time in half. Essential for AI teams iterating on large models where time-to-insight matters.',
  'zaurion-ruby': 'Air-gapped deployment means your AI workloads run completely offline. Critical for defense, healthcare, and financial sectors where data sovereignty and compliance are non-negotiable.',
  'zaurion-duo-ruby': 'Combines multi-GPU performance with enterprise security. Enables high-throughput AI processing while maintaining strict data isolation—ideal for regulated industries.',
  'zaurion-pro': 'Quad-GPU setup with 512GB ECC memory handles the largest models and datasets. Enterprise-grade reliability ensures 24/7 operation for mission-critical AI workloads.',
  // Solutions
  'ai-deep-learning': 'Training large models requires massive parallel compute. Multi-GPU systems distribute the workload across GPUs, reducing training time from weeks to days. Local deployment means you own your models and data.',
  'engineering-cad': 'GPU acceleration transforms CAD workflows—complex assemblies render in real-time, simulations complete faster, and design iterations happen in minutes instead of hours. Professional GPUs ensure certification compliance.',
  'content-creation': 'Media production demands both speed and quality. Multi-GPU rendering enables concurrent workstreams—one GPU handles final renders while others process previews, compositing, and effects. Real-time previews eliminate guesswork.',
  'scientific-research': 'Big data analytics and scientific simulations require massive memory and parallel processing. High-core-count CPUs and multi-GPU configurations enable researchers to process datasets that were previously impossible to analyze locally.'
}

function toggleWhy(id: string) {
  expandedWhyId.value = expandedWhyId.value === id ? null : id
}

// Get currently running workload info for "proof" indicator
const currentRunningInfo = computed(() => {
  const active = workloadsStore.activeWorkloads
  if (active.length === 0) return null
  
  // Get the first active workload
  const workload = active[0]
  const appName = workload.app_name
  
  // Try to get model info from associated models
  let modelInfo = ''
  if (workload.associated_models && workload.associated_models.length > 0) {
    const modelName = workload.associated_models[0]
    // Try to find model size/type from models store
    const model = modelsStore.models.find(m => 
      m.display_name.toLowerCase().includes(modelName.toLowerCase()) || 
      modelName.toLowerCase().includes(m.display_name.toLowerCase())
    )
    if (model) {
      // Format like "70B" or "Llama 3 70B"
      const sizeMatch = model.display_name.match(/(\d+B|\d+GB)/i)
      modelInfo = sizeMatch ? ` (${sizeMatch[1]})` : ` (${model.display_name})`
    } else {
      modelInfo = ` (${modelName})`
    }
  }
  
  return {
    appName,
    modelInfo,
    fullText: `Currently running on this workstation → ${appName}${modelInfo}`
  }
})

// All cards (models + solutions) for tour
const allTourCards = computed(() => {
  if (activeTab.value === 'models') {
    return workstationModels.map(m => ({ id: m.id, type: 'model' as const }))
  } else {
    return solutions.map(s => ({ id: s.id, type: 'solution' as const }))
  }
})

// Get caption for current card
// Get caption for current card (narrative story-driven, one sentence max)
function getCardCaption(cardId: string, type: 'model' | 'solution'): string {
  if (type === 'model') {
    return modelCaptions[cardId] || 'Professional workstation designed for demanding workloads.'
  } else {
    return solutionCaptions[cardId] || 'Optimized solution for enterprise computing needs.'
  }
}

// Record activity (user interaction)
function recordActivity() {
  lastActivityTime.value = Date.now()
  if (isTourActive.value) {
    stopTour()
  }
  // Reset idle timer
  if (idleTimer) {
    clearTimeout(idleTimer)
  }
  idleTimer = setTimeout(checkIdle, IDLE_THRESHOLD_MS)
}

// Check if should start tour
// Only runs in CES mode, when NOT in Showcase Mode (Regular Mode only)
function checkIdle() {
  // Don't start if Showcase Mode is active (we're in full-screen mode)
  if (attractStore.isActive) {
    stopTour()
    return
  }
  
  // Only run in CES mode
  if (!isCESMode.value) {
    console.log('[Auto Highlight Tour] CES mode is disabled')
    return
  }
  
  const idleTime = Date.now() - lastActivityTime.value
  const shouldStart = idleTime >= IDLE_THRESHOLD_MS && 
                      !isTourActive.value &&
                      !attractStore.isActive && // Ensure Showcase Mode is not active
                      allTourCards.value.length > 0
  
  console.log('[Auto Highlight Tour] Check idle:', {
    idleTime: Math.round(idleTime / 1000) + 's',
    threshold: Math.round(IDLE_THRESHOLD_MS / 1000) + 's',
    isCESMode: isCESMode.value,
    isShowcaseMode: attractStore.isActive,
    isTourActive: isTourActive.value,
    cardsCount: allTourCards.value.length,
    shouldStart
  })
  
  if (shouldStart) {
    console.log('[Auto Highlight Tour] Starting tour...')
    startTour()
  }
}

// Start the auto highlight tour
function startTour() {
  if (isTourActive.value || allTourCards.value.length === 0) {
    console.log('[Auto Highlight Tour] Cannot start:', { isTourActive: isTourActive.value, cardsCount: allTourCards.value.length })
    return
  }
  
  console.log('[Auto Highlight Tour] Tour started!')
  isTourActive.value = true
  highlightedCardId.value = null
  tourCaption.value = ''
  
  let currentIndex = 0
  
  function highlightNext() {
    // Safety check: stop if Showcase Mode activated (we're going full-screen)
    if (!isTourActive.value || attractStore.isActive) {
      stopTour()
      return
    }
    
    // Clear previous highlight first
    highlightedCardId.value = null
    tourCaption.value = ''
    
    // Small delay to ensure previous highlight is cleared
    setTimeout(() => {
      if (!isTourActive.value || attractStore.isActive) {
        stopTour()
        return
      }
      
      const card = allTourCards.value[currentIndex]
      highlightedCardId.value = card.id
      tourCaption.value = getCardCaption(card.id, card.type)
      
      console.log('[Auto Highlight Tour] Highlighting card:', card.id, 'Caption:', tourCaption.value)
      
      // Scroll card into view smoothly and calculate caption position
      const cardElement = document.querySelector(`[data-model-id="${card.id}"], .solution-card--${card.id}`)
      if (cardElement) {
        cardElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        
        // Calculate caption position relative to the card
        setTimeout(() => {
          const rect = cardElement.getBoundingClientRect()
          const viewportHeight = window.innerHeight
          const captionHeight = 60 // Approximate caption height with padding
          const spacing = 20 // Spacing from card
          
          // Check if there's enough space above the card
          const spaceAbove = rect.top
          const spaceBelow = viewportHeight - rect.bottom
          
          // Position caption above if there's space, otherwise below
          let top: number
          let transform: string
          
          if (spaceAbove >= captionHeight + spacing) {
            // Position above the card
            top = rect.top - spacing
            transform = 'translate(-50%, -100%)'
          } else if (spaceBelow >= captionHeight + spacing) {
            // Position below the card
            top = rect.bottom + spacing
            transform = 'translate(-50%, 0)'
          } else {
            // Not enough space above or below, position at top of viewport
            top = Math.max(20, rect.top - spacing)
            transform = 'translate(-50%, -100%)'
          }
          
          captionPosition.value = {
            top: `${top}px`,
            left: `${rect.left + rect.width / 2}px`,
            transform: transform
          }
        }, 300) // Wait for scroll animation to complete
      } else {
        console.warn('[Auto Highlight Tour] Card element not found:', card.id)
      }
      
      currentIndex = (currentIndex + 1) % allTourCards.value.length
    }, 100) // Brief delay to clear previous highlight
  }
  
  // Start immediately
  highlightNext()
  
  // Then cycle
  tourInterval = setInterval(highlightNext, TOUR_CYCLE_MS)
}

// Stop the tour
function stopTour() {
  isTourActive.value = false
  highlightedCardId.value = null
  tourCaption.value = ''
  captionPosition.value = { top: '0px', left: '0px', transform: 'translate(-50%, -100%)' }
  if (tourInterval) {
    clearInterval(tourInterval)
    tourInterval = null
  }
}

// Watch for tab changes - restart tour if needed
watch(activeTab, () => {
  if (isTourActive.value) {
    stopTour()
    setTimeout(() => {
      if (Date.now() - lastActivityTime.value >= IDLE_THRESHOLD_MS) {
        startTour()
      }
    }, 500)
  }
})

// Watch for Showcase Mode changes
// When Showcase Mode activates (full-screen), stop the tour immediately
// When Showcase Mode deactivates, the tour can restart if still idle
watch(() => attractStore.isActive, (isActive) => {
  if (isActive) {
    // Showcase Mode activated - stop tour (we're going full-screen)
    stopTour()
  } else {
    // Showcase Mode deactivated - check if we should restart tour (if still idle)
    if (isCESMode.value && Date.now() - lastActivityTime.value >= IDLE_THRESHOLD_MS) {
      setTimeout(checkIdle, 500)
    }
  }
})

onMounted(() => {
  console.log('[Auto Highlight Tour] Mounted. CES Mode:', isCESMode.value, 'Showcase Mode:', attractStore.isActive)
  
  // Fetch workloads and models for "currently running" indicator
  if (workloadsStore.workloads.length === 0) {
    workloadsStore.fetchWorkloads()
  }
  if (modelsStore.models.length === 0) {
    modelsStore.fetchModels()
  }
  
  // Set up activity listeners
  const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'wheel', 'click']
  events.forEach(event => {
    window.addEventListener(event, recordActivity, { passive: true })
  })
  
  // Start idle detection
  console.log('[Auto Highlight Tour] Starting idle detection, will check after', IDLE_THRESHOLD_MS / 1000, 'seconds')
  idleTimer = setTimeout(checkIdle, IDLE_THRESHOLD_MS)
})

onUnmounted(() => {
  // Clean up
  stopTour()
  if (idleTimer) {
    clearTimeout(idleTimer)
  }
  
  const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'wheel', 'click']
  events.forEach(event => {
    window.removeEventListener(event, recordActivity)
  })
})

const workstationModels = [
  {
    id: 'zaurion-aqua',
    name: 'Zaurion Aqua',
    tier: 'Professional',
    gpu: '1x RTX Pro 6000 Blackwell',
    gpuDetails: '96GB GDDR7',
    cpu: 'Intel Xeon W5-2455X / W7-2495X',
    ram: 'Up to 128GB DDR5',
    storage: '2TB NVMe SSD + 4TB SSD',
    bestFor: 'AI workloads, engineering simulation (CFD, FEA), high-end 3D rendering, scientific research',
    capabilities: ['LLM Ready', 'Local AI'],
    neweggUrl: 'https://www.newegg.com/abs-zaurion-aqua-zaw5-2455x-rp6000-tower/p/N82E16859991004',
    featured: false
  },
  {
    id: 'zaurion-duo-aqua',
    name: 'Zaurion Duo Aqua',
    tier: 'Professional',
    gpu: '2x RTX Pro 6000 Blackwell MaxQ',
    gpuDetails: '96GB each',
    cpu: 'Intel Xeon W5/W7 series',
    ram: '64GB–128GB DDR5',
    storage: '1TB–2TB NVMe + 2–4TB SSD',
    bestFor: 'Extreme scale AI training, multi-GPU rendering (film/VFX), engineering simulation',
    capabilities: ['LLM Ready', 'Multi-GPU', 'Local AI'],
    neweggUrl: 'https://www.newegg.com/abs-zaurion-duo-aqua-zaw5-2455x-rp6000mq-tower/p/N82E16859991008',
    featured: false
  },
  {
    id: 'zaurion-ruby',
    name: 'Zaurion Ruby',
    tier: 'Professional',
    gpu: '1x RTX Pro 6000 Blackwell',
    gpuDetails: '96GB GDDR7',
    cpu: 'AMD Threadripper Pro 7975WX',
    ram: 'Up to 128GB DDR5',
    storage: '2TB NVMe + 4TB SSD',
    bestFor: 'HPC applications, scientific computing, engineering, AI research with high parallelism',
    capabilities: ['LLM Ready', 'Local AI', 'Air-Gap Capable'],
    neweggUrl: 'https://www.newegg.com/p/59-991-006',
    featured: false
  },
  {
    id: 'zaurion-duo-ruby',
    name: 'Zaurion Duo Ruby',
    tier: 'Professional',
    gpu: '2x RTX Pro 6000 Blackwell MaxQ',
    gpuDetails: '96GB each',
    cpu: 'AMD Threadripper Pro 7975WX',
    ram: 'Up to 128GB DDR5',
    storage: '2TB NVMe + 4TB SSD',
    bestFor: 'Dual-GPU deep learning, real-time production, rendering, high-throughput simulations',
    capabilities: ['LLM Ready', 'Multi-GPU', 'Local AI', 'Air-Gap Capable'],
    neweggUrl: 'https://www.newegg.com/p/59-991-010',
    featured: false
  },
  {
    id: 'zaurion-pro',
    name: 'Zaurion Pro',
    tier: 'Enterprise',
    gpu: '4x NVIDIA RTX 6000 Ada Generation',
    gpuDetails: '48GB each',
    cpu: 'Intel Xeon W5-3535X (20 cores)',
    ram: '512GB DDR5 ECC',
    storage: '2TB NVMe + 2TB AI Acceleration (aiDAPTIVCache) + 4x 2TB SATA SSD',
    bestFor: 'Enterprise AI/ML, LLM training, generative AI, big data analytics, studio pipeline',
    specialFeature: 'PHISON aiDAPTIV+ AI optimization software',
    capabilities: ['LLM Ready', 'Multi-GPU', 'Local AI', 'Air-Gap Capable', 'Enterprise AI'],
    neweggUrl: 'https://www.newegg.com/p/83-367-003',
    featured: true
  }
]

const solutions = [
  {
    id: 'ai-deep-learning',
    title: 'AI & Deep Learning',
    description: 'Train and deploy large models with multi-GPU performance',
    features: [
      'Multi-GPU configurations for parallel training',
      'CUDA-optimized software stacks',
      'Large memory capacity for big models',
      'Distributed training across GPUs',
      'Local LLM deployment and inference'
    ],
    useCases: [
      'Large language model training and fine-tuning',
      'Computer vision and image recognition',
      'Reinforcement learning experiments',
      'Deep learning research and development',
      'AI model inference at scale'
    ],
    recommendedModels: ['zaurion-pro', 'zaurion-duo-aqua', 'zaurion-duo-ruby']
  },
  {
    id: 'engineering-cad',
    title: 'Engineering / CAD / Simulation',
    description: 'High-performance workstations for design and simulation',
    features: [
      'Professional GPU acceleration for CAD workflows',
      'High core-count CPUs for simulation',
      'Optimized for SOLIDWORKS, AutoCAD, ANSYS',
      'Real-time visualization and rendering',
      'Stable performance for long-running simulations'
    ],
    useCases: [
      'CAD design and modeling',
      'CFD and FEA simulation',
      'Engineering visualization',
      'Product design and prototyping',
      'Technical computing and analysis'
    ],
    recommendedModels: ['zaurion-aqua', 'zaurion-ruby']
  },
  {
    id: 'content-creation',
    title: 'Content Creation / Media',
    description: 'Professional workstations for creative production',
    features: [
      'Multi-GPU configurations for concurrent rendering',
      'Real-time rendering and preview',
      'High-resolution video processing',
      'Studio pipeline acceleration',
      'Optimized storage for media workflows'
    ],
    useCases: [
      'VFX and animation production',
      'Multi-stream video editing',
      'Complex motion graphics',
      'Professional photo editing',
      'Virtual production and real-time rendering'
    ],
    recommendedModels: ['zaurion-pro', 'zaurion-duo-aqua', 'zaurion-duo-ruby', 'zaurion-aqua', 'zaurion-ruby']
  },
  {
    id: 'scientific-research',
    title: 'Scientific Research / Big Data',
    description: 'High-performance computing for research and analytics',
    features: [
      'High memory capacity (up to 512GB ECC)',
      'Multi-GPU configurations for parallel computing',
      'High thread/core count for data processing',
      'Optimized for scientific workloads',
      'Scalable GPU compute for large datasets'
    ],
    useCases: [
      'Genomics and bioinformatics',
      'Big data analytics and visualization',
      'Scientific simulations',
      'Data exploration and analysis',
      'HPC and research computing'
    ],
    recommendedModels: ['zaurion-pro', 'zaurion-ruby', 'zaurion-duo-ruby']
  }
]

function openNewegg(modelId: string) {
  const model = workstationModels.find(m => m.id === modelId)
  if (model?.neweggUrl) {
    window.open(model.neweggUrl + '?utm_source=console&utm_campaign=explore', '_blank')
  }
}

function openContact() {
  window.open('https://absworkstation.com/contact?utm_source=console&utm_campaign=explore', '_blank')
}

function navigateToModel(modelId: string) {
  activeTab.value = 'models'
  setTimeout(() => {
    const el = document.querySelector(`[data-model-id='${modelId}']`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, 100)
}

function getModelById(id: string) {
  return workstationModels.find(m => m.id === id)
}
</script>

<template>
  <div class="page page-explore">
    <!-- Hero Context Layer - Animated Background -->
    <HeroContextLayer />
    
    <div class="page-content">
    <div class="page-header">
      <p class="page-subtitle">Explore the ABS Workstation lineup</p>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button 
        class="tab-button"
        :class="{ 'tab-button--active': activeTab === 'models' }"
        @click="activeTab = 'models'"
      >
        Workstation Models
      </button>
      <button 
        class="tab-button"
        :class="{ 'tab-button--active': activeTab === 'solutions' }"
        @click="activeTab = 'solutions'"
      >
        Solutions by Workload
      </button>
    </div>

    <!-- Models Tab -->
    <div v-if="activeTab === 'models'" class="tab-content">
      <div class="models-grid">
        <div 
          v-for="model in workstationModels" 
          :key="model.id"
          :data-model-id="model.id"
          class="model-card"
          :class="{ 
            'model-card--featured': model.featured,
            'model-card--highlighted': isTourActive && highlightedCardId === model.id
          }"
        >
          <div v-if="model.featured" class="featured-badge">ENTERPRISE</div>
          <div class="model-header">
            <div class="model-tier">{{ model.tier }}</div>
            <div class="gpu-icon">⚡</div>
          </div>
          <h3 class="model-name">{{ model.name }}</h3>
          
          <!-- Currently Running Indicator (shown during tour on highlighted cards) -->
          <!-- Hidden until workloads are available -->
          <!--
          <Transition name="fade-in">
            <div 
              v-if="isTourActive && highlightedCardId === model.id && currentRunningInfo" 
              class="currently-running-indicator"
            >
              <span class="running-icon">●</span>
              <span class="running-text">{{ currentRunningInfo.fullText }}</span>
            </div>
          </Transition>
          -->
          
          <!-- Live Capability Badges -->
          <div class="capability-badges">
            <span 
              v-for="capability in model.capabilities" 
              :key="capability"
              class="capability-badge"
              :class="`capability-badge--${capability.toLowerCase().replace(/\s+/g, '-')}`"
            >
              {{ capability }}
            </span>
          </div>
          
          <!-- Orange accent bar -->
          <div class="model-accent-bar"></div>
          
          <div class="model-specs">
            <div class="spec-row spec-row--gpu">
            <span class="spec-label">GPU</span>
              <div class="spec-value-group">
                <span class="spec-value">{{ model.gpu }}</span>
                <span class="spec-detail">{{ model.gpuDetails }}</span>
              </div>
            </div>
            <div class="spec-row spec-row--cpu">
              <span class="spec-label">CPU</span>
              <span class="spec-value">{{ model.cpu }}</span>
            </div>
            <div class="spec-row spec-row--ram">
              <span class="spec-label">RAM</span>
              <span class="spec-value">{{ model.ram }}</span>
            </div>
            <div class="spec-row spec-row--storage">
              <span class="spec-label">Storage</span>
              <span class="spec-value">{{ model.storage }}</span>
            </div>
            <div v-if="model.specialFeature" class="spec-row spec-row--special">
              <span class="spec-label">Special</span>
              <span class="spec-value spec-value--special">{{ model.specialFeature }}</span>
            </div>
          </div>

          <div class="model-best-for">
            <span class="best-for-label">Best For:</span>
            <span class="best-for-text">{{ model.bestFor }}</span>
          </div>

          <!-- "Why this matters" inline expansion -->
          <div class="why-this-matters">
            <button 
              class="learn-why-link"
              @click="toggleWhy(model.id)"
              :aria-expanded="expandedWhyId === model.id"
            >
              <span v-if="expandedWhyId !== model.id">Learn why</span>
              <span v-else>Hide</span>
              <span class="learn-why-icon">{{ expandedWhyId === model.id ? '▲' : '▼' }}</span>
            </button>
            <Transition name="why-expand">
              <div v-if="expandedWhyId === model.id" class="why-content">
                <p class="why-text">{{ whyThisMatters[model.id] || 'This workstation is optimized for demanding professional workloads.' }}</p>
              </div>
            </Transition>
          </div>

          <div class="model-actions">
            <button 
              class="action-button action-button--primary"
              @click="openNewegg(model.id)"
            >
              View on Newegg
            </button>
            <button 
              class="action-button action-button--secondary"
              @click="openContact"
            >
              Get Quote
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Solutions Tab -->
    <div v-if="activeTab === 'solutions'" class="tab-content">
      <div class="solutions-grid">
        <div 
          v-for="solution in solutions" 
          :key="solution.id"
          class="solution-card"
          :class="[
            `solution-card--${solution.id}`,
            {
              'solution-card--highlighted': isTourActive && highlightedCardId === solution.id
            }
          ]"
        >
          <!-- Background Illustration -->
          <div class="solution-illustration" :class="`solution-illustration--${solution.id}`">
            <!-- AI Nodes for AI & Deep Learning -->
            <svg v-if="solution.id === 'ai-deep-learning'" class="illustration-svg" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
              <!-- Neural network nodes -->
              <circle cx="80" cy="60" r="8" fill="currentColor"/>
              <circle cx="160" cy="40" r="8" fill="currentColor"/>
              <circle cx="240" cy="60" r="8" fill="currentColor"/>
              <circle cx="320" cy="50" r="8" fill="currentColor"/>
              <circle cx="100" cy="140" r="8" fill="currentColor"/>
              <circle cx="200" cy="130" r="8" fill="currentColor"/>
              <circle cx="300" cy="140" r="8" fill="currentColor"/>
              <circle cx="150" cy="220" r="8" fill="currentColor"/>
              <circle cx="250" cy="220" r="8" fill="currentColor"/>
              <!-- Connections -->
              <line x1="80" y1="60" x2="160" y2="40" stroke="currentColor" stroke-width="1"/>
              <line x1="160" y1="40" x2="240" y2="60" stroke="currentColor" stroke-width="1"/>
              <line x1="240" y1="60" x2="320" y2="50" stroke="currentColor" stroke-width="1"/>
              <line x1="80" y1="60" x2="100" y2="140" stroke="currentColor" stroke-width="1"/>
              <line x1="160" y1="40" x2="200" y2="130" stroke="currentColor" stroke-width="1"/>
              <line x1="240" y1="60" x2="300" y2="140" stroke="currentColor" stroke-width="1"/>
              <line x1="100" y1="140" x2="150" y2="220" stroke="currentColor" stroke-width="1"/>
              <line x1="200" y1="130" x2="150" y2="220" stroke="currentColor" stroke-width="1"/>
              <line x1="200" y1="130" x2="250" y2="220" stroke="currentColor" stroke-width="1"/>
              <line x1="300" y1="140" x2="250" y2="220" stroke="currentColor" stroke-width="1"/>
            </svg>
            
            <!-- CAD Wireframes for Engineering -->
            <svg v-if="solution.id === 'engineering-cad'" class="illustration-svg" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
              <!-- 3D wireframe cube -->
              <path d="M 100 80 L 180 50 L 180 130 L 100 160 Z" fill="none" stroke="currentColor" stroke-width="1"/>
              <path d="M 180 50 L 260 80 L 260 160 L 180 130 Z" fill="none" stroke="currentColor" stroke-width="1"/>
              <path d="M 100 160 L 180 130 L 260 160 L 180 190 Z" fill="none" stroke="currentColor" stroke-width="1"/>
              <line x1="100" y1="80" x2="100" y2="160" stroke="currentColor" stroke-width="1"/>
              <line x1="180" y1="50" x2="180" y2="130" stroke="currentColor" stroke-width="1"/>
              <line x1="260" y1="80" x2="260" y2="160" stroke="currentColor" stroke-width="1"/>
              <!-- Grid lines -->
              <line x1="50" y1="200" x2="350" y2="200" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2,2"/>
              <line x1="50" y1="230" x2="350" y2="230" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2,2"/>
              <line x1="50" y1="260" x2="350" y2="260" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2,2"/>
              <line x1="100" y1="180" x2="100" y2="280" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2,2"/>
              <line x1="200" y1="180" x2="200" y2="280" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2,2"/>
              <line x1="300" y1="180" x2="300" y2="280" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2,2"/>
            </svg>
            
            <!-- Camera / Timeline for Content -->
            <svg v-if="solution.id === 'content-creation'" class="illustration-svg" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
              <!-- Camera body -->
              <rect x="120" y="80" width="80" height="60" rx="4" fill="none" stroke="currentColor" stroke-width="1"/>
              <rect x="200" y="90" width="40" height="40" rx="2" fill="none" stroke="currentColor" stroke-width="1"/>
              <circle cx="140" cy="110" r="12" fill="none" stroke="currentColor" stroke-width="1"/>
              <circle cx="140" cy="110" r="6" fill="currentColor"/>
              <!-- Timeline -->
              <rect x="60" y="180" width="280" height="4" fill="currentColor"/>
              <rect x="80" y="175" width="3" height="14" fill="currentColor"/>
              <rect x="120" y="175" width="3" height="14" fill="currentColor"/>
              <rect x="160" y="175" width="3" height="14" fill="currentColor"/>
              <rect x="200" y="175" width="3" height="14" fill="currentColor"/>
              <rect x="240" y="175" width="3" height="14" fill="currentColor"/>
              <rect x="280" y="175" width="3" height="14" fill="currentColor"/>
              <rect x="320" y="175" width="3" height="14" fill="currentColor"/>
              <!-- Playhead -->
              <polygon points="200,170 200,190 210,180" fill="currentColor"/>
              <!-- Waveform -->
              <path d="M 80 240 Q 100 220, 120 240 T 160 240 T 200 240 T 240 240 T 280 240 T 320 240" fill="none" stroke="currentColor" stroke-width="1"/>
              <path d="M 80 260 Q 100 250, 120 260 T 160 260 T 200 260 T 240 260 T 280 260 T 320 260" fill="none" stroke="currentColor" stroke-width="1"/>
            </svg>
            
            <!-- Data Grids for Research -->
            <svg v-if="solution.id === 'scientific-research'" class="illustration-svg" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
              <!-- Data grid -->
              <rect x="60" y="60" width="280" height="180" fill="none" stroke="currentColor" stroke-width="1"/>
              <!-- Grid lines -->
              <line x1="60" y1="100" x2="340" y2="100" stroke="currentColor" stroke-width="0.5"/>
              <line x1="60" y1="140" x2="340" y2="140" stroke="currentColor" stroke-width="0.5"/>
              <line x1="60" y1="180" x2="340" y2="180" stroke="currentColor" stroke-width="0.5"/>
              <line x1="60" y1="220" x2="340" y2="220" stroke="currentColor" stroke-width="0.5"/>
              <line x1="120" y1="60" x2="120" y2="240" stroke="currentColor" stroke-width="0.5"/>
              <line x1="180" y1="60" x2="180" y2="240" stroke="currentColor" stroke-width="0.5"/>
              <line x1="240" y1="60" x2="240" y2="240" stroke="currentColor" stroke-width="0.5"/>
              <line x1="300" y1="60" x2="300" y2="240" stroke="currentColor" stroke-width="0.5"/>
              <!-- Data points -->
              <circle cx="90" cy="80" r="3" fill="currentColor"/>
              <circle cx="150" cy="80" r="3" fill="currentColor"/>
              <circle cx="210" cy="80" r="3" fill="currentColor"/>
              <circle cx="270" cy="80" r="3" fill="currentColor"/>
              <circle cx="90" cy="120" r="3" fill="currentColor"/>
              <circle cx="150" cy="120" r="3" fill="currentColor"/>
              <circle cx="210" cy="120" r="3" fill="currentColor"/>
              <circle cx="270" cy="120" r="3" fill="currentColor"/>
              <circle cx="90" cy="160" r="3" fill="currentColor"/>
              <circle cx="150" cy="160" r="3" fill="currentColor"/>
              <circle cx="210" cy="160" r="3" fill="currentColor"/>
              <circle cx="270" cy="160" r="3" fill="currentColor"/>
              <!-- Chart bars -->
              <rect x="80" y="200" width="20" height="30" fill="currentColor"/>
              <rect x="110" y="200" width="20" height="25" fill="currentColor"/>
              <rect x="140" y="200" width="20" height="35" fill="currentColor"/>
              <rect x="170" y="200" width="20" height="20" fill="currentColor"/>
              <rect x="200" y="200" width="20" height="40" fill="currentColor"/>
              <rect x="230" y="200" width="20" height="28" fill="currentColor"/>
              <rect x="260" y="200" width="20" height="32" fill="currentColor"/>
            </svg>
          </div>
          
          <h3 class="solution-title">{{ solution.title }}</h3>
          <p class="solution-description">{{ solution.description }}</p>
          
          <div class="solution-section">
            <h4 class="solution-section-title">Key Features</h4>
            <ul class="solution-list">
              <li v-for="feature in solution.features" :key="feature">{{ feature }}</li>
            </ul>
          </div>

          <div class="solution-section">
            <h4 class="solution-section-title">Use Cases</h4>
            <ul class="solution-list">
              <li v-for="useCase in solution.useCases" :key="useCase">{{ useCase }}</li>
            </ul>
          </div>

          <div class="solution-section">
            <h4 class="solution-section-title">Recommended Models</h4>
            <div class="recommended-models">
              <button
                v-for="modelId in solution.recommendedModels"
                :key="modelId"
                class="model-chip"
                @click="navigateToModel(modelId)"
              >
                {{ getModelById(modelId)?.name }}
              </button>
            </div>
          </div>

          <!-- "Why this matters" inline expansion -->
          <div class="why-this-matters">
            <button 
              class="learn-why-link"
              @click="toggleWhy(solution.id)"
              :aria-expanded="expandedWhyId === solution.id"
            >
              <span>{{ expandedWhyId === solution.id ? 'Hide' : 'Learn why' }}</span>
              <span class="learn-why-icon">{{ expandedWhyId === solution.id ? '▲' : '▼' }}</span>
            </button>
            <Transition name="why-expand">
              <div v-if="expandedWhyId === solution.id" class="why-content">
                <p class="why-text">{{ whyThisMatters[solution.id] || 'This solution is optimized for specific enterprise computing needs.' }}</p>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>

    <!-- CTA Section -->
    <div class="cta-section">
      <button class="cta-button" @click="openContact">
        Contact Our Team for Custom Configuration
        <span class="cta-arrow">→</span>
      </button>
    </div>
    </div>
    
    <!-- Auto Highlight Tour Caption Overlay -->
    <Transition name="fade-caption">
      <div 
        v-if="isTourActive && tourCaption" 
        class="tour-caption-overlay"
        :style="{ 
          top: captionPosition.top, 
          left: captionPosition.left,
          transform: captionPosition.transform
        }"
      >
        <span class="tour-caption-text">{{ tourCaption }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.page-explore {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  background: var(--abs-black);
}

.page-content {
  position: relative;
  z-index: 1;
  padding: 40px 24px;
  max-width: var(--container-max);
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}

.page-title {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Tabs */
.tabs {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0;
  position: relative;
  z-index: 1;
}

.tab-button {
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
  margin-bottom: -1px;
}

.tab-button:hover {
  color: var(--text-primary);
}

.tab-button--active {
  color: var(--electric-indigo);
  border-bottom-color: var(--electric-indigo);
}

/* Models Grid */
.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
  position: relative;
  z-index: 1;
}

.model-card {
  padding: 32px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  position: relative;
  transition: all var(--duration-normal) var(--ease-smooth);
  display: flex;
  flex-direction: column;
  z-index: 1;
  backdrop-filter: blur(1px);
  overflow: visible; /* Changed from hidden to allow featured badge to show */
}

.model-card:hover {
  border-color: var(--border-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Auto Highlight Tour - Subtle highlight effect */
/* Only apply when tour is active AND this specific card is highlighted */
.model-card.model-card--highlighted {
  border-color: var(--abs-orange) !important;
  box-shadow: 0 0 20px rgba(255, 107, 0, 0.3), var(--shadow-md) !important;
  transform: translateY(-2px) scale(1.02); /* Slight scale when highlighted */
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  animation: highlight-pulse 7s ease-in-out infinite; /* Slow pulsing border glow (7s cycle) */
}

@keyframes highlight-pulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(255, 107, 0, 0.3), var(--shadow-md);
  }
  50% {
    box-shadow: 0 0 30px rgba(255, 107, 0, 0.5), var(--shadow-md);
  }
}

/* Ensure other cards don't have the highlight */
.model-card:not(.model-card--highlighted) {
  border-color: var(--border-subtle);
  box-shadow: none;
}

.model-card:hover .gpu-icon {
  animation: gpu-pulse 1.5s ease-in-out infinite;
}

.model-card:hover .model-accent-bar {
  animation: accent-slide-up 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* On hover/focus, hide all specs first, then reveal them one by one */
.model-card:hover .spec-row,
.model-card:focus-within .spec-row {
  opacity: 0;
  transform: translateX(-10px) scale(2);
  animation: spec-slide-in 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.model-card:hover .spec-row--gpu,
.model-card:focus-within .spec-row--gpu {
  animation-delay: 0.2s;
}

.model-card:hover .spec-row--cpu,
.model-card:focus-within .spec-row--cpu {
  animation-delay: 0.6s;
}

.model-card:hover .spec-row--ram,
.model-card:focus-within .spec-row--ram {
  animation-delay: 1.0s;
}

.model-card:hover .spec-row--storage,
.model-card:focus-within .spec-row--storage {
  animation-delay: 1.4s;
}

.model-card:hover .spec-row--special,
.model-card:focus-within .spec-row--special {
  animation-delay: 1.8s;
}

.model-card--featured {
  border-color: var(--abs-orange);
  box-shadow: 0 0 30px rgba(249, 115, 22, 0.15);
}

.featured-badge {
  position: absolute;
  top: -12px;
  right: 24px;
  padding: 6px 14px;
  background: var(--abs-orange);
  color: white;
  font-family: var(--font-label);
  font-size: 0.65rem;
  z-index: 10; /* Ensure badge appears above other elements */
  white-space: nowrap; /* Prevent text wrapping */
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-radius: 12px;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.model-tier {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.gpu-icon {
  font-size: 1.5rem;
  opacity: 0.6;
  transition: opacity var(--duration-normal) var(--ease-smooth);
  filter: drop-shadow(0 0 4px rgba(249, 115, 22, 0.3));
}

.model-card:hover .gpu-icon {
  opacity: 1;
  filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.6));
}

.model-accent-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--abs-orange), transparent);
  transform: translateY(100%);
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-smooth);
}

.model-card--featured .model-tier {
  color: var(--abs-orange);
}

.model-name {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 16px;
}

.capability-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 20px;
}

.capability-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 12px;
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  line-height: 1;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.capability-badge--llm-ready {
  background: rgba(249, 115, 22, 0.12);
  border-color: rgba(249, 115, 22, 0.25);
  color: var(--abs-orange);
}

.capability-badge--multi-gpu {
  background: rgba(139, 92, 246, 0.12);
  border-color: rgba(139, 92, 246, 0.25);
  color: #8b5cf6;
}

.capability-badge--local-ai {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.25);
  color: var(--status-success);
}

.capability-badge--air-gap-capable {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.25);
  color: #3b82f6;
}

.capability-badge--enterprise-ai {
  background: rgba(249, 115, 22, 0.18);
  border-color: rgba(249, 115, 22, 0.35);
  color: var(--abs-orange);
  box-shadow: 0 0 8px rgba(249, 115, 22, 0.2);
}

.model-card:hover .capability-badge {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

/* Capability badges fade-in sequence during tour */
.model-card.model-card--highlighted .capability-badge {
  animation: capability-fade-in 0.6s ease-out forwards;
  opacity: 0;
}

.model-card.model-card--highlighted .capability-badge:nth-child(1) {
  animation-delay: 0.1s;
}

.model-card.model-card--highlighted .capability-badge:nth-child(2) {
  animation-delay: 0.2s;
}

.model-card.model-card--highlighted .capability-badge:nth-child(3) {
  animation-delay: 0.3s;
}

.model-card.model-card--highlighted .capability-badge:nth-child(4) {
  animation-delay: 0.4s;
}

.model-card.model-card--highlighted .capability-badge:nth-child(5) {
  animation-delay: 0.5s;
}

@keyframes capability-fade-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.model-specs {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  flex: 1;
}

.spec-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
  /* Default: fully visible */
  opacity: 1;
  transform: translateX(0) scale(1);
  transition: none; /* No transition - animation handles it */
  transform-origin: left center;
  will-change: transform, opacity; /* Optimize for animation */
}

.spec-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.spec-row--special {
  background: rgba(249, 115, 22, 0.1);
  padding: 12px;
  border-radius: 8px;
  border-bottom: none;
  margin-top: 8px;
}

.spec-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.spec-value {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--text-primary);
  line-height: 1.4;
}

.spec-value-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.spec-detail {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.spec-value--special {
  color: var(--abs-orange);
  font-weight: 600;
}

.model-best-for {
  margin-bottom: 24px;
  padding: 12px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  border-left: 3px solid var(--electric-indigo);
}

.best-for-label {
  display: block;
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}

.best-for-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.model-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.action-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.action-button--primary {
  background: var(--electric-indigo);
  color: white;
}

.action-button--primary:hover {
  background: var(--electric-indigo-hover);
  transform: translateY(-1px);
}

.action-button--secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.action-button--secondary:hover {
  border-color: var(--electric-indigo);
  color: var(--electric-indigo);
}

/* Solutions Grid */
.solutions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 32px;
  margin-bottom: 48px;
  position: relative;
  z-index: 1;
}

.solution-card {
  padding: 32px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  transition: all var(--duration-normal) var(--ease-smooth);
  z-index: 1;
  backdrop-filter: blur(1px);
  position: relative;
  overflow: hidden;
}

.solution-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-md);
}

/* Auto Highlight Tour - Subtle highlight effect for solutions */
/* Only apply when tour is active AND this specific card is highlighted */
.solution-card.solution-card--highlighted {
  border-color: var(--abs-orange) !important;
  box-shadow: 0 0 20px rgba(255, 107, 0, 0.3), var(--shadow-md) !important;
  transform: translateY(-2px) scale(1.02); /* Slight scale when highlighted */
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  animation: highlight-pulse 7s ease-in-out infinite; /* Slow pulsing border glow (7s cycle) */
}

/* Ensure other solution cards don't have the highlight */
.solution-card:not(.solution-card--highlighted) {
  border-color: var(--border-subtle);
  box-shadow: none;
}

/* Background Illustrations - Mission Control Feel */
.solution-illustration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.04; /* Very low opacity (4%) */
  overflow: hidden;
}

.illustration-svg {
  width: 100%;
  height: 100%;
  color: var(--text-primary); /* Monochrome - uses text color */
  opacity: 1;
}

/* Ensure content is above illustration */
.solution-title,
.solution-description,
.solution-section {
  position: relative;
  z-index: 1;
}

.solution-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.solution-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0 0 24px;
  line-height: 1.5;
}

.solution-section {
  margin-bottom: 24px;
}

.solution-section:last-child {
  margin-bottom: 0;
}

.solution-section-title {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 12px;
}

.solution-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.solution-list li {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}

.solution-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--electric-indigo);
  font-weight: bold;
}

.recommended-models {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.model-chip {
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 6px;
  color: var(--electric-indigo);
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.model-chip:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: var(--electric-indigo);
  transform: translateY(-1px);
}

/* CTA Section */
.cta-section {
  text-align: center;
  margin-top: 48px;
  position: relative;
  z-index: 1;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(135deg, var(--abs-orange), #ff9f43);
  border: none;
  border-radius: 12px;
  color: white;
  font-family: var(--font-label);
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
  box-shadow: var(--shadow-md), 0 0 30px var(--abs-orange-glow);
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg), 0 0 40px var(--abs-orange-glow);
}

.cta-arrow {
  font-size: 1.25rem;
}

/* Responsive */
@media (min-width: 768px) {
  .models-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .solutions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .page-explore {
    padding: 48px 32px;
  }
  
  .page-title {
    font-size: 2.5rem;
  }
  
  .models-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .solutions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1400px) {
  .models-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* GPU-Powered Micro-Animations */
@keyframes gpu-pulse {
  0%, 100% {
    transform: scale(1);
    filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.6));
  }
  50% {
    transform: scale(1.1);
    filter: drop-shadow(0 0 12px rgba(249, 115, 22, 0.8));
  }
}

@keyframes accent-slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes spec-slide-in {
  0% {
    opacity: 0;
    transform: translateX(-10px) scale(2);
  }
  40% {
    opacity: 0.9;
    transform: translateX(-4px) scale(1.15);
  }
  100% {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* Reset to visible state when not hovering */
.model-card:not(:hover):not(:focus-within) .spec-row {
  animation: none;
  opacity: 1;
  transform: translateX(0) scale(1);
  will-change: auto;
}

/* Reset accent bar when not hovering */
.model-card:not(:hover) .model-accent-bar {
  animation: none;
  transform: translateY(100%);
  opacity: 0;
}

/* Auto Highlight Tour Caption Overlay */
.tour-caption-overlay {
  position: fixed;
  /* transform is set dynamically via inline style */
  z-index: 100;
  pointer-events: none; /* Never blocks content - not clickable */
  /* Allow text wrapping for longer narrative sentences */
  white-space: normal;
  max-width: 500px;
}

.tour-caption-text {
  display: inline-block;
  max-width: 500px; /* Limit width for readability */
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.9);
  border: 1px solid var(--abs-orange);
  border-radius: 12px;
  color: var(--abs-orange);
  font-family: var(--font-label);
  font-size: 0.9rem;
  font-weight: 500;
  line-height: 1.5;
  text-align: center;
  letter-spacing: 0.05em;
  box-shadow: 0 0 30px rgba(255, 107, 0, 0.4), 0 4px 20px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  /* Normal case for narrative text (not uppercase) */
  text-transform: none;
}

/* Fade transition for caption */
.fade-caption-enter-active {
  transition: opacity 0.8s ease-in-out, transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-caption-leave-active {
  transition: opacity 0.5s ease-in-out, transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-caption-enter-from {
  opacity: 0;
  /* transform is set dynamically, but we add translateY for animation */
}

.fade-caption-leave-to {
  opacity: 0;
  /* transform is set dynamically */
}

.fade-caption-enter-to,
.fade-caption-leave-from {
  opacity: 1;
  /* transform is set dynamically via inline style */
}

/* "Why this matters" inline expansion */
.why-this-matters {
  margin-top: 20px;
  margin-bottom: 16px;
}

.learn-why-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.learn-why-link:hover {
  border-color: var(--abs-orange);
  color: var(--abs-orange);
  background: rgba(255, 107, 0, 0.05);
}

.learn-why-icon {
  font-size: 0.7rem;
  transition: transform var(--duration-fast) var(--ease-smooth);
}

.why-content {
  margin-top: 12px;
  padding: 16px;
  background: rgba(99, 102, 241, 0.05);
  border-left: 3px solid var(--electric-indigo);
  border-radius: 8px;
  overflow: hidden;
}

.why-text {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

/* Smooth expand/collapse transition */
.why-expand-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.why-expand-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.why-expand-enter-from {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.why-expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.why-expand-enter-to,
.why-expand-leave-from {
  opacity: 1;
  max-height: 200px;
}

/* Currently Running Indicator - Proof layer */
.currently-running-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 8px;
  font-size: 0.8rem;
  line-height: 1.4;
}

.running-icon {
  color: #22c55e;
  font-size: 0.7rem;
  animation: pulse-running 2s ease-in-out infinite;
}

@keyframes pulse-running {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.running-text {
  color: #22c55e;
  font-family: var(--font-label);
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* Fade-in transition for running indicator */
.fade-in-enter-active {
  transition: opacity 0.5s ease-in-out, transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-in-leave-active {
  transition: opacity 0.3s ease-in-out;
}

.fade-in-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}

.fade-in-leave-to {
  opacity: 0;
}

.fade-in-enter-to,
.fade-in-leave-from {
  opacity: 1;
  transform: translateY(0);
}
</style>
