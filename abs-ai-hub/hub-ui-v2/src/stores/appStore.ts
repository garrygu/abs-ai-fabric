import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gateway, type App } from '@/services/gateway'

export const useAppStore = defineStore('apps', () => {
    // State
    const apps = ref<App[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)
    const activeTab = ref<'installed' | 'store'>('installed')

    // Getters
    const installedApps = computed(() =>
        apps.value.filter(a =>
            (a.status === 'online' || a.status === 'offline') &&
            a.id !== 'deposition-summarizer'  // Exclude from installed, keep in store
        )
    )

    const onlineApps = computed(() =>
        apps.value.filter(a => a.status === 'online')
    )

    const offlineApps = computed(() =>
        apps.value.filter(a => a.status === 'offline')
    )

    const appsByCategory = computed(() => {
        const grouped: Record<string, App[]> = {}
        apps.value.forEach(app => {
            const cat = app.category || 'Uncategorized'
            if (!grouped[cat]) grouped[cat] = []
            grouped[cat].push(app)
        })
        return grouped
    })

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

    function setActiveTab(tab: 'installed' | 'store') {
        activeTab.value = tab
    }

    function getApp(id: string): App | undefined {
        return apps.value.find(a => a.id === id)
    }

    return {
        apps,
        loading,
        error,
        activeTab,
        installedApps,
        onlineApps,
        offlineApps,
        appsByCategory,
        fetchApps,
        setActiveTab,
        getApp
    }
})
