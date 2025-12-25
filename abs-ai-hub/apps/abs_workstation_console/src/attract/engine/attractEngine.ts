/**
 * Attract Engine — WebGPU wrapper for Attract Mode
 * 
 * Single integration point for WebGPU initialization, rendering,
 * and scene state application. Wraps existing webgpu/* implementations.
 * 
 * Usage:
 *   const engine = await createAttractEngine(containerElement)
 *   engine.start()
 *   engine.applySceneState(state) // Called by controller
 *   engine.dispose()
 */

import { initWebGPU, isWebGPUSupported } from '@/webgpu/engine'
import { createTelemetryAdapter } from '@/webgpu/telemetry'
import { createSceneDirector } from '@/webgpu/director'
import { createWebGPURuntime } from '@/webgpu/runtime'
import { createWebGPURenderer } from '@/webgpu/renderer'
import type { SceneState } from '@/attract/contracts/attract'

export interface AttractEngine {
    /** The canvas element created by the engine */
    canvas: HTMLCanvasElement
    /** Start the render loop */
    start(): void
    /** Stop the render loop */
    stop(): void
    /** Resize the canvas and renderer */
    resize(width: number, height: number): void
    /** Apply scene state from controller */
    applySceneState(state: SceneState): void
    /** Dispose all resources and remove canvas */
    dispose(): void
}

/**
 * Create an Attract Engine instance
 * 
 * @param container - HTML element to mount the canvas into
 * @throws Error if WebGPU is not supported
 */
export async function createAttractEngine(container: HTMLElement): Promise<AttractEngine> {
    if (!isWebGPUSupported()) {
        throw new Error('WebGPU not supported in this browser')
    }

    // Create canvas overlay
    const canvas = document.createElement('canvas')
    canvas.style.position = 'absolute'
    canvas.style.inset = '0'
    canvas.style.pointerEvents = 'none'
    canvas.style.zIndex = '1'
    canvas.style.width = '100%'
    canvas.style.height = '100%'
    container.appendChild(canvas)

    // Initialize WebGPU
    const deviceContext = await initWebGPU(canvas)

    // Create subsystems
    const telemetry = createTelemetryAdapter()
    const director = createSceneDirector()
    const renderer = createWebGPURenderer(deviceContext)
    const runtime = createWebGPURuntime(deviceContext, renderer, director, telemetry)

    const api: AttractEngine = {
        canvas,

        start(): void {
            runtime.start()
        },

        stop(): void {
            runtime.stop()
        },

        resize(width: number, height: number): void {
            runtime.resize(width, height)
        },

        applySceneState(state: SceneState): void {
            // Map SceneState to director's expected format
            // The director's update() is called internally by runtime, but we can
            // influence behavior through telemetry hints or by extending director API

            // Future: extend director API to accept:
            // - state.sceneId
            // - state.phase  
            // - state.visualIntensity
            // - state.progress01

            // For now, scene state is tracked for integration surface
            // Console log for debugging during development
            if (state.phase === 'enter') {
                console.log(`[Attract Engine] Scene ${state.sceneId} entered`)
            }
        },

        dispose(): void {
            runtime.stop()

            // Dispose renderer if it has a dispose method
            if (typeof (renderer as any).dispose === 'function') {
                (renderer as any).dispose()
            }

            // Remove canvas from DOM
            if (canvas.parentNode) {
                canvas.parentNode.removeChild(canvas)
            }
        }
    }

    return api
}

export { isWebGPUSupported }
