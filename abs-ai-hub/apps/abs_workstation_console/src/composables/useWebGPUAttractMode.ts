/**
 * Vue Composable for WebGPU Attract Mode integration
 * 
 * Thin Vue adapter that delegates to:
 * - SceneController (timing + intensity)
 * - AttractEngine (WebGPU init + rendering)
 * 
 * This composable only handles Vue lifecycle + DOM mounting.
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { createAttractEngine, isWebGPUSupported, type AttractEngine } from '@/attract/engine/attractEngine'
import { SceneController } from '@/attract/controller/sceneController'

export function useWebGPUAttractMode(container: HTMLElement) {
  const isInitialized = ref(false)
  const isSupported = ref(false)
  const error = ref<string | null>(null)

  let engine: AttractEngine | null = null
  let controller: SceneController | null = null
  let offUpdate: (() => void) | null = null
  let onResize: (() => void) | null = null

  /**
   * Resize canvas and renderer to match container
   */
  function resizeNow(): void {
    if (!engine) return
    const rect = container.getBoundingClientRect()
    const width = rect.width * window.devicePixelRatio
    const height = rect.height * window.devicePixelRatio
    engine.canvas.width = width
    engine.canvas.height = height
    engine.canvas.style.width = `${rect.width}px`
    engine.canvas.style.height = `${rect.height}px`
    engine.resize(width, height)
  }

  /**
   * Initialize engine and controller
   */
  async function initialize(): Promise<void> {
    // Check WebGPU support
    if (!isWebGPUSupported()) {
      error.value = 'WebGPU not supported in this browser'
      return
    }

    try {
      // Create engine (handles WebGPU init, canvas creation)
      engine = await createAttractEngine(container)
      isSupported.value = true

      // Initial resize
      resizeNow()

      // Create scene controller
      controller = new SceneController()

      // Subscribe to scene state updates
      offUpdate = controller.onUpdate((state) => {
        engine?.applySceneState(state)
      })

      // Handle window resize (with cleanup)
      onResize = () => resizeNow()
      window.addEventListener('resize', onResize)

      // Start both controller and engine
      controller.start()
      engine.start()

      isInitialized.value = true
      console.log('[Attract Mode] Initialized with controller + engine architecture')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to initialize Attract Mode'
      console.error('[Attract Mode] Initialization error:', err)
    }
  }

  /**
   * Exposed start method
   */
  function start(): void {
    controller?.start()
    engine?.start()
  }

  /**
   * Exposed stop method
   */
  function stop(): void {
    controller?.stop()
    engine?.stop()
  }

  /**
   * Exposed resize method
   */
  function resize(width: number, height: number): void {
    engine?.resize(width, height)
  }

  // Vue lifecycle: mount
  onMounted(() => {
    // Small delay to ensure container is fully mounted
    setTimeout(() => {
      initialize()
    }, 50)
  })

  // Vue lifecycle: unmount (with proper cleanup)
  onUnmounted(() => {
    // Remove resize listener
    if (onResize) {
      window.removeEventListener('resize', onResize)
    }

    // Unsubscribe from controller
    offUpdate?.()

    // Stop and dispose
    controller?.stop()
    engine?.dispose()
  })

  return {
    isInitialized,
    isSupported,
    error,
    start,
    stop,
    resize
  }
}
