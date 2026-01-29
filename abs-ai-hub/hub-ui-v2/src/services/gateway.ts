/**
 * Gateway API Service
 * Centralized API client for Hub Gateway communication.
 * UI = pure client, Gateway = source of truth
 */

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8081'

export interface Asset {
    id: string
    display_name?: string
    class: string
    interface: string
    status: string
    version?: string
    consumers?: string[]
    usage?: {
        gpu?: boolean
    }
}

export interface App {
    id: string
    name: string
    description: string
    category: string
    icon?: string
    url: string
    port: number
    status: 'online' | 'offline' | 'error'
    dependencies: string[]
    path?: string
    metadata?: any
    policy?: any
    lifecycle?: any
}

export interface ServiceStatus {
    name: string
    status: 'running' | 'stopped' | 'error' | 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
    running?: boolean
    version?: string
}

class GatewayService {
    private baseUrl: string

    constructor() {
        this.baseUrl = GATEWAY_URL
    }

    // ============== ASSETS ==============

    async getAssets(): Promise<Asset[]> {
        const response = await fetch(`${this.baseUrl}/v1/assets`)
        if (!response.ok) throw new Error('Failed to fetch assets')
        const data = await response.json()

        // Handle various response formats
        let assets: any[] = []
        if (Array.isArray(data)) assets = data
        else if (data.assets) assets = data.assets
        else if (data.value) assets = data.value

        // Normalize assets to ensure status is populated
        return assets.map(asset => ({
            ...asset,
            display_name: asset.display_name || asset.name || asset.id,
            status: this.deriveStatus(asset),
            usage: asset.usage || {}
        }))
    }

    /**
     * Derive status from available asset fields
     * Priority: status > lifecycle.desired > class-based default
     */
    private deriveStatus(asset: any): string {
        // If status is already set, use it
        if (asset.status && asset.status !== 'unknown') {
            return asset.status
        }

        // Check lifecycle.desired
        if (asset.lifecycle?.desired) {
            const desired = asset.lifecycle.desired.toLowerCase()
            if (desired === 'running' || desired === 'ready' || desired === 'online') {
                return 'ready'
            }
            if (desired === 'stopped' || desired === 'offline') {
                return 'stopped'
            }
        }

        // For models, check if they're loaded (have metadata)
        if (asset.class === 'model') {
            // Models are typically ready if they exist in the registry
            return 'ready'
        }

        // For services, check if there's a health endpoint defined
        if (asset.class === 'service' && asset.metadata?.health) {
            // Service has health endpoint configured - assume ready
            return 'ready'
        }

        // For apps, check if they have a URL configured  
        if ((asset.class === 'app' || asset.class === 'application') && asset.metadata?.url) {
            return 'ready'
        }

        // Default fallback
        return 'unknown'
    }

    async getAsset(id: string): Promise<Asset> {
        const response = await fetch(`${this.baseUrl}/v1/assets/${id}`)
        if (!response.ok) throw new Error(`Failed to fetch asset: ${id}`)
        return response.json()
    }

    // ============== APPS ==============

    async getApps(): Promise<App[]> {
        // Fetch assets to get app dependencies
        const assets = await this.getAssets()

        // Build dependency map from assets
        const assetMap = new Map<string, Asset>()
        assets.forEach(a => assetMap.set(a.id, a))

        // Filter UI apps and enrich with dependency info
        const uiApps = assets.filter(a =>
            a.interface === 'ui' ||
            a.class === 'application' ||
            a.class === 'app'
        )

        return uiApps.map(a => {
            const metadata = (a as any).metadata || {}
            const policy = (a as any).policy || {}
            const lifecycle = (a as any).lifecycle || {}

            // Get dependencies from policy.required_models
            const deps = policy.required_models || a.consumers || []

            // Determine status from asset status
            let status: 'online' | 'offline' | 'error' = 'offline'
            if (a.status === 'ready' || a.status === 'running' || a.status === 'online' || a.status === 'idle') {
                status = 'online'
            } else if (a.status === 'error') {
                status = 'error'
            }

            // Get the app URL and category from metadata
            const appUrl = metadata.url || ''
            const category = metadata.category || a.class || 'Application'

            const app: App = {
                id: a.id,
                name: a.display_name || a.id,
                description: (a as any).description || (a.version ? `Version ${a.version}` : ''),
                category,
                url: appUrl,
                port: metadata.port || 0,
                status,
                dependencies: deps,
                metadata: { ...metadata },
                policy: { ...policy },
                lifecycle: { ...lifecycle }
            }

            console.log(`[Gateway] Mapped app ${app.id}:`, app)
            return app
        })
    }

