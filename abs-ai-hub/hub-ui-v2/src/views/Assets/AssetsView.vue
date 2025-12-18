<template>
  <div class="assets-view">
    <header class="view-header">
      <h1>📦 Assets</h1>
      <p class="view-desc">Manage models, services, and resources in your workspace.</p>
    </header>

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

    <!-- Assets Table -->
    <div v-else class="assets-table-container">
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
            v-for="asset in assetStore.assets" 
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
              <span class="status-dot" :class="asset.status?.toLowerCase()">●</span>
              {{ capitalize(asset.status || 'Unknown') }}
            </td>
            <td>{{ asset.consumers?.length || 0 }}</td>
            <td>{{ asset.usage?.gpu ? '✅' : 'No' }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="assetStore.assets.length === 0" class="empty-state">
        No assets found in this workspace.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'

const router = useRouter()
const route = useRoute()
const assetStore = useAssetStore()

// Fetch on mount (always re-fetch, Gateway is source of truth)
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
    application: '📱'
  }
  return icons[assetClass?.toLowerCase() || ''] || '📦'
}

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}
</script>

<style scoped>
.assets-view {
  max-width: 1200px;
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
  color: #888;
  margin-top: 0.5rem;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #888;
}

.error-state {
  color: #ef4444;
}

.assets-table {
  width: 100%;
  border-collapse: collapse;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
}

.assets-table th,
.assets-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #2a2a4a;
}

.assets-table th {
  background: #16162a;
  color: #888;
  font-weight: 500;
  font-size: 0.85rem;
  text-transform: uppercase;
}

.asset-row {
  cursor: pointer;
  transition: background 0.2s;
}

.asset-row:hover {
  background: rgba(255,255,255,0.03);
}

.asset-name {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.asset-icon {
  font-size: 1.25rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
  border-radius: 4px;
  font-size: 0.8rem;
}

.status-dot {
  margin-right: 0.5rem;
}
.status-dot.ready,
.status-dot.running {
  color: #22c55e;
}
.status-dot.stopped {
  color: #f59e0b;
}
.status-dot.error {
  color: #ef4444;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: #6366f1;
  color: white;
}

.btn-primary:hover {
  background: #4f46e5;
}
</style>
