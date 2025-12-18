import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gateway, type Asset } from '@/services/gateway'

export const useAssetStore = defineStore('assets', () => {
    // State
    const assets = ref<Asset[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)
    const selectedAssetId = ref<string | null>(null)

    // UI State
    const viewMode = ref<'table' | 'grid'>('table')
    const searchQuery = ref('')
    const activeTypeFilter = ref<string | null>(null) // null = All

    // Getters
    const selectedAsset = computed(() =>
        assets.value.find(a => a.id === selectedAssetId.value)
    )

    // Get unique asset types/classes
    const assetTypes = computed(() => {
        const types = new Set<string>()
        assets.value.forEach(asset => {
            if (asset.class) types.add(asset.class)
        })
        return Array.from(types).sort()
    })

    // Filtered assets based on search and type filter
    const filteredAssets = computed(() => {
        let result = assets.value

        // Filter by type
        if (activeTypeFilter.value) {
            result = result.filter(a => a.class === activeTypeFilter.value)
        }

        // Filter by search query
        if (searchQuery.value.trim()) {
            const query = searchQuery.value.toLowerCase()
            result = result.filter(a =>
                a.id.toLowerCase().includes(query) ||
                (a.display_name?.toLowerCase().includes(query)) ||
                (a.class?.toLowerCase().includes(query)) ||
                (a.interface?.toLowerCase().includes(query))
            )
        }

        return result
    })

    const assetsByClass = computed(() => {
        const grouped: Record<string, Asset[]> = {}
        filteredAssets.value.forEach(asset => {
            const cls = asset.class || 'unknown'
            if (!grouped[cls]) grouped[cls] = []
            grouped[cls].push(asset)
        })
        return grouped
    })

    const healthyAssets = computed(() =>
        assets.value.filter(a => a.status === 'ready' || a.status === 'running')
    )

    // Asset counts by type
    const assetCounts = computed(() => {
        const counts: Record<string, number> = { all: assets.value.length }
        assets.value.forEach(asset => {
            const cls = asset.class || 'unknown'
            counts[cls] = (counts[cls] || 0) + 1
        })
        return counts
    })

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

    function setViewMode(mode: 'table' | 'grid') {
        viewMode.value = mode
    }

    function setSearchQuery(query: string) {
        searchQuery.value = query
    }

    function setTypeFilter(type: string | null) {
        activeTypeFilter.value = type
    }

    return {
        // State
        assets,
        loading,
        error,
        selectedAssetId,
        viewMode,
        searchQuery,
        activeTypeFilter,
        // Getters
        selectedAsset,
        assetTypes,
        filteredAssets,
        assetsByClass,
        healthyAssets,
        assetCounts,
        // Actions
        fetchAssets,
        fetchAsset,
        selectAsset,
        setViewMode,
        setSearchQuery,
        setTypeFilter
    }
})
