<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="visible" class="drawer-overlay" @click="close">
        <div class="drawer-panel" @click.stop>
          <!-- Header -->
          <header class="drawer-header">
            <div class="header-content">
              <span class="app-icon-large">{{ getAppIcon(app.category) }}</span>
              <div class="header-text">
                <h2>{{ app.name }}</h2>
                <div class="header-badges">
                  <span class="tier-badge" :class="`tier-${getTier(app)}`">
                    {{ getTierLabel(app) }}
                  </span>
                  <span class="status-badge" :class="`status-${getSemanticStatus(app)}`">
                    {{ getStatusLabel(app) }}
                  </span>
                </div>
              </div>
            </div>
            <button class="close-btn" @click="close" aria-label="Close">×</button>
          </header>

          <!-- Content -->
          <div class="drawer-content">
            <!-- Overview Section -->
            <section class="drawer-section">
              <h3>📋 Overview</h3>
              <p class="description">{{ app.description || getDefaultDescription(app) }}</p>
              <div class="meta-info">
                <div class="meta-item" v-if="app.metadata?.url">
                  <span class="meta-label">URL:</span>
                  <a :href="app.metadata.url" target="_blank" class="meta-value">{{ app.metadata.url }}</a>
                </div>
                <div class="meta-item" v-if="app.metadata?.port">
                  <span class="meta-label">Port:</span>
                  <span class="meta-value">{{ app.metadata.port }}</span>
                </div>
                <div class="meta-item" v-if="app.metadata?.category">
                  <span class="meta-label">Category:</span>
                  <span class="meta-value">{{ app.metadata.category }}</span>
                </div>
              </div>
            </section>

            <!-- Capabilities Section -->
            <section class="drawer-section" v-if="app.policy?.required_models || app.policy?.allowed_embeddings">
              <h3>⚡ Capabilities</h3>
              <div class="capabilities-list">
                <div class="capability-item" v-if="app.policy?.required_models">
                  <span class="capability-icon">🧠</span>
                  <div>
                    <div class="capability-name">LLM Runtime</div>
                    <div class="capability-desc">Supports text generation and analysis</div>
                  </div>
                </div>
                <div class="capability-item" v-if="app.policy?.allowed_embeddings">
                  <span class="capability-icon">📐</span>
                  <div>
                    <div class="capability-name">Vector Embeddings</div>
                    <div class="capability-desc">Document similarity and semantic search</div>
                  </div>
                </div>
              </div>
            </section>

            <!-- Dependencies Section -->
            <section class="drawer-section" v-if="hasDependencies(app)">
              <h3>📦 Dependencies</h3>
              <div class="dependency-group" v-if="app.policy?.required_models">
                <h4>Required Models</h4>
                <div class="dependency-list">
                  <div v-for="model in app.policy.required_models" :key="model" class="dependency-item">
                    <span class="dep-icon">🔹</span>
                    <span class="dep-name">{{ model }}</span>
                    <span class="dep-status status-ready">✓ Available</span>
                  </div>
                </div>
              </div>
              <div class="dependency-group" v-if="app.policy?.allowed_embeddings">
                <h4>Embedding Models</h4>
                <div class="dependency-list">
                  <div v-for="embed in app.policy.allowed_embeddings" :key="embed" class="dependency-item">
                    <span class="dep-icon">🔹</span>
                    <span class="dep-name">{{ embed }}</span>
                    <span class="dep-status status-ready">✓ Available</span>
                  </div>
                </div>
              </div>
            </section>

            <!-- Resource Impact Section -->
            <section class="drawer-section">
              <h3>💻 Resource Impact</h3>
              <div class="resource-grid">
                <div class="resource-card">
                  <div class="resource-icon">💾</div>
                  <div class="resource-label">Memory</div>
                  <div class="resource-value">~2-4 GB</div>
                </div>
                <div class="resource-card">
                  <div class="resource-icon">⚙️</div>
                  <div class="resource-label">CPU</div>
                  <div class="resource-value">Low-Medium</div>
                </div>
                <div class="resource-card" v-if="app.lifecycle?.desired === 'on-demand'">
                  <div class="resource-icon">💤</div>
                  <div class="resource-label">Auto-Sleep</div>
                  <div class="resource-value">{{ app.lifecycle.auto_sleep_min || 15 }} min</div>
                </div>
                <div class="resource-card">
                  <div class="resource-icon">⚡</div>
                  <div class="resource-label">Startup</div>
                  <div class="resource-value">~5-10s</div>
                </div>
              </div>
            </section>

            <!-- Security & License Section -->
            <section class="drawer-section">
              <h3>🔒 Security & License</h3>
              <div class="security-info">
                <div class="info-row">
                  <span class="info-label">Trust Level:</span>
                  <span class="info-value" :class="`tier-${getTier(app)}`">
                    {{ getTierDescription(app) }}
                  </span>
                </div>
                <div class="info-row">
                  <span class="info-label">Permissions:</span>
                  <span class="info-value">Model access, File storage</span>
                </div>
                <div class="info-row" v-if="app.metadata?.documentation_url">
                  <span class="info-label">Documentation:</span>
                  <a :href="app. metadata.documentation_url" target="_blank" class="info-link">
                    View Docs →
                  </a>
                </div>
              </div>
            </section>
          </div>

          <!-- Footer Actions -->
          <footer class="drawer-footer">
            <button v-if="isInstalled" class="btn btn-primary" @click="openApp" :disabled="app.status !== 'online'">
              <span v-if="app.status === 'online'">Open Application</span>
              <span v-else>Offline - Cannot Open</span>
            </button>
            <button v-else class="btn btn-primary" @click="installApp">
              Install Application
            </button>
            <button class="btn btn-secondary" @click="close">Close</button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { App } from '@/services/gateway'

