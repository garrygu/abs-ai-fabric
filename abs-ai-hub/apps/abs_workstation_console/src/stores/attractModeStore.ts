import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useMetricsStore } from './metricsStore'

export const useAttractModeStore = defineStore('attractMode', () => {
    const isActive = ref(false)
    const isEnabled = ref(true)
    const idleTimeoutMs = ref(120000) // 2 minutes
    const currentVisual = ref<'system' | 'image' | 'llm'>('system')

    // GPU budget settings
    const gpuSoftCapPct = ref(60)
    const gpuHardCapPct = ref(70)
    const isPaused = ref(false)

    // Track last activity
    const lastActivityTime = ref(Date.now())
    let idleCheckInterval: ReturnType<typeof setInterval> | null = null

    const metricsStore = useMetricsStore()

    const shouldThrottle = computed(() => {
        const gpuUtil = metricsStore.gpuUtilization
        return gpuUtil > gpuSoftCapPct.value
    })

    const shouldPause = computed(() => {
        const gpuUtil = metricsStore.gpuUtilization
        return gpuUtil > gpuHardCapPct.value
    })

    function activate() {
        if (!isEnabled.value) return
        isActive.value = true
        console.log('[AttractMode] Activated')
    }

    function deactivate() {
        isActive.value = false
        lastActivityTime.value = Date.now()
        console.log('[AttractMode] Deactivated')
    }

    function recordActivity() {
        lastActivityTime.value = Date.now()
        if (isActive.value) {
            deactivate()
        }
    }

    function checkIdle() {
        if (!isEnabled.value || isActive.value) return

        const idleTime = Date.now() - lastActivityTime.value
        if (idleTime >= idleTimeoutMs.value) {
            activate()
        }
    }

    function startIdleDetection() {
        if (idleCheckInterval) return

        // Set up event listeners
        const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'wheel']
        events.forEach(event => {
            window.addEventListener(event, recordActivity, { passive: true })
        })

        // Check idle state every second
        idleCheckInterval = setInterval(checkIdle, 1000)

        console.log('[AttractMode] Idle detection started')
    }

    function stopIdleDetection() {
        if (idleCheckInterval) {
            clearInterval(idleCheckInterval)
            idleCheckInterval = null
        }

        const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'wheel']
        events.forEach(event => {
            window.removeEventListener(event, recordActivity)
        })

        console.log('[AttractMode] Idle detection stopped')
    }

    function setVisual(visual: 'system' | 'image' | 'llm') {
        currentVisual.value = visual
    }

    function enable() {
        isEnabled.value = true
    }

    function disable() {
        isEnabled.value = false
        if (isActive.value) {
            deactivate()
        }
    }

    return {
        // State
        isActive,
        isEnabled,
        idleTimeoutMs,
        currentVisual,
        gpuSoftCapPct,
        gpuHardCapPct,
        isPaused,

        // Computed
        shouldThrottle,
        shouldPause,

        // Actions
        activate,
        deactivate,
        recordActivity,
        startIdleDetection,
        stopIdleDetection,
        setVisual,
        enable,
        disable
    }
})
