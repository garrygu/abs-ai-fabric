// API Service for ABS Workstation Console
// Fetches from Hub Gateway with mock fallbacks

// Gateway base URL - configurable via VITE_GATEWAY_URL env var for multi-machine deployment
// Default to 127.0.0.1 for local development (avoids browser localhost resolution issues)
const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://127.0.0.1:8081'

// GPU Metrics proxy URL - runs on host to access real nvidia-smi data
const GPU_METRICS_URL = import.meta.env.VITE_GPU_METRICS_URL || 'http://127.0.0.1:8083'

// Mock data for development fallback
const MOCK_METRICS = {
    timestamp: new Date().toISOString(),
    gpu: {
        model: 'NVIDIA RTX Pro 6000',
        utilization_pct: 45,
        vram_used_gb: 32,
        vram_total_gb: 48
    },
    cpu: {
        utilization_pct: 28
    },
    memory: {
        used_gb: 64,
        total_gb: 128
    },
    disk: {
        read_mb_s: 125,
        write_mb_s: 85
    },
    uptime_seconds: 8125
}

const MOCK_WORKLOADS = [
    {
        app_id: 'onyx-assistant',
        app_name: 'Onyx AI Assistant',
        workload_type: 'llm_inference',
        status: 'running',
        associated_models: ['llama-3.3-70b']
    },
    {
        app_id: 'contract-reviewer-v2',
        app_name: 'Contract Reviewer',
        workload_type: 'rag',
        status: 'running',
        associated_models: ['llama-3.3-70b', 'nomic-embed']
    },
    {
        app_id: 'abs-workstation-console',
        app_name: 'Workstation Console',
        workload_type: 'model_management',
        status: 'idle',
        associated_models: []
    }
]

const MOCK_MODELS = [
    {
        model_id: 'llama-3.3-70b',
        display_name: 'Llama 3.3 70B',
        type: 'llm',
        size_gb: 40,
        locality: 'local',
        serving_status: 'ready'
    },
    {
        model_id: 'nomic-embed-text',
        display_name: 'Nomic Embed Text',
        type: 'embedding',
        size_gb: 0.5,
        locality: 'local',
        serving_status: 'ready'
    },
    {
        model_id: 'sdxl-turbo',
        display_name: 'SDXL Turbo',
        type: 'image',
        size_gb: 6.5,
        locality: 'local',
        serving_status: 'idle'
    },
    {
        model_id: 'qwen2.5-coder-32b',
        display_name: 'Qwen 2.5 Coder 32B',
        type: 'llm',
        size_gb: 19,
        locality: 'local',
        serving_status: 'idle'
    }
]

export interface SystemMetrics {
    timestamp: string
    gpu: {
        model: string
        utilization_pct: number
        vram_used_gb: number
        vram_total_gb: number
    }
    cpu: {
        utilization_pct: number
    }
    memory: {
        used_gb: number
        total_gb: number
    }
    disk?: {
        read_mb_s: number
        write_mb_s: number
    }
    uptime_seconds: number
}

export interface RunningWorkload {
    app_id: string
    app_name: string
    workload_type: 'llm_inference' | 'rag' | 'embedding' | 'model_management'
    status: 'running' | 'idle'
    associated_models?: string[]
}

export interface InstalledModel {
    model_id: string
    display_name: string
    type: 'llm' | 'image' | 'embedding'
    size_gb?: number
    locality: 'local'
    serving_status: 'ready' | 'idle'
}

// Gateway response format
interface GatewayMetricsResponse {
    cpu: { usage_percent: number }
    memory: { usage_percent: number }
    gpu: Array<{
        id: number
        name: string
        utilization: number
        memory_utilization: number
        temperature?: number
    }>
    timestamp: number
}

// Type for real GPU data from the host-side proxy
type RealGpuData = { name: string; utilization: number; memory_used_mb: number; memory_total_mb: number; temperature: number } | null