    // ============== SERVICES ==============

    async getServicesStatus(): Promise<Record<string, ServiceStatus>> {
        try {
            const response = await fetch(`${this.baseUrl}/v1/admin/health`)
            if (!response.ok) {
                throw new Error(`Failed to fetch service status: ${response.status} ${response.statusText}`)
            }
            const data = await response.json()
            return data.services || {}
        } catch (error) {
            // If backend is down, return empty object so UI doesn't break
            console.error('Failed to fetch services status:', error)
            throw error // Re-throw so store can handle it
        }
    }

    // ============== ADMIN ACTIONS ==============

    async refreshAll(): Promise<void> {
        await fetch(`${this.baseUrl}/v1/admin/refresh`, { method: 'POST' })
    }

    async restartService(serviceName: string): Promise<void> {
        await fetch(`${this.baseUrl}/v1/admin/services/${serviceName}/restart`, { method: 'POST' })
    }

    // ============== ASSET LIFECYCLE CONTROL ==============

    async startAsset(assetId: string): Promise<{ success: boolean; message?: string; state?: string; error?: string }> {
        const response = await fetch(`${this.baseUrl}/v1/assets/${assetId}/start`, { method: 'POST' })
        return response.json()
    }

    async stopAsset(assetId: string): Promise<{ success: boolean; message?: string; state?: string; error?: string }> {
        const response = await fetch(`${this.baseUrl}/v1/assets/${assetId}/stop`, { method: 'POST' })
        return response.json()
    }

    async restartAsset(assetId: string): Promise<{ success: boolean; message?: string; state?: string; error?: string }> {
        const response = await fetch(`${this.baseUrl}/v1/assets/${assetId}/restart`, { method: 'POST' })
        return response.json()
    }

    async getAssetStatus(assetId: string): Promise<{ status: string; running?: boolean; container?: string; error?: string }> {
        const response = await fetch(`${this.baseUrl}/v1/assets/${assetId}/status`)
        return response.json()
    }

    // ============== ADMIN ACTIONS ==============

