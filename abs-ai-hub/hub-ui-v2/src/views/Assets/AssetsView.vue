<template>
  <div class="assets-view">
    <header class="view-header">
      <div class="header-content">
        <h1>📦 Assets</h1>
        <p class="view-desc">Manage and observe all AI assets in your workspace — apps, models, services, tools, and datasets.</p>
      </div>
    </header>

    <!-- Controls Bar -->
    <div class="controls-bar">
      <!-- Search -->
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          type="text" 
          v-model="searchInput"
          @input="debouncedSearch"
          placeholder="Search by name, type, or interface..."
          class="search-input"
        />
        <button v-if="searchInput" @click="clearSearch" class="clear-btn">✕</button>
      </div>

      <!-- View Toggle -->
      <div class="view-toggle">
        <button 
          class="toggle-btn" 
          :class="{ active: assetStore.viewMode === 'table' }"
          @click="assetStore.setViewMode('table')"
          title="Table View"
        >
          ☰
        </button>
        <button 
          class="toggle-btn"
          :class="{ active: assetStore.viewMode === 'grid' }"
          @click="assetStore.setViewMode('grid')"
          title="Grid View"
        >
          ⊞
        </button>
      </div>
    </div>

    <!-- Type Tabs -->
    <div class="type-tabs">
      <button 
        class="type-tab" 
        :class="{ active: assetStore.activeTypeFilter === null }"
        @click="assetStore.setTypeFilter(null)"
      >
        All
        <span class="count">{{ assetStore.assetCounts.all }}</span>
      </button>
      <button 
        v-for="type in assetStore.assetTypes" 
        :key="type"
        class="type-tab"
        :class="{ active: assetStore.activeTypeFilter === type }"
        @click="assetStore.setTypeFilter(type)"
      >
        {{ formatTypeName(type) }}
        <span class="count">{{ assetStore.assetCounts[type] || 0 }}</span>
      </button>
      
      <!-- Advanced Filters Toggle -->
      <button 
        class="advanced-filter-toggle" 
        :class="{ active: showAdvancedFilters }"
        @click="showAdvancedFilters = !showAdvancedFilters"
      >
        ⚙️ Filters
        <span v-if="activeFilterCount > 0" class="filter-count">{{ activeFilterCount }}</span>
      </button>
    </div>
    
    <!-- Advanced Filters Panel -->
    <div v-if="showAdvancedFilters" class="advanced-filters">
      <div class="filter-row">
        <!-- Interface Filter -->
        <div class="filter-group">
          <label>Interface</label>
          <select v-model="filters.interface">
            <option value="">All Interfaces</option>
            <option v-for="iface in uniqueInterfaces" :key="iface" :value="iface">{{ iface }}</option>
          </select>
        </div>
        
        <!-- Desired State Filter -->
        <div class="filter-group">
          <label>Desired State</label>
          <select v-model="filters.desired">
            <option value="">All States</option>
            <option value="running">Always Running</option>
            <option value="on-demand">On Demand</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>
        
        <!-- Provider Filter -->
        <div class="filter-group">
          <label>Provider</label>
          <select v-model="filters.provider">
            <option value="">All Providers</option>
            <option v-for="provider in uniqueProviders" :key="provider" :value="provider">{{ provider }}</option>
          </select>
        </div>
        
        <!-- GPU Required Filter -->
        <div class="filter-group">
          <label>GPU Required</label>
          <select v-model="filters.gpu">
            <option value="">Any</option>
            <option value="yes">🔥 GPU Required</option>
            <option value="no">No GPU</option>
          </select>
        </div>
        
        <!-- Pack Filter -->
        <div class="filter-group">
          <label>Pack</label>
          <select v-model="filters.pack">
            <option value="">All Packs</option>
            <option v-for="pack in uniquePacks" :key="pack" :value="pack">{{ pack }}</option>
          </select>
        </div>
        
        <button v-if="activeFilterCount > 0" class="clear-filters-btn" @click="clearAdvancedFilters">
          ✕ Clear
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="assetStore.loading" class="loading-state">
      <span class="spinner">⏳</span> Loading assets...
    </div>

    <!-- Error State -->
    <div v-else-if="assetStore.error" class="error-state">
      <span class="error-icon">❌</span>
      <p>{{ assetStore.error }}</p>
      <button @click="assetStore.fetchAssets()" class="btn btn-primary">Retry</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="assetStore.filteredAssets.length === 0" class="empty-state">
      <p v-if="assetStore.searchQuery || assetStore.activeTypeFilter">
        No assets match your filters.
      </p>
      <p v-else>No assets found in this workspace.</p>
      <button v-if="assetStore.searchQuery || assetStore.activeTypeFilter" 
        @click="clearFilters" 
        class="btn btn-secondary"
      >
        Clear Filters
      </button>
    </div>

    <!-- Table View -->
    <div v-else-if="assetStore.viewMode === 'table'" class="assets-table-container">
      <table class="assets-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Interface</th>
            <th>Desired</th>
            <th>Status / Health</th>
            <th>Resources</th>
            <th>Consumers</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="asset in advancedFilteredAssets" 
            :key="asset.id"
            class="asset-row"
          >
            <td class="asset-name" @click="goToAsset(asset.id)">
              <span class="asset-icon">{{ getAssetIcon(asset.class) }}</span>
              {{ asset.display_name || asset.id }}
            </td>
            <td>{{ asset.class || '-' }}</td>
            <td><span class="badge">{{ asset.interface || '-' }}</span></td>
            <td class="desired-col">
              <span class="desired-badge" :class="getDesiredClass(asset.lifecycle?.desired)">
                {{ formatDesired(asset.lifecycle?.desired) }}
              </span>
            </td>
            <td class="status-health-col">
              <div class="status-health">
                <span class="status-part" :class="getStatusClass(getObservedState(asset))">
                  {{ getStatusIcon(asset) }} {{ capitalize(getObservedState(asset)) }}
                </span>
                <span class="health-divider">/</span>
                <span class="health-part" :class="getHealthClass(asset)">
                  {{ getHealthLabel(asset) }}
                </span>
              </div>
            </td>
            <td class="resources-col">
              <div class="resource-badges">
                <span v-if="asset.resources?.gpu_required" class="resource-badge gpu">
                  🔥 GPU
                </span>
                <span v-if="asset.resources?.min_vram_gb" class="resource-badge vram">
                  {{ asset.resources.min_vram_gb }}GB
                </span>
                <span v-if="!asset.resources?.gpu_required && !asset.resources?.min_vram_gb" class="resource-badge cpu">
                  CPU
                </span>
              </div>
            </td>
            <td>
              <button 
                class="consumers-btn"
                @click.stop="showDependencies(asset)"
                :disabled="!hasConsumers(asset) && !hasDependencies(asset)"
              >
                {{ getConsumerCount(asset) }}
                <span v-if="hasConsumers(asset) || hasDependencies(asset)" class="link-icon">🔗</span>
              </button>
            </td>
            <td class="actions-col" @click.stop>
              <div class="quick-actions">
                <!-- Service/Runtime Actions -->
                <template v-if="asset.class === 'service'">
                  <button 
                    v-if="canStart(asset)"
                    class="action-btn start" 
                    @click="startAsset(asset)"
                    title="Start"
                  >▶️</button>
                  <button 
                    v-if="canSuspend(asset)"
                    class="action-btn suspend" 
                    @click="suspendAsset(asset)"
                    title="Suspend"
                  >⏸️</button>
                  <button 
                    class="action-btn restart" 
                    @click="restartAsset(asset)"
                    title="Restart"
                  >🔄</button>
                </template>
                
                <!-- App Actions -->
                <template v-else-if="asset.class === 'app'">
                  <button 
                    v-if="getAppUrl(asset)"
                    class="action-btn open" 
                    @click="openApp(asset)"
                    title="Open App"
                  >🚀</button>
                  <button 
                    class="action-btn bindings" 
                    @click="showBindings(asset)"
                    title="View Bindings"
                  >🔍</button>
                </template>
                
                <!-- Model Actions -->
                <template v-else-if="asset.class === 'model'">
                  <button 
                    class="action-btn view" 
                    @click="goToAsset(asset.id)"
                    title="View Details"
                  >👁️</button>
                </template>
                
                <!-- Tool Actions -->
                <template v-else-if="asset.class === 'tool'">
                  <button 
                    class="action-btn view" 
                    @click="goToAsset(asset.id)"
                    title="View Details"
                  >👁️</button>
                </template>
                
                <!-- Dataset Actions -->
                <template v-else-if="asset.class === 'dataset'">
                  <button 
                    class="action-btn view" 
                    @click="goToAsset(asset.id)"
                    title="View Usage"
                  >📊</button>
                  <button 
                    class="action-btn consumers" 
                    @click="showDependencies(asset)"
                    title="View Consumers"
                  >🔗</button>
                </template>
                
                <!-- Default -->
                <template v-else>
                  <button 
                    class="action-btn view" 
                    @click="goToAsset(asset.id)"
                    title="View Details"
                  >👁️</button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Grid View -->
    <div v-else class="assets-grid">
      <div 
        v-for="asset in assetStore.filteredAssets" 
        :key="asset.id"
        class="asset-card"
        @click="goToAsset(asset.id)"
      >
        <div class="card-header">
          <span class="asset-icon-large">{{ getAssetIcon(asset.class) }}</span>
          <span class="status-badge" :class="getStatusClass(getObservedState(asset))">
            {{ capitalize(getObservedState(asset)) }}
          </span>
        </div>
        <h3 class="asset-title">{{ asset.display_name || asset.id }}</h3>
        <div class="asset-meta">
          <span class="meta-badge type">{{ asset.class || 'unknown' }}</span>
          <span class="meta-badge interface">{{ asset.interface || '-' }}</span>
        </div>
        
        <!-- Intent vs Reality -->
        <div class="lifecycle-info">
          <div class="lifecycle-row">
            <span class="lifecycle-label">Desired:</span>
            <span class="lifecycle-value desired" :class="getDesiredClass(asset.lifecycle?.desired)">
              {{ formatDesired(asset.lifecycle?.desired) }}
            </span>
          </div>
        </div>
        
        <div class="asset-stats">
          <div class="stat">
            <span class="stat-label">Consumers</span>
            <span 
              class="stat-value clickable" 
              @click.stop="showDependencies(asset)"
              :class="{ 'has-deps': hasConsumers(asset) || hasDependencies(asset) }"
            >
              {{ getConsumerCount(asset) }}
              <span v-if="hasConsumers(asset) || hasDependencies(asset)">🔗</span>
            </span>
          </div>
          <div class="stat">
            <span class="stat-label">GPU</span>
            <span class="stat-value">{{ asset.resources?.gpu_required ? '✅' : '—' }}</span>
          </div>
        </div>
        
        <!-- Quick Actions for Grid -->
        <div class="card-actions" @click.stop>
          <template v-if="asset.class === 'service'">
            <button v-if="canStart(asset)" class="card-action-btn" @click="startAsset(asset)">▶️ Start</button>
            <button v-if="canSuspend(asset)" class="card-action-btn" @click="suspendAsset(asset)">⏸️ Suspend</button>
          </template>
          <template v-else-if="asset.class === 'app' && getAppUrl(asset)">
            <button class="card-action-btn primary" @click="openApp(asset)">🚀 Open</button>
          </template>
        </div>
      </div>
    </div>

    <!-- Results Count -->
    <div v-if="!assetStore.loading && assetStore.filteredAssets.length > 0" class="results-footer">
      Showing {{ assetStore.filteredAssets.length }} of {{ assetStore.assets.length }} assets
    </div>
    
    <!-- Dependencies Side Panel -->
    <div v-if="showDepsPanel" class="deps-panel-overlay" @click="closeDepsPanel">
      <div class="deps-panel" @click.stop>
        <div class="deps-header">
          <h3>{{ selectedAsset?.display_name || selectedAsset?.id }}</h3>
          <button class="close-btn" @click="closeDepsPanel">✕</button>
        </div>
        <div class="deps-content">
          <div class="deps-section">
            <h4>🔗 Used By</h4>
            <ul v-if="selectedAssetConsumers.length > 0">
              <li v-for="consumer in selectedAssetConsumers" :key="consumer">
                <span class="dep-icon">{{ getAssetIcon(getAssetClass(consumer)) }}</span>
                {{ consumer }}
              </li>
            </ul>
            <p v-else class="no-deps">No consumers</p>
          </div>
          <div class="deps-section">
            <h4>📦 Depends On</h4>
            <ul v-if="selectedAssetDependencies.length > 0">
              <li v-for="dep in selectedAssetDependencies" :key="dep">
                <span class="dep-icon">{{ getAssetIcon(getAssetClass(dep)) }}</span>
                {{ dep }}
              </li>
            </ul>
            <p v-else class="no-deps">No dependencies</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'

