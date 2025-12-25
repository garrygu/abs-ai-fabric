import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendChatCompletion, requestModel, warmupModel } from '@/services/api'
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
  const autoSleepDelay = 600000 // 10 minutes after kiosk is closed

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
  const currentDocument = ref<string | null>(null) // Store current document for summarization
  const isKioskOpen = ref(false) // Track if the "Try It Yourself" kiosk is open

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

    // Pause countdown if model is processing
    if (isProcessing.value) {
      // Don't update the countdown while processing - keep current value
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
    // If requesting same model that's already active, do nothing
    if (activeModel.value === model && modelStatus.value !== 'idle') {
      return
    }

    // If a different model is already active, unload it first
    if (activeModel.value !== null && modelStatus.value !== 'idle') {
      loadingStage.value = 'Unloading previous model...'
      modelStatus.value = 'warming'
      loadingProgress.value = 0
      loadingStartTime.value = Date.now()
      loadingElapsedTime.value = 0

      // Start elapsed timer for switch
      if (loadingElapsedTimer) {
        clearInterval(loadingElapsedTimer)
      }
      loadingElapsedTimer = setInterval(() => {
        if (loadingStartTime.value && modelStatus.value === 'warming') {
          loadingElapsedTime.value = (Date.now() - loadingStartTime.value) / 1000
        }
      }, 100)

      // Unload current model before loading new one
      try {
        const { unloadModel } = await import('@/services/api')
        await unloadModel(activeModel.value)
        console.log(`[DemoControl] Unloaded ${activeModel.value} for switch`)

        // Refresh models store so Assets page shows updated status
        modelsStore.fetchModels().catch(err => {
          console.warn('[DemoControl] Failed to refresh models after unload:', err)
        })
      } catch (error) {
        console.warn('[DemoControl] Error unloading model during switch:', error)
        // Continue with loading new model even if unload fails
      }
    }

    activeModel.value = model
    modelStatus.value = 'warming'
    loadingProgress.value = 0
    loadingStage.value = 'Requesting model...'
    loadingStartTime.value = Date.now()
    loadingDuration.value = null
    loadingElapsedTime.value = 0

    // Start elapsed time timer and update progress
    if (loadingElapsedTimer) {
      clearInterval(loadingElapsedTimer)
    }
    loadingElapsedTimer = setInterval(() => {
      if (loadingStartTime.value && modelStatus.value === 'warming') {
        const elapsed = (Date.now() - loadingStartTime.value) / 1000
        loadingElapsedTime.value = elapsed
        
        // Calculate progress based on elapsed time with smooth curve
        // Typical loading takes 30-60 seconds, simulate over 50 seconds
        // Use easing function for smooth acceleration/deceleration
        const totalTime = 50 // seconds
        const normalizedTime = Math.min(1, elapsed / totalTime)
        
        // Ease-in-out cubic curve for smooth progress
        let easedProgress = 0
        if (normalizedTime < 0.5) {
          easedProgress = 4 * normalizedTime * normalizedTime * normalizedTime
        } else {
          const t = normalizedTime - 1
          easedProgress = 1 + 4 * t * t * t
        }
        
        // Scale to 0-95% (never reaches 100% until actually ready)
        const simulatedProgress = easedProgress * 95
        
        // Always update progress (round to nearest integer)
        const newProgress = Math.round(simulatedProgress)
        // Ensure progress increases smoothly and never goes backwards
        if (newProgress > loadingProgress.value || loadingProgress.value === 0) {
          loadingProgress.value = newProgress
        }
      }
    }, 200) // Update every 200ms for smooth display

    try {
      // Actually request/load the model via API
      if (model === 'dual') {
        // For dual mode, load both models in parallel
        loadingStage.value = 'Loading dual 70B models...'
        // Progress will be updated by timer based on elapsed time
        await Promise.all([
          requestModel('deepseek-r1-70b'),
          requestModel('llama3-70b')
        ])

        // Warmup inference to force models into VRAM
        loadingStage.value = 'Warming up models...'
        // Progress will be updated by timer based on elapsed time
        await Promise.all([
          warmupModel('deepseek-r1-70b'),
          warmupModel('llama3-70b')
        ])
      } else {
        // Single model
        loadingStage.value = 'Loading model...'
        // Progress will be updated by timer based on elapsed time
        await requestModel(model)

        // Warmup inference to force model into VRAM
        loadingStage.value = 'Warming up model...'
        // Progress will be updated by timer based on elapsed time
        await warmupModel(model)
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

      // Session timer disabled - user can manually deactivate or wait for auto-sleep
      // startSessionTimer()

      // Don't start auto-sleep timer immediately - wait until kiosk is closed
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

      // Session timer disabled - user can manually deactivate or wait for auto-sleep
      // startSessionTimer()
      // Don't start auto-sleep timer immediately - wait until kiosk is closed
    }
  }

  function startAutoSleepTimer() {
    if (autoSleepTimer.value) {
      clearTimeout(autoSleepTimer.value)
    }

    // Don't start auto-sleep if model is processing or kiosk is open
    if (isProcessing.value || isKioskOpen.value) {
      return
    }

    autoSleepTimer.value = setTimeout(() => {
      // Double-check processing status and kiosk state before sleeping
      if (isProcessing.value || isKioskOpen.value) {
        // If still processing or kiosk is open, restart timer
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

  function setKioskOpen(open: boolean) {
    isKioskOpen.value = open

    // If kiosk is opened, cancel any auto-sleep timer
    if (open) {
      if (autoSleepTimer.value) {
        clearTimeout(autoSleepTimer.value)
        autoSleepTimer.value = null
      }
    } else {
      // If kiosk is closed, start the auto-sleep timer
      startAutoSleepTimer()
    }
  }

  async function deactivateModel() {
    // Unload the model(s) from VRAM before clearing UI state
    const modelToUnload = activeModel.value
    if (modelToUnload) {
      try {
        const { unloadModel } = await import('@/services/api')
        await unloadModel(modelToUnload)
        console.log(`[DemoControl] Unloaded model: ${modelToUnload}`)
      } catch (error) {
        console.error('[DemoControl] Error unloading model:', error)
        // Continue with deactivation even if unload fails
      }
    }

    // Clear UI state
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
    currentDocument.value = null
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

    // Refresh models list to update status
    try {
      modelsStore.fetchModels()
    } catch (error) {
      console.error('[DemoControl] Error refreshing models:', error)
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

  async function setChallenge(challenge: string, prompt: string) {
    currentChallenge.value = challenge
    currentPrompt.value = prompt

    // Record activity - resets idle timer
    recordActivity()

    // Cancel any existing auto-sleep timer
    if (autoSleepTimer.value) {
      clearTimeout(autoSleepTimer.value)
      autoSleepTimer.value = null
    }

    // For summarize challenge, fetch a sample document from HuggingFace
    if (challenge === 'summarize' && !currentDocument.value) {
      try {
        const { fetchSampleDocument } = await import('@/services/api')
        const sampleDoc = await fetchSampleDocument('cnn_dailymail')
        currentDocument.value = sampleDoc.document
      } catch (error) {
        console.error('[DemoControl] Failed to fetch sample document:', error)
        // Continue without document - model will still respond
      }
    }

    // Ensure model status is 'running' if it's active
    if (activeModel.value !== null && modelStatus.value !== 'idle') {
      modelStatus.value = 'running'
    }

    // Clear previous output
    modelOutput.value = null

    // Mark as processing - this prevents auto-sleep and shows progress
    isProcessing.value = true

    // Update activity time to pause/reset the session timer while processing
    if (modelStatus.value === 'running') {
      lastActivityTime.value = Date.now()
      timeRemaining.value = null // Hide countdown while processing
    }

    // Call real model API to generate output
    ; (async () => {
      try {
        // Only generate output if model is still active
        if (activeModel.value === null) {
          isProcessing.value = false
          return
        }

        const challengeType = currentChallenge.value || undefined

        // For summarize challenge, prepend document content to the prompt
        let fullPrompt = prompt
        if (challengeType === 'summarize' && currentDocument.value) {
          fullPrompt = `Document to analyze:\n\n${currentDocument.value}\n\n---\n\nUser request: ${prompt}`
        }

        if (activeModel.value === 'dual') {
          // Dual model: only generate both outputs if it's a comparison challenge
          if (challengeType === 'compare') {
            const [reasonedResult, explainedResult] = await Promise.all([
              sendChatCompletion('deepseek-r1-70b', fullPrompt, undefined, challengeType).catch(err => {
                console.error('[DemoControl] DeepSeek error:', err)
                return `Error: ${err.message}`
              }),
              sendChatCompletion('llama3-70b', fullPrompt, undefined, challengeType).catch(err => {
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
          } else if (challengeType === 'reasoning') {
            // Even in dual mode, if it's a reasoning challenge, just use DeepSeek
            const result = await sendChatCompletion('deepseek-r1-70b', fullPrompt, undefined, challengeType)
            if (activeModel.value !== null) {
              modelOutput.value = { reasoned: result }
            }
          } else {
            // For other challenges (explanation, etc.), use LLaMA-3 70B
            const result = await sendChatCompletion('llama3-70b', fullPrompt, undefined, challengeType)
            if (activeModel.value !== null) {
              modelOutput.value = { explained: result }
            }
          }
        } else if (activeModel.value === 'deepseek-r1-70b') {
          // Reasoning challenge - use DeepSeek
          const result = await sendChatCompletion(activeModel.value, fullPrompt, undefined, challengeType)

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
          const result = await sendChatCompletion(activeModel.value, fullPrompt, undefined, challengeType)

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

        // Reset activity time when processing completes - this resets the idle timer
        if (modelStatus.value === 'running') {
          lastActivityTime.value = Date.now()
          timeRemaining.value = null // Hide countdown until idle threshold is reached again
          // Don't start auto-sleep timer here - wait until kiosk is closed
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
    // Close kiosk (this will trigger auto-sleep timer)
    setKioskOpen(false)
    // setKioskOpen(false) already calls startAutoSleepTimer(), so no need to call it again
  }

  /**
   * Check Ollama for already-loaded models and sync store state.
   * Call this on app init to detect models loaded before LivePlayground opened.
   */
  async function checkLoadedModels() {
    try {
      // Query Ollama's running models endpoint
      const response = await fetch('http://localhost:11434/api/ps')
      if (!response.ok) {
        console.log('[DemoControl] Could not query Ollama /api/ps')
        return
      }

      const data = await response.json()
      const runningModels = data.models || []

      if (runningModels.length === 0) {
        console.log('[DemoControl] No models currently loaded in Ollama')
        return
      }

      console.log('[DemoControl] Found loaded models:', runningModels.map((m: { name: string }) => m.name))

      // Check which demo models are loaded
      const hasDeepSeek = runningModels.some((m: { name: string }) =>
        m.name.toLowerCase().includes('deepseek') && m.name.includes('70b')
      )
      const hasLlama = runningModels.some((m: { name: string }) =>
        m.name.toLowerCase().includes('llama') && m.name.includes('70b')
      )

      // Only set state if we're currently idle (don't override user actions)
      if (modelStatus.value === 'idle' && activeModel.value === null) {
        if (hasDeepSeek && hasLlama) {
          activeModel.value = 'dual'
          modelStatus.value = 'running'
          console.log('[DemoControl] Detected dual 70B models running, syncing state')
        } else if (hasDeepSeek) {
          activeModel.value = 'deepseek-r1-70b'
          modelStatus.value = 'running'
          console.log('[DemoControl] Detected DeepSeek R1 70B running, syncing state')
        } else if (hasLlama) {
          activeModel.value = 'llama3-70b'
          modelStatus.value = 'running'
          console.log('[DemoControl] Detected LLaMA 3 70B running, syncing state')
        }
      }
    } catch (error) {
      console.log('[DemoControl] Error checking loaded models:', error)
    }
  }

  async function deactivateModelManually() {
    // Manual deactivation - immediately deactivate and unload model
    await deactivateModel()
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
    currentDocument,
    modelOutput,
    isProcessing,
    isKioskOpen,

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
    deactivateModelManually,
    setKioskOpen,
    startAutoSleepTimer,
    startSessionTimer,
    stopSessionTimer,
    updateSessionTimer,
    recordActivity,
    checkLoadedModels
  }
})

