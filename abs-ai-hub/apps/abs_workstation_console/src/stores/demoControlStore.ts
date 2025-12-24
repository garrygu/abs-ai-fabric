import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendChatCompletion, requestModel } from '@/services/api'
import { useModelsStore } from './modelsStore'

export type ModelStatus = 'idle' | 'warming' | 'running' | 'cooling'
export type ActiveModel = 'deepseek-r1-70b' | 'llama3-70b' | 'dual' | null

export const useDemoControlStore = defineStore('demoControl', () => {
  const modelsStore = useModelsStore()
  const activeModel = ref<ActiveModel>(null)
  const modelStatus = ref<ModelStatus>('idle')
  const pendingRequest = ref<ActiveModel | null>(null) // Store which model is waiting
  const sessionDuration = 45000 // 45 seconds in milliseconds
  
  // Model loading progress
  const loadingProgress = ref(0)
  const loadingStage = ref<string>('')
  const loadingStartTime = ref<number | null>(null)
  const loadingDuration = ref<number | null>(null) // Duration in seconds
  const loadingElapsedTime = ref<number>(0) // Elapsed time during loading (in seconds)
  let loadingElapsedTimer: ReturnType<typeof setInterval> | null = null
  
  // Auto-sleep timer
  const autoSleepTimer = ref<ReturnType<typeof setTimeout> | null>(null)
  const autoSleepDelay = 120000 // 2 minutes
  
  // Loading duration display timer (auto-hide after showing)
  const loadingDurationTimer = ref<ReturnType<typeof setTimeout> | null>(null)
  const loadingDurationDisplayTime = 5000 // 5 seconds
  
  // Live inference metrics
  const liveMetrics = ref({
    tokensPerSec: 0,
    timeToFirstToken: 0,
    activeModel: '',
    contextWindow: '128k',
    latency: 0
  })
  
  // Current challenge/prompt
  const currentChallenge = ref<string | null>(null)
  const currentPrompt = ref<string | null>(null)
  const modelOutput = ref<{ reasoned?: string; explained?: string } | null>(null)
  const isProcessing = ref(false) // Track if model is processing a prompt
  
  const isActive = computed(() => activeModel.value !== null && modelStatus.value !== 'idle')
  const isWarming = computed(() => modelStatus.value === 'warming')
  const isRunning = computed(() => modelStatus.value === 'running')
  const isCooling = computed(() => modelStatus.value === 'cooling')
  
  // Computed property for formatted elapsed time
  const loadingElapsedFormatted = computed(() => {
    if (loadingElapsedTime.value === 0) return ''
    return `${loadingElapsedTime.value.toFixed(1)}s`
  })
  
  // Session timer - reactive countdown
  const timeRemaining = ref<number | null>(null)
  const sessionStartTime = ref<number | null>(null) // When model became running
  const lastActivityTime = ref<number | null>(null) // Last user action
  const idleThreshold = 10000 // 10 seconds of idle before starting countdown
  let sessionTimerInterval: ReturnType<typeof setInterval> | null = null
  
  function updateSessionTimer() {
    if (!sessionStartTime.value || modelStatus.value !== 'running') {
      timeRemaining.value = null
      if (sessionTimerInterval) {
        clearInterval(sessionTimerInterval)
        sessionTimerInterval = null
      }
      return
    }
    
    // Check if we've been idle for 10 seconds
    const now = Date.now()
    const timeSinceLastActivity = lastActivityTime.value ? (now - lastActivityTime.value) : (now - sessionStartTime.value)
    
    if (timeSinceLastActivity < idleThreshold) {
      // Still within idle threshold, don't show countdown yet
      timeRemaining.value = null
      return
    }
    
    // Calculate remaining time (45s from when idle threshold was reached)
    const idleStartTime = lastActivityTime.value ? (lastActivityTime.value + idleThreshold) : (sessionStartTime.value + idleThreshold)
    const elapsedSinceIdle = now - idleStartTime
    const remaining = (sessionDuration - elapsedSinceIdle) / 1000
    timeRemaining.value = Math.max(0, Math.floor(remaining))
    
    // Stop timer when it reaches 0
    if (timeRemaining.value <= 0) {
      if (sessionTimerInterval) {
        clearInterval(sessionTimerInterval)
        sessionTimerInterval = null
      }
      // Auto-sleep when session ends
      if (modelStatus.value === 'running') {
        modelStatus.value = 'cooling'
        setTimeout(() => {
          deactivateModel()
        }, 2000)
      }
    }
  }
  
  function startSessionTimer() {
    if (sessionTimerInterval) {
      clearInterval(sessionTimerInterval)
    }
    sessionStartTime.value = Date.now()
    lastActivityTime.value = Date.now()
    updateSessionTimer() // Update immediately
    sessionTimerInterval = setInterval(updateSessionTimer, 1000) // Update every second
  }
  
  function stopSessionTimer() {
    if (sessionTimerInterval) {
      clearInterval(sessionTimerInterval)
      sessionTimerInterval = null
    }
    timeRemaining.value = null
    sessionStartTime.value = null
    lastActivityTime.value = null
  }
  
  function recordActivity() {
    // Reset activity time when user interacts
    if (modelStatus.value === 'running') {
      lastActivityTime.value = Date.now()
      timeRemaining.value = null // Hide countdown immediately when activity detected
    }
  }
  
  async function activateModel(model: ActiveModel) {
    // If a model is already active, store the request to process after current session
    if (activeModel.value !== null && modelStatus.value !== 'idle') {
      pendingRequest.value = model
      return
    }
    
    activeModel.value = model
    modelStatus.value = 'warming'
    loadingProgress.value = 0
    loadingStage.value = 'Requesting model...'
    loadingStartTime.value = Date.now()
    loadingDuration.value = null
    loadingElapsedTime.value = 0
    
    // Start elapsed time timer
    if (loadingElapsedTimer) {
      clearInterval(loadingElapsedTimer)
    }
    loadingElapsedTimer = setInterval(() => {
      if (loadingStartTime.value && modelStatus.value === 'warming') {
        loadingElapsedTime.value = (Date.now() - loadingStartTime.value) / 1000
      }
    }, 100) // Update every 100ms for smooth display
    
    try {
      // Actually request/load the model via API
      if (model === 'dual') {
        // For dual mode, load both models in parallel
        loadingStage.value = 'Loading DeepSeek R1 70B...'
        await Promise.all([
          requestModel('deepseek-r1-70b'),
          requestModel('llama3-70b')
        ])
      } else {
        // Single model
        loadingStage.value = 'Loading model...'
        await requestModel(model)
      }
      
      // Update progress to show model is ready
      loadingProgress.value = 100
      loadingStage.value = 'Ready'
      
      // Small delay to show "Ready" state
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Calculate loading duration
      if (loadingStartTime.value) {
        const elapsed = (Date.now() - loadingStartTime.value) / 1000 // Convert to seconds
        loadingDuration.value = Math.round(elapsed * 10) / 10 // Round to 1 decimal place
        
        // Auto-hide loading duration after display time
        if (loadingDurationTimer.value) {
          clearTimeout(loadingDurationTimer.value)
        }
        loadingDurationTimer.value = setTimeout(() => {
          loadingDuration.value = null
          loadingDurationTimer.value = null
        }, loadingDurationDisplayTime)
      }
      
      // Mark as running
      modelStatus.value = 'running'
      loadingStage.value = ''
      
      // Stop elapsed time timer
      if (loadingElapsedTimer) {
        clearInterval(loadingElapsedTimer)
        loadingElapsedTimer = null
      }
      
      // Refresh models store to pick up updated lifecycle state from Gateway
      // This ensures the assets page and models page show the correct status
      setTimeout(() => {
        modelsStore.fetchModels().catch(err => {
          console.warn('[DemoControl] Failed to refresh models after activation:', err)
        })
      }, 1000) // Small delay to allow Gateway to update lifecycle state
      
      // Start session timer (will start countdown after 10s idle)
      startSessionTimer()
      
      // Start auto-sleep timer
      startAutoSleepTimer()
    } catch (error) {
      console.error('[DemoControl] Error activating model:', error)
      // Even if load fails, mark as running - model will load on first use
      modelStatus.value = 'running'
      loadingStage.value = ''
      loadingProgress.value = 100
      
      if (loadingStartTime.value) {
        const elapsed = (Date.now() - loadingStartTime.value) / 1000
        loadingDuration.value = Math.round(elapsed * 10) / 10
      }
      
      // Stop elapsed time timer
      if (loadingElapsedTimer) {
        clearInterval(loadingElapsedTimer)
        loadingElapsedTimer = null
      }
      
      // Refresh models store to pick up updated lifecycle state
      setTimeout(() => {
        modelsStore.fetchModels().catch(err => {
          console.warn('[DemoControl] Failed to refresh models after activation (error case):', err)
        })
      }, 1000)
      
      startSessionTimer()
      startAutoSleepTimer()
    }
  }
  
  function startAutoSleepTimer() {
    if (autoSleepTimer.value) {
      clearTimeout(autoSleepTimer.value)
    }
    
    // Don't start auto-sleep if model is processing
    if (isProcessing.value) {
      return
    }
    
    autoSleepTimer.value = setTimeout(() => {
      // Double-check processing status before sleeping
      if (isProcessing.value) {
        // If still processing, restart timer
        startAutoSleepTimer()
        return
      }
      
      if (modelStatus.value === 'running' || modelStatus.value === 'idle') {
        modelStatus.value = 'cooling'
        setTimeout(() => {
          deactivateModel()
        }, 2000) // 2 seconds cooling animation
      }
    }, autoSleepDelay)
  }
  
  function deactivateModel() {
    activeModel.value = null
    modelStatus.value = 'idle'
    loadingProgress.value = 0
    loadingStage.value = ''
    loadingStartTime.value = null
    loadingDuration.value = null
    loadingElapsedTime.value = 0
    currentChallenge.value = null
    currentPrompt.value = null
    modelOutput.value = null
    isProcessing.value = false // Reset processing flag
    
    // Stop elapsed time timer
    if (loadingElapsedTimer) {
      clearInterval(loadingElapsedTimer)
      loadingElapsedTimer = null
    }
    
    stopSessionTimer()
    
    if (autoSleepTimer.value) {
      clearTimeout(autoSleepTimer.value)
      autoSleepTimer.value = null
    }
    
    if (loadingDurationTimer.value) {
      clearTimeout(loadingDurationTimer.value)
      loadingDurationTimer.value = null
    }
    
    // Process pending request if any
    if (pendingRequest.value) {
      const nextModel = pendingRequest.value
      pendingRequest.value = null
      // Small delay before activating next model for smooth transition
      setTimeout(() => {
        activateModel(nextModel)
      }, 500)
    }
  }
  
  function cancelPendingRequest() {
    pendingRequest.value = null
  }
  
  function setLiveMetrics(metrics: Partial<typeof liveMetrics.value>) {
    liveMetrics.value = { ...liveMetrics.value, ...metrics }
  }
  
  function setChallenge(challenge: string, prompt: string) {
    currentChallenge.value = challenge
    currentPrompt.value = prompt
    
    // Record activity - resets idle timer
    recordActivity()
    
    // Cancel any existing auto-sleep timer
    if (autoSleepTimer.value) {
      clearTimeout(autoSleepTimer.value)
      autoSleepTimer.value = null
    }
    
    // Ensure model status is 'running' if it's active
    if (activeModel.value !== null && modelStatus.value !== 'idle') {
      modelStatus.value = 'running'
    }
    
    // Clear previous output
    modelOutput.value = null
    
    // Mark as processing - this prevents auto-sleep and shows progress
    isProcessing.value = true
    
    // Call real model API to generate output
    ;(async () => {
      try {
        // Only generate output if model is still active
        if (activeModel.value === null) {
          isProcessing.value = false
          return
        }
        
        const challengeType = currentChallenge.value || undefined
        
        if (activeModel.value === 'dual') {
          // Dual model: generate both outputs in parallel
          const [reasonedResult, explainedResult] = await Promise.all([
            sendChatCompletion('deepseek-r1-70b', prompt, undefined, challengeType).catch(err => {
              console.error('[DemoControl] DeepSeek error:', err)
              return `Error: ${err.message}`
            }),
            sendChatCompletion('llama3-70b', prompt, undefined, challengeType).catch(err => {
              console.error('[DemoControl] LLaMA error:', err)
              return `Error: ${err.message}`
            })
          ])
          
          // Check if model was deactivated during API call
          if (activeModel.value === null) {
            isProcessing.value = false
            return
          }
          
          modelOutput.value = {
            reasoned: reasonedResult,
            explained: explainedResult
          }
        } else if (activeModel.value === 'deepseek-r1-70b') {
          // Reasoning challenge - use DeepSeek
          const result = await sendChatCompletion(activeModel.value, prompt, undefined, challengeType)
          
          // Check if model was deactivated during API call
          if (activeModel.value === null) {
            isProcessing.value = false
            return
          }
          
          modelOutput.value = {
            reasoned: result
          }
        } else if (activeModel.value === 'llama3-70b') {
          // Executive explanation or summarization challenge
          const result = await sendChatCompletion(activeModel.value, prompt, undefined, challengeType)
          
          // Check if model was deactivated during API call
          if (activeModel.value === null) {
            isProcessing.value = false
            return
          }
          
          modelOutput.value = {
            explained: result
          }
        }
        
        // Mark processing as complete
        isProcessing.value = false
        
        // Start auto-sleep timer after output is generated (user might interact with it)
        if (modelStatus.value === 'running') {
          startAutoSleepTimer()
        }
      } catch (error) {
        console.error('[DemoControl] Error generating model output:', error)
        isProcessing.value = false
        
        // Show error message to user
        const errorMessage = error instanceof Error ? error.message : 'Failed to generate response'
        if (activeModel.value === 'dual') {
          modelOutput.value = {
            reasoned: `Error: ${errorMessage}`,
            explained: `Error: ${errorMessage}`
          }
        } else if (activeModel.value === 'deepseek-r1-70b') {
          modelOutput.value = {
            reasoned: `Error: ${errorMessage}`
          }
        } else if (activeModel.value === 'llama3-70b') {
          modelOutput.value = {
            explained: `Error: ${errorMessage}`
          }
        }
      }
    })()
  }
  
  // Hard-coded response functions removed - now using real API calls via sendChatCompletion
  
  function setModelOutput(output: { reasoned?: string; explained?: string }) {
    modelOutput.value = output
  }
  
  function clearSession() {
    deactivateModel()
  }
  
  return {
    // State
    activeModel,
    modelStatus,
    pendingRequest,
    loadingProgress,
    loadingStage,
    loadingStartTime,
    loadingDuration,
    loadingElapsedTime,
    loadingElapsedFormatted,
    liveMetrics,
    currentChallenge,
    currentPrompt,
    modelOutput,
    isProcessing,
    
    // Computed
    isActive,
    isWarming,
    isRunning,
    isCooling,
    timeRemaining,
    
    // Actions
    activateModel,
    deactivateModel,
    cancelPendingRequest,
    setLiveMetrics,
    setChallenge,
    setModelOutput,
    clearSession,
    startAutoSleepTimer,
    startSessionTimer,
    stopSessionTimer,
    updateSessionTimer,
    recordActivity
  }
})

