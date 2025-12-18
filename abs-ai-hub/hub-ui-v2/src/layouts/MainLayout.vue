<template>
  <div class="layout">
    <!-- Top Navigation -->
    <nav class="main-nav">
      <div class="nav-brand">
        <span class="brand-icon">⚡</span>
        <span class="brand-text">ABS AI Hub</span>
      </div>
      
      <div class="nav-tabs">
        <router-link 
          :to="`/workspace/${workspaceId}/apps`"
          class="nav-tab"
          :class="{ active: route.name === 'apps' || route.name === 'app-detail' }"
        >
          📱 Apps
        </router-link>
        <router-link 
          :to="`/workspace/${workspaceId}/assets`"
          class="nav-tab"
          :class="{ active: route.name === 'assets' || route.name === 'asset-detail' }"
        >
          📦 Assets
        </router-link>
        <router-link 
          :to="`/workspace/${workspaceId}/observability`"
          class="nav-tab"
          :class="{ active: route.name === 'observability' }"
        >
          📊 Observability
        </router-link>
        <router-link 
          :to="`/workspace/${workspaceId}/admin`"
          class="nav-tab"
          :class="{ active: route.name === 'admin' }"
        >
          ⚙️ Admin
        </router-link>
      </div>

      <div class="nav-end">
        <span class="workspace-badge">🏢 {{ workspaceId }}</span>
        <span class="health-indicator" :class="{ healthy: systemHealth.allHealthy }">
          {{ systemHealth.allHealthy ? '🟢' : '🟡' }}
        </span>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="footer">
      <p>ABS Legal AI Suite v2.0.0 | Secure On-Prem Deployment</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSystemHealthStore } from '@/stores/systemHealthStore'

const route = useRoute()
const systemHealth = useSystemHealthStore()

const workspaceId = computed(() => 
  (route.params.workspaceId as string) || 'default'
)
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0f0f1a;
  color: #fff;
}

.main-nav {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(180deg, #1a1a2e 0%, #16162a 100%);
  border-bottom: 1px solid #2a2a4a;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  margin-right: 2rem;
}

.brand-icon {
  font-size: 1.5rem;
}

.nav-tabs {
  display: flex;
  gap: 0.5rem;
}

.nav-tab {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  color: #888;
  transition: all 0.2s;
}

.nav-tab:hover {
  background: rgba(255,255,255,0.05);
  color: #fff;
}

.nav-tab.active {
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
}

.nav-end {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.workspace-badge {
  padding: 0.25rem 0.75rem;
  background: rgba(255,255,255,0.1);
  border-radius: 4px;
  font-size: 0.85rem;
}

.health-indicator {
  font-size: 0.75rem;
}

.main-content {
  flex: 1;
  padding: 1.5rem;
}

.footer {
  padding: 1rem;
  text-align: center;
  font-size: 0.8rem;
  color: #666;
  border-top: 1px solid #2a2a4a;
}
</style>