const router = useRouter()
const route = useRoute()
const assetStore = useAssetStore()

const searchInput = ref('')
const showDepsPanel = ref(false)
const selectedAsset = ref<any>(null)

// V2 Advanced Filters
const showAdvancedFilters = ref(false)
const filters = ref({
  interface: '',
  desired: '',
  provider: '',
  gpu: '',
  pack: ''
})

// Computed: Unique filter options from assets
const uniqueInterfaces = computed(() => {
  const interfaces = assetStore.assets.map((a: any) => a.interface).filter(Boolean)
  return [...new Set(interfaces)].sort()
})

const uniqueProviders = computed(() => {
  const providers = assetStore.assets.map((a: any) => a.ownership?.provider).filter(Boolean)
  return [...new Set(providers)].sort()
})

const uniquePacks = computed(() => {
  const packs = assetStore.assets.map((a: any) => a.pack_id).filter(Boolean)
  return [...new Set(packs)].sort()
})

// Count of active advanced filters
const activeFilterCount = computed(() => {
  return Object.values(filters.value).filter(v => v !== '').length
})

// Apply advanced filters on top of store's filtered assets
const advancedFilteredAssets = computed(() => {
  let result = assetStore.filteredAssets
  
  if (filters.value.interface) {
    result = result.filter((a: any) => a.interface === filters.value.interface)
  }
  if (filters.value.desired) {
    result = result.filter((a: any) => a.lifecycle?.desired === filters.value.desired)
  }
  if (filters.value.provider) {
    result = result.filter((a: any) => a.ownership?.provider === filters.value.provider)
  }
  if (filters.value.gpu === 'yes') {
    result = result.filter((a: any) => a.resources?.gpu_required === true)
  } else if (filters.value.gpu === 'no') {
    result = result.filter((a: any) => !a.resources?.gpu_required)
  }
  if (filters.value.pack) {
    result = result.filter((a: any) => a.pack_id === filters.value.pack)
  }
  
  return result
})

