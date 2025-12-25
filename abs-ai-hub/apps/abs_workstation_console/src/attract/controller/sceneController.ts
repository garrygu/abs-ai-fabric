/**
 * Scene Controller — FSM for Attract Mode scene rotation
 * 
 * Rotates through scenes A→E, emitting SceneState on each frame.
 * Owns timing, phase detection, and intensity curve sampling.
 * 
 * Usage:
 *   const controller = new SceneController()
 *   controller.onUpdate((state) => engine.applySceneState(state))
 *   controller.start()
 */

import type { SceneState, ScenePhase } from '@/attract/contracts/attract'
import { SCENE_MANIFEST, DEFAULT_ENTER_01, DEFAULT_EXIT_01, type IntensityKey } from '@/attract/config/sceneManifest'

// Utility functions
function lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t
}

function clamp01(x: number): number {
    return Math.max(0, Math.min(1, x))
}

/**
 * Sample intensity curve at given progress
 */
function sampleCurve(keys: IntensityKey[], t01: number): number {
    const t = clamp01(t01)
    if (keys.length === 0) return 0
    if (t <= keys[0].t01) return keys[0].v

    for (let i = 0; i < keys.length - 1; i++) {
        const a = keys[i]
        const b = keys[i + 1]
        if (t >= a.t01 && t <= b.t01) {
            const local = (t - a.t01) / Math.max(1e-6, b.t01 - a.t01)
            return lerp(a.v, b.v, local)
        }
    }

    return keys[keys.length - 1].v
}

/**
 * Determine phase from progress
 */
function phaseFor(progress01: number, enter01 = DEFAULT_ENTER_01, exit01 = DEFAULT_EXIT_01): ScenePhase {
    if (progress01 < enter01) return 'enter'
    if (progress01 > (1 - exit01)) return 'exit'
    return 'idle'
}

export interface SceneControllerOptions {
    /** Initial scene index (0-4, default 0) */
    initialSceneIndex?: number
}

export class SceneController {
    private raf = 0
    private running = false
    private sceneIndex = 0
    private sceneStart = 0
    private listeners = new Set<(state: SceneState) => void>()

    constructor(opts: SceneControllerOptions = {}) {
        this.sceneIndex = opts.initialSceneIndex ?? 0
    }

    /**
     * Register a listener for scene state updates
     * Returns unsubscribe function
     */
    onUpdate(cb: (state: SceneState) => void): () => void {
        this.listeners.add(cb)
        return () => this.listeners.delete(cb)
    }

    /**
     * Start the scene rotation loop
     */
    start(): void {
        if (this.running) return
        this.running = true
        this.sceneStart = performance.now()
        this.tick()
    }

    /**
     * Stop the scene rotation loop
     */
    stop(): void {
        this.running = false
        cancelAnimationFrame(this.raf)
    }

    /**
     * Reset to first scene
     */
    reset(): void {
        this.sceneIndex = 0
        this.sceneStart = performance.now()
    }

    /**
     * Get current scene index
     */
    getCurrentSceneIndex(): number {
        return this.sceneIndex
    }

    private emit(state: SceneState): void {
        for (const cb of this.listeners) {
            cb(state)
        }
    }

    private tick = (): void => {
        if (!this.running) return

        const now = performance.now()
        const scene = SCENE_MANIFEST[this.sceneIndex]
        const elapsed = now - this.sceneStart
        const progress01 = clamp01(elapsed / scene.durationMs)

        const phase = phaseFor(progress01, scene.enter01, scene.exit01)
        const visualIntensity = sampleCurve(scene.intensity, progress01)

        this.emit({
            sceneId: scene.id,
            phase,
            visualIntensity,
            sceneTimeMs: elapsed,
            progress01
        })

        // Check for scene transition
        if (elapsed >= scene.durationMs) {
            this.sceneIndex = (this.sceneIndex + 1) % SCENE_MANIFEST.length
            this.sceneStart = now
        }

        this.raf = requestAnimationFrame(this.tick)
    }
}
