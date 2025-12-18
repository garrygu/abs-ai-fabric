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
    icon?: string
    url: string
    status: string
    dependencies?: string[]
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
        if (Array.isArray(data)) return data
        if (data.assets) return data.assets
        if (data.value) return data.value
        return []
    }

    async getAsset(id: string): Promise<Asset> {
        const response = await fetch(`${this.baseUrl}/v1/assets/${id}`)
        if (!response.ok) throw new Error(`Failed to fetch asset: ${id}`)
        return response.json()
    }

    // ============== APPS ==============

    async getApps(): Promise<App[]> {
        const assets = await this.getAssets()
        return assets
            .filter(a => a.interface === 'ui' || a.class === 'application')
            .map(a => ({
                id: a.id,
                name: a.display_name || a.id,
                description: '',
                url: `/apps/${a.id}`,
                status: a.status,
                dependencies: a.consumers
            }))
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