function clearAdvancedFilters() {
  filters.value = { interface: '', desired: '', provider: '', gpu: '', pack: '' }
}

// Health vs Status helpers (V2 enhancement 4.5)
function getStatusIcon(asset: any): string {
  const state = getObservedState(asset)
  const icons: Record<string, string> = {
    running: '🟢', idle: '🟡', suspended: '⏸️', warming: '⚡', error: '🔴'
  }
  return icons[state] || '⚪'
}

function getHealthClass(asset: any): string {
  // Health is separate from status - based on heartbeat/readiness
  // For now, derive from observed state vs desired
  const state = getObservedState(asset)
  const desired = asset.lifecycle?.desired
  
  if (state === 'error') return 'unhealthy'
  if (state === 'running') return 'healthy'
  if (state === 'warming') return 'degraded'
  if (desired === 'running' && state !== 'running') return 'degraded'
  return 'healthy' // idle/suspended when on-demand = healthy
}

function getHealthLabel(asset: any): string {
  const healthClass = getHealthClass(asset)
  const labels: Record<string, string> = {
    healthy: 'Healthy',
    degraded: 'Degraded', 
    unhealthy: 'Unhealthy'
  }
  return labels[healthClass] || 'Unknown'
}
// Computed properties for dependency panel
const selectedAssetConsumers = computed(() => {
  if (!selectedAsset.value) return []
  // In a real implementation, this would come from the API
  // For now, derive from policy
  return []
})

