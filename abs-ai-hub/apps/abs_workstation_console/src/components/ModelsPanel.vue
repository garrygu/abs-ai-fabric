<script setup lang="ts">
import { onMounted } from 'vue'
import { useModelsStore } from '@/stores/modelsStore'

const modelsStore = useModelsStore()

onMounted(() => {
  if (modelsStore.models.length === 0) {
    modelsStore.fetchModels()
  }
})
</script>

<template>
  <div class="models-panel">
    <div class="section-header">
      <h2 class="section-title">Installed Models</h2>
      <span class="model-count text-muted">{{ modelsStore.models.length }} models • {{ modelsStore.totalSize.toFixed(1) }} GB</span>
    </div>
    
    <div class="trust-badges">
      <span class="badge badge--local">🔒 Local</span>
      <span class="badge">☁️ No Cloud</span>
      <span class="badge badge--enterprise">🏢 Enterprise Ready</span>
    </div>
    
    <div class="models-grid">
      <div 
        v-for="model in modelsStore.models" 
        :key="model.model_id"
        class="model-card card"
        :class="{ 'model-card--ready': model.serving_status === 'ready' }"
      >
        <div class="model-header">
          <span class="model-icon">{{ modelsStore.getModelTypeIcon(model.type) }}</span>
          <div class="model-info">
            <h3 class="model-name">{{ model.display_name }}</h3>
            <span class="model-type text-muted">{{ modelsStore.getModelTypeLabel(model.type) }}</span>
          </div>
        </div>
        
        <div class="model-meta">
          <span v-if="model.size_gb" class="model-size">
            {{ model.size_gb.toFixed(1) }} GB
          </span>
          <span 
            class="model-status"
            :class="model.serving_status === 'ready' ? 'model-status--ready' : 'model-status--idle'"
          >
            {{ model.serving_status === 'ready' ? '● Ready' : '○ Idle' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.models-panel {
  width: 100%;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 1.375rem;
  margin: 0;
}

.model-count {
  font-size: 0.875rem;
}

.trust-badges {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.model-card {
  padding: 18px 20px;
}

.model-card--ready {
  border-color: rgba(99, 102, 241, 0.3);
}

.model-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.model-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-name {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.model-type {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.model-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.model-size {
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.model-status {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.model-status--ready {
  color: var(--status-success);
}

.model-status--idle {
  color: var(--text-muted);
}
</style>
