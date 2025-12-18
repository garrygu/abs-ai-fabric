<template>
  <div class="app-card" :class="{ online: app.status === 'online', offline: app.status === 'offline' }">
    <div class="card-header">
      <span class="app-icon">{{ getAppIcon(app.category) }}</span>
      <div class="app-title">
        <h3>{{ app.name }}</h3>
        <span class="status-badge" :class="app.status">
          {{ app.status === 'online' ? 'Online' : app.status === 'offline' ? 'Offline' : 'Error' }}
        </span>
      </div>
    </div>

    <p class="app-description">{{ app.description || getDefaultDescription(app) }}</p>

    <div class="dependencies-section" v-if="app.dependencies.length > 0">
      <span class="deps-label">Dependencies:</span>
      <div class="deps-list">
        <span 
          v-for="dep in visibleDeps" 
          :key="dep" 
          class="dep-badge"
        >
          {{ formatDep(dep) }}
        </span>
        <span v-if="hiddenDepsCount > 0" class="dep-badge more">
          +{{ hiddenDepsCount }} more
        </span>
      </div>
    </div>

    <div class="card-actions">
      <button 
        v-if="showInstall" 
        class="btn btn-install"
        @click.stop="$emit('install', app)"
      >
        Install
      </button>
      <button 
        v-else
        class="btn btn-open"
        :class="{ disabled: app.status !== 'online' }"
        :disabled="app.status !== 'online'"
        @click.stop="$emit('open', app)"
      >
        Open {{ formatAppName(app.name) }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { App } from '@/services/gateway'

const props = defineProps<{
  app: App
  showInstall?: boolean
}>()

defineEmits<{
  open: [app: App]
  install: [app: App]
}>()

const MAX_VISIBLE_DEPS = 3

const visibleDeps = computed(() => 
  props.app.dependencies.slice(0, MAX_VISIBLE_DEPS)
)

const hiddenDepsCount = computed(() => 
  Math.max(0, props.app.dependencies.length - MAX_VISIBLE_DEPS)
)

function getAppIcon(category: string): string {
  const icons: Record<string, string> = {
    'Legal Apps': '⚖️',
    'Application': '📱',
    'Utility Services': '🔧',
    'app': '📱',
    'application': '📱'
  }
  return icons[category] || '🤖'
}

function getDefaultDescription(app: App): string {
  const descriptions: Record<string, string> = {
    'legal-assistant': 'Rich legal assistant with chat, RAG, and contract analysis.',
    'contract-reviewer': 'Analyze contracts, extract key clauses, flag risks.',
    'contract-reviewer-v2': 'Professional AI-powered contract analysis platform.',
    'rag-pdf-voice': 'Document analysis with voice interaction capabilities.',
    'onyx-suite': 'Full-feature Onyx deployment (local).',
    'open-webui': 'Open-source web interface for LLM chat and model management.'
  }
  return descriptions[app.id] || 'AI-powered application.'
}

function formatDep(dep: string): string {
  if (dep.length > 20) {
    return dep.substring(0, 17) + '...'
  }
  return dep
}

function formatAppName(name: string): string {
  return name.replace(/^(Open |Launch )/, '')
}
</script>

<style scoped>
.app-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}

.app-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.app-card.online {
  border-color: rgba(34, 197, 94, 0.3);
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.app-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.app-title {
  flex: 1;
  min-width: 0;
}

.app-title h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  margin-top: 0.25rem;
}

.status-badge.online {
  background: rgba(34, 197, 94, 0.2);
  color: var(--status-success);
}

.status-badge.offline {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.status-badge.error {
  background: rgba(239, 68, 68, 0.2);
  color: var(--status-error);
}

.app-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 0 0 1rem;
  line-height: 1.5;
  flex: 1;
}

.dependencies-section {
  margin-bottom: 1rem;
}

.deps-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.deps-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.dep-badge {
  padding: 0.2rem 0.5rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}

.dep-badge.more {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.card-actions {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.btn {
  width: 100%;
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-open {
  background: var(--accent-primary);
  color: white;
}

.btn-open:hover:not(.disabled) {
  background: var(--accent-hover);
}

.btn-open.disabled {
  background: var(--bg-tertiary);
  color: var(--text-muted);
  cursor: not-allowed;
}

.btn-install {
  background: rgba(34, 197, 94, 0.2);
  color: var(--status-success);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.btn-install:hover {
  background: rgba(34, 197, 94, 0.3);
}
</style>
