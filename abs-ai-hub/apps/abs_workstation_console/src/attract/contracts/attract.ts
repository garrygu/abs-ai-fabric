/**
 * Attract Mode Contracts — Type definitions
 * 
 * Shared types for controller, engine, and UI layers.
 * These types are the contract between components.
 */

/** Scene identifiers matching the 5-scene structure */
export type SceneId = 'sceneA' | 'sceneB' | 'sceneC' | 'sceneD' | 'sceneE'

/** Scene phase within a scene's lifecycle */
export type ScenePhase = 'enter' | 'idle' | 'exit'

/** Complete scene state emitted by controller on each frame */
export interface SceneState {
    /** Current scene identifier */
    sceneId: SceneId
    /** Current phase within scene */
    phase: ScenePhase
    /** Normalized visual intensity (0..1) from intensity curve */
    visualIntensity: number
    /** Milliseconds since scene started */
    sceneTimeMs: number
    /** Progress within scene (0..1) */
    progress01: number
}

/** Telemetry snapshot for read-only display */
export interface TelemetrySnapshot {
    /** GPU utilization (0..1) */
    gpuUtil01: number
    /** VRAM used in MB */
    vramUsedMB: number
    /** VRAM total in MB */
    vramTotalMB: number
    /** RAM used in MB */
    ramUsedMB: number
    /** RAM total in MB */
    ramTotalMB: number
    /** System uptime in seconds */
    uptimeSeconds: number
    /** Model states */
    models: ModelState[]
    /** Timestamp of snapshot */
    timestamp: number
}

/** Individual model state */
export interface ModelState {
    modelId: string
    displayName: string
    class: 'llm' | 'auxiliary'
    state: 'RUNNING' | 'READY' | 'IDLE'
    sizeGB?: number
}

/** Scene C control plane mode */
export type SceneCMode = 'AUTO' | 'LIVE' | 'SHOWCASE'

/** Scene C request to control plane */
export interface SceneCRequest {
    sceneId: 'sceneC'
    requestedIntent: 'LOAD_ACTIVITY'
    visualContext?: {
        currentScene: string
        desiredIntensity: 'LOW' | 'HIGH'
    }
}

/** Scene C control plane response */
export interface SceneCResponse {
    approved: boolean
    mode: SceneCMode
    constraints?: {
        maxDurationSeconds: number
        maxVramMB: number
    }
    reason?: string
}
