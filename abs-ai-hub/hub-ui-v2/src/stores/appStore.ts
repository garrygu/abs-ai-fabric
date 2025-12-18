import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gateway, type App } from '@/services/gateway'

export const useAppStore = defineStore('apps', () => {
    // State
    const apps = ref<App[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)

    // Getters
    const installedApps = computed(() =>
        apps.value.filter(a => a.status === 'running' || a.status === 'ready')
    )

    const availableApps = computed(() =>
        apps.value.filter(a => a.status === 'available')
    )

    // Actions
    async function fetchApps() {
        loading.value = true
        error.value = null
        try {
            apps.value = await gateway.getApps()
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Failed to load apps'
        } finally {
            loading.value = false
        }
    }

    return {
        apps,
        loading,
        error,
        installedApps,
        availableApps,
        fetchApps
    }
})
