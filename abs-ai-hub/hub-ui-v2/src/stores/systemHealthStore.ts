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
        services.value.every((s: ServiceStatus) => s.status === 'healthy')
    )

    const servicesByStatus = computed(() => ({
        running: services.value.filter((s: ServiceStatus) => ['running', 'healthy', 'degraded'].includes(s.status)),
        stopped: services.value.filter((s: ServiceStatus) => s.status === 'stopped'),
        error: services.value.filter((s: ServiceStatus) => ['error', 'unhealthy'].includes(s.status))
    }))

    // Actions
    async function fetchStatus() {
        loading.value = true
        error.value = null
        try {
            const result = await gateway.getServicesStatus()
            // Transform object { serviceName: { status, version, running } } to array
            services.value = Object.entries(result).map(([name, data]) => {
                const serviceData = data as { status: string; running?: boolean; version?: string }
                return {
                    name,
                    status: serviceData.status as ServiceStatus['status'],
                    running: serviceData.running,
                    version: serviceData.version
                }
            })
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
