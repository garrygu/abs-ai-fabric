<template>
  <div class="admin-view">
    <header class="view-header">
      <div class="header-content">
        <h1>⚙️ Admin</h1>
        <p class="view-desc">System administration and configuration.</p>
      </div>
    </header>
    
    <!-- Toast Notification -->
    <div v-if="toastMessage" class="toast" :class="toastType">
      {{ toastMessage }}
    </div>

    <!-- Tab Navigation -->
    <div class="admin-tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- Quick Actions -->
    <section v-if="activeTab === 'actions'" class="admin-section">
      <div class="section-header">
        <h2>🚀 Quick Actions</h2>
      </div>
      <div class="actions-grid">
        <button class="action-card" @click="refreshAll" :disabled="loading.refresh">
          <span class="action-icon">🔄</span>
          <span class="action-label">Refresh All</span>
          <span class="action-desc">Reload assets and status</span>
        </button>
        <button class="action-card" @click="reloadAssets" :disabled="loading.assets">
          <span class="action-icon">📦</span>
          <span class="action-label">Reload Assets</span>
          <span class="action-desc">Re-scan asset registry</span>
        </button>
        <button class="action-card warning" @click="clearCache" :disabled="loading.cache">
          <span class="action-icon">🗑️</span>
          <span class="action-label">Clear Cache</span>
          <span class="action-desc">Clear document & embedding cache</span>
        </button>
        <button class="action-card" @click="checkHealth">
          <span class="action-icon">💓</span>
          <span class="action-label">Health Check</span>
          <span class="action-desc">Run system diagnostics</span>
        </button>
      </div>
    </section>

    <!-- Service Controls -->
    <section v-if="activeTab === 'services'" class="admin-section">
      <div class="section-header">
        <h2>🔧 Service Controls</h2>
        <button class="btn btn-sm" @click="refreshAll" :disabled="loading.refresh">🔄 Refresh</button>
      </div>
      
      <!-- Health & Readiness Legend -->
      <div class="health-legend">
        <h3>❤️ Health & Readiness</h3>
        <div class="legend-items">
          <div class="legend-item">
            <span class="legend-emoji">🟢</span>
            <span class="legend-label">Healthy</span>
            <span class="legend-desc">/health OK</span>
          </div>
          <div class="legend-item">
            <span class="legend-emoji">🟡</span>
            <span class="legend-label">Degraded</span>
            <span class="legend-desc">Running but dependency issue</span>
          </div>
          <div class="legend-item">
            <span class="legend-emoji">🔴</span>
            <span class="legend-label">Unhealthy</span>
            <span class="legend-desc">Running but failing checks</span>
          </div>
          <div class="legend-item">
            <span class="legend-emoji">⚪</span>
            <span class="legend-label">Stopped</span>
            <span class="legend-desc">Not running</span>
          </div>
        </div>
      </div>
      
      <!-- Backend Connection Error -->
      <div v-if="systemHealth.error" class="error-banner">
        <span class="error-icon">⚠️</span>
        <div class="error-content">
          <strong>Backend Unavailable</strong>
          <p>{{ systemHealth.error }}</p>
          <p class="error-hint">Make sure the gateway service is running on port 8081</p>
        </div>
      </div>

      <div class="services-table" v-if="!systemHealth.error || systemHealth.services.length > 0">


        <div class="service-row header">
          <span class="col-name">Service</span>
          <span class="col-status">Status</span>
          <span class="col-health">Health</span>
          <span class="col-port">Port</span>
          <span class="col-actions">Actions</span>
        </div>
        <div 
          v-for="service in services" 
          :key="service.name" 
          class="service-row-wrapper"
        >
        <div 
          class="service-row"
          :class="service.status"
        >
          <span class="col-name">
            <span class="service-icon">{{ service.icon }}</span>
            {{ service.name }}
          </span>
          <span class="col-status">
             <span class="status-indicator" :class="service.running ? 'running' : 'stopped'"></span>
             {{ service.running ? 'Running' : 'Stopped' }}
          </span>
          <span class="col-health" :title="service.healthDescription">
            <span class="health-emoji">{{ service.healthEmoji }}</span>
            <span class="health-text">{{ service.statusText }}</span>
            <span class="health-hint" v-if="service.healthDescription !== '/health OK'">
              ({{ service.healthDescription }})
            </span>
          </span>
          <span class="col-port">{{ service.port || '-' }}</span>
          <span class="col-actions">
            <button 
              v-if="!service.running"
              class="btn btn-sm btn-success"
              @click="startService(service)"
              :disabled="service.loading"
            >
              ▶ Start
            </button>
            <button 
              v-if="service.running"
              class="btn btn-sm btn-warning"
              @click="stopService(service)"
              :disabled="service.loading"
            >
              ⏹ Stop
            </button>
            <button 
              class="btn btn-sm"
              @click="restartService(service)"
              :disabled="service.loading"
            >
              🔄 Restart
            </button>
            <button 
              class="btn btn-sm btn-secondary"
              @click="togglePolicyControls(service.name)"
              :title="expandedServices[service.name] ? 'Hide policy controls' : 'Show policy controls'"
            >
              {{ expandedServices[service.name] ? '▼' : '▶' }} Policy
            </button>
            
            <!-- Diagnostic & Ops Actions Menu -->
            <div class="actions-menu-wrapper">
              <button 
                class="btn btn-sm btn-icon"
                @click.stop="toggleMenu(service.name)"
                :title="'Diagnostic & Ops Actions'"
              >
                ⋮
              </button>
              <div 
                v-if="openMenus[service.name]" 
                class="actions-menu"
                @click.stop
              >
                <button 
                  class="menu-item"
                  @click="viewServiceLogs(service)"
                >
                  <span class="menu-icon">📜</span>
                  <span>View Recent Logs</span>
                </button>
                <button 
                  class="menu-item"
                  @click="jumpToObservability(service)"
                >
                  <span class="menu-icon">🔍</span>
                  <span>Jump to Observability</span>
                </button>
                <button 
                  class="menu-item"
                  @click="downloadServiceLogs(service)"
                >
                  <span class="menu-icon">💾</span>
                  <span>Download Logs</span>
                </button>
              </div>
            </div>
          </span>
        </div>
        
        <!-- Policy & Automation Controls (Expandable) -->
        <div v-if="expandedServices[service.name]" class="policy-controls">
          <div class="policy-header">
            <h4>🕒 Auto-Wake / Auto-Sleep</h4>
            <span class="policy-subtitle">Cost-saving automation controls</span>
          </div>
          
          <div class="policy-grid">
            <div class="policy-item">
              <label class="policy-label">
                <input 
                  type="checkbox" 
                  :checked="service.idleSleepEnabled"
                  @change="updateAutoSleep(service, $event)"
                  :disabled="service.policyLoading"
                />
                <span>Enable auto-sleep</span>
              </label>
              <span class="policy-desc">Automatically suspend when idle</span>
            </div>
            
            <div class="policy-item">
              <label class="policy-label">
                Idle timeout (minutes):
                <input 
                  type="number" 
                  :value="service.idleTimeout || globalIdleTimeout"
                  @change="updateIdleTimeout(service, $event)"
                  :disabled="!service.idleSleepEnabled || service.policyLoading"
                  min="1"
                  max="1440"
                  class="policy-input"
                />
              </label>
              <span class="policy-desc">Time before auto-suspend</span>
            </div>
            
            <div class="policy-item">
              <label class="policy-label">Current idle duration:</label>
              <span class="policy-value">{{ formatIdleDuration(service.idleDuration) }}</span>
              <span class="policy-desc">{{ service.idleDuration > 0 ? 'Time since last use' : 'Not idle' }}</span>
            </div>
          </div>
          
          <div class="policy-actions">
            <button 
              v-if="service.running"
              class="btn btn-sm btn-warning"
              @click="suspendService(service)"
              :disabled="service.policyLoading"
            >
              ⏸️ Suspend now
            </button>
            <button 
              v-if="service.running"
              class="btn btn-sm btn-success"
              @click="keepWarm(service, 30)"
              :disabled="service.policyLoading"
            >
              🔥 Keep warm for 30 min
            </button>
          </div>
          
          <!-- Governance & Usage -->
          <div class="governance-section">
            <div class="policy-header">
              <h4>🔐 Governance & Usage</h4>
              <span class="policy-subtitle">Policy controls - Apps don't own infra, policies do</span>
            </div>
            
            <div v-if="loadingPolicies[service.name]" class="policy-loading">
              Loading policy data...
            </div>
            
            <div v-else-if="assetPolicies[service.name]" class="governance-grid">
              <!-- Allowed Apps (for services/runtimes) -->
              <div v-if="assetPolicies[service.name].allowed_apps && assetPolicies[service.name].allowed_apps.length > 0" class="governance-item">
                <label class="governance-label">Allowed Apps:</label>
                <div class="governance-value-list">
                  <span 
                    v-for="app in assetPolicies[service.name].allowed_apps" 
                    :key="app"
                    class="governance-tag"
                  >
                    {{ app }}
                  </span>
                </div>
                <span class="policy-desc">Apps that can use this service</span>
              </div>
              
              <!-- Max Concurrency -->
              <div v-if="assetPolicies[service.name].max_concurrency" class="governance-item">
                <label class="governance-label">Max Concurrency:</label>
                <span class="governance-value">{{ assetPolicies[service.name].max_concurrency }}</span>
                <span class="policy-desc">Maximum concurrent requests</span>
              </div>
              
              <!-- Required Models (for apps) -->
              <div v-if="assetPolicies[service.name].required_models && assetPolicies[service.name].required_models.length > 0" class="governance-item">
                <label class="governance-label">Required Models:</label>
                <div class="governance-value-list">
                  <span 
                    v-for="model in assetPolicies[service.name].required_models" 
                    :key="model"
                    class="governance-tag"
                  >
                    {{ model }}
                  </span>
                </div>
                <span class="policy-desc">Models required by this app</span>
              </div>
              
              <!-- Served Models (for runtimes) -->
              <div v-if="assetPolicies[service.name].served_models && assetPolicies[service.name].served_models.length > 0" class="governance-item">
                <label class="governance-label">Served Models:</label>
                <div class="governance-value-list">
                  <span 
                    v-for="model in assetPolicies[service.name].served_models" 
                    :key="model"
                    class="governance-tag"
                  >
                    {{ model }}
                  </span>
                </div>
                <span class="policy-desc">Models served by this runtime</span>
              </div>
              
              <!-- No Policy Data -->
              <div v-if="!assetPolicies[service.name].allowed_apps && !assetPolicies[service.name].max_concurrency && !assetPolicies[service.name].required_models && !assetPolicies[service.name].served_models" class="governance-item">
                <span class="policy-desc">No policy data available for this service</span>
              </div>
            </div>
            
            <div v-else class="governance-item">
              <button 
                class="btn btn-sm"
                @click="loadServicePolicy(service)"
                :disabled="loadingPolicies[service.name]"
              >
                {{ loadingPolicies[service.name] ? 'Loading...' : '📋 Load Policy Data' }}
              </button>
            </div>
          </div>
        </div>
        </div>
      </div>
    </section>

    <!-- Model Management -->
    <section v-if="activeTab === 'models'" class="admin-section">
      <div class="section-header">
        <h2>🧠 Model Management</h2>
        <button class="btn btn-sm btn-primary" @click="showPullModal = true">
          ⬇️ Pull Model
        </button>
      </div>

      <div class="models-grid">
        <div v-for="model in models" :key="model.name" class="model-card">
          <div class="model-header">
            <span class="model-name">{{ model.name }}</span>
            <span class="model-size">{{ formatSize(model.size) }}</span>
          </div>
          <div class="model-meta">
            <span class="meta-item">
              <span class="meta-label">Modified</span>
              <span class="meta-value">{{ formatDate(model.modified_at) }}</span>
            </span>
            <span class="meta-item" v-if="model.details?.parameter_size">
              <span class="meta-label">Params</span>
              <span class="meta-value">{{ model.details.parameter_size }}</span>
            </span>
          </div>
          <div class="model-actions">
            <button class="btn btn-sm" @click="loadModel(model)">📥 Load</button>
            <button class="btn btn-sm btn-danger" @click="deleteModel(model)">🗑️ Delete</button>
          </div>
        </div>
        
        <div v-if="models.length === 0" class="empty-state">
          <p>No models found. Pull a model to get started.</p>
        </div>
      </div>

      <!-- Pull Model Modal -->
      <Teleport to="body">
        <div v-if="showPullModal" class="modal-overlay" @click.self="showPullModal = false">
          <div class="modal-content small">
            <div class="modal-header">
              <h2>⬇️ Pull Model</h2>
              <button @click="showPullModal = false" class="close-btn">✕</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label>Model Name</label>
                <input 
                  v-model="pullModelName" 
                  type="text" 
                  placeholder="e.g., llama3.2:3b, mistral:7b"
                  class="form-input"
                />
              </div>
              <p class="form-help">
                Enter the model name from <a href="https://ollama.com/library" target="_blank">Ollama Library</a>
              </p>
            </div>
            <div class="modal-footer">
              <button @click="showPullModal = false" class="btn btn-secondary">Cancel</button>
              <button @click="pullModel" class="btn btn-primary" :disabled="!pullModelName || pulling">
                {{ pulling ? 'Pulling...' : '⬇️ Pull Model' }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </section>

    <!-- Logs & Diagnostics -->
    <section v-if="activeTab === 'logs'" class="admin-section">
      <div class="section-header">
        <h2>📋 Logs & Diagnostics</h2>
        <div class="header-actions">
          <select v-model="logFilter" class="log-filter">
            <option value="all">All Logs</option>
            <option value="error">Errors Only</option>
            <option value="warning">Warnings</option>
            <option value="info">Info</option>
          </select>
          <button class="btn btn-sm" @click="refreshLogs">🔄 Refresh</button>
        </div>
      </div>

      <div class="logs-container">
        <div 
          v-for="(log, idx) in filteredLogs" 
          :key="idx" 
          class="log-entry"
          :class="log.level"
        >
          <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
          <span class="log-level" :class="log.level">{{ log.level.toUpperCase() }}</span>
          <span class="log-source">{{ log.source }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div v-if="filteredLogs.length === 0" class="empty-logs">
          No logs to display.
        </div>
      </div>
    </section>

    <!-- Configuration -->
    <section v-if="activeTab === 'config'" class="admin-section">
      <div class="section-header">
        <h2>🔑 Configuration</h2>
      </div>

      <div class="config-grid">
        <div class="config-card">
          <h3>Gateway Settings</h3>
          <div class="config-item">
            <span class="config-label">Gateway URL</span>
            <code class="config-value">{{ config.gatewayUrl }}</code>
          </div>
          <div class="config-item">
            <span class="config-label">Ollama URL</span>
            <code class="config-value">{{ config.ollamaUrl }}</code>
          </div>
        </div>

        <div class="config-card">
          <h3>Storage</h3>
          <div class="config-item">
            <span class="config-label">Document Cache</span>
            <span class="config-value">{{ config.cacheSize }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">Vector Store</span>
            <span class="config-value">{{ config.vectorStore }}</span>
          </div>
        </div>

        <div class="config-card">
          <h3>Features</h3>
          <div class="config-item toggle">
            <span class="config-label">Debug Mode</span>
            <label class="switch">
              <input type="checkbox" v-model="config.debugMode">
              <span class="slider"></span>
            </label>
          </div>
          <div class="config-item toggle">
            <span class="config-label">GPU Acceleration</span>
            <label class="switch">
              <input type="checkbox" v-model="config.gpuEnabled" disabled>
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>
    </section>

    <!-- Clear Cache Confirmation Modal (outside tab sections) -->
    <Teleport to="body">
      <div v-if="showClearCacheModal" class="modal-overlay" @click.self="showClearCacheModal = false">
        <div class="modal-content small">
          <div class="modal-header warning-header">
            <h2>⚠️ Clear Cache</h2>
            <button @click="showClearCacheModal = false" class="close-btn">✕</button>
          </div>
          <div class="modal-body">
            <p class="warning-text">
              <strong>Select cache types to clear:</strong>
            </p>
            <ul class="cache-list selectable">
              <li :class="{ selected: cacheSelection.documents }" @click="cacheSelection.documents = !cacheSelection.documents">
                <div class="cache-checkbox">
                  <input type="checkbox" :checked="cacheSelection.documents" readonly>
                  <span class="checkmark"></span>
                </div>
                <span class="cache-icon">📄</span>
                <span><strong>Document Cache</strong> - Parsed document metadata and content</span>
              </li>
              <li :class="{ selected: cacheSelection.embeddings }" @click="cacheSelection.embeddings = !cacheSelection.embeddings">
                <div class="cache-checkbox">
                  <input type="checkbox" :checked="cacheSelection.embeddings" readonly>
                  <span class="checkmark"></span>
                </div>
                <span class="cache-icon">🔢</span>
                <span><strong>Embedding Cache</strong> - Vector embeddings for RAG queries</span>
              </li>
              <li :class="{ selected: cacheSelection.cache }" @click="cacheSelection.cache = !cacheSelection.cache">
                <div class="cache-checkbox">
                  <input type="checkbox" :checked="cacheSelection.cache" readonly>
                  <span class="checkmark"></span>
                </div>
                <span class="cache-icon">💾</span>
                <span><strong>Response Cache</strong> - Cached API responses</span>
              </li>
            </ul>
            <p class="warning-note">
              ⚡ Apps using cached data will experience slower first requests while caches rebuild.
            </p>
          </div>
          <div class="modal-footer">
            <button @click="showClearCacheModal = false" class="btn btn-secondary">Cancel</button>
            <button 
              @click="confirmClearCache" 
              class="btn btn-danger" 
              :disabled="loading.cache || (!cacheSelection.documents && !cacheSelection.embeddings && !cacheSelection.cache)">
              {{ loading.cache ? 'Clearing...' : '🗑️ Clear Selected' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'
import { useSystemHealthStore } from '@/stores/systemHealthStore'
import { gateway } from '@/services/gateway'

const router = useRouter()
const route = useRoute()
const assetStore = useAssetStore()
const systemHealth = useSystemHealthStore()

// Tab state
const tabs = [
  { id: 'actions', icon: '🚀', label: 'Quick Actions' },
  { id: 'services', icon: '🔧', label: 'Services' },
  { id: 'models', icon: '🧠', label: 'Models' },
  { id: 'logs', icon: '📋', label: 'Logs' },
  { id: 'config', icon: '🔑', label: 'Config' }
]
const activeTab = ref('actions')

// Loading states
const loading = reactive({
  refresh: false,
  assets: false,
  cache: false,
  health: false
})

// Service Metadata
const SERVICE_CONFIG: Record<string, { icon: string, port?: number, displayName?: string, assetId?: string }> = {
  gateway: { icon: '🌐', port: 8081, displayName: 'Gateway', assetId: 'hub-gateway' },
  ollama: { icon: '🦙', port: 11434, displayName: 'Ollama', assetId: 'llm-runtime' },
  qdrant: { icon: '🔍', port: 6333, displayName: 'Qdrant', assetId: 'vector-store' },
  redis: { icon: '📦', port: 6379, displayName: 'Redis', assetId: 'cache-queue' },
  postgresql: { icon: '🐘', port: 5432, displayName: 'PostgreSQL', assetId: 'metadata-store' },
  onyx: { icon: '🤖', displayName: 'Onyx Assistant', assetId: 'onyx-assistant' },
  'whisper-server': { icon: '👂', displayName: 'Whisper', assetId: 'speech' }
}

const serviceLoading = reactive<Record<string, boolean>>({})
const expandedServices = reactive<Record<string, boolean>>({})
const openMenus = reactive<Record<string, boolean>>({})

// Idle status and policy data
const idleStatus = ref<any>(null)
const globalIdleTimeout = ref(60) // Default from backend

// Asset policy data (for governance)
const assetPolicies = ref<Record<string, any>>({})
const loadingPolicies = ref<Record<string, boolean>>({})

// Services Computed from Store
const services = computed(() => {
  // Sort by order in config or name
  const sortedNames = Object.keys(SERVICE_CONFIG)
  
  // Merge store data with config
  return systemHealth.services.map(s => {
    const config = SERVICE_CONFIG[s.name] || { icon: '❓', displayName: s.name }
    let statusText = 'Unknown'
    let statusClass = 'status-unknown'
    let healthEmoji = '⚪'
    let healthDescription = 'Unknown state'
    
    // Determine health status based on service status and running state
    if (!s.running || s.status === 'stopped') {
      statusText = 'Stopped'
      statusClass = 'status-stopped'
      healthEmoji = '⚪'
      healthDescription = 'Not running'
    } else {
      switch(s.status) {
        case 'healthy':
          statusText = 'Healthy'
          statusClass = 'status-success'
          healthEmoji = '🟢'
          healthDescription = '/health OK'
          break
        case 'degraded':
          statusText = 'Degraded'
          statusClass = 'status-warning'
          healthEmoji = '🟡'
          healthDescription = 'Running but dependency issue'
          break
        case 'unhealthy':
          statusText = 'Unhealthy'
          statusClass = 'status-error'
          healthEmoji = '🔴'
          healthDescription = 'Running but failing checks'
          break
        case 'running':
          // If status is 'running' but we don't have health check, assume healthy
          statusText = 'Running'
          statusClass = 'status-success'
          healthEmoji = '🟢'
          healthDescription = '/health OK'
          break
        case 'error':
          statusText = 'Error'
          statusClass = 'status-error'
          healthEmoji = '🔴'
          healthDescription = 'Error state'
          break
        default:
          statusText = s.status
          statusClass = 'status-unknown'
          healthEmoji = '⚪'
          healthDescription = 'Unknown state'
      }
    }
    
    // Get idle/policy data from idleStatus
    const serviceRegistry = idleStatus.value?.serviceRegistry || {}
    const serviceInfo = serviceRegistry[s.name] || {}
    const lastUsed = serviceInfo.last_used || 0
    const currentTime = Date.now() / 1000
    const idleDuration = lastUsed > 0 ? Math.max(0, currentTime - lastUsed) : 0
    
    return {
      ...s,
      displayName: config.displayName || s.name,
      icon: config.icon,
      port: config.port,
      statusText,
      statusClass,
      healthEmoji,
      healthDescription,
      loading: serviceLoading[s.name] || false,
      idleSleepEnabled: serviceInfo.idle_sleep_enabled ?? true,
      idleTimeout: serviceInfo.idle_timeout_minutes,
      idleDuration,
      policyLoading: false
    }
  }).sort((a, b) => {
     // Config order
     const idxA = sortedNames.indexOf(a.name)
     const idxB = sortedNames.indexOf(b.name)
     if (idxA === -1 && idxB === -1) return a.name.localeCompare(b.name)
     if (idxA === -1) return 1
     if (idxB === -1) return -1
     return idxA - idxB
  })
})

// Models
const models = ref<any[]>([])
const showPullModal = ref(false)
const pullModelName = ref('')
const pulling = ref(false)

// Clear Cache Modal
const showClearCacheModal = ref(false)
const cacheSelection = reactive({
  documents: true,
  embeddings: true,
  cache: true
})

// Logs
const logs = ref([
  { timestamp: new Date(), level: 'info', source: 'Gateway', message: 'Server started on port 8081' },
  { timestamp: new Date(Date.now() - 60000), level: 'info', source: 'Ollama', message: 'Model llama3.2:3b loaded' },
  { timestamp: new Date(Date.now() - 120000), level: 'warning', source: 'Assets', message: 'Asset whisper-server returned unknown status' },
  { timestamp: new Date(Date.now() - 180000), level: 'error', source: 'Gateway', message: 'Failed to connect to Redis (connection refused)' }
])
const logFilter = ref('all')

const filteredLogs = computed(() => {
  if (logFilter.value === 'all') return logs.value
  return logs.value.filter(l => l.level === logFilter.value)
})

// Config
const config = reactive({
  gatewayUrl: 'http://localhost:8081',
  ollamaUrl: 'http://localhost:11434',
  cacheSize: '256 MB',
  vectorStore: 'Qdrant (localhost:6333)',
  debugMode: false,
  gpuEnabled: true
})

onMounted(async () => {
  // Load services first (critical), then idle status (optional)
  await Promise.all([
    loadModels(),
    systemHealth.fetchStatus()
  ])
  // Fetch idle status separately so it doesn't block services from loading
  fetchIdleStatus().catch(err => {
    console.warn('Idle status unavailable, services will work with defaults:', err)
  })
  
  // Close menus when clicking outside
  document.addEventListener('click', () => {
    Object.keys(openMenus).forEach(key => {
      openMenus[key] = false
    })
  })
})

// Watch for tab changes to refresh idle status
watch(activeTab, (newTab) => {
  if (newTab === 'services') {
    // Don't block on idle status fetch
    fetchIdleStatus().catch(err => {
      console.warn('Failed to refresh idle status:', err)
    })
  }
})

// Toast notifications
const toastMessage = ref<string | null>(null)
const toastType = ref<'success' | 'error'>('success')

function showToast(message: string, type: 'success' | 'error' = 'success') {
  toastMessage.value = message
  toastType.value = type
  setTimeout(() => { toastMessage.value = null }, 4000)
}

// Actions
async function refreshAll() {
  loading.refresh = true
  try {
    await Promise.all([
      assetStore.fetchAssets(),
      systemHealth.fetchStatus()
    ])
    showToast('✅ All data refreshed successfully')
  } catch (e) {
    showToast(`❌ Refresh failed: ${e}`, 'error')
  } finally {
    loading.refresh = false
  }
}

async function reloadAssets() {
  loading.assets = true
  try {
    const result = await gateway.reloadAssets()
    if (result.success) {
      await assetStore.fetchAssets()
      showToast(`✅ ${result.asset_count || 0} assets reloaded`)
    } else {
      showToast(`❌ Failed to reload: ${result.message}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Reload failed: ${e}`, 'error')
  } finally {
    loading.assets = false
  }
}

function clearCache() {
  // Show confirmation modal first
  showClearCacheModal.value = true
}

async function confirmClearCache() {
  showClearCacheModal.value = false
  loading.cache = true
  try {
    const result = await gateway.clearCache(cacheSelection)
    if (result.success) {
      const total = result.cleared?.total || 0
      const docs = result.cleared?.documents || 0
      const embeds = result.cleared?.embeddings || 0
      const cache = result.cleared?.cache || 0
      showToast(`✅ cache cleared - Docs: ${docs}, Embeds: ${embeds}, Resp: ${cache}`)
    } else {
      showToast(`❌ ${result.message || 'Failed to clear cache'}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Clear cache failed: ${e}`, 'error')
  } finally {
    loading.cache = false
  }
}

async function checkHealth() {
  loading.health = true
  try {
    const result = await gateway.healthCheck()
    const status = result.overall === 'healthy' ? '✅ Healthy' : 
                   result.overall === 'degraded' ? '⚠️ Degraded' : '🔴 Warning'
    showToast(`${status} - CPU: ${result.resources?.cpu_usage?.toFixed(0)}%, Mem: ${result.resources?.memory_usage?.toFixed(0)}%`)
  } catch (e) {
    showToast(`❌ Health check failed: ${e}`, 'error')
  } finally {
    loading.health = false
  }
}

// Services - now using Gateway API
async function startService(service: any) {
  serviceLoading[service.name] = true
  try {
    const result = await gateway.startAsset(service.name) // Use raw name
    if (result.success) {
      showToast(`✅ ${service.displayName} started`)
      // Refresh status after short delay to allow container to spin up
      setTimeout(() => systemHealth.fetchStatus(), 1000)
    } else {
      showToast(`❌ Failed to start: ${result.error}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to start: ${e}`, 'error')
  } finally {
    serviceLoading[service.name] = false
  }
}

async function stopService(service: any) {
  serviceLoading[service.name] = true
  try {
    const result = await gateway.stopAsset(service.name)
    if (result.success) {
      showToast(`⏸️ ${service.displayName} stopped`)
      setTimeout(() => systemHealth.fetchStatus(), 1000)
    } else {
      showToast(`❌ Failed to stop: ${result.error}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to stop: ${e}`, 'error')
  } finally {
    serviceLoading[service.name] = false
  }
}

async function restartService(service: any) {
  serviceLoading[service.name] = true
  try {
    const result = await gateway.restartAsset(service.name)
    if (result.success) {
      showToast(`🔄 ${service.displayName} restarted`)
      setTimeout(() => systemHealth.fetchStatus(), 2000)
    } else {
      showToast(`❌ Failed to restart: ${result.error}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to restart: ${e}`, 'error')
  } finally {
    serviceLoading[service.name] = false
  }
}

// Policy & Automation Controls
async function fetchIdleStatus() {
  try {
    const status = await gateway.getIdleStatus()
    idleStatus.value = status
    globalIdleTimeout.value = status.idleTimeout || 60
  } catch (e) {
    console.warn('Failed to fetch idle status, using defaults:', e)
    // Set default values so UI doesn't break
    if (!idleStatus.value) {
      idleStatus.value = {
        autoWakeEnabled: true,
        idleTimeout: 60,
        idleSleepEnabled: true,
        serviceRegistry: {}
      }
      globalIdleTimeout.value = 60
    }
  }
}

function togglePolicyControls(serviceName: string) {
  expandedServices[serviceName] = !expandedServices[serviceName]
  if (expandedServices[serviceName]) {
    fetchIdleStatus() // Refresh idle status when expanding
    // Auto-load policy data when expanding
    const service = services.value.find(s => s.name === serviceName)
    if (service && !assetPolicies.value[serviceName]) {
      loadServicePolicy(service)
    }
  }
}

function formatIdleDuration(seconds: number): string {
  if (seconds <= 0) return 'Not idle'
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  }
  return `${minutes}m`
}

async function updateAutoSleep(service: any, event: Event) {
  const target = event.target as HTMLInputElement
  service.policyLoading = true
  try {
    const result = await gateway.updateServiceAutoSleep(service.name, target.checked)
    if (result.status === 'success') {
      showToast(`✅ Auto-sleep ${target.checked ? 'enabled' : 'disabled'} for ${service.displayName}`)
      await fetchIdleStatus()
    } else {
      showToast(`❌ Failed to update auto-sleep`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to update: ${e}`, 'error')
  } finally {
    service.policyLoading = false
  }
}

async function updateIdleTimeout(service: any, event: Event) {
  const target = event.target as HTMLInputElement
  const timeout = parseInt(target.value)
  if (isNaN(timeout) || timeout < 1) return
  
  service.policyLoading = true
  try {
    const result = await gateway.updateServiceAutoSleep(service.name, service.idleSleepEnabled, timeout)
    if (result.status === 'success') {
      showToast(`✅ Idle timeout updated to ${timeout} minutes`)
      await fetchIdleStatus()
    } else {
      showToast(`❌ Failed to update timeout`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to update: ${e}`, 'error')
  } finally {
    service.policyLoading = false
  }
}

async function suspendService(service: any) {
  service.policyLoading = true
  try {
    const result = await gateway.suspendService(service.name)
    if (result.status === 'success') {
      showToast(`⏸️ ${service.displayName} suspended`)
      await Promise.all([systemHealth.fetchStatus(), fetchIdleStatus()])
    } else {
      showToast(`❌ Failed to suspend: ${result.message}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to suspend: ${e}`, 'error')
  } finally {
    service.policyLoading = false
  }
}

async function keepWarm(service: any, durationMinutes: number) {
  service.policyLoading = true
  try {
    const result = await gateway.keepServiceWarm(service.name, durationMinutes)
    if (result.status === 'success') {
      showToast(`🔥 ${service.displayName} will stay warm for ${durationMinutes} minutes`)
      await fetchIdleStatus()
    } else {
      showToast(`❌ Failed to keep warm: ${result.message}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to keep warm: ${e}`, 'error')
  } finally {
    service.policyLoading = false
  }
}

// Governance & Usage - Load Policy Data
async function loadServicePolicy(service: any) {
  const config = SERVICE_CONFIG[service.name]
  const assetId = config?.assetId || service.name
  
  loadingPolicies.value[service.name] = true
  try {
    const asset = await gateway.getAsset(assetId)
    if (asset && asset.policy) {
      assetPolicies.value[service.name] = {
        allowed_apps: asset.policy.allowed_apps || [],
        max_concurrency: asset.policy.max_concurrency,
        required_models: asset.policy.required_models || [],
        served_models: asset.policy.served_models || []
      }
    } else {
      assetPolicies.value[service.name] = {}
    }
  } catch (e) {
    console.warn(`Failed to load policy for ${service.name}:`, e)
    // Try alternative asset IDs
    const alternatives = [service.name, `${service.name}-runtime`, `abs-${service.name}`]
    for (const altId of alternatives) {
      if (altId === assetId) continue
      try {
        const asset = await gateway.getAsset(altId)
        if (asset && asset.policy) {
          assetPolicies.value[service.name] = {
            allowed_apps: asset.policy.allowed_apps || [],
            max_concurrency: asset.policy.max_concurrency,
            required_models: asset.policy.required_models || [],
            served_models: asset.policy.served_models || []
          }
          break
        }
      } catch {
        // Continue to next alternative
      }
    }
    if (!assetPolicies.value[service.name]) {
      assetPolicies.value[service.name] = {}
    }
  } finally {
    loadingPolicies.value[service.name] = false
  }
}

// Diagnostic & Ops Actions
function toggleMenu(serviceName: string) {
  // Close all other menus
  Object.keys(openMenus).forEach(key => {
    if (key !== serviceName) {
      openMenus[key] = false
    }
  })
  openMenus[serviceName] = !openMenus[serviceName]
}

function viewServiceLogs(service: any) {
  openMenus[service.name] = false
  // Switch to Logs tab and filter by service
  activeTab.value = 'logs'
  logFilter.value = service.name.toLowerCase()
  showToast(`📜 Viewing logs for ${service.displayName}`)
}

function jumpToObservability(service: any) {
  openMenus[service.name] = false
  // Navigate to Observability page with service filter
  const workspaceId = route.params.workspaceId || 'default'
  router.push({
    path: `/workspace/${workspaceId}/observability`,
    query: { 
      service: service.name,
      filter: service.name.toLowerCase()
    }
  })
  showToast(`🔍 Opening Observability for ${service.displayName}`)
}

async function downloadServiceLogs(service: any) {
  openMenus[service.name] = false
  try {
    // Try to fetch logs from backend
    const config = SERVICE_CONFIG[service.name]
    const assetId = config?.assetId || service.name
    
    // For now, create a simple log file with service info
    // In production, this would fetch actual logs from the backend
    const logContent = `Service: ${service.displayName} (${service.name})
Status: ${service.running ? 'Running' : 'Stopped'}
Health: ${service.statusText}
Port: ${service.port || 'N/A'}
Timestamp: ${new Date().toISOString()}

[Logs would be fetched from backend in production]
For support, include this file along with service logs from Docker:
docker logs ${service.name} --tail 1000 > ${service.name}-logs.txt
`
    
    const blob = new Blob([logContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${service.name}-logs-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    showToast(`💾 Logs downloaded for ${service.displayName}`)
  } catch (e) {
    showToast(`❌ Failed to download logs: ${e}`, 'error')
  }
}

// Models
async function loadModels() {
  try {
    const response = await fetch('http://localhost:11434/api/tags')
    if (response.ok) {
      const data = await response.json()
      models.value = data.models || []
    }
  } catch (e) {
    console.error('Failed to load models:', e)
  }
}

async function pullModel() {
  if (!pullModelName.value) return
  pulling.value = true
  try {
    // Would use streaming API for progress
    await fetch('http://localhost:11434/api/pull', {
      method: 'POST',
      body: JSON.stringify({ name: pullModelName.value })
    })
    showPullModal.value = false
    pullModelName.value = ''
    await loadModels()
  } catch (e) {
    alert('Failed to pull model: ' + e)
  } finally {
    pulling.value = false
  }
}

async function loadModel(model: any) {
  alert(`Loading ${model.name}...`)
}

async function deleteModel(model: any) {
  if (!confirm(`Delete model ${model.name}?`)) return
  try {
    await fetch('http://localhost:11434/api/delete', {
      method: 'DELETE',
      body: JSON.stringify({ name: model.name })
    })
    await loadModels()
  } catch (e) {
    alert('Failed to delete model: ' + e)
  }
}

function refreshLogs() {
  // Would fetch from gateway
}

// Formatters
function formatSize(bytes: number): string {
  if (!bytes) return '-'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(1)} GB`
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(0)} MB`
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString()
}

function formatLogTime(date: Date): string {
  return date.toLocaleTimeString()
}
</script>

<style scoped>
.admin-view {
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 1.5rem;
}

.view-header h1 {
  margin: 0;
  font-size: 1.75rem;
}

.view-desc {
  color: var(--text-secondary);
  margin-top: 0.5rem;
}

/* Tabs */
.admin-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
  overflow-x: auto;
}

.tab-btn {
  padding: 0.6rem 1rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.9rem;
  border-radius: 6px 6px 0 0;
  white-space: nowrap;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.tab-btn.active {
  color: var(--accent-primary);
  background: var(--accent-subtle);
  border-bottom: 2px solid var(--accent-primary);
}

/* Sections */
.admin-section {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin: 0;
  font-size: 1.1rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

/* Quick Actions */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.action-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 1.25rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-card:hover:not(:disabled) {
  border-color: var(--accent-primary);
  transform: translateY(-2px);
}

.action-card:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-card.warning:hover:not(:disabled) {
  border-color: var(--status-warning);
}

.action-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.75rem;
}

.action-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.action-desc {
  display: block;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* Services Table */
.services-table {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.service-row-wrapper {
  border-bottom: 1px solid var(--border-color);
}

.service-row-wrapper:last-child {
  border-bottom: none;
}

.service-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr 0.5fr 2fr;
  padding: 1rem;
  align-items: center;
}

.service-row.header {
  background: var(--bg-tertiary);
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.service-icon {
  margin-right: 0.5rem;
}

.col-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.status-dot {
  font-size: 1.2rem;
  margin-right: 0.5rem;
}

.status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  background-color: var(--text-muted);
}
.status-indicator.running { background-color: var(--success); }
.status-indicator.stopped { background-color: var(--danger); } 

.status-dot.status-success { color: var(--success); }
.status-dot.status-warning { color: var(--warning); }
.status-dot.status-error { color: var(--danger); }
.status-dot.status-stopped { color: var(--text-muted); }
.status-dot.status-unknown { color: #ccc; }

.status-dot.running { color: var(--success); } /* Legacy support */
.status-dot.stopped { color: var(--text-muted); } /* Legacy support */
.status-dot.error { color: var(--status-error); }
.status-dot.restarting { color: var(--accent-primary); }

/* Health & Readiness Legend */
.health-legend {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border-color);
}

.health-legend h3 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 600;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.legend-emoji {
  font-size: 1.2rem;
}

.legend-label {
  font-weight: 600;
  color: var(--text-primary);
  min-width: 80px;
}

.legend-desc {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

/* Health Column Styling */
.col-health {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: help;
}

.health-emoji {
  font-size: 1.1rem;
  line-height: 1;
}

.health-text {
  font-weight: 500;
  color: var(--text-primary);
}

.health-hint {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-style: italic;
}

/* Policy & Automation Controls */
.policy-controls {
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border-color);
  padding: 1.5rem;
  margin: 0;
  border-radius: 0 0 8px 8px;
}

.policy-header {
  margin-bottom: 1rem;
}

.policy-header h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.policy-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.policy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.policy-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.policy-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.policy-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.policy-input {
  width: 80px;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.9rem;
}

.policy-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.policy-value {
  font-weight: 600;
  color: var(--accent-primary);
  font-size: 0.95rem;
}

.policy-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.policy-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

/* Governance & Usage Section */
.governance-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.governance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.governance-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.governance-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.governance-value {
  font-weight: 500;
  color: var(--accent-primary);
  font-size: 1rem;
}

.governance-value-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.25rem 0;
}

.governance-tag {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
  color: var(--text-primary);
  font-family: monospace;
}

.policy-loading {
  padding: 1rem;
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
}

/* Actions Menu (⋮) */
.actions-menu-wrapper {
  position: relative;
  display: inline-block;
}

.btn-icon {
  min-width: 32px;
  padding: 0.4rem 0.5rem;
  font-size: 1.2rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.actions-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 1000;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  text-align: left;
  color: var(--text-primary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.menu-item:hover {
  background: var(--bg-tertiary);
}

.menu-item:active {
  background: var(--bg-secondary);
}

.menu-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

/* Error Banner */
.error-banner {
  background: var(--status-error);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-content strong {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.error-content p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
  opacity: 0.95;
}

.error-hint {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  opacity: 0.85;
  font-style: italic;
}

/* Models Grid */
.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.model-card {
  background: var(--bg-tertiary);
  border-radius: 10px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.model-name {
  font-weight: 600;
}

.model-size {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.model-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.meta-item {
  font-size: 0.8rem;
}

.meta-label {
  color: var(--text-muted);
  display: block;
}

.model-actions {
  display: flex;
  gap: 0.5rem;
}

/* Logs */
.log-filter {
  padding: 0.4rem 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
}

.logs-container {
  max-height: 400px;
  overflow-y: auto;
  background: var(--bg-primary);
  border-radius: 8px;
  padding: 0.5rem;
  font-family: monospace;
  font-size: 0.85rem;
}

.log-entry {
  display: grid;
  grid-template-columns: 80px 60px 100px 1fr;
  gap: 0.75rem;
  padding: 0.5rem;
  border-bottom: 1px solid var(--border-color);
}

.log-time {
  color: var(--text-muted);
}

.log-level {
  font-weight: 600;
}
.log-level.error { color: var(--status-error); }
.log-level.warning { color: var(--status-warning); }
.log-level.info { color: var(--status-success); }

.log-source {
  color: var(--accent-primary);
}

.empty-logs {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

/* Config */
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.config-card {
  background: var(--bg-tertiary);
  border-radius: 10px;
  padding: 1.25rem;
}

.config-card h3 {
  margin: 0 0 1rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.config-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
}

.config-item:last-child {
  border-bottom: none;
}

.config-label {
  color: var(--text-secondary);
}

.config-value {
  font-family: monospace;
}

/* Switch Toggle */
.switch {
  position: relative;
  width: 40px;
  height: 22px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  background: var(--border-color);
  border-radius: 22px;
  cursor: pointer;
  transition: 0.3s;
}

.slider:before {
  content: "";
  position: absolute;
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background: #fff;
  border-radius: 50%;
  transition: 0.3s;
}

input:checked + .slider {
  background: var(--accent-primary);
}

input:checked + .slider:before {
  transform: translateX(18px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-secondary);
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  border: 1px solid var(--border-color);
}

.modal-content.small {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.1rem;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.25rem;
  cursor: pointer;
}

.modal-body {
  padding: 1.25rem;
}

.modal-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.form-input {
  width: 100%;
  padding: 0.6rem 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.form-help {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.form-help a {
  color: var(--accent-primary);
}

/* Buttons */
.btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.15);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
}

.btn-primary {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-success {
  background: rgba(34, 197, 94, 0.2);
  border-color: var(--status-success);
  color: var(--status-success);
}

.btn-warning {
  background: rgba(245, 158, 11, 0.2);
  border-color: var(--status-warning);
  color: var(--status-warning);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.2);
  border-color: var(--status-error);
  color: var(--status-error);
}

.btn-secondary {
  background: transparent;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

/* Toast Notifications */
.toast {
  position: fixed;
  top: 1rem;
  right: 1rem;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  background: rgba(34, 197, 94, 0.95);
  color: white;
}

.toast.error {
  background: rgba(239, 68, 68, 0.95);
  color: white;
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* Clear Cache Modal */
.warning-header {
  background: rgba(245, 158, 11, 0.1);
  border-color: var(--status-warning);
}

.warning-header h2 {
  color: var(--status-warning);
}

.warning-text {
  margin: 0 0 1rem;
  color: var(--text-primary);
}

.cache-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem;
}

.cache-list li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.cache-list.selectable li {
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.cache-list.selectable li:hover {
  background: var(--bg-secondary);
}

.cache-list.selectable li.selected {
  background: rgba(34, 197, 94, 0.05);
  border-color: var(--status-success);
}

/* Custom Checkbox */
.cache-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  user-select: none;
  margin-right: 0.25rem;
}

.cache-checkbox input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  height: 20px;
  width: 20px;
  background-color: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 4px;
  transition: all 0.2s;
  position: relative;
}

.cache-checkbox:hover input ~ .checkmark {
  border-color: var(--primary-color);
}

.cache-checkbox input:checked ~ .checkmark {
  background-color: var(--status-success);
  border-color: var(--status-success);
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.cache-checkbox input:checked ~ .checkmark:after {
  display: block;
}

.cache-checkbox .checkmark:after {
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.cache-icon {
  font-size: 1.25rem;
}

.cache-list li span:last-child {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.cache-list li strong {
  color: var(--text-primary);
}

.warning-note {
  padding: 0.75rem;
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid var(--status-warning);
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0;
}
</style>
