<template>
  <Transition name="slide-down">
    <div v-if="isCESMode" class="ces-mode-banner">
      <div class="ces-mode-banner__content">
        <div class="ces-mode-banner__icon">🔒</div>
        <div class="ces-mode-banner__message">
          <div class="ces-mode-banner__title">CES Demo Mode Active</div>
          <div class="ces-mode-banner__description">
            Admin operations are read-only. Viewing and monitoring enabled; destructive actions disabled for demo safety.
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useCESMode } from '@/composables/useCESMode'

const { isCESMode } = useCESMode()
</script>

<style scoped>
.ces-mode-banner {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.15) 0%, rgba(249, 115, 22, 0.05) 100%);
  border: 1px solid rgba(249, 115, 22, 0.3);
  border-left: 4px solid var(--abs-orange);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
}

.ces-mode-banner__content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.ces-mode-banner__icon {
  font-size: 1.5rem;
  flex-shrink: 0;
  margin-top: 2px;
}

.ces-mode-banner__message {
  flex: 1;
  min-width: 0;
}

.ces-mode-banner__title {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--abs-orange);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.ces-mode-banner__description {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease-out;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>

