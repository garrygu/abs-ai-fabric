<template>
  <div class="app-card" :class="`status-${getSemanticStatus(app)}`">
    <div class="card-header">
      <span class="app-icon">{{ getAppIcon(app.category) }}</span>
      <div class="app-title">
        <h3>{{ app.name }}</h3>
        
        <!-- Trust Badge (Phase 2A.1) -->
        <div class="app-tier-badge" :class="`tier-${getTier(app)}`">
          <span v-if="getTier(app) === 'abs'">🟧 ABS Official</span>
          <span v-else-if="getTier(app) === 'partner'">🟦 Partner</span>
          <span v-else-if="getTier(app) === 'community'">🟨 Community</span>
          <span v-else>⚠️ Unverified</span>
        </div>
        
        <!-- Semantic Status Badge (Phase 2A.2) -->
        <span class="app-status-badge" :class="`semantic-${getSemanticStatus(app)}`">
          {{ getStatusLabel(app) }}
        </span>
      </div>
    </div>

    <p class="app-description">{{ app.description || getDefaultDescription(app) }}</p>

    <!-- Phase 2B: Dependency UX with Collapsed Capability View -->
    <div class="dependencies-section" v-if="hasDependencies(app)">
      <div class="dependency-summary" @click="toggleDependencies">
        <span class="dep-capability-badge">🧠 LLM Runtime</span>
        <span class="dep-capability-badge" v-if="app.policy?.allowed_embeddings">📐 Embeddings</span>
        <span class="dep-count" v-if="app.dependencies && app.dependencies.length > 3">
          ➕ {{ app.dependencies.length - 3 }} more
        </span>
      </div>
      
      <!-- Expanded dependency details -->
      <div class="dependency-details" v-if="dependenciesExpanded">
        <div class="deps-list">
          <span v-for="dep in (app.dependencies || [])" :key="dep" class="dep-badge-inline">
            {{ formatDep(dep) }}
          </span>
        </div>
      </div>
      
      <!-- Phase 2B.2: Resource Cost Badges -->
      <div class="resource-hints" v-if="showResourceHints(app)">
        <span class="hint" v-if="app.lifecycle?.desired === 'on-demand'">💤 Auto-sleep</span>
        <span class="hint" v-if="app.lifecycle?.auto_sleep_min">⚡ Sleep after {{ app.lifecycle.auto_sleep_min }}min</span>
      </div>
    </div>

    <!-- Phase 2A.3: Normalized CTAs -->
    <div class="card-actions">
      <template v-if="showInstall">
        <!-- App Store CTAs -->
        <button class="btn btn-primary btn-install" @click.stop="$emit('install', app)">
          Install
        </button>
        <button class="btn btn-secondary" @click.stop="showRequirements">
          View Requirements
        </button>
      </template>
      <template v-else>
        <!-- Installed Apps CTAs -->
        <button 
          class="btn btn-primary btn-open"
          :class="{ disabled: !isActionable(app) }"
          :disabled="!isActionable(app)"
          @click.stop="$emit('open', app)"
        >
          Open
        </button>
        <button class="btn btn-secondary" @click.stop="showDetails">
          Details
        </button>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { App } from '@/services/gateway'

const props = defineProps<{
  app: App
  showInstall?: boolean
}>()

defineEmits<{
  open: [app: App]
  install: [app: App]
}>()

const dependenciesExpanded = ref(false)

function getTier(app: App): string {
  return (app.metadata as any)?.tier || 'local'
}

function getSemanticStatus(app: App): string {
  const status = app.status
  
  // Map technical status to semantic status
  if (status === 'online') return 'ready'
  if (status === 'offline') return 'idle'
  if (status === 'error') return 'error'
  if (status === 'blocked') return 'blocked'
  if (status === 'starting') return 'starting'
  if (status === 'degraded') return 'degraded'
  
  return 'idle'
}

function getStatusLabel(app: App): string {
  const semantic = getSemanticStatus(app)
  
  const labels: Record<string, string> = {
    ready: '🟢 Ready',
    idle: '🟡 Idle',
    starting: '🔵 Starting',
    error: '🔴 Error',
    blocked: '⚠️ Blocked',
    degraded: '🟠 Degraded'
  }
  
  return labels[semantic] || '⚪ Unknown'
}