const props = defineProps<{
  visible: boolean
  app: App
  isInstalled?: boolean
}>()

const emit = defineEmits<{
  close: []
  open: [app: App]
  install: [app: App]
}>()

function close() {
  emit('close')
}

function openApp() {
  emit('open', props.app)
  close()
}

function installApp() {
  emit('install', props.app)
  close()
}

function getTier(app: App): string {
  return (app.metadata as any)?.tier || 'local'
}

function getTierLabel(app: App): string {
  const tier = getTier(app)
  const labels = {
    abs: '🟧 ABS Official',
    partner: '🟦 Partner',
    community: '🟨 Community',
    local: '⚠️ Unverified'
  }
  return labels[tier as keyof typeof labels] || labels.local
}

function getTierDescription(app: App): string {
  const tier = getTier(app)
  const descriptions = {
    abs: 'Official ABS application - Full support and warranty',
    partner: 'Certified partner application - Verified by ABS',
    community: 'Community application - Use at own discretion',
    local: 'Local/custom application - No external vetting'
  }
  return descriptions[tier as keyof typeof descriptions] || descriptions.local
}

function getSemanticStatus(app: App): string {
  const status = app.status
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
  const labels = {
    ready: '🟢 Ready',
    idle: '🟡 Idle',
    starting: '🔵 Starting',
    error: '🔴 Error',
    blocked: '⚠️ Blocked',
    degraded: '🟠 Degraded'
  }
  return labels[semantic as keyof typeof labels] || '⚪ Unknown'
}

function getAppIcon(category: string): string {
  const icons: Record<string, string> = {
    'Legal Apps': '⚖️',
    'AI Assistants': '🤖',
    'AI Platforms': '🔮',
    'Application': '📱',
    'Utility Services': '🔧'
  }
  return icons[category] || '🤖'
}

function getDefaultDescription(app: App): string {
  const descriptions: Record<string, string> = {
    'legal-assistant': 'Rich legal assistant with chat, RAG, and contract analysis.',
    'contract-reviewer-v2': 'Professional AI-powered contract analysis platform.',
    'deposition-summarizer': 'Summarize deposition transcripts and extract key information.',
    'onyx-assistant': 'AI assistant with chat interface, RAG capabilities, and agent management.',
    'onyx-suite': 'Full-feature Onyx deployment (local).',
    'open-webui': 'Open-source web interface for LLM chat and model management.'
  }
  return descriptions[app.id] || 'AI-powered application.'
}

function hasDependencies(app: App): boolean {
  return !!(app.policy?.required_models?.length || app.policy?.allowed_embeddings?.length)
}
</script>

<style scoped>
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9999;
  display: flex;
  justify-content: flex-end;
}

.drawer-panel {
  width: 600px;
  max-width: 90vw;
  background: var(--bg-primary);
  height: 100vh;
  overflow-y: auto;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.drawer-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  background: var(--bg-secondary);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-content {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  flex: 1;
}

.app-icon-large {
  font-size: 3rem;
}

.header-text h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.header-badges {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.tier-badge,
.status-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
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

.status-ready {
  background: rgba(34, 197, 94, 0.1);
  color: rgb(34, 197, 94);
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.status-idle {
  background: rgba(234, 179, 8, 0.1);
  color: rgb(234, 179, 8);
  border: 1px solid rgba(234, 179, 8, 0.2);
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.drawer-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.drawer-section {
  margin-bottom: 2rem;
}

.drawer-section h3 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.description {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 1rem;
}

.meta-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.meta-item {
  display: flex;
  gap: 0.5rem;
}

.meta-label {
  font-weight: 600;
  color: var(--text-primary);
  min-width: 80px;
}

.meta-value, .meta-value a {
  color: var(--text-secondary);
}

.meta-value a:hover {
  color: var(--accent-primary);
}

.capabilities-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.capability-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.capability-icon {
  font-size: 1.5rem;
}

.capability-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.capability-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.dependency-group {
  margin-bottom: 1.5rem;
}

.dependency-group h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.75rem;
}

.dependency-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dependency-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.dep-icon {
  color: var(--accent-primary);
}

.dep-name {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
}

.dep-status {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.resource-card {
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  text-align: center;
  border: 1px solid var(--border-color);
}

.resource-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.resource-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.resource-value {
  font-weight: 600;
  color: var(--text-primary);
}

.security-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.info-label {
  font-weight: 600;
  color: var(--text-primary);
}

.info-value {
  color: var(--text-secondary);
}

.info-link {
  color: var(--accent-primary);
  text-decoration: none;
  font-weight: 500;
}

.info-link:hover {
  text-decoration: underline;
}

.drawer-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 0.75rem;
  background: var(--bg-secondary);
  position: sticky;
  bottom: 0;
}

.btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:disabled {
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

/* Transition Animations */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s ease;
}

.drawer-enter-active .drawer-panel,
.drawer-leave-active .drawer-panel {
  transition: transform 0.3s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .drawer-panel,
.drawer-leave-to .drawer-panel {
  transform: translateX(100%);
}
</style>
