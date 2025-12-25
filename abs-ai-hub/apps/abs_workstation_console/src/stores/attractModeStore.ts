import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useMetricsStore } from './metricsStore'
import { DEV_MODE } from '@/attract/config/sceneManifest'

export type SceneId = 'A' | 'B' | 'C' | 'D' | 'E'

export interface SceneConfig {
    id: SceneId
    name: string
    duration: number // Duration in milliseconds
}

export const useAttractModeStore = defineStore('attractMode', () => {
    const isActive = ref(false)
    const isEnabled = ref(true)
    const idleTimeoutMs = ref(DEV_MODE ? 10000 : 120000) // 10s in dev, 2min in prod

    // Scene-based system
    const currentScene = ref<SceneId>('A')
    const sceneIndex = ref(0)

    // Scene configurations: A-E with durations (8-15 seconds)
    const scenes: SceneConfig[] = [
        { id: 'A', name: 'Hero System Status', duration: 9000 }, // 8-10s, using 9s
        { id: 'B', name: 'Installed Models Power Wall', duration: 11000 }, // 10-12s, using 11s
        { id: 'C', name: 'Live Load Surge', duration: 9000 }, // 8-10s, using 9s
        { id: 'D', name: 'Platform Message', duration: 7000 }, // 6-8s, using 7s
        { id: 'E', name: 'Gentle Invitation', duration: 7000 } // 6-8s, using 7s
    ]

    // Total loop time: ~43 seconds (within 45-55s target)

    // GPU budget settings
    const gpuSoftCapPct = ref(60)
    const gpuHardCapPct = ref(70)
    const isPaused = ref(false)

    // Track last activity
    const lastActivityTime = ref(Date.now())
    let idleCheckInterval: ReturnType<typeof setInterval> | null = null
    let sceneTimer: ReturnType<typeof setTimeout> | null = null

    // Easter egg power flex (every ~3 minutes)
    const easterEggActive = ref(false)
    let easterEggTimer: ReturnType<typeof setTimeout> | null = null
    const EASTER_EGG_INTERVAL = 180000 // 3 minutes

    const metricsStore = useMetricsStore()

    const shouldThrottle = computed(() => {
        const gpuUtil = metricsStore.gpuUtilization
        return gpuUtil > gpuSoftCapPct.value
    })

    const shouldPause = computed(() => {
        const gpuUtil = metricsStore.gpuUtilization
        return gpuUtil > gpuHardCapPct.value
    })

    const currentSceneConfig = computed(() => scenes[sceneIndex.value])

    function activate() {
        if (!isEnabled.value) return
        isActive.value = true
        sceneIndex.value = 0
        currentScene.value = scenes[0].id
        startSceneTimer()
        startEasterEggTimer()
        console.log('[AttractMode] Activated, starting Scene A')
    }

    function deactivate() {
        isActive.value = false
        lastActivityTime.value = Date.now()
        stopSceneTimer()
        stopEasterEggTimer()
        easterEggActive.value = false
        console.log('[AttractMode] Deactivated')
    }

    function startEasterEggTimer() {
        stopEasterEggTimer()
        easterEggTimer = setTimeout(() => {
            if (isActive.value) {
                triggerEasterEgg()
                startEasterEggTimer() // Schedule next one
            }
        }, EASTER_EGG_INTERVAL)
    }

    function stopEasterEggTimer() {
        if (easterEggTimer) {
            clearTimeout(easterEggTimer)
            easterEggTimer = null
        }
    }

    function triggerEasterEgg() {
        easterEggActive.value = true
        console.log('[AttractMode] Easter egg power flex triggered')

        // Auto-hide after 5 seconds
        setTimeout(() => {
            easterEggActive.value = false
        }, 5000)
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

    function startSceneTimer() {
        stopSceneTimer()
        const config = currentSceneConfig.value
        sceneTimer = setTimeout(() => {
            nextScene()
        }, config.duration)
    }

    function stopSceneTimer() {
        if (sceneTimer) {
            clearTimeout(sceneTimer)
            sceneTimer = null
        }
    }

    function nextScene() {
        sceneIndex.value = (sceneIndex.value + 1) % scenes.length
        currentScene.value = scenes[sceneIndex.value].id
        startSceneTimer()
        console.log(`[AttractMode] Advanced to Scene ${currentScene.value}`)
    }

    function previousScene() {
        sceneIndex.value = (sceneIndex.value - 1 + scenes.length) % scenes.length
        currentScene.value = scenes[sceneIndex.value].id
        startSceneTimer()
        console.log(`[AttractMode] Went back to Scene ${currentScene.value}`)
    }

    function goToScene(sceneId: SceneId) {
        const index = scenes.findIndex(s => s.id === sceneId)
        if (index !== -1) {
            sceneIndex.value = index
            currentScene.value = sceneId
            startSceneTimer()
            console.log(`[AttractMode] Jumped to Scene ${sceneId}`)
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

        stopSceneTimer()
        stopEasterEggTimer()

        const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'wheel']
        events.forEach(event => {
            window.removeEventListener(event, recordActivity)
        })

        console.log('[AttractMode] Idle detection stopped')
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
        currentScene,
        sceneIndex,
        scenes,
        gpuSoftCapPct,
        gpuHardCapPct,
        isPaused,
        easterEggActive,

        // Computed
        shouldThrottle,
        shouldPause,
        currentSceneConfig,

        // Actions
        activate,
        deactivate,
        recordActivity,
        startIdleDetection,
        stopIdleDetection,
        nextScene,
        previousScene,
        goToScene,
        enable,
        disable,
        triggerEasterEgg
    }
})