function isActionable(app: App): boolean {
  return app.status === 'online'
}

function hasDependencies(app: App): boolean {
  return (app.dependencies && app.dependencies.length > 0) || 
         (app.policy?.required_models && app.policy.required_models.length > 0)
}

function showResourceHints(app: App): boolean {
  return app.lifecycle?.desired === 'on-demand' ||  !!app.lifecycle?.auto_sleep_min
}

function toggleDependencies() {
  dependenciesExpanded.value = !dependenciesExpanded.value
}

function showDetails() {
  console.log('Show details for:', props.app.name)
  // TODO: Implement details modal/drawer
}

function showRequirements() {
  console.log('Show requirements for:', props.app.name)
  // TODO: Implement requirements modal
}

function getAppIcon(category: string): string {
  const icons: Record<string, string> = {
    'Legal Apps': '⚖️',
    'AI Assistants': '🤖',
    'AI Platforms': '🔮',
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
    'deposition-summarizer': 'Summarize deposition transcripts and extract key information.',
    'onyx-assistant': 'AI assistant with chat interface, RAG capabilities, and agent management.',
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

.app-card.status-ready {
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

/* Phase 2A.1: Trust Badges */
.app-tier-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
  margin-top: 0.25rem;
  font-weight: 600;
}

.tier-abs {
  background: rgba(255, 107, 0, 0.1);
  color: #FF6B00;
  border: 1px solid rgba(255, 107, 0, 0.2);
}

.tier-partner {
  background: rgba(59, 130, 246, 0.1);
  color: #3B82F6;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.tier-community {
  background: rgba(234, 179, 8, 0.1);
  color: #EAB308;
  border: 1px solid rgba(234, 179, 8, 0.2);
}

.tier-local {
  background: rgba(156, 163, 175, 0.1);
  color: #9CA3AF;
  border: 1px solid rgba(156, 163, 175, 0.2);
}

/* Phase 2A.2: Semantic Status Badges */
.app-status-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  margin-top: 0.25rem;
  margin-left: 0.5rem;
}

.semantic-ready {
  background: rgba(34, 197, 94, 0.1);
  color: rgb(34, 197, 94);
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.semantic-idle {
  background: rgba(234, 179, 8, 0.1);
  color: rgb(234, 179, 8);
  border: 1px solid rgba(234, 179, 8, 0.2);
}

.semantic-starting {
  background: rgba(59, 130, 246, 0.1);
  color: rgb(59, 130, 246);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.semantic-error {
  background: rgba(239, 68, 68, 0.1);
  color: rgb(239, 68, 68);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.semantic-blocked {
  background: rgba(245, 158, 11, 0.1);
  color: rgb(245, 158, 11);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.semantic-degraded {
  background: rgba(251, 146, 60, 0.1);
  color: rgb(251, 146, 60);
  border: 1px solid rgba(251, 146, 60, 0.2);
}

.app-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 0 0 1rem;
  line-height: 1.5;
  flex: 1;
}

/* Phase 2B: Dependency UX */
.dependencies-section {
  margin-bottom: 1rem;
}

.dependency-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  align-items: center;
  cursor: pointer;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
  transition: background 0.2s;
}

.dependency-summary:hover {
  background: rgba(0, 0, 0, 0.04);
}

.dep-capability-badge {
  padding: 0.25rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  color: rgb(99, 102, 241);
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.dep-count {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 500;
}

.dependency-details {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.deps-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.dep-badge-inline {
  padding: 0.2rem 0.5rem;
  background: var(--accent-subtle);
  color: var(--accent-primary);
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}

/* Phase 2B.2: Resource Hints */
.resource-hints {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.resource-hints .hint {
  font-size: 0.7rem;
  color: var(--text-muted);
  padding: 0.2rem 0.4rem;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 4px;
}

.card-actions {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 0.5rem;
}

.btn {
  flex: 1;
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
}

.btn-primary:hover:not(.disabled) {
  background: var(--accent-hover);
}

.btn-primary.disabled {
  background: var(--bg-tertiary);
  color: var(--text-muted);
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.btn-install {
  background: rgba(34, 197, 94, 0.15);
  color: rgb(34, 197, 94);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.btn-install:hover {
  background: rgba(34, 197, 94, 0.25);
}
</style>
