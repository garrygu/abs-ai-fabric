<template>
  <div class="admin-view">
    <header class="view-header">
      <div class="header-content">
        <h1>⚙️ Admin</h1>
        <p class="view-desc">System administration and configuration.</p>
      </div>
    </header>

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
        <button class="btn btn-sm" @click="loadServices">🔄 Refresh</button>
      </div>
      
      <div class="services-table">
        <div class="service-row header">
          <span class="col-name">Service</span>
          <span class="col-status">Status</span>
          <span class="col-port">Port</span>
          <span class="col-actions">Actions</span>
        </div>
        <div 
          v-for="service in services" 
          :key="service.name" 
          class="service-row"
          :class="service.status"
        >
          <span class="col-name">
            <span class="service-icon">{{ service.icon }}</span>
            {{ service.name }}
          </span>
          <span class="col-status">
            <span class="status-dot" :class="service.status">●</span>
            {{ service.statusText }}
          </span>
          <span class="col-port">{{ service.port || '-' }}</span>
          <span class="col-actions">
            <button 
              v-if="service.status === 'stopped'"
              class="btn btn-sm btn-success"
              @click="startService(service)"
              :disabled="service.loading"
            >
              ▶ Start
            </button>
            <button 
              v-if="service.status === 'running'"
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
          </span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAssetStore } from '@/stores/assetStore'
import { useSystemHealthStore } from '@/stores/systemHealthStore'
import { gateway } from '@/services/gateway'

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
  cache: false
})

// Services
const services = ref([
  { name: 'Gateway', icon: '🌐', status: 'running', statusText: 'Running', port: 8081, loading: false },
  { name: 'Ollama', icon: '🦙', status: 'running', statusText: 'Running', port: 11434, loading: false },
  { name: 'Qdrant', icon: '🔍', status: 'running', statusText: 'Running', port: 6333, loading: false },
  { name: 'Redis', icon: '📦', status: 'stopped', statusText: 'Stopped', port: 6379, loading: false },
  { name: 'PostgreSQL', icon: '🐘', status: 'running', statusText: 'Running', port: 5432, loading: false }
])

// Models
const models = ref<any[]>([])
const showPullModal = ref(false)
const pullModelName = ref('')
const pulling = ref(false)

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
  await loadModels()
})

// Actions
async function refreshAll() {
  loading.refresh = true
  try {
    await Promise.all([
      assetStore.fetchAssets(),
      systemHealth.fetchStatus()
    ])
  } finally {
    loading.refresh = false
  }
}

async function reloadAssets() {
  loading.assets = true
  try {
    await assetStore.fetchAssets()
  } finally {
    loading.assets = false
  }
}

async function clearCache() {
  loading.cache = true
  try {
    // Simulated - would call gateway.clearCache()
    await new Promise(r => setTimeout(r, 1000))
    alert('Cache cleared successfully!')
  } finally {
    loading.cache = false
  }
}

function checkHealth() {
  alert('Health check initiated. See Observability page for results.')
}

// Services
async function loadServices() {
  // Would fetch from gateway
}

async function startService(service: any) {
  service.loading = true
  await new Promise(r => setTimeout(r, 1000))
  service.status = 'running'
  service.statusText = 'Running'
  service.loading = false
}

async function stopService(service: any) {
  service.loading = true
  await new Promise(r => setTimeout(r, 1000))
  service.status = 'stopped'
  service.statusText = 'Stopped'
  service.loading = false
}

async function restartService(service: any) {
  service.loading = true
  service.status = 'restarting'
  service.statusText = 'Restarting...'
  await new Promise(r => setTimeout(r, 2000))
  service.status = 'running'
  service.statusText = 'Running'
  service.loading = false
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

.service-row {
  display: grid;
  grid-template-columns: 2fr 1fr 0.5fr 2fr;
  padding: 1rem;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.service-row:last-child {
  border-bottom: none;
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
  margin-right: 0.5rem;
}
.status-dot.running { color: var(--status-success); }
.status-dot.stopped { color: var(--status-warning); }
.status-dot.error { color: var(--status-error); }
.status-dot.restarting { color: var(--accent-primary); }

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
</style>
