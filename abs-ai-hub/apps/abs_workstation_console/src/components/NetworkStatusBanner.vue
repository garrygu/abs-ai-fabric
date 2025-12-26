<template>
  <Transition name="slide-down">
    <div v-if="networkStore.showOfflineBanner && networkStore.statusMessage" 
         class="network-status-banner"
         :class="{
           'network-status-banner--critical': !networkStore.isPartiallyOnline,
           'network-status-banner--warning': networkStore.isPartiallyOnline
         }">
      <div class="network-status-banner__content">
        <div class="network-status-banner__icon">
          <svg v-if="!networkStore.isPartiallyOnline" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        
        <div class="network-status-banner__message">
          <div class="network-status-banner__title">
            {{ !networkStore.isPartiallyOnline ? 'Services Unavailable' : 'Limited Connectivity' }}
          </div>
          <div class="network-status-banner__details">
            {{ networkStore.statusMessage }}
          </div>
          <div v-if="networkStore.lastChecked" class="network-status-banner__timestamp">
            Last checked: {{ formatTime(networkStore.lastChecked) }}
          </div>
        </div>
        
        <div class="network-status-banner__actions">
          <button 
            @click="retryConnection" 
            class="network-status-banner__retry"
            :disabled="isRetrying">
            <svg v-if="!isRetrying" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            <span v-else class="network-status-banner__spinner"></span>
            {{ isRetrying ? 'Checking...' : 'Retry' }}
          </button>
          
          <button 
            @click="networkStore.dismissBanner" 
            class="network-status-banner__dismiss"
            aria-label="Dismiss">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Service status indicators -->
      <div class="network-status-banner__services">
        <div class="network-status-banner__service" 
             :class="{ 'network-status-banner__service--online': networkStore.hasInternet }">
          <span class="network-status-banner__service-dot"></span>
          <span>Internet</span>
        </div>
        <div class="network-status-banner__service" 
             :class="{ 'network-status-banner__service--online': networkStore.hasGateway }">
          <span class="network-status-banner__service-dot"></span>
          <span>Gateway</span>
        </div>
        <div class="network-status-banner__service" 
             :class="{ 'network-status-banner__service--online': networkStore.hasOllama }">
          <span class="network-status-banner__service-dot"></span>
          <span>Ollama</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useNetworkStore } from '@/stores/networkStore'

const networkStore = useNetworkStore()
const isRetrying = ref(false)

function formatTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHour = Math.floor(diffMin / 60)
  return `${diffHour}h ago`
}

async function retryConnection() {
  isRetrying.value = true
  try {
    await networkStore.checkAllServices()
  } finally {
    isRetrying.value = false
  }
}
</script>

<style scoped>
.network-status-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  background: rgba(17, 24, 39, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 2px solid var(--abs-orange);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.network-status-banner--critical {
  border-bottom-color: #ef4444;
}

.network-status-banner--warning {
  border-bottom-color: #f59e0b;
}

.network-status-banner__content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.network-status-banner__icon {
  flex-shrink: 0;
  color: var(--abs-orange);
}

.network-status-banner--critical .network-status-banner__icon {
  color: #ef4444;
}

.network-status-banner--warning .network-status-banner__icon {
  color: #f59e0b;
}

.network-status-banner__message {
  flex: 1;
  min-width: 0;
}

.network-status-banner__title {
  font-weight: 600;
  font-size: 0.875rem;
  color: #ffffff;
  margin-bottom: 4px;
}

.network-status-banner__details {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.4;
}

.network-status-banner__timestamp {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.network-status-banner__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.network-status-banner__retry {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.3);
  border-radius: 6px;
  color: var(--abs-orange);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.network-status-banner__retry:hover:not(:disabled) {
  background: rgba(249, 115, 22, 0.2);
  border-color: rgba(249, 115, 22, 0.5);
}

.network-status-banner__retry:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.network-status-banner__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(249, 115, 22, 0.3);
  border-top-color: var(--abs-orange);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.network-status-banner__dismiss {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}

.network-status-banner__dismiss:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
}

.network-status-banner__services {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 24px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  max-width: 1400px;
  margin: 0 auto;
}

.network-status-banner__service {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.network-status-banner__service-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.6);
  box-shadow: 0 0 4px rgba(239, 68, 68, 0.4);
}

.network-status-banner__service--online .network-status-banner__service-dot {
  background: rgba(34, 197, 94, 0.8);
  box-shadow: 0 0 4px rgba(34, 197, 94, 0.4);
}

.network-status-banner__service--online {
  color: rgba(255, 255, 255, 0.8);
}

/* Slide down animation */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease-out;
}

.slide-down-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>

