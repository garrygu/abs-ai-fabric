/**
 * Scene Director - FSM that cycles through Attract Mode scenes
 * 
 * Owns timing, transitions, and "wow moments"
 * Emits SceneParams to render pipeline
 */

import { SceneParams } from './engine'
import { RenderState } from './engine'

export type SceneId = 'A' | 'B' | 'C' | 'D' | 'E'

export interface SceneConfig {
  id: SceneId
  name: string
  duration: number // Duration in seconds
}

export interface SceneDirector {
  update: (dt: number, renderState: RenderState) => SceneParams
  getCurrentScene: () => SceneId
  reset: () => void
}

const SCENES: SceneConfig[] = [
  { id: 'A', name: 'Hero System Status', duration: 9 },
  { id: 'B', name: 'Installed Models Power Wall', duration: 11 },
  { id: 'C', name: 'Live Load Surge', duration: 9 },
  { id: 'D', name: 'Platform Message', duration: 7 },
  { id: 'E', name: 'Gentle Invitation', duration: 7 }
]

const TRANSITION_DURATION = 1.0 // 0.8-1.2s transition

export function createSceneDirector(): SceneDirector {
  let currentSceneIndex = 0
  let sceneTime = 0
  let totalTime = 0
  let transitionTime = 0
  let isTransitioning = false

  function update(dt: number, renderState: RenderState): SceneParams {
    totalTime += dt
    sceneTime += dt

    const currentScene = SCENES[currentSceneIndex]
    const sceneDuration = currentScene.duration

    // Check if scene should end
    if (sceneTime >= sceneDuration && !isTransitioning) {
      isTransitioning = true
      transitionTime = 0
    }

    // Handle transition
    if (isTransitioning) {
      transitionTime += dt
      const transitionT01 = Math.min(1, transitionTime / TRANSITION_DURATION)

      if (transitionT01 >= 1) {
        // Move to next scene
        currentSceneIndex = (currentSceneIndex + 1) % SCENES.length
        sceneTime = 0
        isTransitioning = false
        transitionTime = 0
      }
    }

    // Calculate scene progress (0..1)
    const sceneT01 = Math.min(1, sceneTime / sceneDuration)

    // Calculate transition progress (0..1)
    const transitionT01 = isTransitioning ? Math.min(1, transitionTime / TRANSITION_DURATION) : 0

    // Calculate accent (how "hot" visuals should be)
    // Boost during high GPU util, warming, or running states
    let accent01 = renderState.gpuUtil01 * 0.5
    if (renderState.modelState === 'warming') {
      accent01 = Math.max(accent01, 0.7)
    } else if (renderState.modelState === 'running') {
      accent01 = Math.max(accent01, 0.8)
    }

    // Camera jitter (subtle, for load events)
    let cameraJitter01 = 0
    if (renderState.modelState === 'warming' && renderState.coldStartProgress01 > 0.7) {
      // Jitter during high load spin-up
      cameraJitter01 = Math.sin(totalTime * 10) * 0.02 * renderState.coldStartProgress01
    } else if (renderState.gpuUtil01 > 0.6) {
      // Micro-jitter during high GPU load
      cameraJitter01 = Math.sin(totalTime * 5) * 0.01 * (renderState.gpuUtil01 - 0.6) * 2.5
    }

    return {
      sceneId: currentScene.id,
      sceneT01,
      transitionT01,
      accent01: Math.max(0, Math.min(1, accent01)),
      cameraJitter01: Math.max(0, Math.min(0.05, cameraJitter01))
    }
  }

  function getCurrentScene(): SceneId {
    return SCENES[currentSceneIndex].id
  }

  function reset() {
    currentSceneIndex = 0
    sceneTime = 0
    totalTime = 0
    transitionTime = 0
    isTransitioning = false
  }

  return {
    update,
    getCurrentScene,
    reset
  }
}