const selectedAssetDependencies = computed(() => {
  if (!selectedAsset.value) return []
  const deps: string[] = []
  const policy = selectedAsset.value.policy || {}
  
  // Apps depend on required_models
  if (policy.required_models) {
    deps.push(...policy.required_models)
  }
  // Services serve models
  if (policy.served_models) {
    deps.push(...policy.served_models.map((m: string) => `model:${m}`))
  }
  return deps
})

// Debounced search
let searchTimeout: ReturnType<typeof setTimeout> | null = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    assetStore.setSearchQuery(searchInput.value)
  }, 300)
}

function clearSearch() {
  searchInput.value = ''
  assetStore.setSearchQuery('')
}

function clearFilters() {
  searchInput.value = ''
  assetStore.setSearchQuery('')
  assetStore.setTypeFilter(null)
}

// Sync search input with store on mount
watch(() => assetStore.searchQuery, (val) => {
  if (searchInput.value !== val) {
    searchInput.value = val
  }
})

onMounted(() => {
  assetStore.fetchAssets()
})

function goToAsset(id: string) {
  router.push(`/workspace/${route.params.workspaceId}/assets/${id}`)
}

function getAssetIcon(assetClass?: string): string {
  const icons: Record<string, string> = {
    model: '🧠',
    service: '⚙️',
    tool: '🛠️',
    dataset: '📚',
    application: '📱',
    app: '📱',
    embedding: '🔗'
  }
  return icons[assetClass?.toLowerCase() || ''] || '📦'
}

