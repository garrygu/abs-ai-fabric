import { ref, computed } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useDemoControlStore } from '@/stores/demoControlStore'

export function useBloomEffect() {
  const metricsStore = useMetricsStore()
  const demoControlStore = useDemoControlStore()

  // Bloom intensity based on GPU utilization and model state
  const bloomIntensity = computed(() => {
    const baseIntensity = metricsStore.gpuUtilization / 100
    const modelBoost = demoControlStore.isRunning ? 0.3 : (demoControlStore.isWarming ? 0.15 : 0)
    return Math.min(1, baseIntensity * 0.5 + modelBoost)
  })

  // Bloom radius based on activity - REDUCED for readability
  const bloomRadius = computed(() => {
    if (demoControlStore.isRunning) return 8
    if (demoControlStore.isWarming) return 6
    return 4
  })

  // CSS filter string for bloom effect - REDUCED intensity
  const bloomFilter = computed(() => {
    const intensity = bloomIntensity.value
    const radius = bloomRadius.value
    return `blur(${radius * 0.5}px) brightness(${1 + intensity * 0.2})`
  })

  // HDR-style glow for specific elements - REDUCED for text clarity
  const getElementGlow = (baseColor: string, intensity: number = 1) => {
    const radius = bloomRadius.value
    // Subtle glow that doesn't overwhelm text
    return {
      filter: `drop-shadow(0 0 ${radius}px ${baseColor})`,
      boxShadow: `0 0 ${radius * 1.5}px ${baseColor}30, 0 0 ${radius}px ${baseColor}20`,
      textShadow: `0 0 ${radius}px ${baseColor}80`
    }
  }

  return {
    bloomIntensity,
    bloomRadius,
    bloomFilter,
    getElementGlow
  }
}

