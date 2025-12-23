<script setup lang="ts">
import { onMounted } from 'vue'
import { useWorkloadsStore } from '@/stores/workloadsStore'

const workloadsStore = useWorkloadsStore()

onMounted(() => {
  if (workloadsStore.workloads.length === 0) {
    workloadsStore.fetchWorkloads()
  }
})
</script>

<template>
  <div class="workloads-panel">
    <div class="section-header">
      <h2 class="section-title">Current AI Workloads</h2>
      <span class="workload-count badge">{{ workloadsStore.totalActive }} Active</span>
    </div>
    
    <p class="section-description text-secondary">
      Visually connecting Apps → Models → Hardware
    </p>
    
    <div class="workloads-grid">
      <div 
        v-for="workload in workloadsStore.workloads" 
        :key="workload.app_id"
        class="workload-card card"
        :class="{ 'workload-card--running': workload.status === 'running' }"
      >
        <div class="workload-header">
          <span 
            class="status-dot" 
            :class="workload.status === 'running' ? 'status-dot--running' : 'status-dot--idle'"
          ></span>
          <h3 class="workload-name">{{ workload.app_name }}</h3>
        </div>
        
        <div class="workload-type">
          <span class="type-arrow">→</span>
          <span class="type-label">{{ workloadsStore.getWorkloadTypeLabel(workload.workload_type) }}</span>
        </div>
        
        <div v-if="workload.associated_models?.length" class="workload-models">
          <span 
            v-for="model in workload.associated_models" 
            :key="model" 
            class="model-tag"
          >
            {{ model }}
          </span>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-if="workloadsStore.workloads.length === 0" class="empty-state">
        <span class="empty-icon">📭</span>
        <p class="empty-text">No active workloads</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workloads-panel {
  width: 100%;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.section-title {
  font-size: 1.375rem;
  margin: 0;
}

.section-description {
  font-size: 0.875rem;
  margin: 0 0 24px 0;
}

.workloads-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.workload-card {
  padding: 20px;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.workload-card--running {
  border-color: rgba(34, 197, 94, 0.3);
}

.workload-card--running:hover {
  border-color: var(--status-success);
}

.workload-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.workload-name {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.workload-type {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.type-arrow {
  color: var(--electric-indigo);
  font-weight: bold;
}

.type-label {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.workload-models {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.model-tag {
  padding: 4px 8px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: var(--border-subtle);
  border-radius: 4px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 48px 24px;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  display: block;
}

.empty-text {
  font-size: 1rem;
  color: var(--text-muted);
  margin: 0;
}
</style>