function getStatusClass(status?: string): string {
  if (!status) return 'unknown'
  const s = status.toLowerCase()
  if (s === 'ready' || s === 'running' || s === 'online' || s === 'idle') return 'ready'
  if (s === 'stopped' || s === 'offline' || s === 'suspended') return 'stopped'
  if (s === 'warming') return 'warming'
  if (s === 'error') return 'error'
  return 'unknown'
}

function getDesiredClass(desired?: string): string {
  if (!desired) return 'unknown'
  const d = desired.toLowerCase()
  if (d === 'running') return 'running'
  if (d === 'on-demand') return 'on-demand'
  if (d === 'suspended') return 'suspended'
  return 'unknown'
}

function formatDesired(desired?: string): string {
  if (!desired) return '—'
  return desired.charAt(0).toUpperCase() + desired.slice(1).replace('-', ' ')
}

function getObservedState(asset: any): string {
  // Priority: lifecycle.state > status > derive from desired
  return asset.lifecycle?.state || asset.status || 'unknown'
}

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

function formatTypeName(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1) + 's'
}

// Consumer/Dependency helpers
function getConsumerCount(asset: any): number {
  return asset.consumers?.length || 0
}

function hasConsumers(asset: any): boolean {
  return (asset.consumers?.length || 0) > 0
}

function hasDependencies(asset: any): boolean {
  const policy = asset.policy || {}
  return (policy.required_models?.length || 0) > 0 || (policy.served_models?.length || 0) > 0
}

function showDependencies(asset: any) {
  selectedAsset.value = asset
  showDepsPanel.value = true
}

function closeDepsPanel() {
  showDepsPanel.value = false
  selectedAsset.value = null
}

function getAssetClass(assetId: string): string {
  const asset = assetStore.assets.find((a: any) => a.id === assetId || a.asset_id === assetId)
  return asset?.class || 'unknown'
}

// Action helpers
function canStart(asset: any): boolean {
  const state = getObservedState(asset)
  const desired = asset.lifecycle?.desired
  return (state === 'idle' || state === 'suspended' || state === 'stopped') && desired === 'running'
}

