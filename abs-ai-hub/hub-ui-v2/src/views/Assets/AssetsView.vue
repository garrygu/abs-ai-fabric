<template>
  <div class="assets-view">
    <header class="view-header">
      <div class="header-content">
        <h1>📦 Assets</h1>
        <p class="view-desc">Manage models, services, and resources in your workspace.</p>
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
            <th>Status</th>
            <th>Consumers</th>
            <th>GPU</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="asset in assetStore.filteredAssets" 
            :key="asset.id"
            class="asset-row"
            @click="goToAsset(asset.id)"
          >
            <td class="asset-name">
              <span class="asset-icon">{{ getAssetIcon(asset.class) }}</span>
              {{ asset.display_name || asset.id }}
            </td>
            <td>{{ asset.class || '-' }}</td>
            <td><span class="badge">{{ asset.interface || '-' }}</span></td>
            <td>
              <span class="status-dot" :class="getStatusClass(asset.status)">●</span>
              {{ capitalize(asset.status || 'Unknown') }}
            </td>
            <td>{{ asset.consumers?.length || 0 }}</td>
            <td>{{ asset.usage?.gpu ? '✅' : 'No' }}</td>
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
          <span class="status-badge" :class="getStatusClass(asset.status)">
            {{ capitalize(asset.status || 'Unknown') }}
          </span>
        </div>
        <h3 class="asset-title">{{ asset.display_name || asset.id }}</h3>
        <div class="asset-meta">
          <span class="meta-badge type">{{ asset.class || 'unknown' }}</span>
          <span class="meta-badge interface">{{ asset.interface || '-' }}</span>
        </div>
        <div class="asset-stats">
          <div class="stat">
            <span class="stat-label">Consumers</span>
            <span class="stat-value">{{ asset.consumers?.length || 0 }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">GPU</span>
            <span class="stat-value">{{ asset.usage?.gpu ? '✅' : '—' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Count -->
    <div v-if="!assetStore.loading && assetStore.filteredAssets.length > 0" class="results-footer">
      Showing {{ assetStore.filteredAssets.length }} of {{ assetStore.assets.length }} assets
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'

const router = useRouter()
const route = useRoute()
const assetStore = useAssetStore()

const searchInput = ref('')

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
  if (s === 'ready' || s === 'running' || s === 'online') return 'ready'
  if (s === 'stopped' || s === 'offline') return 'stopped'
  if (s === 'error') return 'error'
  return 'unknown'
}

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

function formatTypeName(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1) + 's'
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
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.assets-table th {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.asset-row {
  cursor: pointer;
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

.status-dot {
  margin-right: 0.5rem;
}
.status-dot.ready { color: var(--status-success); }
.status-dot.stopped { color: var(--status-warning); }
.status-dot.error { color: var(--status-error); }
.status-dot.unknown { color: var(--text-secondary); }

/* Grid View */
.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
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
  margin-bottom: 1rem;
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
