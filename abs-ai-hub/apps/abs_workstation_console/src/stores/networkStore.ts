import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Gateway base URL - configurable via VITE_GATEWAY_URL env var
const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://127.0.0.1:8081'
const OLLAMA_URL = 'http://localhost:11434'

export interface NetworkStatus {
  internet: 'online' | 'offline' | 'checking'
  gateway: 'online' | 'offline' | 'checking'
  ollama: 'online' | 'offline' | 'checking'
  lastChecked: Date | null
}

export const useNetworkStore = defineStore('network', () => {
  // State
  const internetStatus = ref<'online' | 'offline' | 'checking'>('checking')
  const gatewayStatus = ref<'online' | 'offline' | 'checking'>('checking')
  const ollamaStatus = ref<'online' | 'offline' | 'checking'>('checking')
  const lastChecked = ref<Date | null>(null)
  const showOfflineBanner = ref(false)

  // Computed
  const isFullyOnline = computed(() => {
    return internetStatus.value === 'online' && 
           gatewayStatus.value === 'online' && 
           ollamaStatus.value === 'online'
  })

  const isPartiallyOnline = computed(() => {
    return gatewayStatus.value === 'online' || ollamaStatus.value === 'online'
  })

  const hasInternet = computed(() => internetStatus.value === 'online')
  const hasGateway = computed(() => gatewayStatus.value === 'online')
  const hasOllama = computed(() => ollamaStatus.value === 'online')

  const statusMessage = computed(() => {
    if (isFullyOnline.value) return null
    
    const issues: string[] = []
    if (internetStatus.value === 'offline') issues.push('No internet connection')
    if (gatewayStatus.value === 'offline') issues.push('Gateway service unavailable')
    if (ollamaStatus.value === 'offline') issues.push('Ollama service unavailable')
    
    if (issues.length === 0) return null
    return issues.join(' • ')
  })

  // Check internet connectivity (external)
  async function checkInternet(): Promise<boolean> {
    internetStatus.value = 'checking'
    
    // Quick check with navigator.onLine
    if (!navigator.onLine) {
      internetStatus.value = 'offline'
      return false
    }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000)
      
      // Try a lightweight external endpoint
      await fetch('https://www.google.com/favicon.ico', {
        method: 'HEAD',
        mode: 'no-cors',
        signal: controller.signal,
        cache: 'no-cache'
      })
      
      clearTimeout(timeoutId)
      internetStatus.value = 'online'
      return true
    } catch (error) {
      internetStatus.value = 'offline'
      return false
    }
  }

  // Check Gateway service (local)
  async function checkGateway(): Promise<boolean> {
    gatewayStatus.value = 'checking'
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 2000)
      
      const response = await fetch(`${GATEWAY_URL}/v1/admin/system/metrics`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        gatewayStatus.value = 'online'
        return true
      } else {
        gatewayStatus.value = 'offline'
        return false
      }
    } catch (error) {
      gatewayStatus.value = 'offline'
      return false
    }
  }

  // Check Ollama service (local)
  async function checkOllama(): Promise<boolean> {
    ollamaStatus.value = 'checking'
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 2000)
      
      const response = await fetch(`${OLLAMA_URL}/api/tags`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        ollamaStatus.value = 'online'
        return true
      } else {
        ollamaStatus.value = 'offline'
        return false
      }
    } catch (error) {
      ollamaStatus.value = 'offline'
      return false
    }
  }

  // Check all services
  async function checkAllServices() {
    lastChecked.value = new Date()
    
    // Check all in parallel
    await Promise.all([
      checkInternet(),
      checkGateway(),
      checkOllama()
    ])
    
    // Show banner if any critical service is offline
    showOfflineBanner.value = !isFullyOnline.value
  }

  // Start periodic checking
  let checkInterval: ReturnType<typeof setInterval> | null = null
  
  function startPeriodicCheck(intervalMs: number = 30000) {
    if (checkInterval) return
    
    // Check immediately
    checkAllServices()
    
    // Then check periodically
    checkInterval = setInterval(checkAllServices, intervalMs)
    
    // Also listen to browser online/offline events
    window.addEventListener('online', () => {
      checkInternet()
      checkAllServices()
    })
    
    window.addEventListener('offline', () => {
      internetStatus.value = 'offline'
      showOfflineBanner.value = true
    })
  }

  function stopPeriodicCheck() {
    if (checkInterval) {
      clearInterval(checkInterval)
      checkInterval = null
    }
  }

  function dismissBanner() {
    showOfflineBanner.value = false
  }

  return {
    // State
    internetStatus,
    gatewayStatus,
    ollamaStatus,
    lastChecked,
    showOfflineBanner,
    
    // Computed
    isFullyOnline,
    isPartiallyOnline,
    hasInternet,
    hasGateway,
    hasOllama,
    statusMessage,
    
    // Actions
    checkInternet,
    checkGateway,
    checkOllama,
    checkAllServices,
    startPeriodicCheck,
    stopPeriodicCheck,
    dismissBanner
  }
})

