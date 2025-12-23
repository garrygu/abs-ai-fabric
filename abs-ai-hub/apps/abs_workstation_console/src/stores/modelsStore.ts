import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchInstalledModels, type InstalledModel } from '@/services/api'

export const useModelsStore = defineStore('models', () => {
    const models = ref<InstalledModel[]>([])
    const isLoading = ref(false)
    const error = ref<string | null>(null)

    const llmModels = computed(() =>
        models.value.filter(m => m.type === 'llm')
    )

    const imageModels = computed(() =>
        models.value.filter(m => m.type === 'image')
    )

    const embeddingModels = computed(() =>
        models.value.filter(m => m.type === 'embedding')
    )

    const readyModels = computed(() =>
        models.value.filter(m => m.serving_status === 'ready')
    )

    const totalSize = computed(() =>
        models.value.reduce((sum, m) => sum + (m.size_gb || 0), 0)
    )

    async function fetchModels() {
        try {
            isLoading.value = true
            error.value = null
            models.value = await fetchInstalledModels()
        } catch (err) {
            error.value = err instanceof Error ? err.message : 'Failed to fetch models'
        } finally {
            isLoading.value = false
        }
    }

    function getModelTypeIcon(type: string): string {
        const icons: Record<string, string> = {
            'llm': '🧠',
            'image': '🎨',
            'embedding': '📊'
        }
        return icons[type] || '📦'
    }

    function getModelTypeLabel(type: string): string {
        const labels: Record<string, string> = {
            'llm': 'Language Model',
            'image': 'Image Generation',
            'embedding': 'Embedding Model'
        }
        return labels[type] || type
    }

    return {
        models,
        isLoading,
        error,
        llmModels,
        imageModels,
        embeddingModels,
        readyModels,
        totalSize,
        fetchModels,
        getModelTypeIcon,
        getModelTypeLabel
    }
})