// Transform Gateway response to our SystemMetrics format
function transformGatewayMetrics(data: GatewayMetricsResponse, realGpuData: RealGpuData = null): SystemMetrics {
    // Get memory info from system (psutil gives percent, we estimate GB)
    // Assuming 128GB total RAM for ABS workstation
    const totalRamGb = 128
    const usedRamGb = (data.memory.usage_percent / 100) * totalRamGb

    // GPU metrics - prefer real data from host proxy
    let gpuUtil: number
    let usedVramGb: number
    let totalVramGb: number
    let gpuModel: string

    if (realGpuData) {
        // Use real GPU data from nvidia-smi via host proxy
        gpuModel = realGpuData.name
        gpuUtil = realGpuData.utilization
        usedVramGb = realGpuData.memory_used_mb / 1024
        totalVramGb = realGpuData.memory_total_mb / 1024
    } else {
        // Fallback: simulate GPU metrics
        gpuModel = 'NVIDIA RTX Pro 6000'
        totalVramGb = 48
        const baseUtil = Math.min(60, data.cpu.usage_percent * 1.5)
        gpuUtil = Math.max(8, baseUtil + (Math.sin(Date.now() / 5000) * 15) + (Math.random() * 10))
        usedVramGb = 28 + (Math.sin(Date.now() / 10000) * 4) + (Math.random() * 2)
    }

    return {
        timestamp: new Date(data.timestamp * 1000).toISOString(),
        gpu: {
            model: gpuModel,
            utilization_pct: Math.round(gpuUtil * 10) / 10,
            vram_used_gb: Math.round(usedVramGb * 10) / 10,
            vram_total_gb: Math.round(totalVramGb * 10) / 10
        },
        cpu: {
            utilization_pct: data.cpu.usage_percent
        },
        memory: {
            used_gb: usedRamGb,
            total_gb: totalRamGb
        },
        disk: {
            read_mb_s: Math.max(0, 50 + (Math.random() * 100) + (Math.sin(Date.now() / 3000) * 30)),
            write_mb_s: Math.max(0, 30 + (Math.random() * 60) + (Math.sin(Date.now() / 4000) * 20))
        },
        uptime_seconds: Math.floor(Date.now() / 1000) % 86400
    }
}

// Simulate realistic metric changes for development (uses real GPU if available)
function simulateMetrics(realGpuData: RealGpuData = null): SystemMetrics {
    const base = { ...MOCK_METRICS }
    base.timestamp = new Date().toISOString()

    if (realGpuData) {
        // Use real GPU data from host proxy
        base.gpu = {
            model: realGpuData.name,
            utilization_pct: realGpuData.utilization,
            vram_used_gb: Math.round((realGpuData.memory_used_mb / 1024) * 10) / 10,
            vram_total_gb: Math.round((realGpuData.memory_total_mb / 1024) * 10) / 10
        }
    } else {
        base.gpu = {
            ...base.gpu,
            utilization_pct: Math.min(95, Math.max(15, base.gpu.utilization_pct + (Math.random() * 10 - 5))),
            vram_used_gb: Math.min(base.gpu.vram_total_gb, Math.max(20, base.gpu.vram_used_gb + (Math.random() * 2 - 1)))
        }
    }

    base.cpu = {
        utilization_pct: Math.min(100, Math.max(5, base.cpu.utilization_pct + (Math.random() * 8 - 4)))
    }
    base.memory = {
        ...base.memory,
        used_gb: Math.min(base.memory.total_gb, Math.max(40, base.memory.used_gb + (Math.random() * 4 - 2)))
    }
    base.disk = {
        read_mb_s: Math.max(0, Math.min(500, (base.disk?.read_mb_s ?? 125) + (Math.random() * 40 - 20))),
        write_mb_s: Math.max(0, Math.min(500, (base.disk?.write_mb_s ?? 85) + (Math.random() * 30 - 15)))
    }
    base.uptime_seconds = Math.floor(Date.now() / 1000) % 86400
    return base
}

