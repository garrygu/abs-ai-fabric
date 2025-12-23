<script setup lang="ts">
import { useModelsStore } from '@/stores/modelsStore'

const modelsStore = useModelsStore()

function getModelIcon(type: string): string {
  const icons: Record<string, string> = {
    'llm': '🧠',
    'embedding': '🔗',
    'image': '🖼️'
  }
  return icons[type] || '📦'
}

function getModelTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'llm': 'Large Language Model',
    'embedding': 'Embedding Model',
    'image': 'Image Generation'
  }
  return labels[type] || type
}
</script>

<template>
  <div class="page page-models">
    <p class="page-subtitle">All AI models installed locally on this workstation</p>

    <div class="models-grid">
      <div 
        v-for="model in modelsStore.models" 
        :key="model.model_id"
        class="model-card"
        :class="{ 'model-card--ready': model.serving_status === 'ready' }"
      >
        <div class="model-header">
          <span class="model-icon">{{ getModelIcon(model.type) }}</span>
          <span class="model-status" :class="model.serving_status">
            {{ model.serving_status === 'ready' ? '● Ready' : '○ Idle' }}
          </span>
        </div>
        <h3 class="model-name">{{ model.display_name }}</h3>
        <div class="model-meta">
          <span class="model-type">{{ getModelTypeLabel(model.type) }}</span>
          <span v-if="model.size_gb" class="model-size">{{ model.size_gb }} GB</span>
        </div>
        <div class="model-locality">
          <span class="locality-badge">🏠 LOCAL</span>
        </div>
      </div>

      <div v-if="modelsStore.models.length === 0" class="empty-state">
        <span class="empty-icon">📦</span>
        <p>No models installed</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-models {
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

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.model-card {
  padding: 24px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.model-card--ready {
  border-color: rgba(34, 197, 94, 0.3);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.model-icon {
  font-size: 1.5rem;
}

.model-status {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.model-status.ready {
  color: var(--status-success);
}

.model-status.idle {
  color: var(--text-muted);
}

.model-name {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.model-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.model-type {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.model-size {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.locality-badge {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.empty-state {
  grid-column: 1 / -1;
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
