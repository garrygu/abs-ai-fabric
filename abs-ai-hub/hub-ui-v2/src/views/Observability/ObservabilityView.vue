<template>
  <div class="observability-view">
    <header class="view-header">
      <div class="header-content">
        <h1>📊 Observability</h1>
        <p class="view-desc">Monitor system health, services, and resource usage.</p>
      </div>
      <button @click="refreshAll" class="btn btn-primary" :disabled="loading">
        🔄 {{ loading ? 'Refreshing...' : 'Refresh All' }}
      </button>
    </header>

    <!-- Overview Cards -->
    <section class="overview-section">
      <div class="overview-grid">
        <!-- System Health -->
        <div class="overview-card health-card" :class="overallHealth.class">
          <div class="card-icon">{{ overallHealth.icon }}</div>
          <div class="card-content">
            <h3>System Health</h3>
            <p class="status-text">{{ overallHealth.text }}</p>
            <span class="status-badge" :class="overallHealth.class">{{ overallHealth.badge }}</span>
          </div>
        </div>

        <!-- Assets Summary -->
        <div class="overview-card">
          <div class="card-icon">📦</div>
          <div class="card-content">
            <h3>Assets</h3>
            <div class="stats-row">
              <div class="stat">
                <span class="stat-value">{{ assetStore.assets.length }}</span>
                <span class="stat-label">Total</span>
              </div>
              <div class="stat healthy">
                <span class="stat-value">{{ healthyCount }}</span>
                <span class="stat-label">Healthy</span>
              </div>
              <div class="stat warning" v-if="warningCount > 0">
                <span class="stat-value">{{ warningCount }}</span>
                <span class="stat-label">Warning</span>
              </div>
              <div class="stat error" v-if="errorCount > 0">
                <span class="stat-value">{{ errorCount }}</span>
                <span class="stat-label">Error</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="overview-card">
          <div class="card-icon">⚡</div>
          <div class="card-content">
            <h3>Quick Stats</h3>
            <div class="stats-row">
              <div class="stat">
                <span class="stat-value">{{ modelCount }}</span>
                <span class="stat-label">Models</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ serviceCount }}</span>
                <span class="stat-label">Services</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ appCount }}</span>
                <span class="stat-label">Apps</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Asset Type Sections -->
    <section class="type-sections">
      <!-- Models Section -->
      <div class="type-section" v-if="models.length > 0">
        <div class="section-header" @click="toggleSection('models')">
          <h2>🧠 Models <span class="count">({{ models.length }})</span></h2>
          <span class="toggle-icon">{{ expandedSections.models ? '▼' : '▶' }}</span>
        </div>
        <div v-show="expandedSections.models" class="section-content">
          <div class="asset-metrics-grid">
            <div 
              v-for="asset in models" 
              :key="asset.id" 
              class="asset-metric-card"
              :class="getStatusClass(asset.status)"
              @click="selectAsset(asset)"
            >
              <div class="metric-header">
                <span class="asset-name">{{ asset.display_name || asset.id }}</span>
                <span class="status-indicator" :class="getStatusClass(asset.status)">●</span>
              </div>
              <div class="metric-details">
                <div class="metric">
                  <span class="metric-label">Status</span>
                  <span class="metric-value">{{ asset.status || 'Unknown' }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">GPU</span>
                  <span class="metric-value">{{ asset.usage?.gpu ? '✅ Yes' : '❌ No' }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Consumers</span>
                  <span class="metric-value">{{ asset.consumers?.length || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Services Section -->
      <div class="type-section" v-if="services.length > 0">
        <div class="section-header" @click="toggleSection('services')">
          <h2>⚙️ Services <span class="count">({{ services.length }})</span></h2>
          <span class="toggle-icon">{{ expandedSections.services ? '▼' : '▶' }}</span>
        </div>
        <div v-show="expandedSections.services" class="section-content">
          <div class="asset-metrics-grid">
            <div 
              v-for="asset in services" 
              :key="asset.id" 
              class="asset-metric-card"
              :class="getStatusClass(asset.status)"
              @click="selectAsset(asset)"
            >
              <div class="metric-header">
                <span class="asset-name">{{ asset.display_name || asset.id }}</span>
                <span class="status-indicator" :class="getStatusClass(asset.status)">●</span>
              </div>
              <div class="metric-details">
                <div class="metric">
                  <span class="metric-label">Status</span>
                  <span class="metric-value">{{ asset.status || 'Unknown' }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Interface</span>
                  <span class="metric-value">{{ asset.interface || '-' }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Version</span>
                  <span class="metric-value">{{ asset.version || '-' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Apps Section -->
      <div class="type-section" v-if="apps.length > 0">
        <div class="section-header" @click="toggleSection('apps')">
          <h2>📱 Applications <span class="count">({{ apps.length }})</span></h2>
          <span class="toggle-icon">{{ expandedSections.apps ? '▼' : '▶' }}</span>
        </div>
        <div v-show="expandedSections.apps" class="section-content">
          <div class="asset-metrics-grid">
            <div 
              v-for="asset in apps" 
              :key="asset.id" 
              class="asset-metric-card"
              :class="getStatusClass(asset.status)"
              @click="selectAsset(asset)"
            >
              <div class="metric-header">
                <span class="asset-name">{{ asset.display_name || asset.id }}</span>
                <span class="status-indicator" :class="getStatusClass(asset.status)">●</span>
              </div>
              <div class="metric-details">
                <div class="metric">
                  <span class="metric-label">Status</span>
                  <span class="metric-value">{{ asset.status || 'Unknown' }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Interface</span>
                  <span class="metric-value">{{ asset.interface || 'ui' }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Dependencies</span>
                  <span class="metric-value">{{ asset.consumers?.length || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Asset Detail Modal -->
    <Teleport to="body">
      <div v-if="selectedAsset" class="modal-overlay" @click.self="selectedAsset = null">
        <div class="modal-content">
          <div class="modal-header">
            <h2>{{ getAssetIcon(selectedAsset.class) }} {{ selectedAsset.display_name || selectedAsset.id }}</h2>
            <button @click="selectedAsset = null" class="close-btn">✕</button>
          </div>
          <div class="modal-body">
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">ID</span>
                <span class="detail-value"><code>{{ selectedAsset.id }}</code></span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Type</span>
                <span class="detail-value">{{ selectedAsset.class }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Interface</span>
                <span class="detail-value">{{ selectedAsset.interface || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Status</span>
                <span class="detail-value status" :class="getStatusClass(selectedAsset.status)">
                  ● {{ selectedAsset.status || 'Unknown' }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Version</span>
                <span class="detail-value">{{ selectedAsset.version || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">GPU Required</span>
                <span class="detail-value">{{ selectedAsset.usage?.gpu ? 'Yes' : 'No' }}</span>
              </div>
            </div>

            <!-- Consumers -->
            <div v-if="selectedAsset.consumers?.length" class="detail-section">
              <h3>Consumers ({{ selectedAsset.consumers.length }})</h3>
              <div class="consumers-list">
                <span v-for="c in selectedAsset.consumers" :key="c" class="consumer-badge">
                  {{ c }}
                </span>
              </div>
            </div>

            <!-- Metrics (placeholder for real metrics) -->
            <div class="detail-section">
              <h3>Metrics</h3>
              <div class="metrics-placeholder">
                <p>Real-time metrics will be displayed here when available.</p>
                <div class="mock-metrics">
                  <div class="mock-metric">
                    <span class="mock-label">Requests (24h)</span>
                    <span class="mock-value">--</span>
                  </div>
                  <div class="mock-metric">
                    <span class="mock-label">Avg Latency</span>
                    <span class="mock-value">--</span>
                  </div>
                  <div class="mock-metric">
                    <span class="mock-label">Error Rate</span>
                    <span class="mock-value">--</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="goToAssetDetail" class="btn btn-primary">
              View Full Details →
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'
import { useSystemHealthStore } from '@/stores/systemHealthStore'
import type { Asset } from '@/services/gateway'

const router = useRouter()
const route = useRoute()
const assetStore = useAssetStore()
const systemHealth = useSystemHealthStore()

const loading = ref(false)
const selectedAsset = ref<Asset | null>(null)
const expandedSections = reactive({
  models: true,
  services: true,
  apps: true
})

// Computed - filter by type
const models = computed(() => 
  assetStore.assets.filter(a => a.class === 'model')
)

const services = computed(() => 
  assetStore.assets.filter(a => a.class === 'service')
)

const apps = computed(() => 
  assetStore.assets.filter(a => a.class === 'app' || a.class === 'application')
)

// Counts
const modelCount = computed(() => models.value.length)
const serviceCount = computed(() => services.value.length)
const appCount = computed(() => apps.value.length)

const healthyCount = computed(() => 
  assetStore.assets.filter(a => 
    a.status === 'ready' || a.status === 'running' || a.status === 'online'
  ).length
)

const warningCount = computed(() => 
  assetStore.assets.filter(a => 
    a.status === 'stopped' || a.status === 'offline' || a.status === 'unknown'
  ).length
)

const errorCount = computed(() => 
  assetStore.assets.filter(a => a.status === 'error').length
)

// Overall health
const overallHealth = computed(() => {
  if (assetStore.assets.length === 0) {
    return { icon: '⚪', text: 'No assets loaded', badge: 'Unknown', class: 'unknown' }
  }
  if (errorCount.value > 0) {
    return { icon: '🔴', text: `${errorCount.value} assets in error state`, badge: 'Critical', class: 'error' }
  }
  if (healthyCount.value === assetStore.assets.length) {
    return { icon: '🟢', text: 'All Systems Operational', badge: 'Healthy', class: 'healthy' }
  }
  return { icon: '🟡', text: `${healthyCount.value}/${assetStore.assets.length} assets healthy`, badge: 'Degraded', class: 'warning' }
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
  } finally {
    loading.value = false
  }
}

function toggleSection(section: 'models' | 'services' | 'apps') {
  expandedSections[section] = !expandedSections[section]
}

function selectAsset(asset: Asset) {
  selectedAsset.value = asset
}

function goToAssetDetail() {
  if (selectedAsset.value) {
    router.push(`/workspace/${route.params.workspaceId}/assets/${selectedAsset.value.id}`)
  }
}

function getAssetIcon(assetClass?: string): string {
  const icons: Record<string, string> = {
    model: '🧠',
    service: '⚙️',
    tool: '🛠️',
    dataset: '📚',
    application: '📱',
    app: '📱'
  }
  return icons[assetClass?.toLowerCase() || ''] || '📦'
}

function getStatusClass(status?: string): string {
  if (!status) return 'unknown'
  const s = status.toLowerCase()
  if (s === 'ready' || s === 'running' || s === 'online') return 'healthy'
  if (s === 'stopped' || s === 'offline') return 'warning'
  if (s === 'error') return 'error'
  return 'unknown'
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

/* Overview Section */
.overview-section {
  margin-bottom: 2rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.overview-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  gap: 1rem;
  border: 1px solid var(--border-color);
}

.overview-card.healthy {
  border-color: rgba(34, 197, 94, 0.3);
}

.overview-card.warning {
  border-color: rgba(245, 158, 11, 0.3);
}

.overview-card.error {
  border-color: rgba(239, 68, 68, 0.3);
}

.card-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.card-content h3 {
  margin: 0 0 0.5rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.status-text {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.healthy {
  background: rgba(34, 197, 94, 0.2);
  color: var(--status-success);
}

.status-badge.warning {
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

.stats-row {
  display: flex;
  gap: 1.5rem;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.75rem;
  font-weight: 600;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.stat.healthy .stat-value { color: var(--status-success); }
.stat.warning .stat-value { color: var(--status-warning); }
.stat.error .stat-value { color: var(--status-error); }

/* Type Sections */
.type-section {
  background: var(--bg-secondary);
  border-radius: 12px;
  margin-bottom: 1rem;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.section-header:hover {
  background: var(--bg-tertiary);
}

.section-header h2 {
  margin: 0;
  font-size: 1.1rem;
}

.section-header .count {
  color: var(--text-secondary);
  font-weight: 400;
}

.toggle-icon {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.section-content {
  padding: 0 1.5rem 1.5rem;
}

.asset-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.asset-metric-card {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.asset-metric-card:hover {
  border-color: var(--accent-primary);
  transform: translateY(-1px);
}

.asset-metric-card.healthy {
  border-left: 3px solid var(--status-success);
}

.asset-metric-card.warning {
  border-left: 3px solid var(--status-warning);
}

.asset-metric-card.error {
  border-left: 3px solid var(--status-error);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.asset-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-indicator {
  font-size: 0.75rem;
}

.status-indicator.healthy { color: var(--status-success); }
.status-indicator.warning { color: var(--status-warning); }
.status-indicator.error { color: var(--status-error); }
.status-indicator.unknown { color: var(--text-secondary); }

.metric-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.metric {
  flex: 1;
  min-width: 60px;
}

.metric-label {
  display: block;
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
}

.metric-value {
  font-size: 0.85rem;
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
  max-height: 90vh;
  overflow: auto;
  border: 1px solid var(--border-color);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.25rem;
  cursor: pointer;
}

.modal-body {
  padding: 1.5rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.detail-value {
  font-size: 0.95rem;
}

.detail-value code {
  background: var(--bg-tertiary);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85rem;
}

.detail-value.status.healthy { color: var(--status-success); }
.detail-value.status.warning { color: var(--status-warning); }
.detail-value.status.error { color: var(--status-error); }

.detail-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.detail-section h3 {
  margin: 0 0 1rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.consumers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.consumer-badge {
  padding: 0.25rem 0.75rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.8rem;
}

.metrics-placeholder {
  text-align: center;
  padding: 1rem;
  color: var(--text-muted);
}

.mock-metrics {
  display: flex;
  gap: 2rem;
  justify-content: center;
  margin-top: 1rem;
}

.mock-metric {
  text-align: center;
}

.mock-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.mock-value {
  font-size: 1.25rem;
  color: var(--text-muted);
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  text-align: right;
}

/* Buttons */
.btn {
  padding: 0.6rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #4f46e5;
}
</style>
