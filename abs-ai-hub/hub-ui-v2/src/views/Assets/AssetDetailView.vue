<template>
  <div class="asset-detail">
    <!-- Back Navigation -->
    <router-link :to="`/workspace/${workspaceId}/assets`" class="back-link">
      ← Back to Assets
    </router-link>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <span class="spinner">⏳</span> Loading asset...
    </div>

    <!-- 404 State -->
    <div v-else-if="!asset" class="error-state">
      <span class="error-icon">❌</span>
      <h2>Asset Not Found</h2>
      <p>The requested asset does not exist or has been removed.</p>
      <router-link :to="`/workspace/${workspaceId}/assets`" class="btn btn-primary">
        Return to Assets
      </router-link>
    </div>

    <!-- Asset Content -->
    <div v-else class="asset-content">
      
      <!-- 6.1 Header: Identity + Status + Primary Action -->
      <header class="detail-header">
        <div class="header-main">
          <span class="asset-icon">{{ getAssetIcon(asset.class) }}</span>
          <div class="header-info">
            <h1>{{ asset.display_name || asset.id }}</h1>
            <div class="header-badges">
              <span class="badge class-badge">{{ asset.class }}</span>
              <span class="badge interface-badge">{{ asset.interface }}</span>
              <span class="status-badge" :class="getStateClass(observedState)">
                {{ getStateIcon(observedState) }} {{ observedState }}
              </span>
            </div>
            <div class="header-summary">
              <span>Used by {{ consumerCount }} apps</span>
              <span v-if="providerCount > 0">• Requires {{ providerCount }} dependencies</span>
            </div>
          </div>
        </div>
        
        <!-- Primary Action for Apps -->
        <div v-if="isApp && appUrl" class="primary-action">
          <button class="btn btn-hero" @click="openApp">
            🚀 Open App
          </button>
        </div>
      </header>

      <!-- 6.2 Identity & Contract -->
      <section class="detail-section">
        <h2>📋 Identity & Contract</h2>
        <div class="info-grid">
          <div class="info-item">
            <dt>Asset ID</dt>
            <dd><code>{{ asset.id }}</code></dd>
          </div>
          <div class="info-item">
            <dt>Version</dt>
            <dd>{{ asset.version || 'N/A' }}</dd>
          </div>
          <div class="info-item">
            <dt>Class</dt>
            <dd>{{ asset.class }}</dd>
          </div>
          <div class="info-item">
            <dt>Interface</dt>
            <dd>{{ asset.interface }}</dd>
          </div>
          <div class="info-item">
            <dt>Interface Version</dt>
            <dd>{{ asset.interface_version || 'v1' }}</dd>
          </div>
          <div class="info-item">
            <dt>Provider</dt>
            <dd>{{ asset.ownership?.provider || 'N/A' }}</dd>
          </div>
          <div class="info-item">
            <dt>Visibility</dt>
            <dd>{{ asset.ownership?.visibility || 'private' }}</dd>
          </div>
          <div v-if="asset.pack_id" class="info-item">
            <dt>Pack ID</dt>
            <dd>{{ asset.pack_id }}</dd>
          </div>
        </div>
      </section>

      <!-- 6.3 Lifecycle: Intent, State & Health -->
      <section class="detail-section lifecycle-section">
        <h2>🔄 Lifecycle – Intent vs Observed</h2>
        
        <div class="state-comparison">
          <div class="state-box desired">
            <span class="state-label">Desired</span>
            <span class="state-value" :class="desiredState">{{ formatDesired(desiredState) }}</span>
          </div>
          <span class="state-arrow">→</span>
          <div class="state-box observed">
            <span class="state-label">Observed</span>
            <span class="state-value" :class="observedState">
              {{ getStateIcon(observedState) }} {{ observedState }}
            </span>
          </div>
        </div>

        <div class="lifecycle-details">
          <div v-if="autoSleepMin" class="lifecycle-item">
            <span class="label">💤 Auto-sleep</span>
            <span class="value">{{ autoSleepMin }} minutes of inactivity</span>
          </div>
          <div v-if="asset.metadata?._status?.last_used_at" class="lifecycle-item">
            <span class="label">📅 Last Used</span>
            <span class="value">{{ formatTime(asset.metadata._status.last_used_at) }}</span>
          </div>
          <div v-if="asset.metadata?._status?.last_started_at" class="lifecycle-item">
            <span class="label">▶️ Last Started</span>
            <span class="value">{{ formatTime(asset.metadata._status.last_started_at) }}</span>
          </div>
        </div>

        <!-- Health Check Insight -->
        <div class="health-insight">
          <h3>Health Insight</h3>
          <div class="health-checks">
            <div class="health-check" :class="healthStatus.service">
              <span class="check-icon">{{ healthStatus.service === 'ok' ? '✓' : healthStatus.service === 'degraded' ? '⚠️' : '✗' }}</span>
              <span>Service Health: {{ healthStatus.service === 'ok' ? 'OK' : healthStatus.service === 'degraded' ? 'Degraded' : 'Failed' }}</span>
            </div>
            <div class="health-check" :class="healthStatus.deps">
              <span class="check-icon">{{ healthStatus.deps === 'ok' ? '✓' : '✗' }}</span>
              <span>Dependency Health: {{ healthStatus.deps === 'ok' ? 'All available' : 'Issues detected' }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 6.4 Policy & Resource Constraints -->
      <section class="detail-section">
        <h2>📦 Policy & Resources</h2>
        
        <!-- Resource Badges -->
        <div class="resource-badges">
          <span v-if="asset.resources?.gpu_required" class="resource-badge gpu">
            🔥 GPU
          </span>
          <span v-if="asset.resources?.min_vram_gb" class="resource-badge vram">
            {{ asset.resources.min_vram_gb }}GB VRAM
          </span>
          <span v-if="asset.resources?.cold_start_sec" class="resource-badge cold">
            ⏱️ {{ asset.resources.cold_start_sec }}s cold start
          </span>
          <span v-if="!asset.resources?.gpu_required" class="resource-badge cpu">
            CPU only
          </span>
        </div>

        <!-- Policy Details by Asset Type -->
        <div class="policy-details">
          <!-- Model Policy -->
          <template v-if="asset.class === 'model'">
            <div v-if="asset.runtime?.served_by" class="policy-item">
              <dt>Served By</dt>
              <dd>{{ asset.runtime.served_by }}</dd>
            </div>
            <div v-if="asset.metadata?.format" class="policy-item">
              <dt>Format</dt>
              <dd>{{ asset.metadata.format }}</dd>
            </div>
            <div v-if="asset.metadata?.parameter_size" class="policy-item">
              <dt>Parameters</dt>
              <dd>{{ asset.metadata.parameter_size }}</dd>
            </div>
          </template>

          <!-- App Policy -->
          <template v-if="isApp">
            <div v-if="requiredModels.length > 0" class="policy-item">
              <dt>Required Models</dt>
              <dd>
                <div class="dep-list">
                  <span v-for="model in requiredModels" :key="model" class="dep-badge">{{ model }}</span>
                </div>
              </dd>
            </div>
          </template>

          <!-- Service Policy -->
          <template v-if="asset.class === 'service'">
            <div v-if="asset.policy?.served_models?.length" class="policy-item">
              <dt>Provided Interfaces</dt>
              <dd>
                <div class="dep-list">
                  <span v-for="iface in asset.policy.served_models" :key="iface" class="dep-badge">{{ iface }}</span>
                </div>
              </dd>
            </div>
          </template>
        </div>
      </section>

      <!-- 6.5 Relationships -->
      <section class="detail-section">
        <h2>🔗 Relationships</h2>
        
        <div class="relationship-grid">
          <!-- Consumers -->
          <div class="relationship-panel">
            <h3>Used By (Consumers)</h3>
            <div v-if="consumers.length === 0" class="empty-deps">
              No known consumers
            </div>
            <div v-else class="dep-list">
              <router-link 
                v-for="consumer in consumers" 
                :key="consumer"
                :to="`/workspace/${workspaceId}/assets/${consumer}`"
                class="dep-link"
              >
                {{ consumer }}
              </router-link>
            </div>
          </div>

          <!-- Providers -->
          <div class="relationship-panel">
            <h3>Depends On (Providers)</h3>
            <div v-if="providers.length === 0" class="empty-deps">
              No dependencies
            </div>
            <div v-else class="dep-list">
              <router-link 
                v-for="provider in providers" 
                :key="provider"
                :to="`/workspace/${workspaceId}/assets/${provider}`"
                class="dep-link"
              >
                {{ provider }}
              </router-link>
            </div>
          </div>
        </div>

        <div class="relationship-note">
          <strong>Note:</strong> Relationship data reflects authored intent from policy definitions.
          Runtime consumer tracking is a planned enhancement.
        </div>
      </section>

      <!-- 6.6 Runtime & Status -->
      <section class="detail-section">
        <h2>📊 Runtime Status</h2>
        <div class="info-grid">
          <div class="info-item">
            <dt>Health</dt>
            <dd class="health-value" :class="healthStatus.service">
              {{ healthStatus.service === 'ok' ? '✓ Healthy' : healthStatus.service === 'degraded' ? '⚠️ Degraded' : '✗ Unhealthy' }}
            </dd>
          </div>
          <div v-if="asset.metadata?._status?.active_requests !== undefined" class="info-item">
            <dt>Active Requests</dt>
            <dd>{{ asset.metadata._status.active_requests }}</dd>
          </div>
          <div v-if="asset.resources?.cold_start_sec" class="info-item">
            <dt>Cold Start Time</dt>
            <dd>{{ asset.resources.cold_start_sec }}s</dd>
          </div>
          <div v-if="asset.metadata?._status?.reason" class="info-item">
            <dt>Status Reason</dt>
            <dd>{{ asset.metadata._status.reason }}</dd>
          </div>
        </div>
      </section>

      <!-- 6.7 Contextual Actions -->
      <section class="detail-section actions-section">
        <h2>⚡ Actions</h2>
        <div class="action-buttons">
          <!-- App Actions -->
          <template v-if="isApp">
            <button v-if="appUrl" class="btn btn-primary" @click="openApp">
              🚀 Open App
            </button>
            <button class="btn btn-secondary" @click="viewBindings">
              🔗 View Bindings
            </button>
          </template>

          <!-- Service Actions -->
          <template v-else-if="asset.class === 'service'">
            <button v-if="canStart" class="btn btn-success" @click="startService" :disabled="actionLoading">
              {{ actionLoading ? '⏳' : '▶️' }} Start
            </button>
            <button v-if="canStop" class="btn btn-warning" @click="stopService" :disabled="actionLoading">
              {{ actionLoading ? '⏳' : '⏸️' }} Stop
            </button>
            <button class="btn btn-secondary" @click="restartService" :disabled="actionLoading">
              {{ actionLoading ? '⏳' : '🔄' }} Restart
            </button>
          </template>

          <!-- Model Actions -->
          <template v-else-if="asset.class === 'model'">
            <button class="btn btn-secondary" @click="viewUsage">
              📊 View Usage
            </button>
          </template>

          <!-- Dataset/Tool Actions -->
          <template v-else>
            <button class="btn btn-secondary" @click="viewUsage">
              📊 View Usage
            </button>
          </template>
        </div>
        
        <!-- Action Feedback -->
        <div v-if="actionSuccess" class="action-alert success">
          ✓ {{ actionSuccess }}
        </div>
        <div v-if="actionError" class="action-alert error">
          ✗ {{ actionError }}
        </div>
      </section>
    </div>
    
    <!-- Bindings Modal -->
    <div v-if="showBindingsModal" class="modal-overlay" @click.self="showBindingsModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>🔗 App Bindings</h2>
          <button class="modal-close" @click="showBindingsModal = false">✕</button>
        </div>
        <div class="modal-body">
          <!-- Required Models -->
          <div v-if="requiredModels.length > 0" class="binding-section">
            <h3>🧠 Required Models</h3>
            <div class="binding-list">
              <div v-for="model in requiredModels" :key="model" class="binding-item">
                <span class="binding-badge model">{{ model }}</span>
              </div>
            </div>
          </div>
          
          <!-- Allowed Embeddings -->
          <div v-if="allowedEmbeddings.length > 0" class="binding-section">
            <h3>🔢 Allowed Embeddings</h3>
            <div class="binding-list">
              <div v-for="embed in allowedEmbeddings" :key="embed" class="binding-item">
                <span class="binding-badge embed">{{ embed }}</span>
              </div>
            </div>
          </div>
          
          <!-- Defaults -->
          <div v-if="bindingDefaults && Object.keys(bindingDefaults).length > 0" class="binding-section">
            <h3>⚙️ Default Configuration</h3>
            <div class="defaults-grid">
              <div v-for="(value, key) in bindingDefaults" :key="key" class="default-item">
                <span class="default-key">{{ formatKey(key) }}</span>
                <span class="default-value">{{ value }}</span>
              </div>
            </div>
          </div>
          
          <!-- No bindings -->
          <div v-if="requiredModels.length === 0 && allowedEmbeddings.length === 0" class="no-bindings">
            No bindings configured for this app.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'

const route = useRoute()
const router = useRouter()
const assetStore = useAssetStore()

const loading = ref(true)

const workspaceId = computed(() => route.params.workspaceId as string)
const assetId = computed(() => route.params.assetId as string)

const asset = computed(() => 
  assetStore.assets.find((a: any) => a.id === assetId.value)
)

// Computed: isApp
const isApp = computed(() => 
  asset.value?.class === 'app' || asset.value?.class === 'application'
)

// Computed: App URL from metadata
const appUrl = computed(() => asset.value?.metadata?.url || '')

// Computed: Lifecycle states
const desiredState = computed(() => asset.value?.lifecycle?.desired || 'on-demand')
const observedState = computed(() => asset.value?.lifecycle?.state || asset.value?.status || 'unknown')
const autoSleepMin = computed(() => asset.value?.lifecycle?.auto_sleep_min)

// Computed: Required models from policy
const requiredModels = computed(() => asset.value?.policy?.required_models || [])

// Computed: Consumers and Providers
const consumers = computed(() => asset.value?.consumers || [])
const providers = computed(() => {
  // Derive from policy.required_models
  return asset.value?.policy?.required_models || []
})
const consumerCount = computed(() => consumers.value.length)
const providerCount = computed(() => providers.value.length)

// Computed: Health status (derived)
const healthStatus = computed(() => {
  const state = observedState.value
  const hasError = state === 'error'
  const isRunning = state === 'running'
  const isWarning = state === 'warming'
  
  return {
    service: hasError ? 'error' : isWarning ? 'degraded' : 'ok',
    deps: 'ok' // Placeholder - needs backend
  }
})

// Computed: Service action states
const canStart = computed(() => {
  const state = observedState.value
  return state === 'stopped' || state === 'suspended' || state === 'idle'
})
const canStop = computed(() => {
  const state = observedState.value
  return state === 'running'
})

onMounted(async () => {
  loading.value = true
  try {
    await assetStore.fetchAsset(assetId.value)
  } finally {
    loading.value = false
  }
})

// Helper functions
function getAssetIcon(assetClass?: string): string {
  const icons: Record<string, string> = {
    model: '🧠',
    service: '⚙️',
    tool: '🛠️',
    dataset: '📚',
    app: '📱',
    application: '📱'
  }
  return icons[assetClass?.toLowerCase() || ''] || '📦'
}

function getStateIcon(state: string): string {
  const icons: Record<string, string> = {
    running: '🟢',
    idle: '🟡',
    suspended: '⏸️',
    stopped: '⏹️',
    warming: '⚡',
    error: '🔴'
  }
  return icons[state?.toLowerCase()] || '⚪'
}

function getStateClass(state: string): string {
  const classes: Record<string, string> = {
    running: 'running',
    idle: 'idle',
    suspended: 'suspended',
    stopped: 'stopped',
    warming: 'warming',
    error: 'error'
  }
  return classes[state?.toLowerCase()] || 'unknown'
}

function formatDesired(desired: string): string {
  const labels: Record<string, string> = {
    running: 'Always Running',
    'on-demand': 'On Demand',
    suspended: 'Suspended'
  }
  return labels[desired] || desired
}

function formatTime(timestamp: string): string {
  if (!timestamp) return 'N/A'
  return new Date(timestamp).toLocaleString()
}

// Action handlers
function openApp() {
  if (appUrl.value) {
    window.open(appUrl.value, '_blank')
  }
}

// Bindings Modal state
const showBindingsModal = ref(false)

// Computed: Allowed embeddings from policy
const allowedEmbeddings = computed(() => asset.value?.policy?.allowed_embeddings || [])

// Computed: Binding defaults from policy
const bindingDefaults = computed(() => asset.value?.policy?.defaults || {})

function viewBindings() {
  showBindingsModal.value = true
}

function formatKey(key: string): string {
  // Convert snake_case to Title Case
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function viewUsage() {
  alert('View Usage: Coming soon')
}

const actionLoading = ref(false)
const actionError = ref<string | null>(null)
const actionSuccess = ref<string | null>(null)

async function startService() {
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  
  try {
    const { gateway } = await import('@/services/gateway')
    const result = await gateway.startAsset(assetId.value)
    
    if (result.success) {
      actionSuccess.value = result.message || 'Started successfully'
      // Refresh asset data
      await assetStore.fetchAsset(assetId.value)
    } else {
      actionError.value = result.error || 'Start failed'
    }
  } catch (e) {
    actionError.value = e instanceof Error ? e.message : 'Failed to start'
  } finally {
    actionLoading.value = false
    // Clear messages after delay
    setTimeout(() => {
      actionSuccess.value = null
      actionError.value = null
    }, 5000)
  }
}

async function stopService() {
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  
  try {
    const { gateway } = await import('@/services/gateway')
    const result = await gateway.stopAsset(assetId.value)
    
    if (result.success) {
      actionSuccess.value = result.message || 'Stopped successfully'
      await assetStore.fetchAsset(assetId.value)
    } else {
      actionError.value = result.error || 'Stop failed'
    }
  } catch (e) {
    actionError.value = e instanceof Error ? e.message : 'Failed to stop'
  } finally {
    actionLoading.value = false
    setTimeout(() => {
      actionSuccess.value = null
      actionError.value = null
    }, 5000)
  }
}

async function restartService() {
  actionLoading.value = true
  actionError.value = null
  actionSuccess.value = null
  
  try {
    const { gateway } = await import('@/services/gateway')
    const result = await gateway.restartAsset(assetId.value)
    
    if (result.success) {
      actionSuccess.value = result.message || 'Restarted successfully'
      await assetStore.fetchAsset(assetId.value)
    } else {
      actionError.value = result.error || 'Restart failed'
    }
  } catch (e) {
    actionError.value = e instanceof Error ? e.message : 'Failed to restart'
  } finally {
    actionLoading.value = false
    setTimeout(() => {
      actionSuccess.value = null
      actionError.value = null
    }, 5000)
  }
}
</script>

<style scoped>
.asset-detail {
  max-width: 1000px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  color: var(--accent-primary);
  text-decoration: none;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.back-link:hover {
  text-decoration: underline;
}

/* Header */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.header-main {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.asset-icon {
  font-size: 3rem;
}

.header-info h1 {
  margin: 0 0 0.5rem;
  font-size: 1.75rem;
}

.header-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.class-badge {
  background: var(--accent-subtle);
  color: var(--accent-primary);
}

.interface-badge {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.status-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge.running { background: rgba(34, 197, 94, 0.15); color: var(--status-success); }
.status-badge.idle { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.status-badge.suspended { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }
.status-badge.warming { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.status-badge.error { background: rgba(239, 68, 68, 0.15); color: var(--status-error); }

.header-summary {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.primary-action {
  flex-shrink: 0;
}

.btn-hero {
  padding: 0.75rem 1.5rem;
  background: var(--accent-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-hero:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

/* Sections */
.detail-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
}

.detail-section h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem;
  color: var(--text-primary);
}

.detail-section h3 {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0 0 0.75rem;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item dt {
  color: var(--text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item dd {
  margin: 0.25rem 0 0;
  font-size: 0.95rem;
}

code {
  background: var(--bg-tertiary);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85rem;
}

/* Lifecycle Section */
.state-comparison {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.state-box {
  flex: 1;
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.state-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.state-value {
  font-size: 1rem;
  font-weight: 600;
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
}

.state-value.running { background: rgba(34, 197, 94, 0.15); color: var(--status-success); }
.state-value.on-demand { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }
.state-value.idle { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.state-value.suspended { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }

.state-arrow {
  font-size: 1.5rem;
  color: var(--text-muted);
}

.lifecycle-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.lifecycle-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.lifecycle-item .label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.lifecycle-item .value {
  font-size: 0.9rem;
}

/* Health Insight */
.health-insight {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 1rem;
}

.health-checks {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.health-check {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.health-check.ok { color: var(--status-success); }
.health-check.degraded { color: #f59e0b; }
.health-check.error { color: var(--status-error); }

.check-icon {
  font-size: 1rem;
}

/* Resource Badges */
.resource-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.resource-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}

.resource-badge.gpu {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.resource-badge.vram {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.resource-badge.cold {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.resource-badge.cpu {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

/* Policy Details */
.policy-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.policy-item dt {
  color: var(--text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}

.policy-item dd {
  margin: 0;
}

.dep-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.dep-badge {
  padding: 0.25rem 0.5rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.8rem;
}

/* Relationships */
.relationship-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.relationship-panel {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 1rem;
}

.relationship-panel h3 {
  margin: 0 0 0.75rem;
}

.empty-deps {
  color: var(--text-muted);
  font-size: 0.85rem;
  font-style: italic;
}

.dep-link {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.8rem;
  text-decoration: none;
}

.dep-link:hover {
  background: var(--accent-primary);
  color: white;
}

.relationship-note {
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 6px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* Health value in runtime */
.health-value.ok { color: var(--status-success); }
.health-value.degraded { color: #f59e0b; }
.health-value.error { color: var(--status-error); }

/* Actions */
.actions-section .action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.btn {
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--accent-hover);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  border-color: var(--accent-primary);
}

.btn-success {
  background: rgba(34, 197, 94, 0.2);
  color: var(--status-success);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.btn-success:hover {
  background: rgba(34, 197, 94, 0.3);
}

.btn-warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.btn-warning:hover {
  background: rgba(245, 158, 11, 0.3);
}

/* States */
.loading-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-secondary);
}

.error-state .error-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.error-state h2 {
  margin: 0 0 0.5rem;
}

.error-state p {
  margin: 0 0 1.5rem;
}

.spinner {
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
  }
  
  .relationship-grid {
    grid-template-columns: 1fr;
  }
  
  .state-comparison {
    flex-direction: column;
  }
  
  .state-arrow {
    transform: rotate(90deg);
  }
}

/* Action Alerts */
.action-alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.action-alert.success {
  background: rgba(34, 197, 94, 0.15);
  color: var(--status-success);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.action-alert.error {
  background: rgba(239, 68, 68, 0.15);
  color: var(--status-error);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Bindings Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0.25rem;
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
}

.binding-section {
  margin-bottom: 1.5rem;
}

.binding-section h3 {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0 0 0.75rem;
}

.binding-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.binding-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
}

.binding-badge.model {
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.binding-badge.embed {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.defaults-grid {
  display: grid;
  gap: 0.75rem;
}

.default-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
}

.default-key {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.default-value {
  font-weight: 500;
  color: var(--text-primary);
}

.no-bindings {
  text-align: center;
  color: var(--text-muted);
  padding: 2rem;
  font-style: italic;
}
</style>
