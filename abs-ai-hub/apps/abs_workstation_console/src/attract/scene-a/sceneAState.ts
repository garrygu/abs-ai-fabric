/**
 * Scene A State Machine
 * 
 * Implements 3-state system:
 * - IDLE_READY: Attract + "LOCAL AI / NO CLOUD" trust
 * - LOADING_70B: Process theatre during model loading
 * - LIVE_INFERENCE: Prove performance with real metrics
 * 
 * Based on scene_a_engineering_spec.md
 */

import { ref, computed, readonly } from 'vue'

// ============================================================================
// Types
// ============================================================================

export type SceneAState = 'IDLE_READY' | 'LOADING_70B' | 'LIVE_INFERENCE'

export type LoadPhase = 'pull' | 'quant' | 'warm' | 'ready'

export interface SceneATelemetry {
    ts: number                    // epoch ms
    gpuUtilPct: number            // 0-100
    vramUsedGB: number
    vramTotalGB: number
    ramUsedGB: number
    ramTotalGB: number
    uptimeSec: number

    // Optional "wow" fields
    activeModel?: string          // "Llama 70B"
    loadPhase?: LoadPhase
    loadProgress?: number         // 0..1
    tokPerSec?: number
    ttftMs?: number
    contextTokens?: number
}

export interface SceneAUniforms {
    state: SceneAState
    gpuUtil01: number             // 0..1
    tokPulse01: number            // 0..1 (tok/s normalized)
    progress01: number            // 0..1 (load progress)
    isTelemetryFresh: boolean
}

// ============================================================================
// EMA Smoothing
// ============================================================================

function ema(prev: number, next: number, alpha = 0.15): number {
    return prev + alpha * (next - prev)
}

function clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value))
}

// ============================================================================
// State Controller
// ============================================================================

export function createSceneAController() {
    // State
    const state = ref<SceneAState>('IDLE_READY')
    const lastTelemetryTs = ref(0)

    // Smoothed values
    const gpuUtil = ref(0)
    const tokPerSec = ref(0)
    const loadProgress = ref(0)

    // Raw telemetry (latest)
    const rawTelemetry = ref<SceneATelemetry | null>(null)

    // Stale threshold (3 seconds)
    const STALE_THRESHOLD_MS = 3000

    function enter(next: SceneAState) {
        if (state.value !== next) {
            console.log(`[SceneA] State transition: ${state.value} → ${next}`)
            state.value = next
        }
    }

    function onTelemetry(t: SceneATelemetry) {
        lastTelemetryTs.value = t.ts
        rawTelemetry.value = t

        // EMA smoothing
        gpuUtil.value = ema(gpuUtil.value, clamp(t.gpuUtilPct, 0, 100))

        if (t.tokPerSec != null) {
            tokPerSec.value = ema(tokPerSec.value, clamp(t.tokPerSec, 0, 200))
        }

        if (t.loadProgress != null) {
            loadProgress.value = ema(loadProgress.value, clamp(t.loadProgress, 0, 1))
        }

        // State decision logic
        if (t.loadProgress != null && t.loadProgress < 1 && t.loadProgress > 0) {
            // Model is loading
            enter('LOADING_70B')
        } else if (t.tokPerSec != null && t.tokPerSec > 0) {
            // Active inference
            enter('LIVE_INFERENCE')
        } else if (t.gpuUtilPct > 20) {
            // High GPU util = likely inference
            enter('LIVE_INFERENCE')
        } else {
            // Idle/ready state
            enter('IDLE_READY')
        }
    }

    function tick(now: number) {
        const stale = (now - lastTelemetryTs.value) > STALE_THRESHOLD_MS

        if (stale && state.value !== 'IDLE_READY') {
            // Telemetry stale - decay to IDLE
            enter('IDLE_READY')
            // Slowly decay smoothed values
            gpuUtil.value = ema(gpuUtil.value, 8, 0.05)  // Decay toward 8%
            tokPerSec.value = ema(tokPerSec.value, 0, 0.05)
        }
    }

    // Computed uniforms for WebGPU/visual layer
    const uniforms = computed<SceneAUniforms>(() => ({
        state: state.value,
        gpuUtil01: gpuUtil.value / 100,
        tokPulse01: Math.min(1, tokPerSec.value / 80),  // Normalize to 80 tok/s
        progress01: loadProgress.value,
        isTelemetryFresh: (Date.now() - lastTelemetryTs.value) < STALE_THRESHOLD_MS
    }))

    // Display values (for HUD)
    const display = computed(() => {
        const t = rawTelemetry.value

        return {
            state: state.value,
            gpuUtilPct: Math.round(gpuUtil.value),
            vramUsed: t?.vramUsedGB?.toFixed(0) ?? '—',
            vramTotal: t?.vramTotalGB?.toFixed(0) ?? '—',
            ramUsed: t?.ramUsedGB?.toFixed(0) ?? '—',
            ramTotal: t?.ramTotalGB?.toFixed(0) ?? '—',
            uptime: t?.uptimeSec ?? 0,

            // Loading state
            loadPhase: t?.loadPhase ?? null,
            loadProgressPct: Math.round(loadProgress.value * 100),

            // Live state
            tokPerSec: tokPerSec.value.toFixed(1),
            ttftMs: t?.ttftMs ?? null,
            activeModel: t?.activeModel ?? null,

            // Status label based on state
            statusLabel: getStatusLabel(state.value, t),
            isFresh: (Date.now() - lastTelemetryTs.value) < STALE_THRESHOLD_MS
        }
    })

    function getStatusLabel(s: SceneAState, t: SceneATelemetry | null): string {
        switch (s) {
            case 'IDLE_READY':
                // Consistent terminology: READY = models loaded into VRAM, IDLE = not loaded
                // Trust rule: high VRAM + low GPU = models loaded into VRAM
                if (t && t.vramUsedGB > 30 && t.gpuUtilPct < 10) {
                    return 'READY'
                }
                return 'IDLE'
            case 'LOADING_70B':
                const phase = t?.loadPhase ?? 'loading'
                const phaseLabelMap: Record<string, string> = {
                    pull: 'PULLING MODEL',
                    quant: 'QUANTIZING',
                    warm: 'WARMING UP',
                    ready: 'READY',
                    loading: 'LOADING'
                }
                return phaseLabelMap[phase] ?? 'LOADING'
            case 'LIVE_INFERENCE':
                return 'RUNNING'
        }
    }

    return {
        state: readonly(state),
        uniforms,
        display,
        onTelemetry,
        tick,
        enter  // Allow external state override (for demo)
    }
}

// Singleton instance for use across components
let _instance: ReturnType<typeof createSceneAController> | null = null

export function useSceneAController() {
    if (!_instance) {
        _instance = createSceneAController()
    }
    return _instance
}
