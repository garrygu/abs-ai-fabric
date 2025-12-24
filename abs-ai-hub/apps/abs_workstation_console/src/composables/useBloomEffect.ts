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
  
  // Bloom radius based on activity
  const bloomRadius = computed(() => {
    if (demoControlStore.isRunning) return 20
    if (demoControlStore.isWarming) return 15
    return 10
  })
  
  // CSS filter string for bloom effect
  const bloomFilter = computed(() => {
    const intensity = bloomIntensity.value
    const radius = bloomRadius.value
    return `blur(${radius}px) brightness(${1 + intensity * 0.5})`
  })
  
  // HDR-style glow for specific elements
  const getElementGlow = (baseColor: string, intensity: number = 1) => {
    const glowIntensity = bloomIntensity.value * intensity
    return {
      filter: `drop-shadow(0 0 ${bloomRadius.value * 2}px ${baseColor}) drop-shadow(0 0 ${bloomRadius.value}px ${baseColor})`,
      boxShadow: `0 0 ${bloomRadius.value * 3}px ${baseColor}40, 0 0 ${bloomRadius.value * 1.5}px ${baseColor}60`,
      textShadow: `0 0 ${bloomRadius.value * 2}px ${baseColor}, 0 0 ${bloomRadius.value}px ${baseColor}`
    }
  }
  
  return {
    bloomIntensity,
    bloomRadius,
    bloomFilter,
    getElementGlow
  }
}