export async function fetchSystemMetrics(): Promise<SystemMetrics> {
    // First, try to get real GPU metrics from the host-side proxy
    let realGpuData: { name: string; utilization: number; memory_used_mb: number; memory_total_mb: number; temperature: number } | null = null

    try {
        const gpuResponse = await fetch(`${GPU_METRICS_URL}/gpu-metrics`, {
            headers: { 'Accept': 'application/json' }
        })
        if (gpuResponse.ok) {
            const gpuData = await gpuResponse.json()
            if (gpuData.gpus && gpuData.gpus.length > 0) {
                realGpuData = gpuData.gpus[0]
                console.log('[API] Real GPU data from proxy:', realGpuData)
            }
        }
    } catch (e) {
        console.log('[API] GPU proxy unavailable, will use simulation')
    }

    try {
        // Add timeout to prevent Gateway fetch from hanging indefinitely
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout

        const response = await fetch(`${GATEWAY_URL}/v1/admin/system/metrics`, {
            headers: { 'Accept': 'application/json' },
            signal: controller.signal
        })
        clearTimeout(timeoutId)

        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error')
            console.error(`[API] Gateway returned ${response.status}:`, errorText)
            throw new Error(`Gateway HTTP ${response.status}: ${errorText.substring(0, 100)}`)
        }

        const data: GatewayMetricsResponse = await response.json()
        console.log('[API] Gateway metrics:', { cpu: data.cpu?.usage_percent, memory: data.memory?.usage_percent })

        // Transform with real GPU data if available
        const transformed = transformGatewayMetrics(data, realGpuData)
        console.log('[API] Returning transformed metrics:', transformed)
        console.log('[API] GPU model in result:', transformed.gpu.model)
        return transformed
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        console.error('[API] Gateway unavailable, using simulated metrics. Error:', errorMessage)
        // Still return simulated metrics so the UI doesn't break
        const simulated = simulateMetrics(realGpuData)
        console.log('[API] Returning simulated metrics:', simulated)
        return simulated
    }
}

export async function fetchActiveWorkloads(): Promise<RunningWorkload[]> {
    try {
        // Try to get real workloads from assets API
        const response = await fetch(`${GATEWAY_URL}/v1/assets`)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const assets = await response.json()
        const apps = (Array.isArray(assets) ? assets : []).filter(
            (a: any) => a.class === 'app' || a.interface === 'application' || a.interface === 'ui'
        )

        return apps.map((app: any): RunningWorkload => ({
            app_id: app.asset_id || app.id,
            app_name: app.display_name || app.name || app.id,
            workload_type: 'llm_inference',
            status: app.lifecycle?.state === 'running' ? 'running' : 'idle',
            associated_models: app.policy?.required_models || []
        }))
    } catch {
        console.log('[API] Using mock workloads')
        return MOCK_WORKLOADS as RunningWorkload[]
    }
}

export async function fetchInstalledModels(): Promise<InstalledModel[]> {
    try {
        // Get assets from Gateway and filter for models
        const response = await fetch(`${GATEWAY_URL}/v1/assets`)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)

        const data = await response.json()
        console.log('[API] Assets response:', data)

        // Handle both array and object response formats
        const assets = Array.isArray(data) ? data : (data.assets || data.data || [])
        console.log('[API] Parsed assets count:', assets.length)

        // Filter for model-related assets: class: model OR services with llm-runtime/embedding-runtime
        const modelAssets = assets.filter((asset: any) => {
            const iface = asset.interface || ''
            const assetClass = asset.class || ''
            const isModel = assetClass === 'model'
            const isRuntime = iface === 'llm-runtime' || iface === 'embedding-runtime' || iface === 'image-runtime'
            return isModel || isRuntime
        })

        console.log('[API] Filtered model assets:', modelAssets.length, modelAssets.map((a: any) => a.id))


        return modelAssets.map((asset: any): InstalledModel => {
            // Determine type based on interface or metadata
            let type: 'llm' | 'embedding' | 'image' = 'llm'
            if (asset.interface === 'embedding-runtime' || asset.id?.includes('embed')) {
                type = 'embedding'
            } else if (asset.interface === 'image-runtime' || asset.id?.includes('sdxl') || asset.id?.includes('flux')) {
                type = 'image'
            }

            return {
                model_id: asset.id || asset.asset_id,
                display_name: asset.display_name || asset.name || asset.id,
                type,
                size_gb: asset.resources?.disk_gb || asset.metadata?.size_gb || 0,
                locality: 'local',
                serving_status: asset.lifecycle?.state === 'running' || asset.status === 'running' ? 'ready' : 'idle'
            }
        })
    } catch (err) {
        console.log('[API] Models fetch failed, using mock:', err)
        return MOCK_MODELS as InstalledModel[]
    }
}

