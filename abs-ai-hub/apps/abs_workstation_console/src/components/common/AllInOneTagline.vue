<script setup lang="ts">
import { useCESMode } from '@/composables/useCESMode'

const { isCESMode } = useCESMode()
</script>

<template>
  <div v-if="isCESMode" class="all-in-one-tagline">
    One PC. Multiple AI minds. Zero cloud dependency.
  </div>
</template>

<style scoped>
.all-in-one-tagline {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  opacity: 0.7;
  pointer-events: none;
  text-align: center;
  padding: 8px 16px;
  background: rgba(15, 15, 24, 0.6);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
</style>

