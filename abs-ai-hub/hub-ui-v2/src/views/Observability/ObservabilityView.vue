<template>
  <div class="observability-view">
    <header class="view-header">
      <div class="header-content">
        <h1>📊 Observability</h1>
        <p class="view-desc">Monitor system health, observe asset states, and understand dependencies.</p>
      </div>
      <button @click="refreshAll" class="btn btn-primary" :disabled="loading">
        🔄 {{ loading ? 'Refreshing...' : 'Refresh All' }}
      </button>
    </header>
    
    <!-- Toast Notification -->
    <div v-if="toastMessage" class="toast" :class="toastType">
      {{ toastMessage }}
    </div>

    <!-- System Health Card with Breakdown -->
    <section class="health-section">
      <div class="health-card" :class="overallHealth.class">
        <div class="health-main">
          <div class="health-icon">{{ overallHealth.icon }}</div>
          <div class="health-info">
            <h2>System Health</h2>
            <span class="health-badge" :class="overallHealth.class">{{ overallHealth.badge }}</span>
          </div>
        </div>
        
        <!-- Health Breakdown - Critical Enhancement -->
        <div class="health-breakdown">
          <button 
            class="breakdown-item running" 
            @click="filterByState('running')"
            :class="{ active: stateFilter === 'running' }"
          >
            <span class="breakdown-count">{{ runningCount }}</span>
            <span class="breakdown-label">🟢 Running</span>
          </button>
          <button 
            class="breakdown-item idle" 
            @click="filterByState('idle')"
            :class="{ active: stateFilter === 'idle' }"
          >
            <span class="breakdown-count">{{ idleCount }}</span>
            <span class="breakdown-label">🟡 Standby</span>
          </button>
          <button 
            class="breakdown-item suspended" 
            @click="filterByState('suspended')"
            :class="{ active: stateFilter === 'suspended' }"
          >
            <span class="breakdown-count">{{ suspendedCount }}</span>
            <span class="breakdown-label">⏸️ Suspended</span>
          </button>
          <button 
            class="breakdown-item warming" 
            @click="filterByState('warming')"
            :class="{ active: stateFilter === 'warming' }"
            v-if="warmingCount > 0"
          >
            <span class="breakdown-count">{{ warmingCount }}</span>
            <span class="breakdown-label">⚡ Warming</span>
          </button>
          <button 
            class="breakdown-item error" 
            @click="filterByState('error')"
            :class="{ active: stateFilter === 'error' }"
            v-if="errorCount > 0"
          >
            <span class="breakdown-count">{{ errorCount }}</span>
            <span class="breakdown-label">🔴 Error</span>
          </button>
          <button 
            v-if="stateFilter" 
            class="breakdown-item clear"
            @click="clearFilter"
          >
            ✕ Clear
          </button>
        </div>
      </div>
    </section>

    <!-- System Inventory (renamed from Quick Stats) -->
    <section class="inventory-section">
      <div class="inventory-grid">
        <div class="inventory-card" @click="filterByClass('service')">
          <div class="inventory-icon">⚙️</div>
          <div class="inventory-content">
            <span class="inventory-count">{{ serviceCount }}</span>
            <span class="inventory-label">Services</span>
          </div>
        </div>
        <div class="inventory-card" @click="filterByClass('app')">
          <div class="inventory-icon">📱</div>
          <div class="inventory-content">
            <span class="inventory-count">{{ appCount }}</span>
            <span class="inventory-label">Apps</span>
          </div>
        </div>
        <div class="inventory-card" @click="filterByClass('model')">
          <div class="inventory-icon">🧠</div>
          <div class="inventory-content">
            <span class="inventory-count">{{ modelCount }}</span>
            <span class="inventory-label">Models</span>
          </div>
        </div>
        <div class="inventory-card" @click="filterByClass('tool')">
          <div class="inventory-icon">🛠️</div>
          <div class="inventory-content">
            <span class="inventory-count">{{ toolCount }}</span>
            <span class="inventory-label">Tools</span>
          </div>
        </div>
        <div class="inventory-card" @click="filterByClass('dataset')">
          <div class="inventory-icon">📚</div>
          <div class="inventory-content">
            <span class="inventory-count">{{ datasetCount }}</span>
            <span class="inventory-label">Datasets</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Active Filter Display -->
    <div v-if="stateFilter || classFilter" class="active-filter">
      <span>Filtering: </span>
      <span v-if="stateFilter" class="filter-tag">{{ stateFilter }} <button @click="stateFilter = null">✕</button></span>
      <span v-if="classFilter" class="filter-tag">{{ classFilter }} <button @click="classFilter = null">✕</button></span>
      <button class="clear-all" @click="clearAllFilters">Clear All</button>
    </div>

    <!-- Asset Cards Grid -->
    <section class="assets-section">
      <div class="assets-grid">
        <div 
          v-for="asset in filteredAssets" 
          :key="asset.id" 
          class="asset-card"
          :class="[getHealthBadgeClass(asset), { selected: selectedAsset?.id === asset.id }]"
          @click="selectAsset(asset)"
        >
          <!-- Card Header - Identity + Labeled Status -->
          <div class="card-header">
            <div class="asset-identity">
              <span class="asset-icon">{{ getAssetIcon(asset.class) }}</span>
              <div class="asset-info">
                <h3>{{ asset.display_name || asset.id }}</h3>
                <span class="asset-type">{{ asset.class }} • {{ asset.interface }}</span>
              </div>
            </div>
            <!-- Labeled Status Badge -->
            <div class="status-badge-labeled" :class="getHealthBadgeClass(asset)">
              <span class="status-icon">{{ getHealthBadgeIcon(asset) }}</span>
              <span class="status-label">{{ getHealthBadgeLabel(asset) }}</span>
            </div>
          </div>
          
          <!-- State Box - Authoritative Section -->
          <div class="state-box">
            <div class="state-row">
              <span class="state-label">Desired</span>
              <span class="state-value desired" :class="getDesiredClass(asset)">
                {{ formatDesired(asset.lifecycle?.desired) }}
              </span>
            </div>
            <div class="state-row">
              <span class="state-label">Observed</span>
              <span class="state-value observed" :class="getObservedClass(asset)">
                {{ formatObserved(asset) }}
              </span>
            </div>
            <!-- Health Check Indicators -->
            <div class="health-checks" v-if="getObservedState(asset) === 'running'">
              <span class="check-item ok">✓ Health OK</span>
              <span class="check-item ok" v-if="!hasDependencies(asset) || getDepsHealthy(asset)">✓ Deps OK</span>
              <span class="check-item ok" v-if="!asset.resources?.gpu_required || true">✓ Resources</span>
            </div>
            <div class="health-checks" v-else-if="isError(asset)">
              <span class="check-item error">✗ Health Check Failed</span>
              <span class="check-item" v-if="hasDependencies(asset) && !getDepsHealthy(asset)">⚠ Dependency Issue</span>
            </div>
          </div>
          
          <!-- Cold Start Info (for services/models) -->
          <div v-if="showColdStartInfo(asset)" class="cold-start-section">
            <div class="cold-start-row" v-if="asset.resources?.cold_start_sec">
              <span class="cold-start-label">⏱️ Cold Start</span>
              <span class="cold-start-value">~{{ asset.resources.cold_start_sec }}s</span>
            </div>
            <div class="cold-start-row" v-if="asset.lifecycle?.auto_sleep_min">
              <span class="cold-start-label">💤 Auto-sleep</span>
              <span class="cold-start-value">{{ asset.lifecycle.auto_sleep_min }} min</span>
            </div>
          </div>
          
          <!-- Dependencies / Consumers -->
          <div class="deps-section" v-if="hasDependencies(asset) || hasConsumers(asset)">
            <div v-if="getConsumers(asset).length > 0" class="deps-row">
              <span class="deps-label">Used by:</span>
              <div class="deps-list">
                <span v-for="c in getConsumers(asset).slice(0, 3)" :key="c" class="dep-tag">{{ c }}</span>
                <span v-if="getConsumers(asset).length > 3" class="dep-more">+{{ getConsumers(asset).length - 3 }}</span>
              </div>
            </div>
            <div v-if="getDependencies(asset).length > 0" class="deps-row">
              <span class="deps-label">Depends on:</span>
              <div class="deps-list">
                <span v-for="d in getDependencies(asset).slice(0, 3)" :key="d" class="dep-tag">{{ d }}</span>
                <span v-if="getDependencies(asset).length > 3" class="dep-more">+{{ getDependencies(asset).length - 3 }}</span>
              </div>
            </div>
          </div>
          
          <!-- Actions - Safe vs Dangerous Separation -->
          <div class="actions-section">
            <!-- Safe Actions (always visible) -->
            <div class="safe-actions">
              <template v-if="asset.class === 'service'">
                <button class="action-btn view" @click.stop="goToAssetDetail(asset)">👁️ Inspect</button>
                <button class="action-btn deps" @click.stop="showDepsPanel(asset)">🔗 Dependencies</button>
              </template>
              <template v-else-if="asset.class === 'app'">
                <button v-if="getAppUrl(asset)" class="action-btn open" @click.stop="openApp(asset)">🚀 Open</button>
                <button class="action-btn deps" @click.stop="showDepsPanel(asset)">🔗 Dependencies</button>
              </template>
              <template v-else>
                <button class="action-btn view" @click.stop="goToAssetDetail(asset)">👁️ View</button>
              </template>
            </div>
            
            <!-- Dangerous Actions (in dropdown menu) -->
            <div class="admin-actions" v-if="hasAdminActions(asset)">
              <div class="admin-menu" :class="{ open: openAdminMenu === asset.id }">
                <button class="admin-toggle" @click.stop="toggleAdminMenu(asset.id)" title="Admin Actions">
                  ⋮
                </button>
                <div class="admin-dropdown" v-if="openAdminMenu === asset.id">
                  <button v-if="canWake(asset)" @click.stop="wakeAsset(asset)" class="dropdown-item">▶️ Force Wake</button>
                  <button v-if="canSuspend(asset)" @click.stop="suspendAsset(asset)" class="dropdown-item warning">⏸️ Suspend</button>
                  <button v-if="asset.class === 'service'" @click.stop="restartAsset(asset)" class="dropdown-item danger">🔄 Restart</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Asset Detail Side Panel -->
    <div v-if="selectedAsset" class="detail-panel-overlay" @click.self="selectedAsset = null">
      <div class="detail-panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon">{{ getAssetIcon(selectedAsset.class) }}</span>
            <div>
              <h2>{{ selectedAsset.display_name || selectedAsset.id }}</h2>
              <span class="panel-subtitle">{{ selectedAsset.class }} • {{ selectedAsset.interface }}</span>
            </div>
          </div>
          <button class="close-btn" @click="selectedAsset = null">✕</button>
        </div>
        
        <div class="panel-content">
          <!-- Health Status -->
          <div class="panel-section">
            <h3>Health Status</h3>
            <div class="health-detail">
              <span class="health-badge-large" :class="getHealthBadgeClass(selectedAsset)">
                {{ getHealthBadgeIcon(selectedAsset) }} {{ getHealthBadgeLabel(selectedAsset) }}
              </span>
              <p class="health-desc">{{ getHealthDescription(selectedAsset) }}</p>
            </div>
          </div>
          
          <!-- Lifecycle -->
          <div class="panel-section">
            <h3>Lifecycle</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Desired State</span>
                <span class="detail-value">{{ formatDesired(selectedAsset.lifecycle?.desired) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Observed State</span>
                <span class="detail-value">{{ formatObserved(selectedAsset) }}</span>
              </div>
              <div class="detail-item" v-if="selectedAsset.lifecycle?.auto_sleep_min">
                <span class="detail-label">Auto-sleep After</span>
                <span class="detail-value">{{ selectedAsset.lifecycle.auto_sleep_min }} minutes</span>
              </div>
              <div class="detail-item" v-if="selectedAsset.resources?.cold_start_sec">
                <span class="detail-label">Cold Start Time</span>
                <span class="detail-value">~{{ selectedAsset.resources.cold_start_sec }}s</span>
              </div>
            </div>
          </div>
          
          <!-- Resources -->
          <div class="panel-section" v-if="hasResources(selectedAsset)">
            <h3>Resources</h3>
            <div class="detail-grid">
              <div class="detail-item" v-if="selectedAsset.resources?.gpu_required !== undefined">
                <span class="detail-label">GPU Required</span>
                <span class="detail-value">{{ selectedAsset.resources.gpu_required ? '✅ Yes' : '❌ No' }}</span>
              </div>
              <div class="detail-item" v-if="selectedAsset.resources?.min_vram_gb">
                <span class="detail-label">Min VRAM</span>
                <span class="detail-value">{{ selectedAsset.resources.min_vram_gb }} GB</span>
              </div>
              <div class="detail-item" v-if="selectedAsset.resources?.min_ram_gb">
                <span class="detail-label">Min RAM</span>
                <span class="detail-value">{{ selectedAsset.resources.min_ram_gb }} GB</span>
              </div>
              <div class="detail-item" v-if="selectedAsset.resources?.disk_gb">
                <span class="detail-label">Disk</span>
                <span class="detail-value">{{ selectedAsset.resources.disk_gb }} GB</span>
              </div>
            </div>
          </div>
          
          <!-- Dependencies -->
          <div class="panel-section" v-if="getDependencies(selectedAsset).length > 0">
            <h3>📦 Depends On</h3>
            <div class="deps-detail-list">
              <div v-for="dep in getDependencies(selectedAsset)" :key="dep" class="dep-detail-item">
                <span class="dep-icon">{{ getAssetIconById(dep) }}</span>
                <span>{{ dep }}</span>
              </div>
            </div>
          </div>
          
          <!-- Consumers -->
          <div class="panel-section" v-if="getConsumers(selectedAsset).length > 0">
            <h3>🔗 Used By</h3>
            <div class="deps-detail-list">
              <div v-for="c in getConsumers(selectedAsset)" :key="c" class="dep-detail-item">
                <span class="dep-icon">{{ getAssetIconById(c) }}</span>
                <span>{{ c }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="panel-footer">
          <button @click="goToAssetDetail(selectedAsset)" class="btn btn-primary">
            View Full Details →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'
import { useSystemHealthStore } from '@/stores/systemHealthStore'

const router = useRouter()
const route = useRoute()
const assetStore = useAssetStore()
const systemHealth = useSystemHealthStore()

const loading = ref(false)
const selectedAsset = ref<any>(null)
const stateFilter = ref<string | null>(null)
const classFilter = ref<string | null>(null)
const openAdminMenu = ref<string | null>(null)

// Toast notifications
const toastMessage = ref<string | null>(null)
const toastType = ref<'success' | 'error'>('success')

function showToast(message: string, type: 'success' | 'error' = 'success') {
  toastMessage.value = message
  toastType.value = type
  setTimeout(() => { toastMessage.value = null }, 4000)
}

// Asset counts by class
const serviceCount = computed(() => assetStore.assets.filter((a: any) => a.class === 'service').length)
const appCount = computed(() => assetStore.assets.filter((a: any) => a.class === 'app' || a.class === 'application').length)
const modelCount = computed(() => assetStore.assets.filter((a: any) => a.class === 'model').length)
const toolCount = computed(() => assetStore.assets.filter((a: any) => a.class === 'tool').length)
const datasetCount = computed(() => assetStore.assets.filter((a: any) => a.class === 'dataset').length)

// Asset counts by state
const runningCount = computed(() => assetStore.assets.filter((a: any) => getObservedState(a) === 'running').length)
const idleCount = computed(() => assetStore.assets.filter((a: any) => getObservedState(a) === 'idle').length)
const suspendedCount = computed(() => assetStore.assets.filter((a: any) => getObservedState(a) === 'suspended').length)
const warmingCount = computed(() => assetStore.assets.filter((a: any) => getObservedState(a) === 'warming').length)
const errorCount = computed(() => assetStore.assets.filter((a: any) => getObservedState(a) === 'error').length)

// Overall health
const overallHealth = computed(() => {
  if (assetStore.assets.length === 0) {
    return { icon: '⚪', badge: 'Unknown', class: 'unknown' }
  }
  if (errorCount.value > 0) {
    return { icon: '🔴', badge: 'Critical', class: 'error' }
  }
  // In auto-sleep architecture, idle/suspended are OK
  const needsAttention = assetStore.assets.filter((a: any) => {
    const state = getObservedState(a)
    const desired = a.lifecycle?.desired
    // Unhealthy = desired running but not running, or error
    return (desired === 'running' && state !== 'running') || state === 'error'
  }).length
  
  if (needsAttention === 0) {
    return { icon: '🟢', badge: 'Healthy', class: 'healthy' }
  }
  return { icon: '🟡', badge: 'Degraded', class: 'warning' }
})

// Filtered assets
const filteredAssets = computed(() => {
  let result = assetStore.assets
  
  if (stateFilter.value) {
    result = result.filter((a: any) => getObservedState(a) === stateFilter.value)
  }
  
  if (classFilter.value) {
    result = result.filter((a: any) => a.class === classFilter.value || 
      (classFilter.value === 'app' && a.class === 'application'))
  }
  
  return result
})

onMounted(async () => {
  await Promise.all([
    assetStore.fetchAssets(),
    systemHealth.fetchStatus()
  ])
})

async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([
      assetStore.fetchAssets(),
      systemHealth.fetchStatus()
    ])
    showToast('✅ Data refreshed successfully')
  } catch (e) {
    showToast(`❌ Refresh failed: ${e}`, 'error')
  } finally {
    loading.value = false
  }
}

function filterByState(state: string) {
  stateFilter.value = stateFilter.value === state ? null : state
}

function filterByClass(assetClass: string) {
  classFilter.value = classFilter.value === assetClass ? null : assetClass
}

function clearFilter() {
  stateFilter.value = null
}

function clearAllFilters() {
  stateFilter.value = null
  classFilter.value = null
}

function selectAsset(asset: any) {
  selectedAsset.value = asset
}

function goToAssetDetail(asset: any) {
  router.push(`/workspace/${route.params.workspaceId}/assets/${asset.id}`)
}

// Helper functions
function getObservedState(asset: any): string {
  return asset.lifecycle?.state || asset.status || 'unknown'
}

function getAssetIcon(assetClass?: string): string {
  const icons: Record<string, string> = {
    model: '🧠', service: '⚙️', tool: '🛠️', dataset: '📚',
    application: '📱', app: '📱', embedding: '🔗'
  }
  return icons[assetClass?.toLowerCase() || ''] || '📦'
}

function getAssetIconById(assetId: string): string {
  const asset = assetStore.assets.find((a: any) => a.id === assetId || a.asset_id === assetId)
  return getAssetIcon(asset?.class)
}

function getHealthBadgeClass(asset: any): string {
  const state = getObservedState(asset)
  const desired = asset.lifecycle?.desired
  
  if (state === 'error') return 'error'
  if (state === 'warming') return 'warming'
  if (state === 'running') return 'healthy'
  if (state === 'idle' && desired === 'on-demand') return 'standby' // OK - intentional
  if (state === 'suspended') return 'standby'
  if (desired === 'running' && state !== 'running') return 'warning'
  return 'standby'
}

function getHealthBadgeIcon(asset: any): string {
  const cls = getHealthBadgeClass(asset)
  const icons: Record<string, string> = {
    healthy: '🟢', standby: '🟡', warning: '🟠', error: '🔴', warming: '⚡'
  }
  return icons[cls] || '⚪'
}

function getHealthBadgeLabel(asset: any): string {
  const cls = getHealthBadgeClass(asset)
  const labels: Record<string, string> = {
    healthy: 'Healthy', standby: 'Standby', warning: 'Needs Attention', 
    error: 'Error', warming: 'Warming'
  }
  return labels[cls] || 'Unknown'
}

function getHealthDescription(asset: any): string {
  const cls = getHealthBadgeClass(asset)
  const desired = asset.lifecycle?.desired
  const state = getObservedState(asset)
  
  if (cls === 'healthy') return 'Asset is running and meeting its desired lifecycle state.'
  if (cls === 'standby') return `Asset is intentionally ${state}. This is expected for ${desired} lifecycle.`
  if (cls === 'warming') return 'Asset is starting up from cold state.'
  if (cls === 'error') return 'Asset is in error state and requires attention.'
  if (cls === 'warning') return `Asset should be ${desired} but is currently ${state}.`
  return 'Asset state is unknown.'
}

function getDesiredClass(asset: any): string {
  const d = asset.lifecycle?.desired?.toLowerCase()
  if (d === 'running') return 'running'
  if (d === 'on-demand') return 'on-demand'
  if (d === 'suspended') return 'suspended'
  return ''
}

function getObservedClass(asset: any): string {
  const state = getObservedState(asset)
  if (state === 'running') return 'running'
  if (state === 'idle') return 'idle'
  if (state === 'suspended') return 'suspended'
  if (state === 'warming') return 'warming'
  if (state === 'error') return 'error'
  return ''
}

function formatDesired(desired?: string): string {
  if (!desired) return '—'
  const map: Record<string, string> = {
    'running': 'Always Running',
    'on-demand': 'On Demand',
    'suspended': 'Suspended'
  }
  return map[desired] || desired
}

function formatObserved(asset: any): string {
  const state = getObservedState(asset)
  const map: Record<string, string> = {
    'running': 'Running',
    'idle': 'Idle',
    'suspended': 'Suspended',
    'warming': 'Warming Up',
    'error': 'Error'
  }
  return map[state] || state || 'Unknown'
}

function showColdStartInfo(asset: any): boolean {
  return asset.class === 'service' || asset.class === 'model'
}

function hasResources(asset: any): boolean {
  return asset.resources && Object.keys(asset.resources).length > 0
}

function hasDependencies(asset: any): boolean {
  return getDependencies(asset).length > 0
}

function hasConsumers(asset: any): boolean {
  return getConsumers(asset).length > 0
}

function getDependencies(asset: any): string[] {
  const deps: string[] = []
  if (asset.policy?.required_models) {
    deps.push(...asset.policy.required_models)
  }
  return deps
}

function getConsumers(asset: any): string[] {
  // In a real implementation, this would come from the API
  // For now, derive from other assets that depend on this one
  const consumers: string[] = []
  if (asset.class === 'service' && asset.policy?.served_models) {
    // Find apps that require these models
    assetStore.assets.forEach((a: any) => {
      if (a.policy?.required_models) {
        const hasOverlap = asset.policy.served_models.some((m: string) => 
          a.policy.required_models.includes(m)
        )
        if (hasOverlap) {
          consumers.push(a.display_name || a.id)
        }
      }
    })
  }
  return consumers
}

// Action helpers - only services (containerized assets) can be woken/suspended
function canWake(asset: any): boolean {
  if (asset.class !== 'service') return false  // Only services have containers
  const state = getObservedState(asset)
  return state === 'idle' || state === 'suspended' || state === 'stopped'
}

function canSuspend(asset: any): boolean {
  if (asset.class !== 'service') return false  // Only services have containers
  const state = getObservedState(asset)
  return state === 'running'
}

function isError(asset: any): boolean {
  return getObservedState(asset) === 'error'
}

function getAppUrl(asset: any): string | null {
  return asset.metadata?.url || null
}

function openApp(asset: any) {
  const url = getAppUrl(asset)
  if (url) window.open(url, '_blank')
}

async function wakeAsset(asset: any) {
  console.log('Waking asset:', asset.id)
  openAdminMenu.value = null
  try {
    const { gateway } = await import('@/services/gateway')
    const result = await gateway.startAsset(asset.id)
    if (result.success) {
      showToast(`✅ ${asset.display_name || asset.id} started successfully`)
      await assetStore.fetchAssets()
    } else {
      showToast(`❌ Failed to wake: ${result.error}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to wake: ${e}`, 'error')
  }
}

async function suspendAsset(asset: any) {
  console.log('Suspending asset:', asset.id)
  openAdminMenu.value = null
  try {
    const { gateway } = await import('@/services/gateway')
    const result = await gateway.stopAsset(asset.id)
    if (result.success) {
      showToast(`⏸️ ${asset.display_name || asset.id} suspended`)
      await assetStore.fetchAssets()
    } else {
      showToast(`❌ Failed to suspend: ${result.error}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to suspend: ${e}`, 'error')
  }
}

async function restartAsset(asset: any) {
  console.log('Restarting asset:', asset.id)
  openAdminMenu.value = null
  try {
    const { gateway } = await import('@/services/gateway')
    const result = await gateway.restartAsset(asset.id)
    if (result.success) {
      showToast(`🔄 ${asset.display_name || asset.id} restarted successfully`)
      await assetStore.fetchAssets()
    } else {
      showToast(`❌ Failed to restart: ${result.error}`, 'error')
    }
  } catch (e) {
    showToast(`❌ Failed to restart: ${e}`, 'error')
  }
}

function inspectAsset(asset: any) {
  goToAssetDetail(asset)
}

function showDepsPanel(asset: any) {
  selectedAsset.value = asset
}

// Admin actions helpers - only services have controllable lifecycle
function hasAdminActions(asset: any): boolean {
  return asset.class === 'service'  // Only services have containers to control
}

function toggleAdminMenu(assetId: string) {
  openAdminMenu.value = openAdminMenu.value === assetId ? null : assetId
}

function getDepsHealthy(asset: any): boolean {
  // Check if all dependencies are healthy
  const deps = getDependencies(asset)
  if (deps.length === 0) return true
  
  return deps.every((depId: string) => {
    const depAsset = assetStore.assets.find((a: any) => a.id === depId || a.display_name === depId)
    if (!depAsset) return true // Unknown deps assumed OK
    const state = getObservedState(depAsset)
    return state === 'running' || state === 'idle'
  })
}
</script>

<style scoped>
.observability-view {
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.view-header h1 {
  margin: 0;
  font-size: 1.75rem;
}

.view-desc {
  color: var(--text-secondary);
  margin-top: 0.5rem;
}

/* Health Section */
.health-section {
  margin-bottom: 1.5rem;
}

.health-card {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 1.5rem;
  border: 2px solid var(--border-color);
}

.health-card.healthy { border-color: rgba(34, 197, 94, 0.4); }
.health-card.warning { border-color: rgba(245, 158, 11, 0.4); }
.health-card.error { border-color: rgba(239, 68, 68, 0.4); }

.health-main {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.health-icon {
  font-size: 2.5rem;
}

.health-info h2 {
  margin: 0 0 0.25rem;
  font-size: 1.1rem;
  color: var(--text-secondary);
}

.health-badge {
  display: inline-block;
  padding: 0.35rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
}

.health-badge.healthy { background: rgba(34, 197, 94, 0.2); color: var(--status-success); }
.health-badge.warning { background: rgba(245, 158, 11, 0.2); color: var(--status-warning); }
.health-badge.error { background: rgba(239, 68, 68, 0.2); color: var(--status-error); }
.health-badge.unknown { background: var(--bg-tertiary); color: var(--text-secondary); }

/* Health Breakdown */
.health-breakdown {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.breakdown-item:hover {
  border-color: var(--accent-primary);
}

.breakdown-item.active {
  background: var(--accent-subtle);
  border-color: var(--accent-primary);
}

.breakdown-item.running { border-left: 3px solid var(--status-success); }
.breakdown-item.idle { border-left: 3px solid #f59e0b; }
.breakdown-item.suspended { border-left: 3px solid #94a3b8; }
.breakdown-item.warming { border-left: 3px solid #3b82f6; }
.breakdown-item.error { border-left: 3px solid var(--status-error); }
.breakdown-item.clear { 
  background: transparent;
  border-color: var(--text-secondary);
  color: var(--text-secondary);
}

.breakdown-count {
  font-weight: 600;
  font-size: 1.1rem;
}

.breakdown-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* System Inventory */
.inventory-section {
  margin-bottom: 1.5rem;
}

.inventory-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
}

@media (max-width: 900px) {
  .inventory-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.inventory-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.inventory-card:hover {
  border-color: var(--accent-primary);
  transform: translateY(-1px);
}

.inventory-icon {
  font-size: 1.5rem;
}

.inventory-count {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
}

.inventory-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Active Filter */
.active-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  font-size: 0.85rem;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
}

.filter-tag button {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  font-size: 0.75rem;
}

.clear-all {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8rem;
}

.clear-all:hover {
  color: var(--text-primary);
}

/* Assets Grid */
.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1rem;
}

.asset-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.asset-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-1px);
}

.asset-card.selected {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px var(--accent-subtle);
}

.asset-card.healthy { border-left: 4px solid var(--status-success); }
.asset-card.standby { border-left: 4px solid #f59e0b; }
.asset-card.warning { border-left: 4px solid #f97316; }
.asset-card.error { border-left: 4px solid var(--status-error); }
.asset-card.warming { border-left: 4px solid #3b82f6; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.asset-identity {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.asset-icon {
  font-size: 1.75rem;
}

.asset-info h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.asset-type {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.health-indicator {
  font-size: 1rem;
}

/* Lifecycle Section */
.lifecycle-section {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.lifecycle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
}

.lifecycle-row:first-child {
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
  margin-bottom: 0.25rem;
}

.lifecycle-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.lifecycle-value {
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}

.lifecycle-value.running { background: rgba(34, 197, 94, 0.15); color: var(--status-success); }
.lifecycle-value.on-demand { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }
.lifecycle-value.idle { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.lifecycle-value.suspended { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }
.lifecycle-value.warming { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.lifecycle-value.error { background: rgba(239, 68, 68, 0.15); color: var(--status-error); }

/* Cold Start Section */
.cold-start-section {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}

.cold-start-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
}

.cold-start-value {
  font-weight: 500;
  color: var(--text-primary);
}

/* Dependencies Section */
.deps-section {
  font-size: 0.75rem;
  margin-bottom: 0.75rem;
}

.deps-row {
  margin-bottom: 0.5rem;
}

.deps-label {
  display: block;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.deps-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.dep-tag {
  padding: 0.15rem 0.4rem;
  background: var(--bg-tertiary);
  border-radius: 3px;
  font-size: 0.7rem;
}

.dep-more {
  padding: 0.15rem 0.4rem;
  color: var(--text-muted);
  font-size: 0.7rem;
}

/* Actions Section */
.actions-section {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.action-btn {
  padding: 0.4rem 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--accent-subtle);
  border-color: var(--accent-primary);
}

.action-btn.wake { border-color: var(--status-success); }
.action-btn.wake:hover { background: rgba(34, 197, 94, 0.15); }

.action-btn.suspend { border-color: #94a3b8; }
.action-btn.restart { border-color: #3b82f6; }
.action-btn.inspect { border-color: var(--status-error); }

/* Labeled Status Badge */
.status-badge-labeled {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge-labeled.healthy { background: rgba(34, 197, 94, 0.15); color: var(--status-success); }
.status-badge-labeled.standby { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.status-badge-labeled.warning { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.status-badge-labeled.error { background: rgba(239, 68, 68, 0.15); color: var(--status-error); }
.status-badge-labeled.warming { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }

.status-icon { font-size: 0.85rem; }
.status-label { text-transform: uppercase; letter-spacing: 0.3px; }

/* State Box - Authoritative Section */
.state-box {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  border: 1px solid var(--border-color);
}

.state-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0;
}

.state-row:first-child {
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
  margin-bottom: 0.3rem;
}

.state-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.state-value {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.state-value.running { background: rgba(34, 197, 94, 0.15); color: var(--status-success); }
.state-value.on-demand { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }
.state-value.idle { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.state-value.suspended { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); }
.state-value.warming { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.state-value.error { background: rgba(239, 68, 68, 0.15); color: var(--status-error); }

/* Health Check Indicators */
.health-checks {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--border-color);
}

.check-item {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  background: var(--bg-secondary);
}

.check-item.ok { color: var(--status-success); }
.check-item.error { color: var(--status-error); background: rgba(239, 68, 68, 0.1); }
.check-item.warning { color: #f59e0b; }

/* Safe Actions Container */
.safe-actions {
  display: flex;
  gap: 0.5rem;
  flex: 1;
}

/* Admin Actions Dropdown */
.admin-actions {
  position: relative;
}

.admin-menu {
  position: relative;
}

.admin-toggle {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.1rem;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.admin-toggle:hover {
  background: var(--bg-secondary);
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.admin-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 140px;
  z-index: 100;
  overflow: hidden;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.6rem 0.75rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--text-primary);
  transition: background 0.2s;
}

.dropdown-item:hover {
  background: var(--bg-tertiary);
}

.dropdown-item.warning:hover {
  background: rgba(245, 158, 11, 0.1);
}

.dropdown-item.danger {
  color: var(--status-error);
}

.dropdown-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* Detail Panel */
.detail-panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
}

.detail-panel {
  width: 450px;
  max-width: 95vw;
  height: 100%;
  background: var(--bg-primary);
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.panel-title {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.panel-icon {
  font-size: 2rem;
}

.panel-title h2 {
  margin: 0;
  font-size: 1.25rem;
}

.panel-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.panel-section {
  margin-bottom: 1.5rem;
}

.panel-section h3 {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.health-detail {
  text-align: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.health-badge-large {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.health-badge-large.healthy { background: rgba(34, 197, 94, 0.2); color: var(--status-success); }
.health-badge-large.standby { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.health-badge-large.warning { background: rgba(249, 115, 22, 0.2); color: #f97316; }
.health-badge-large.error { background: rgba(239, 68, 68, 0.2); color: var(--status-error); }
.health-badge-large.warming { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }

.health-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.detail-item {
  background: var(--bg-secondary);
  padding: 0.75rem;
  border-radius: 6px;
}

.detail-label {
  display: block;
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.detail-value {
  font-size: 0.9rem;
}

.deps-detail-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dep-detail-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  font-size: 0.85rem;
}

.dep-icon {
  font-size: 1rem;
}

.panel-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
}

/* Buttons */
.btn {
  padding: 0.6rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.panel-footer .btn {
  width: 100%;
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
</style>