    async clearCache(selection?: { documents: boolean; embeddings: boolean; cache: boolean }): Promise<{ success: boolean; message?: string; cleared?: { documents: number; embeddings: number; cache?: number; total?: number } }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/cache/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(selection || { documents: true, embeddings: true, cache: true })
        })
        return response.json()
    }

    async healthCheck(): Promise<{ overall: string; services: Record<string, { status: string; running: boolean }>; resources: Record<string, number> }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/health`)
        return response.json()
    }

    async reloadAssets(): Promise<{ success: boolean; message?: string; asset_count?: number }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/assets/reload`, { method: 'POST' })
        return response.json()
    }

    // ============== AUTO-SLEEP & IDLE MANAGEMENT ==============

    async getIdleStatus(): Promise<{
        autoWakeEnabled: boolean
        idleTimeout: number
        idleSleepEnabled: boolean
        serviceRegistry: Record<string, { desired: string; actual: string; last_used: number; idle_sleep_enabled: boolean }>
    }> {
        try {
            const response = await fetch(`${this.baseUrl}/v1/admin/idle-status`)
            if (!response.ok) {
                throw new Error(`Failed to fetch idle status: ${response.status} ${response.statusText}`)
            }
            return response.json()
        } catch (error) {
            // If the endpoint doesn't exist or backend is down, return a default structure
            console.warn('Idle status endpoint unavailable, using defaults:', error)
            return {
                autoWakeEnabled: true,
                idleTimeout: 60,
                idleSleepEnabled: true,
                serviceRegistry: {}
            }
        }
    }

    async suspendService(serviceName: string): Promise<{ status: string; message: string }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/services/${serviceName}/suspend`, { method: 'POST' })
        if (!response.ok) throw new Error('Failed to suspend service')
        return response.json()
    }

    async keepServiceWarm(serviceName: string, durationMinutes: number = 30): Promise<{ status: string; message: string; keep_warm_until?: number }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/services/${serviceName}/keep-warm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: durationMinutes })
        })
        if (!response.ok) throw new Error('Failed to keep service warm')
        return response.json()
    }

    async updateServiceAutoSleep(serviceName: string, enabled: boolean, idleTimeoutMinutes?: number): Promise<{ status: string; message: string; idle_sleep_enabled: boolean }> {
        const body: any = { enabled }
        if (idleTimeoutMinutes !== undefined) {
            body.idle_timeout_minutes = idleTimeoutMinutes
        }
        const response = await fetch(`${this.baseUrl}/v1/admin/services/${serviceName}/auto-sleep`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        })
        if (!response.ok) {
            const errorText = await response.text()
            throw new Error(`Failed to update auto-sleep settings: ${errorText}`)
        }
        return response.json()
    }

    // ============== METRICS ==============

    async getServiceMetrics(serviceName: string): Promise<{
        cpu_percent: number
        memory_percent: number
        memory_usage?: string
        gpu_vram_percent?: number | null
        requests_per_min: number
        timestamp: number
    }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/services/${serviceName}/metrics`)
        if (!response.ok) throw new Error('Failed to fetch service metrics')
        return response.json()
    }

    async inspectService(serviceName: string): Promise<{ dependencies: string[], consumers: any[] }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/services/${serviceName}/inspect`)
        if (!response.ok) throw new Error('Failed to inspect service')
        return response.json()
    }

    // Model Management
    async listModels(): Promise<{ models: any[] }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/models/list`)
        if (!response.ok) throw new Error('Failed to list models')
        return response.json()
    }

    async pullModel(modelName: string): Promise<{ status: string, message: string }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/models/pull`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelName })
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }))
            throw new Error(error.detail || 'Failed to pull model')
        }
        return response.json()
    }

    /**
     * Pull a model with streaming progress (NDJSON). onProgress receives { status?, completed?, total?, error? }.
     * If the stream endpoint returns 404 (old gateway), falls back to non-streaming pull so Pull still works.
     */
    async pullModelWithProgress(
        modelName: string,
        onProgress: (event: { status?: string; completed?: number; total?: number; error?: string; done?: boolean }) => void
    ): Promise<void> {
        const response = await fetch(`${this.baseUrl}/v1/admin/models/pull/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelName })
        })
        if (response.status === 404) {
            // Old gateway without /pull/stream — use non-streaming pull so Pull still works
            onProgress({ status: 'Pulling (no progress stream)...' })
            const result = await this.pullModel(modelName)
            onProgress({ status: result.message || 'Done', done: true })
            return
        }
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }))
            onProgress({ error: err.detail || 'Failed to start pull' })
            throw new Error(err.detail || 'Failed to pull model')
        }
        const reader = response.body?.getReader()
        if (!reader) {
            onProgress({ error: 'No response body' })
            throw new Error('No response body')
        }
        const decoder = new TextDecoder()
        let buffer = ''
        try {
            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() ?? ''
                for (const line of lines) {
                    if (!line.trim()) continue
                    try {
                        const data = JSON.parse(line)
                        if (data.error) {
                            onProgress({ error: data.error })
                            throw new Error(data.error)
                        }
                        onProgress({
                            status: data.status,
                            completed: data.completed,
                            total: data.total,
                            done: data.status === 'success'
                        })
                    } catch (e) {
                        if (e instanceof Error && e.message !== line) throw e
                    }
                }
            }
        } finally {
            reader.releaseLock()
        }
    }

    async loadModel(modelName: string): Promise<{ status: string, message: string }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/models/${encodeURIComponent(modelName)}/load`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }))
            throw new Error(error.detail || 'Failed to load model')
        }
        return response.json()
    }

    async unloadModel(modelName: string): Promise<{ status: string, message: string }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/models/${encodeURIComponent(modelName)}/unload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }))
            throw new Error(error.detail || 'Failed to unload model')
        }
        return response.json()
    }

    async deleteModel(modelName: string): Promise<{ status: string, message: string }> {
        const response = await fetch(`${this.baseUrl}/v1/admin/models/${encodeURIComponent(modelName)}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }))
            throw new Error(error.detail || 'Failed to delete model')
        }
        return response.json()
    }

    // ============== MODEL TYPE ENDPOINTS ==============

    async getLLMModels(): Promise<Asset[]> {
        const response = await fetch(`${this.baseUrl}/v1/assets/models/llm`)
        if (!response.ok) throw new Error('Failed to fetch LLM models')
        const data = await response.json()

        // Normalize assets
        return data.map((asset: any) => ({
            ...asset,
            display_name: asset.display_name || asset.name || asset.id,
            status: this.deriveStatus(asset)
        }))
    }

    async getEmbeddingModels(): Promise<Asset[]> {
        const response = await fetch(`${this.baseUrl}/v1/assets/models/embedding`)
        if (!response.ok) throw new Error('Failed to fetch embedding models')
        const data = await response.json()

        // Normalize assets
        return data.map((asset: any) => ({
            ...asset,
            display_name: asset.display_name || asset.name || asset.id,
            status: this.deriveStatus(asset)
        }))
    }
}

// Singleton instance
export const gateway = new GatewayService()

