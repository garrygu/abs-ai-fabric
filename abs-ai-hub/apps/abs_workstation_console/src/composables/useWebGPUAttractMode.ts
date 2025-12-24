/**
 * Vue Composable for WebGPU Attract Mode integration
 * 
 * Provides WebGPU-powered visual fabric layer for showcase scenes
 */

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { initWebGPU, isWebGPUSupported } from '@/webgpu/engine'
import { createTelemetryAdapter } from '@/webgpu/telemetry'
import { createSceneDirector } from '@/webgpu/director'
import { createWebGPURuntime, WebGPURenderer } from '@/webgpu/runtime'
import { createWebGPURenderer } from '@/webgpu/renderer'

export function useWebGPUAttractMode(container: HTMLElement) {
  const canvas = ref<HTMLCanvasElement | null>(null)
  const isInitialized = ref(false)
  const isSupported = ref(false)
  const error = ref<string | null>(null)

  let deviceContext: Awaited<ReturnType<typeof initWebGPU>> | null = null
  let runtime: ReturnType<typeof createWebGPURuntime> | null = null
  let renderer: WebGPURenderer | null = null

  async function initialize() {
    if (!isWebGPUSupported()) {
      error.value = 'WebGPU not supported'
      return
    }

    try {
      // Create canvas
      const canvasEl = document.createElement('canvas')
      canvasEl.style.position = 'absolute'
      canvasEl.style.inset = '0'
      canvasEl.style.pointerEvents = 'none'
      canvasEl.style.zIndex = '1'
      canvasEl.style.width = '100%'
      canvasEl.style.height = '100%'
      canvasEl.style.opacity = '1'
      container.appendChild(canvasEl)
      canvas.value = canvasEl
      console.log('[WebGPU] Canvas created and added to container')

      // Resize canvas
      const resizeCanvas = () => {
        if (!canvas.value) return
        const rect = container.getBoundingClientRect()
        const width = rect.width * window.devicePixelRatio
        const height = rect.height * window.devicePixelRatio
        canvas.value.width = width
        canvas.value.height = height
        canvas.value.style.width = `${rect.width}px`
        canvas.value.style.height = `${rect.height}px`
        
        // Update renderer viewport
        if (runtime) {
          runtime.resize(width, height)
        }
      }
      resizeCanvas()
      window.addEventListener('resize', resizeCanvas)

      // Initialize WebGPU
      deviceContext = await initWebGPU(canvas.value)
      isSupported.value = true

      // Create telemetry adapter
      const telemetry = createTelemetryAdapter()

      // Create scene director
      const director = createSceneDirector()

      // Create renderer (full WebGPU implementation)
      renderer = createWebGPURenderer(deviceContext)

      // Create runtime
      runtime = createWebGPURuntime(deviceContext, renderer, director, telemetry)

      isInitialized.value = true
      console.log('[WebGPU] Successfully initialized renderer')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to initialize WebGPU'
      console.error('[WebGPU] Initialization error:', err)
      // Fallback: show error in console but don't break the app
    }
  }

  function start() {
    if (runtime && isInitialized.value) {
      runtime.start()
    }
  }

  function stop() {
    if (runtime) {
      runtime.stop()
    }
  }

  function resize(width: number, height: number) {
    if (runtime) {
      runtime.resize(width, height)
    }
  }

  onMounted(() => {
    // Small delay to ensure container is fully mounted
    setTimeout(() => {
      initialize()
    }, 50)
  })

  onUnmounted(() => {
    stop()
    if (canvas.value && canvas.value.parentNode) {
      canvas.value.parentNode.removeChild(canvas.value)
    }
  })

  return {
    canvas,
    isInitialized,
    isSupported,
    error,
    start,
    stop,
    resize
  }
}