export function formatUptime(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

export function formatBytes(gb: number): string {
    return gb.toFixed(1)
}

// Chat completion request/response types
export interface ChatMessage {
    role: 'system' | 'user' | 'assistant'
    content: string
}

export interface ChatCompletionRequest {
    model?: string
    messages: ChatMessage[]
    temperature?: number
    max_tokens?: number
}

export interface ChatCompletionResponse {
    choices: Array<{
        message: {
            role: string
            content: string
        }
    }>
    usage?: {
        prompt_tokens: number
        completion_tokens: number
        total_tokens: number
    }
}

// Map demo model IDs to actual model names used by gateway
function mapModelIdToGatewayModel(modelId: string | null): string | null {
    if (!modelId) return null
    
    const modelIdLower = modelId.toLowerCase()
    
    // Map demo model IDs to actual model names (from asset.yaml files)
    if (modelIdLower.includes('deepseek') && (modelIdLower.includes('70b') || modelIdLower.includes('r1'))) {
        return 'deepseek-r1:70b' // From assets/models/deepseek_r1_70b/asset.yaml
    }
    if (modelIdLower.includes('llama') && modelIdLower.includes('70b')) {
        return 'llama3:70b' // Expected model name format
    }
    if (modelIdLower === 'dual') {
        return null // Dual model handled separately
    }
    
    // Return as-is if it's already in the correct format
    return modelId
}

// Request/load a model into memory
export async function requestModel(modelId: string | null): Promise<void> {
    try {
        const gatewayModel = mapModelIdToGatewayModel(modelId)
        
        if (!gatewayModel) {
            throw new Error(`Model ${modelId} not available`)
        }
        
        console.log('[API] Requesting model load:', gatewayModel)
        
        // URL encode the model name (handles colons and special characters)
        const encodedModelName = encodeURIComponent(gatewayModel)
        
        // Call the model load endpoint to pre-load the model into VRAM
        const response = await fetch(`${GATEWAY_URL}/v1/admin/models/${encodedModelName}/load`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        })
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error')
            console.error(`[API] Model load failed: ${response.status}`, errorText)
            // Don't throw - model might already be loaded, or will load on first use
            console.log('[API] Model may already be loaded or will load on first use')
        } else {
            const data = await response.json()
            console.log('[API] Model load success:', data)
        }
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        console.error('[API] Model load error:', errorMessage)
        // Don't throw - model will be loaded on first chat completion request anyway
        console.log('[API] Model will be loaded automatically on first use')
    }
}

export async function sendChatCompletion(
    modelId: string | null,
    prompt: string,
    systemPrompt?: string,
    challengeType?: string
): Promise<string> {
    try {
        // Map model ID to gateway model name
        const gatewayModel = mapModelIdToGatewayModel(modelId)
        
        if (!gatewayModel) {
            throw new Error(`Model ${modelId} not available`)
        }
        
        // Build system prompt based on challenge type
        let systemMessage = systemPrompt || 'You are a helpful AI assistant.'
        
        if (challengeType === 'reasoning') {
            systemMessage = 'You are an expert at reasoning and analysis. Provide detailed, structured analysis with clear recommendations, assumptions, and risk assessments.'
        } else if (challengeType === 'explanation') {
            systemMessage = 'You are an executive communication expert. Translate technical or complex information into clear, business-friendly language. Focus on business implications, bottom line, and actionable insights.'
        } else if (challengeType === 'compare') {
            systemMessage = 'You are a strategic advisor. Provide balanced comparisons of options, highlighting pros/cons, trade-offs, and recommendations based on priorities.'
        } else if (challengeType === 'summarize') {
            systemMessage = 'You are a document analysis expert. Extract and organize key information from documents, including main points, action items, risks, stakeholders, and deadlines.'
        }
        
        const request: ChatCompletionRequest = {
            model: gatewayModel,
            messages: [
                {
                    role: 'system',
                    content: systemMessage
                },
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: challengeType === 'reasoning' ? 0.3 : 0.7,
            max_tokens: 2000
        }
        
        console.log('[API] Sending chat completion request:', { model: gatewayModel, prompt: prompt.substring(0, 100) + '...' })
        
        const response = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(request)
        })
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error')
            console.error(`[API] Chat completion failed: ${response.status}`, errorText)
            throw new Error(`Model API error: ${response.status} - ${errorText.substring(0, 200)}`)
        }
        
        const data: ChatCompletionResponse = await response.json()
        const content = data.choices?.[0]?.message?.content || 'No response generated'
        
        console.log('[API] Chat completion success, response length:', content.length)
        
        return content
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        console.error('[API] Chat completion error:', errorMessage)
        throw error
    }
}

