import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchSystemMetrics, type SystemMetrics, formatUptime } from '@/services/api'

export const useMetricsStore = defineStore('metrics', () => {
    const metrics = ref<SystemMetrics | null>(null)
    const lastUpdated = ref<Date | null>(null)
    const isLoading = ref(false)
    const error = ref<string | null>(null)

    // Polling interval handle
    let pollInterval: ReturnType<typeof setInterval> | null = null

    // Computed values for easy template access
    const gpuUtilization = computed(() => metrics.value?.gpu.utilization_pct ?? 0)
    const gpuModel = computed(() => metrics.value?.gpu.model ?? 'Unknown GPU')
    const vramUsed = computed(() => metrics.value?.gpu.vram_used_gb ?? 0)
    const vramTotal = computed(() => metrics.value?.gpu.vram_total_gb ?? 0)
    const vramPercent = computed(() => vramTotal.value ? (vramUsed.value / vramTotal.value) * 100 : 0)

    const cpuUtilization = computed(() => metrics.value?.cpu.utilization_pct ?? 0)

    const memoryUsed = computed(() => metrics.value?.memory.used_gb ?? 0)
    const memoryTotal = computed(() => metrics.value?.memory.total_gb ?? 0)
    const memoryPercent = computed(() => memoryTotal.value ? (memoryUsed.value / memoryTotal.value) * 100 : 0)

    const diskRead = computed(() => metrics.value?.disk?.read_mb_s ?? 0)
    const diskWrite = computed(() => metrics.value?.disk?.write_mb_s ?? 0)

    const uptimeFormatted = computed(() => {
        return metrics.value ? formatUptime(metrics.value.uptime_seconds) : '00:00:00'
    })

    const timeSinceUpdate = computed(() => {
        if (!lastUpdated.value) return 'Never'
        const seconds = Math.floor((Date.now() - lastUpdated.value.getTime()) / 1000)
        return `${seconds}s ago`
    })

    async function fetchMetrics() {
        try {
            isLoading.value = true
            error.value = null
            const result = await fetchSystemMetrics()
            console.log('[MetricsStore] Received metrics:', result)
            console.log('[MetricsStore] GPU data:', result?.gpu)
            metrics.value = result
            lastUpdated.value = new Date()
        } catch (err) {
            console.error('[MetricsStore] Error fetching metrics:', err)
            error.value = err instanceof Error ? err.message : 'Failed to fetch metrics'
        } finally {
            isLoading.value = false
        }
    }

    function startPolling(intervalMs: number = 2000) {
        if (pollInterval) return

        // Fetch immediately
        fetchMetrics()

        // Then poll at interval
        pollInterval = setInterval(fetchMetrics, intervalMs)
    }

    function stopPolling() {
        if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
        }
    }

    return {
        // State
        metrics,
        lastUpdated,
        isLoading,
        error,

        // Computed
        gpuUtilization,
        gpuModel,
        vramUsed,
        vramTotal,
        vramPercent,
        cpuUtilization,
        memoryUsed,
        memoryTotal,
        memoryPercent,
        diskRead,
        diskWrite,
        uptimeFormatted,
        timeSinceUpdate,

        // Actions
        fetchMetrics,
        startPolling,
        stopPolling
    }
})
