/**
 * Telemetry Adapter - Normalizes Gateway metrics to RenderState
 * 
 * Uses EMA smoothing to avoid jitter, polls Gateway at 5-10 Hz
 */

import { RenderState } from './engine'
import { useMetricsStore } from '@/stores/metricsStore'
import { useDemoControlStore } from '@/stores/demoControlStore'

export interface TelemetryAdapter {
  update: () => void
  getState: () => RenderState
  start: () => void
  stop: () => void
}

/**
 * Exponential Moving Average smoothing
 */
function ema(prev: number, next: number, alpha: number = 0.15): number {
  return prev + (next - prev) * alpha
}

/**
 * Create telemetry adapter that polls Gateway metrics
 */
export function createTelemetryAdapter(): TelemetryAdapter {
  const metricsStore = useMetricsStore()
  const demoControlStore = useDemoControlStore()

  // Smoothed values (EMA)
  let smoothedGpuUtil = 0
  let smoothedVramUtil = 0
  let smoothedRamUtil = 0

  // Time tracking
  let startTime = Date.now()
  let lastUpdateTime = Date.now()

  // Polling interval (5-10 Hz = 100-200ms)
  let pollInterval: ReturnType<typeof setInterval> | null = null
  const POLL_INTERVAL_MS = 150 // ~6.7 Hz

  function update() {
    const now = Date.now()
    const dt = (now - lastUpdateTime) / 1000
    lastUpdateTime = now

    // Get raw metrics
    const rawGpuUtil = metricsStore.gpuUtilization / 100
    const rawVramUtil = metricsStore.vramUsed / metricsStore.vramTotal
    const rawRamUtil = metricsStore.memoryUsed / metricsStore.memoryTotal

    // Apply EMA smoothing
    smoothedGpuUtil = ema(smoothedGpuUtil, rawGpuUtil, 0.15)
    smoothedVramUtil = ema(smoothedVramUtil, rawVramUtil, 0.15)
    smoothedRamUtil = ema(smoothedRamUtil, rawRamUtil, 0.15)
  }

  function getState(): RenderState {
    const now = Date.now()
    const timeSec = (now - startTime) / 1000
    const dtSec = Math.min(0.05, (now - lastUpdateTime) / 1000)

    // Determine model state
    let modelState: 'idle' | 'warming' | 'running' | 'error' = 'idle'
    if (demoControlStore.isWarming) {
      modelState = 'warming'
    } else if (demoControlStore.isRunning) {
      modelState = 'running'
    }

    // Cold start progress (for Scene C)
    let coldStartProgress01 = 0
    if (demoControlStore.isWarming && demoControlStore.loadingProgress > 0) {
      coldStartProgress01 = demoControlStore.loadingProgress / 100
    }

    return {
      gpuUtil01: Math.max(0, Math.min(1, smoothedGpuUtil)),
      vramUtil01: Math.max(0, Math.min(1, smoothedVramUtil)),
      ramUtil01: Math.max(0, Math.min(1, smoothedRamUtil)),
      modelState,
      coldStartProgress01,
      timeSec,
      dtSec
    }
  }

  function start() {
    if (pollInterval) return

    startTime = Date.now()
    lastUpdateTime = Date.now()

    // Initial update
    update()

    // Start polling
    pollInterval = setInterval(update, POLL_INTERVAL_MS)
  }

  function stop() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  return {
    update,
    getState,
    start,
    stop
  }
}

