import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAllInOneDemoStore = defineStore('allInOneDemo', () => {
  const isActive = ref(false)
  const isEnabled = ref(true) // Only enabled in CES mode
  const currentStep = ref(0)
  const lastActivityTime = ref(Date.now())
  const activationTime = ref(0) // Track when demo was activated
  const isNavigatingProgrammatically = ref(false) // Flag to prevent watch from stopping demo
  
  // Demo flow sequence: [pageIndex, durationMs]
  const demoSequence = [
    { pageIndex: 0, duration: 10000, name: 'Overview' },      // Step 1: Identity (10s)
    { pageIndex: 1, duration: 10000, name: 'Performance' },  // Step 2: Power Without Waste (10s)
    { pageIndex: 4, duration: 25000, name: 'Orchestration' }, // Step 3: Intelligence (25s)
    { pageIndex: 3, duration: 15000, name: 'Models' },       // Step 4: Proof of All-In-One (15s)
    { pageIndex: 1, duration: 10000, name: 'Performance' }  // Step 5: Close the Loop (10s)
  ]
  
  let demoInterval: ReturnType<typeof setInterval> | null = null
  let stepTimeout: ReturnType<typeof setTimeout> | null = null
  
  const totalDuration = computed(() => 
    demoSequence.reduce((sum, step) => sum + step.duration, 0)
  )
  
  function activate() {
    if (!isEnabled.value) return
    isActive.value = true
    currentStep.value = 0
    activationTime.value = Date.now()
    lastActivityTime.value = Date.now()
    console.log('[AllInOneDemo] Activated at', new Date().toISOString())
  }
  
  function deactivate() {
    isActive.value = false
    currentStep.value = 0
    stopDemo()
    lastActivityTime.value = Date.now()
    console.log('[AllInOneDemo] Deactivated')
  }
  
  function recordActivity() {
    const now = Date.now()
    lastActivityTime.value = now
    
    if (!isActive.value) return
    
    // Don't stop if we just activated (grace period of 2 seconds)
    const timeSinceActivation = now - activationTime.value
    if (timeSinceActivation > 2000) {
      console.log('[AllInOneDemo] User activity detected, stopping demo (activated', Math.round(timeSinceActivation / 1000), 's ago)')
      deactivate()
    } else {
      console.log('[AllInOneDemo] Activity ignored (grace period, activated', Math.round(timeSinceActivation / 1000), 's ago)')
    }
  }
  
  function startDemo(goToPage: (index: number) => void) {
    console.log('[AllInOneDemo] startDemo called', {
      isActive: isActive.value,
      hasInterval: !!demoInterval,
      isEnabled: isEnabled.value
    })
    
    if (!isActive.value) {
      console.warn('[AllInOneDemo] Cannot start: not active')
      return
    }
    
    if (!isEnabled.value) {
      console.warn('[AllInOneDemo] Cannot start: not enabled')
      return
    }
    
    if (demoInterval) {
      console.warn('[AllInOneDemo] Demo already running')
      return
    }
    
    // Start from first step
    currentStep.value = 0
    const step = demoSequence[currentStep.value]
    
    console.log('[AllInOneDemo] Navigating to first step:', step)
    
    // Mark as programmatic navigation
    isNavigatingProgrammatically.value = true
    goToPage(step.pageIndex)
    setTimeout(() => {
      isNavigatingProgrammatically.value = false
    }, 100) // Reset flag after navigation completes
    
    // Set up step timeout
    console.log('[AllInOneDemo] Setting initial timeout for', step.duration, 'ms')
    stepTimeout = setTimeout(() => {
      console.log('[AllInOneDemo] Initial timeout fired, calling advanceStep')
      advanceStep(goToPage)
    }, step.duration)
    
    console.log('[AllInOneDemo] Started at step', currentStep.value, 'page', step.pageIndex, 'next step in', step.duration, 'ms')
  }
  
  function advanceStep(goToPage: (index: number) => void) {
    console.log('[AllInOneDemo] advanceStep called', {
      isActive: isActive.value,
      currentStep: currentStep.value
    })
    
    if (!isActive.value) {
      console.warn('[AllInOneDemo] Cannot advance: not active')
      return
    }
    
    currentStep.value = (currentStep.value + 1) % demoSequence.length
    const step = demoSequence[currentStep.value]
    
    console.log('[AllInOneDemo] Advancing to step', currentStep.value, 'page', step.pageIndex, step.name)
    
    // Mark as programmatic navigation
    isNavigatingProgrammatically.value = true
    goToPage(step.pageIndex)
    
    // Reset flag after navigation completes
    setTimeout(() => {
      isNavigatingProgrammatically.value = false
      console.log('[AllInOneDemo] Navigation flag reset')
    }, 200) // Increased delay to ensure navigation completes
    
    // Clear previous timeout
    if (stepTimeout) {
      clearTimeout(stepTimeout)
      stepTimeout = null
    }
    
    // Set up next step timeout
    console.log('[AllInOneDemo] Setting timeout for', step.duration, 'ms')
    stepTimeout = setTimeout(() => {
      console.log('[AllInOneDemo] Timeout fired, calling advanceStep')
      advanceStep(goToPage)
    }, step.duration)
    
    console.log('[AllInOneDemo] Advanced to step', currentStep.value, 'page', step.pageIndex, 'next step in', step.duration, 'ms')
  }
  
  function stopDemo() {
    if (stepTimeout) {
      clearTimeout(stepTimeout)
      stepTimeout = null
    }
    if (demoInterval) {
      clearInterval(demoInterval)
      demoInterval = null
    }
  }
  
  function getCurrentPageIndex(): number {
    if (!isActive.value || currentStep.value >= demoSequence.length) return -1
    return demoSequence[currentStep.value].pageIndex
  }
  
  function getCurrentStepName(): string {
    if (!isActive.value || currentStep.value >= demoSequence.length) return ''
    return demoSequence[currentStep.value].name
  }
  
  function isProgrammaticNavigation(): boolean {
    return isNavigatingProgrammatically.value
  }
  
  return {
    // State
    isActive,
    isEnabled,
    currentStep,
    
    // Computed
    totalDuration,
    demoSequence,
    
    // Actions
    activate,
    deactivate,
    recordActivity,
    startDemo,
    stopDemo,
    getCurrentPageIndex,
    getCurrentStepName,
    isProgrammaticNavigation
  }
})

