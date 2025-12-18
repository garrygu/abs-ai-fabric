import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gateway, type Asset } from '@/services/gateway'

export const useAssetStore = defineStore('assets', () => {
    // State
    const assets = ref<Asset[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)
    const selectedAssetId = ref<string | null>(null)

    // Getters
    const selectedAsset = computed(() =>
        assets.value.find(a => a.id === selectedAssetId.value)
    )

    const assetsByClass = computed(() => {
        const grouped: Record<string, Asset[]> = {}
        assets.value.forEach(asset => {
            const cls = asset.class || 'unknown'
            if (!grouped[cls]) grouped[cls] = []
            grouped[cls].push(asset)
        })
        return grouped
    })

    const healthyAssets = computed(() =>
        assets.value.filter(a => a.status === 'ready' || a.status === 'running')
    )

    // Actions - Always re-fetch, Gateway is source of truth
    async function fetchAssets() {
        loading.value = true
        error.value = null
        try {
            assets.value = await gateway.getAssets()
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Failed to load assets'
        } finally {
            loading.value = false
        }
    }

    async function fetchAsset(id: string) {
        loading.value = true
        error.value = null
        try {
            const asset = await gateway.getAsset(id)
            // Update in list if exists, otherwise add
            const idx = assets.value.findIndex(a => a.id === id)
            if (idx >= 0) {
                assets.value[idx] = asset
            } else {
                assets.value.push(asset)
            }
            selectedAssetId.value = id
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Failed to load asset'
        } finally {
            loading.value = false
        }
    }

    function selectAsset(id: string | null) {
        selectedAssetId.value = id
    }

    return {
        // State
        assets,
        loading,
        error,
        selectedAssetId,
        // Getters
        selectedAsset,
        assetsByClass,
        healthyAssets,
        // Actions
        fetchAssets,
        fetchAsset,
        selectAsset
    }
})
