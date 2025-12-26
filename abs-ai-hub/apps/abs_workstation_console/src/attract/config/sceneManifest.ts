/**
 * Scene Manifest — Timing + Intensity Curves
 * 
 * Data-driven configuration for all 5 scenes.
 * Durations and intensity curves match the Visual Design spec.
 */

import type { SceneId } from '@/attract/contracts/attract'

/** Keyframe for intensity curve: t01 is progress (0..1), v is intensity (0..1) */
export interface IntensityKey {
    t01: number
    v: number
}

/** Configuration for a single scene */
export interface SceneManifestItem {
    id: SceneId
    name: string
    durationMs: number
    /** Phase split: enter phase ends at this progress (default 0.12) */
    enter01?: number
    /** Phase split: exit phase starts at (1 - exit01) (default 0.12) */
    exit01?: number
    /** Intensity curve keyframes */
    intensity: IntensityKey[]
}

/**
 * Scene Manifest — matches timing from Visual Design & Motion Prototyping spec
 * 
 * Total loop: ~43s (9 + 11 + 9 + 7 + 7) in production
 * 
 * DEV_MODE: Set to true for faster testing (3s per scene)
 */
export const DEV_MODE = false  // Toggle for faster testing

/** Duration multiplier for dev mode */
const DURATION_MULT = DEV_MODE ? 0.33 : 1.0  // ~3x faster in dev mode

export const SCENE_MANIFEST: SceneManifestItem[] = [
    {
        id: 'sceneA',
        name: 'Hero System Status',
        durationMs: 9000 * DURATION_MULT,
        intensity: [
            { t01: 0.0, v: 0.20 },
            { t01: 0.5, v: 0.28 },
            { t01: 1.0, v: 0.22 }
        ]
    },
    {
        id: 'sceneB',
        name: 'Installed Models Power Wall',
        durationMs: 11000 * DURATION_MULT,
        intensity: [
            { t01: 0.0, v: 0.30 },
            { t01: 0.6, v: 0.45 },
            { t01: 1.0, v: 0.35 }
        ]
    },
    {
        id: 'sceneC',
        name: 'Live Load Surge',
        durationMs: 9000 * DURATION_MULT,
        intensity: [
            { t01: 0.0, v: 0.25 },
            { t01: 0.55, v: 0.60 },
            { t01: 0.78, v: 1.00 },  // Peak — only scene reaching 1.0
            { t01: 1.0, v: 0.35 }
        ]
    },
    {
        id: 'sceneD',
        name: 'Platform Message',
        durationMs: 7000 * DURATION_MULT,
        intensity: [
            { t01: 0.0, v: 0.20 },
            { t01: 0.55, v: 0.30 },
            { t01: 0.75, v: 0.55 },  // Small spike during cloud dissolve
            { t01: 1.0, v: 0.20 }
        ]
    },
    {
        id: 'sceneE',
        name: 'Gentle Invitation',
        durationMs: 7000 * DURATION_MULT,
        intensity: [
            { t01: 0.0, v: 0.18 },
            { t01: 0.6, v: 0.28 },
            { t01: 1.0, v: 0.22 }
        ]
    }
]

/** Total loop duration in milliseconds */
export const TOTAL_LOOP_MS = SCENE_MANIFEST.reduce((sum, s) => sum + s.durationMs, 0)

/** Default phase split percentages */
export const DEFAULT_ENTER_01 = 0.12
export const DEFAULT_EXIT_01 = 0.12
