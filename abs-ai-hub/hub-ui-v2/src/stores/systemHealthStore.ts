import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gateway, type ServiceStatus } from '@/services/gateway'

export const useSystemHealthStore = defineStore('systemHealth', () => {
    // State
    const services = ref<ServiceStatus[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)
    const lastUpdated = ref<Date | null>(null)

    // Getters
    const allHealthy = computed(() =>
        services.value.every(s => s.status === 'running')
    )

    const servicesByStatus = computed(() => ({
        running: services.value.filter(s => s.status === 'running'),
        stopped: services.value.filter(s => s.status === 'stopped'),
        error: services.value.filter(s => s.status === 'error')
    }))

    // Actions
    async function fetchStatus() {
        loading.value = true
        error.value = null
        try {
            services.value = await gateway.getServicesStatus()
            lastUpdated.value = new Date()
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Failed to fetch system health'
        } finally {
            loading.value = false
        }
    }

    async function refreshAll() {
        loading.value = true
        try {
            await gateway.refreshAll()
            await fetchStatus()
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Refresh failed'
        } finally {
            loading.value = false
        }
    }

    return {
        services,
        loading,
        error,
        lastUpdated,
        allHealthy,
        servicesByStatus,
        fetchStatus,
        refreshAll
    }
})
