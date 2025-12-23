import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchActiveWorkloads, type RunningWorkload } from '@/services/api'

export const useWorkloadsStore = defineStore('workloads', () => {
    const workloads = ref<RunningWorkload[]>([])
    const isLoading = ref(false)
    const error = ref<string | null>(null)

    const activeWorkloads = computed(() =>
        workloads.value.filter(w => w.status === 'running')
    )

    const idleWorkloads = computed(() =>
        workloads.value.filter(w => w.status === 'idle')
    )

    const totalActive = computed(() => activeWorkloads.value.length)

    async function fetchWorkloads() {
        try {
            isLoading.value = true
            error.value = null
            workloads.value = await fetchActiveWorkloads()
        } catch (err) {
            error.value = err instanceof Error ? err.message : 'Failed to fetch workloads'
        } finally {
            isLoading.value = false
        }
    }

    function getWorkloadTypeLabel(type: string): string {
        const labels: Record<string, string> = {
            'llm_inference': 'LLM Inference',
            'rag': 'RAG + Embeddings',
            'embedding': 'Embeddings',
            'model_management': 'Model Management'
        }
        return labels[type] || type
    }

    return {
        workloads,
        isLoading,
        error,
        activeWorkloads,
        idleWorkloads,
        totalActive,
        fetchWorkloads,
        getWorkloadTypeLabel
    }
})
