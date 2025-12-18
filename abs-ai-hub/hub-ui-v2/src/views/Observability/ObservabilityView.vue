<template>
  <div class="observability-view">
    <header class="view-header">
      <h1>📊 Observability</h1>
      <p class="view-desc">Monitor system health, services, and resource usage.</p>
    </header>

    <div class="dashboard-grid">
      <div class="dashboard-card">
        <h2>System Health</h2>
        <div class="health-indicator">
          {{ systemHealth.allHealthy ? '🟢 All Systems Operational' : '🟡 Issues Detected' }}
        </div>
        <p v-if="systemHealth.lastUpdated" class="last-updated">
          Last updated: {{ systemHealth.lastUpdated.toLocaleTimeString() }}
        </p>
      </div>

      <div class="dashboard-card">
        <h2>Services</h2>
        <ul class="service-list">
          <li v-for="service in systemHealth.services" :key="service.name">
            <span class="status-dot" :class="service.status">●</span>
            {{ service.name }}
          </li>
        </ul>
      </div>

      <div class="dashboard-card">
        <h2>Assets Summary</h2>
        <div class="stats">
          <div class="stat">
            <span class="stat-value">{{ assetStore.assets.length }}</span>
            <span class="stat-label">Total Assets</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ assetStore.healthyAssets.length }}</span>
            <span class="stat-label">Healthy</span>
          </div>
        </div>
      </div>
    </div>

    <button @click="refresh" class="btn btn-primary">
      🔄 Refresh All
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useSystemHealthStore } from '@/stores/systemHealthStore'
import { useAssetStore } from '@/stores/assetStore'

const systemHealth = useSystemHealthStore()
const assetStore = useAssetStore()

onMounted(() => {
  systemHealth.fetchStatus()
  assetStore.fetchAssets()
})

function refresh() {
  systemHealth.refreshAll()
  assetStore.fetchAssets()
}
</script>

<style scoped>
.observability-view {
  max-width: 1200px;
  margin: 0 auto;
}

.view-header h1 {
  margin: 0;
}

.view-desc {
  color: #888;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.dashboard-card {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 1.5rem;
}

.dashboard-card h2 {
  margin: 0 0 1rem;
  font-size: 1rem;
  color: #888;
}

.health-indicator {
  font-size: 1.25rem;
}

.last-updated {
  color: #666;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.service-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.service-list li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #2a2a4a;
}

.status-dot.running { color: #22c55e; }
.status-dot.stopped { color: #f59e0b; }
.status-dot.error { color: #ef4444; }

.stats {
  display: flex;
  gap: 2rem;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 600;
}

.stat-label {
  color: #888;
  font-size: 0.85rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: #6366f1;
  color: white;
}
</style>
