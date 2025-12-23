<script setup lang="ts">
import { useCESMode } from '@/composables/useCESMode'

const { isCESMode } = useCESMode()
</script>

<template>
  <div class="branding-layer">
    <div class="brand-content">
      <div class="live-badge">
        <span class="live-dot"></span>
        <span class="live-text">LIVE LOCAL AI</span>
      </div>
      
      <p class="brand-tagline">LIVE • LOCAL • ENTERPRISE</p>
      
      <div class="brand-logo">
        <svg width="100" height="24" viewBox="0 0 100 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="24" height="24" rx="4" fill="url(#abs-brand-gradient)"/>
          <path d="M6 17L12 7L18 17H6Z" fill="white" fill-opacity="0.9"/>
          <text x="32" y="17" fill="white" fill-opacity="0.6" font-family="Barlow Condensed, sans-serif" font-size="14" font-weight="600" letter-spacing="0.1em">ABS</text>
          <defs>
            <linearGradient id="abs-brand-gradient" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
              <stop stop-color="#6366f1"/>
              <stop offset="1" stop-color="#4f46e5"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      
      <p class="powered-by">Powered by ABS Workstation</p>
    </div>
  </div>
</template>

<style scoped>
.branding-layer {
  text-align: right;
}

.brand-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-success);
  box-shadow: 0 0 10px var(--status-success);
  animation: pulse 2s ease-in-out infinite;
}

.live-text {
  font-family: var(--font-display);
  font-size: 0.8125rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--status-success);
}

.brand-tagline {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--text-muted);
  margin: 0;
  opacity: 0.7;
}

.brand-logo {
  margin: 8px 0;
}

.powered-by {
  font-family: var(--font-label);
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
  opacity: 0.5;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