function canSuspend(asset: any): boolean {
  const state = getObservedState(asset)
  const desired = asset.lifecycle?.desired
  return state === 'running' && desired === 'on-demand'
}

function getAppUrl(asset: any): string | null {
  return asset.metadata?.url || null
}

function openApp(asset: any) {
  const url = getAppUrl(asset)
  if (url) {
    window.open(url, '_blank')
  }
}

function startAsset(asset: any) {
  console.log('Starting asset:', asset.id)
  // TODO: Call Gateway API to start asset
}

function suspendAsset(asset: any) {
  console.log('Suspending asset:', asset.id)
  // TODO: Call Gateway API to suspend asset
}

function restartAsset(asset: any) {
  console.log('Restarting asset:', asset.id)
  // TODO: Call Gateway API to restart asset
}

function showBindings(asset: any) {
  // Navigate to asset detail with bindings tab
  router.push(`/workspace/${route.params.workspaceId}/assets/${asset.id}?tab=bindings`)
}
</script>

<style scoped>
.assets-view {
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

/* Controls Bar */
.controls-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  align-items: center;
}

.search-box {
  flex: 1;
  max-width: 400px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 0.9rem;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.6rem 2rem 0.6rem 2.25rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.clear-btn {
  position: absolute;
  right: 0.5rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
}

.view-toggle {
  display: flex;
  background: var(--bg-secondary);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.toggle-btn {
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.toggle-btn:hover {
  color: var(--text-primary);
}

.toggle-btn.active {
  background: var(--accent-primary);
  color: #fff;
}

/* Type Tabs */
.type-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.type-tab {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.type-tab:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.type-tab.active {
  background: var(--accent-subtle);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.type-tab .count {
  padding: 0.125rem 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 10px;
  font-size: 0.75rem;
}

.type-tab.active .count {
  background: var(--accent-subtle);
}

/* Advanced Filters Toggle */
.advanced-filter-toggle {
  margin-left: auto;
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.advanced-filter-toggle:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.advanced-filter-toggle.active {
  background: var(--accent-subtle);
  border-style: solid;
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.filter-count {
  background: var(--accent-primary);
  color: white;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Advanced Filters Panel */
.advanced-filters {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.filter-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 140px;
}

.filter-group label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-group select {
  padding: 0.5rem 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 0.85rem;
  cursor: pointer;
}

.filter-group select:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.clear-filters-btn {
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
  align-self: flex-end;
}

.clear-filters-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: var(--status-error);
  color: var(--status-error);
}

/* Status / Health Column */
.status-health-col {
  white-space: nowrap;
}

.status-health {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
}

.status-part {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.status-part.ready { color: var(--status-success); }
.status-part.stopped { color: var(--status-warning); }
.status-part.warming { color: #3b82f6; }
.status-part.error { color: var(--status-error); }

.health-divider {
  color: var(--text-muted);
}

.health-part {
  font-size: 0.8rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
}

.health-part.healthy { 
  color: var(--status-success); 
  background: rgba(34, 197, 94, 0.1);
}
.health-part.degraded { 
  color: #f59e0b; 
  background: rgba(245, 158, 11, 0.1);
}
.health-part.unhealthy { 
  color: var(--status-error); 
  background: rgba(239, 68, 68, 0.1);
}

/* Resources Column */
.resources-col {
  white-space: nowrap;
}

.resource-badges {
  display: flex;
  gap: 0.35rem;
}

.resource-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
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

.resource-badge.cpu {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

/* Table View */
.assets-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-secondary);
  border-radius: 12px;
  overflow: hidden;
}

.assets-table th,
.assets-table td {
  padding: 0.875rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.assets-table th {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.asset-row {
  transition: background 0.2s;
}

.asset-row:hover {
  background: var(--bg-tertiary);
}

.asset-name {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
  cursor: pointer;
}

.asset-icon {
  font-size: 1.25rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.8rem;
}

/* Desired Column */
.desired-col {
  font-size: 0.85rem;
}

.desired-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.desired-badge.running {
  background: rgba(34, 197, 94, 0.15);
  color: var(--status-success);
}

.desired-badge.on-demand {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text-secondary);
}

.desired-badge.suspended {
  background: rgba(245, 158, 11, 0.15);
  color: var(--status-warning);
}

/* Status */
.status-dot {
  margin-right: 0.5rem;
}
.status-dot.ready { color: var(--status-success); }
.status-dot.stopped { color: var(--status-warning); }
.status-dot.warming { color: #3b82f6; }
.status-dot.error { color: var(--status-error); }
.status-dot.unknown { color: var(--text-secondary); }

/* Consumers Button */
.consumers-btn {
  background: none;
  border: 1px solid transparent;
  color: var(--text-primary);
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.consumers-btn:not(:disabled):hover {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
}

.consumers-btn:disabled {
  cursor: default;
  color: var(--text-muted);
}

.link-icon {
  margin-left: 0.25rem;
  font-size: 0.75rem;
}

/* Actions Column */
.actions-col {
  width: 120px;
}

.quick-actions {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--accent-subtle);
  border-color: var(--accent-primary);
}

/* Grid View */
.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.25rem;
}

.asset-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}

.asset-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-hover);
}

.asset-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.asset-icon-large {
  font-size: 2rem;
}

.status-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-badge.ready {
  background: rgba(34, 197, 94, 0.2);
  color: var(--status-success);
}
.status-badge.stopped {
  background: rgba(245, 158, 11, 0.2);
  color: var(--status-warning);
}
.status-badge.warming {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}
.status-badge.error {
  background: rgba(239, 68, 68, 0.2);
  color: var(--status-error);
}
.status-badge.unknown {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.asset-title {
  margin: 0 0 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asset-meta {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.meta-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.meta-badge.type {
  background: var(--accent-subtle);
  color: var(--accent-primary);
}

.meta-badge.interface {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

/* Lifecycle Info */
.lifecycle-info {
  padding: 0.5rem 0;
  margin-bottom: 0.5rem;
  border-top: 1px solid var(--border-color);
}

.lifecycle-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.lifecycle-label {
  color: var(--text-muted);
}

.lifecycle-value {
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-size: 0.75rem;
}

.lifecycle-value.desired.running {
  background: rgba(34, 197, 94, 0.15);
  color: var(--status-success);
}

.lifecycle-value.desired.on-demand {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text-secondary);
}

.lifecycle-value.desired.suspended {
  background: rgba(245, 158, 11, 0.15);
  color: var(--status-warning);
}

.asset-stats {
  display: flex;
  gap: 1.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.stat-value {
  font-size: 0.9rem;
  font-weight: 500;
}

.stat-value.clickable {
  cursor: pointer;
}

.stat-value.has-deps:hover {
  color: var(--accent-primary);
}

/* Card Actions */
.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.card-action-btn {
  flex: 1;
  padding: 0.4rem 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.card-action-btn:hover {
  background: var(--accent-subtle);
  border-color: var(--accent-primary);
}

.card-action-btn.primary {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: white;
}

.card-action-btn.primary:hover {
  opacity: 0.9;
}

/* Dependencies Panel */
.deps-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
}

.deps-panel {
  width: 400px;
  max-width: 90vw;
  background: var(--bg-primary);
  height: 100%;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.deps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.deps-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0.25rem;
}

.close-btn:hover {
  color: var(--text-primary);
}

.deps-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.deps-section {
  margin-bottom: 1.5rem;
}

.deps-section h4 {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.deps-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.deps-section li {
  padding: 0.5rem 0.75rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.dep-icon {
  font-size: 1rem;
}

.no-deps {
  color: var(--text-muted);
  font-style: italic;
  font-size: 0.9rem;
}

/* States */
.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}

.error-state {
  color: var(--status-error);
}

.results-footer {
  margin-top: 1rem;
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn:hover {
  opacity: 0.9;
}
</style>
