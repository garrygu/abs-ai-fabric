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
}

export interface ServiceStatus {
    name: string
    status: 'running' | 'stopped' | 'error'
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
            // Get dependencies (what this app consumes)
            const deps = a.consumers || []

            // Determine status from asset status
            let status: 'online' | 'offline' | 'error' = 'offline'
            if (a.status === 'ready' || a.status === 'running' || a.status === 'online') {
                status = 'online'
            } else if (a.status === 'error') {
                status = 'error'
            }

            return {
                id: a.id,
                name: a.display_name || a.id,
                description: a.version ? `Version ${a.version}` : '',
                category: a.class || 'Application',
                url: `/apps/${a.id}`,
                port: 0,
                status,
                dependencies: deps
            }
        })
    }

    // ============== SERVICES ==============

    async getServicesStatus(): Promise<ServiceStatus[]> {
        const response = await fetch(`${this.baseUrl}/v1/admin/services/status`)
        if (!response.ok) throw new Error('Failed to fetch service status')
        const data = await response.json()
        return data.services || []
    }

    // ============== ADMIN ACTIONS ==============

    async refreshAll(): Promise<void> {
        await fetch(`${this.baseUrl}/v1/admin/refresh`, { method: 'POST' })
    }

    async restartService(serviceName: string): Promise<void> {
        await fetch(`${this.baseUrl}/v1/admin/services/${serviceName}/restart`, { method: 'POST' })
    }
}

// Singleton instance
export const gateway = new GatewayService()
