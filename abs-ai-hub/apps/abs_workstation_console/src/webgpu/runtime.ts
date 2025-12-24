/**
 * WebGPU Runtime - Main render loop orchestration
 * 
 * Coordinates telemetry, scene director, and renderer
 */

import { GPUDeviceContext, RenderState, SceneParams } from './engine'
import { TelemetryAdapter } from './telemetry'
import { SceneDirector } from './director'

export interface WebGPURenderer {
  frame: (
    encoder: GPUCommandEncoder,
    view: GPUTextureView,
    state: {
      renderState: RenderState
      sceneParams: SceneParams
      dt: number
      now: number
    }
  ) => void
  resize: (width: number, height: number) => void
  destroy: () => void
}

export interface WebGPURuntime {
  start: () => void
  stop: () => void
  resize: (width: number, height: number) => void
}

/**
 * Create WebGPU runtime with render loop
 */
export function createWebGPURuntime(
  deviceContext: GPUDeviceContext,
  renderer: WebGPURenderer,
  director: SceneDirector,
  telemetry: TelemetryAdapter
): WebGPURuntime {
  const { device, context } = deviceContext

  let animationFrame: number | null = null
  let lastTime = performance.now()
  let isRunning = false

  function tick(now: number) {
    if (!isRunning) return

    try {
      const dt = Math.min(0.05, (now - lastTime) / 1000)
      lastTime = now

      // Update telemetry
      telemetry.update()
      const renderState = telemetry.getState()

      // Update scene director
      const sceneParams = director.update(dt, renderState)

      // Render frame
      const view = context.getCurrentTexture().createView()
      const encoder = device.createCommandEncoder()

      renderer.frame(encoder, view, {
        renderState,
        sceneParams,
        dt,
        now
      })

      device.queue.submit([encoder.finish()])

      animationFrame = requestAnimationFrame(tick)
    } catch (err) {
      console.error('[WebGPU] Render error:', err)
      // Stop rendering on error to prevent spam
      isRunning = false
    }
  }

  function start() {
    if (isRunning) return

    isRunning = true
    lastTime = performance.now()
    telemetry.start()
    animationFrame = requestAnimationFrame(tick)
  }

  function stop() {
    if (!isRunning) return

    isRunning = false
    telemetry.stop()

    if (animationFrame !== null) {
      cancelAnimationFrame(animationFrame)
      animationFrame = null
    }
  }

  function resize(width: number, height: number) {
    renderer.resize(width, height)
  }

  return {
    start,
    stop,
    resize
  }
}

