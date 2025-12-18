<template>
  <div class="asset-detail">
    <router-link :to="`/workspace/${workspaceId}/assets`" class="back-link">
      ← Back to Assets
    </router-link>

    <div v-if="assetStore.loading" class="loading-state">
      Loading asset...
    </div>

    <div v-else-if="asset" class="asset-content">
      <header class="detail-header">
        <span class="asset-icon">{{ getAssetIcon(asset.class) }}</span>
        <div>
          <h1>{{ asset.display_name || asset.id }}</h1>
          <div class="meta">
            <span class="badge">{{ asset.class }}</span>
            <span class="badge">{{ asset.interface }}</span>
            <span class="status" :class="asset.status?.toLowerCase()">
              ● {{ asset.status }}
            </span>
          </div>
        </div>
      </header>

      <section class="detail-section">
        <h2>Details</h2>
        <dl class="detail-grid">
          <div>
            <dt>ID</dt>
            <dd><code>{{ asset.id }}</code></dd>
          </div>
          <div>
            <dt>Version</dt>
            <dd>{{ asset.version || 'N/A' }}</dd>
          </div>
          <div>
            <dt>GPU Required</dt>
            <dd>{{ asset.usage?.gpu ? 'Yes' : 'No' }}</dd>
          </div>
          <div>
            <dt>Consumers</dt>
            <dd>{{ asset.consumers?.length || 0 }}</dd>
          </div>
        </dl>
      </section>

      <section v-if="asset.consumers?.length" class="detail-section">
        <h2>Consumers</h2>
        <ul class="consumer-list">
          <li v-for="consumer in asset.consumers" :key="consumer">
            {{ consumer }}
          </li>
        </ul>
      </section>
    </div>

    <div v-else class="error-state">
      Asset not found.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAssetStore } from '@/stores/assetStore'

const route = useRoute()
const assetStore = useAssetStore()

const workspaceId = computed(() => route.params.workspaceId as string)
const assetId = computed(() => route.params.assetId as string)

const asset = computed(() => 
  assetStore.assets.find(a => a.id === assetId.value)
)

onMounted(() => {
  if (assetId.value) {
    assetStore.fetchAsset(assetId.value)
  }
})

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
</script>

<style scoped>
.asset-detail {
  max-width: 900px;
  margin: 0 auto;
}

.back-link {
  display: inline-block;
  color: var(--accent-primary);
  text-decoration: none;
  margin-bottom: 1.5rem;
}

.back-link:hover {
  text-decoration: underline;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
}

.detail-header .asset-icon {
  font-size: 3rem;
}

.detail-header h1 {
  margin: 0;
  font-size: 1.75rem;
}

.meta {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.8rem;
}

.status {
  font-size: 0.85rem;
}
.status.ready,
.status.running,
.status.online {
  color: var(--status-success);
}
.status.stopped,
.status.offline {
  color: var(--status-warning);
}
.status.error {
  color: var(--status-error);
}

.detail-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.detail-section h2 {
  font-size: 1rem;
  margin: 0 0 1rem;
  color: var(--text-secondary);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.detail-grid dt {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.detail-grid dd {
  margin: 0.25rem 0 0;
  font-size: 1rem;
}

code {
  background: var(--bg-tertiary);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.consumer-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.consumer-list li {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
}

.consumer-list li:last-child {
  border-bottom: none;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}
</style>
