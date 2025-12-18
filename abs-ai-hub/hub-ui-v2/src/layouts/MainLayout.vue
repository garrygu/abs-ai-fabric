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
        <!-- Theme Toggle -->
        <button 
          class="theme-toggle" 
          @click="themeStore.toggleTheme()"
          :title="themeStore.theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        >
          {{ themeStore.theme === 'dark' ? '☀️' : '🌙' }}
        </button>
        
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
import { useThemeStore } from '@/stores/themeStore'

const route = useRoute()
const systemHealth = useSystemHealthStore()
const themeStore = useThemeStore()

const workspaceId = computed(() => 
  (route.params.workspaceId as string) || 'default'
)
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.main-nav {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.3s ease, border-color 0.3s ease;
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
  color: var(--text-secondary);
  transition: all 0.2s;
}

.nav-tab:hover {
  background: var(--accent-subtle);
  color: var(--text-primary);
  text-decoration: none;
}

.nav-tab.active {
  background: var(--accent-subtle);
  color: var(--accent-primary);
}

.nav-end {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.theme-toggle {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.theme-toggle:hover {
  background: var(--border-color);
  border-color: var(--border-hover);
}

.workspace-badge {
  padding: 0.25rem 0.75rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.85rem;
}

.health-indicator {
  font-size: 0.75rem;
}

.main-content {
  flex: 1;
  padding: 1.5rem;
  background: var(--bg-primary);
}

.footer {
  padding: 1rem;
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}
</style>
