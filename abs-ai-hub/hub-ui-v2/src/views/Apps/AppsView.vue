<template>
  <div class="apps-view">
    <header class="view-header">
      <div class="header-content">
        <h1>📱 Applications</h1>
        <p class="view-desc">Discover and launch AI-powered applications available in your workspace.</p>
      </div>
    </header>

    <!-- Sub Navigation Tabs -->
    <div class="sub-nav">
      <button 
        class="tab-btn" 
        :class="{ active: appStore.activeTab === 'installed' }"
        @click="appStore.setActiveTab('installed')"
      >
        Installed Apps
      </button>
      <button 
        class="tab-btn"
        :class="{ active: appStore.activeTab === 'store' }"
        @click="appStore.setActiveTab('store')"
      >
        App Store
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="appStore.loading" class="loading-state">
      <span class="spinner">⏳</span> Loading applications...
    </div>

    <!-- Error State -->
    <div v-else-if="appStore.error" class="error-state">
      <span class="error-icon">❌</span>
      <p>{{ appStore.error }}</p>
      <button @click="appStore.fetchApps()" class="btn btn-primary">Retry</button>
    </div>

    <!-- Installed Apps Tab -->
    <div v-else-if="appStore.activeTab === 'installed'" class="apps-content">
      <div v-if="appStore.installedApps.length === 0" class="empty-state">
        <p>No apps installed yet.</p>
        <button @click="appStore.setActiveTab('store')" class="btn btn-primary">
          Browse App Store
        </button>
      </div>

      <div v-else class="apps-grid">
        <AppCard 
          v-for="app in appStore.installedApps" 
          :key="app.id"
          :app="app"
          @open="openApp"
        />
      </div>
    </div>

    <!-- App Store Tab -->
    <div v-else-if="appStore.activeTab === 'store'" class="apps-content">
      <div class="store-header">
        <h2>🛒 App Store</h2>
        <p>Browse and install new AI applications</p>
      </div>
      <div class="apps-grid">
        <AppCard 
          v-for="app in storeApps" 
          :key="app.id"
          :app="app"
          :showInstall="true"
          @install="installApp"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/appStore'
import type { App } from '@/services/gateway'
import AppCard from '@/components/AppCard.vue'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

// Mock store apps for now
const storeApps = ref<App[]>([
  {
    id: 'legal-researcher-pro',
    name: 'Legal Researcher Pro',
    description: 'Advanced caselaw search and analysis.',
    category: 'Legal Apps',
    url: '#',
    port: 0,
    status: 'offline',
    dependencies: ['llama3.2:3b', 'llama3.2:latest']
  },
  {
    id: 'deposition-summarizer',
    name: 'Deposition Summarizer',
    description: 'Summarize deposition transcripts and extract key information.',
    category: 'Legal Apps',
    url: '#',
    port: 0,
    status: 'offline',
    dependencies: ['llama3.2:3b', 'all-minilm:latest']
  }
])

onMounted(() => {
  appStore.fetchApps()
})

function openApp(app: App) {
  // Use the URL from metadata (e.g., http://localhost:8050)
  if (app.url && app.url.startsWith('http')) {
    window.open(app.url, '_blank')
  } else if (app.port) {
    window.open(`http://localhost:${app.port}`, '_blank')
  } else {
    router.push(`/workspace/${route.params.workspaceId}/apps/${app.id}`)
  }
}

function installApp(app: App) {
  console.log('Installing app:', app.id)
  alert(`Installing ${app.name}...`)
}
</script>

<style scoped>
.apps-view {
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

.sub-nav {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.95rem;
  border-radius: 6px 6px 0 0;
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

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

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

.store-header {
  margin-bottom: 1.5rem;
}

.store-header h2 {
  margin: 0 0 0.25rem;
}

.store-header p {
  color: var(--text-secondary);
  margin: 0;
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

.btn-primary:hover {
  background: var(--accent-hover);
}
</style>
