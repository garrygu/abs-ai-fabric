<template>
  <div class="apps-view">
    <header class="view-header">
      <h1>📱 Apps</h1>
      <p class="view-desc">AI applications powered by your assets.</p>
    </header>

    <div class="apps-grid">
      <div 
        v-for="app in appStore.installedApps" 
        :key="app.id"
        class="app-card"
        @click="goToApp(app.id)"
      >
        <span class="app-icon">{{ app.icon || '🤖' }}</span>
        <h3>{{ app.name }}</h3>
        <p>{{ app.description || 'AI Application' }}</p>
        <span class="status" :class="app.status">● {{ app.status }}</span>
      </div>

      <div v-if="appStore.installedApps.length === 0" class="empty-state">
        No apps installed yet. Check the App Store!
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/appStore'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

onMounted(() => {
  appStore.fetchApps()
})

function goToApp(id: string) {
  router.push(`/workspace/${route.params.workspaceId}/apps/${id}`)
}
</script>

<style scoped>
.apps-view {
  max-width: 1200px;
  margin: 0 auto;
}

.view-header h1 {
  margin: 0;
}

.view-desc {
  color: #888;
  margin-top: 0.5rem;
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.app-card {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.app-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.app-icon {
  font-size: 2.5rem;
}

.app-card h3 {
  margin: 1rem 0 0.5rem;
}

.app-card p {
  color: #888;
  font-size: 0.9rem;
  margin: 0;
}

.status {
  display: inline-block;
  margin-top: 1rem;
  font-size: 0.85rem;
}

.status.running {
  color: #22c55e;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 3rem;
  color: #888;
}
</style>
