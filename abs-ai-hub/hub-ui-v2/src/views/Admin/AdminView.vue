<template>
  <div class="admin-view">
    <header class="view-header">
      <h1>⚙️ Admin</h1>
      <p class="view-desc">System administration and configuration.</p>
    </header>

    <div class="admin-sections">
      <section class="admin-card">
        <h2>Quick Actions</h2>
        <div class="action-buttons">
          <button class="btn" @click="systemHealth.refreshAll()">🔄 Refresh All</button>
          <button class="btn">📦 Reload Assets</button>
          <button class="btn">🗑️ Clear Cache</button>
        </div>
      </section>

      <section class="admin-card">
        <h2>Service Controls</h2>
        <p class="placeholder">Service management controls coming soon...</p>
      </section>

      <section class="admin-card">
        <h2>Model Management</h2>
        <p class="placeholder">Model configuration coming soon...</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSystemHealthStore } from '@/stores/systemHealthStore'

const systemHealth = useSystemHealthStore()
</script>

<style scoped>
.admin-view {
  max-width: 1200px;
  margin: 0 auto;
}

.view-header h1 {
  margin: 0;
}

.view-desc {
  color: #888;
}

.admin-sections {
  display: grid;
  gap: 1.5rem;
  margin-top: 2rem;
}

.admin-card {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 1.5rem;
}

.admin-card h2 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.75rem 1rem;
  background: rgba(255,255,255,0.1);
  border: 1px solid #2a2a4a;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

.btn:hover {
  background: rgba(255,255,255,0.15);
}

.placeholder {
  color: #666;
}
</style>
