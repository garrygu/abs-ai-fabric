<script setup lang="ts">
import { useWorkloadsStore } from '@/stores/workloadsStore'

const workloadsStore = useWorkloadsStore()

function getWorkloadIcon(type: string): string {
  const icons: Record<string, string> = {
    'llm_inference': '🧠',
    'rag': '📚',
    'embedding': '🔗',
    'model_management': '⚙️'
  }
  return icons[type] || '📱'
}

function getWorkloadLabel(type: string): string {
  const labels: Record<string, string> = {
    'llm_inference': 'LLM Inference',
    'rag': 'RAG Pipeline',
    'embedding': 'Embeddings',
    'model_management': 'Management'
  }
  return labels[type] || type
}
</script>

<template>
  <div class="page page-workloads">
    <p class="page-subtitle">Currently active AI applications on this workstation</p>

    <div class="workloads-list">
      <div 
        v-for="workload in workloadsStore.workloads" 
        :key="workload.app_id"
        class="workload-card"
        :class="{ 'workload-card--active': workload.status === 'running' }"
      >
        <div class="workload-icon">{{ getWorkloadIcon(workload.workload_type) }}</div>
        <div class="workload-content">
          <h3 class="workload-name">{{ workload.app_name }}</h3>
          <div class="workload-meta">
            <span class="workload-type">{{ getWorkloadLabel(workload.workload_type) }}</span>
            <span class="workload-status" :class="workload.status">
              {{ workload.status === 'running' ? '● Running' : '○ Idle' }}
            </span>
          </div>
          <div v-if="workload.associated_models?.length" class="workload-models">
            <span class="models-label">Models:</span>
            <span 
              v-for="model in workload.associated_models" 
              :key="model" 
              class="model-badge"
            >
              {{ model }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="workloadsStore.workloads.length === 0" class="empty-state">
        <span class="empty-icon">💤</span>
        <p>No active workloads</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-workloads {
  padding: 40px 24px;
  max-width: var(--container-max);
  margin: 0 auto;
}

.page-subtitle {
  text-align: center;
  color: var(--text-muted);
  font-family: var(--font-label);
  font-size: 0.875rem;
  margin-bottom: 32px;
}

.workloads-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.workload-card {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 24px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.workload-card--active {
  border-color: rgba(34, 197, 94, 0.3);
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.05);
}

.workload-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.workload-content {
  flex: 1;
  min-width: 0;
}

.workload-name {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.workload-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.workload-type {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.workload-status {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
}

.workload-status.running {
  color: var(--status-success);
}

.workload-status.idle {
  color: var(--text-muted);
}

.workload-models {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.models-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
}

.model-badge {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--electric-indigo);
}

.empty-state {
  text-align: center;
  padding: 60px 24px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 16px;
}
</style>
