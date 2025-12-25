<script setup lang="ts">
import { PAGES, type PageConfig } from '@/navigation/usePageNavigation'
import { useAllInOneDemoStore } from '@/stores/allInOneDemoStore'
import { useAttractModeStore } from '@/stores/attractModeStore'

const allInOneDemoStore = useAllInOneDemoStore()
const attractStore = useAttractModeStore()

defineProps<{
  currentIndex: number
  canGoPrev: boolean
  canGoNext: boolean
  currentPage: PageConfig
}>()

const emit = defineEmits<{
  prev: []
  next: []
  goTo: [index: number]
  toggleGuidedTour: []
  triggerAttractMode: []
}>()

function toggleGuidedTour(event: Event) {
  event.stopPropagation()
  emit('toggleGuidedTour')
}

function triggerAttractMode(event: Event) {
  event.stopPropagation()
  emit('triggerAttractMode')
}
</script>

<template>
  <nav class="page-navigation">
    <div class="nav-controls">
      <!-- Previous Button -->
      <button 
        class="nav-btn nav-btn--prev"
        :disabled="!canGoPrev"
        @click="emit('prev')"
      >
        <span class="nav-arrow">←</span>
        <span class="nav-label">Prev</span>
      </button>

      <!-- Page Title -->
      <div class="nav-center">
        <h1 class="page-title">{{ currentPage.title }}</h1>
      </div>

      <!-- Next Button -->
      <button 
        class="nav-btn nav-btn--next"
        :disabled="!canGoNext"
        @click="emit('next')"
      >
        <span class="nav-label">Next</span>
        <span class="nav-arrow">→</span>
      </button>
    </div>

    <!-- Page Indicator Dots -->
    <div class="page-indicators">
      <button
        v-for="(page, index) in PAGES"
        :key="page.id"
        class="indicator"
        :class="{ 'indicator--active': index === currentIndex }"
        :title="page.title"
        @click="emit('goTo', index)"
      >
        <span class="indicator-label">{{ page.shortTitle }}</span>
      </button>
      
      <!-- Guided Tour Toggle -->
      <button
        class="indicator indicator--guided-tour"
        :class="{ 'indicator--active': allInOneDemoStore.isActive }"
        :title="allInOneDemoStore.isActive ? 'Deactivate Guided Tour' : 'Activate Guided Tour'"
        @click="toggleGuidedTour"
      >
        <span class="indicator-label">Guided Tour</span>
        <span v-if="allInOneDemoStore.isActive" class="guided-tour-status">Activated</span>
      </button>
      
      <!-- Showcase Mode Toggle -->
      <button
        class="indicator indicator--attract-mode"
        :class="{ 'indicator--active': attractStore.isActive }"
        :title="attractStore.isActive ? 'Deactivate Showcase Mode' : 'Activate Showcase Mode'"
        @click="triggerAttractMode"
      >
        <span class="indicator-label">Showcase Mode</span>
        <span v-if="attractStore.isActive" class="attract-mode-status">Active</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.page-navigation {
  position: sticky;
  top: 0;
  z-index: 50;
  background: linear-gradient(to bottom, var(--abs-dark) 0%, rgba(15, 15, 24, 0.95) 100%);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-subtle);
  padding: 16px 24px 12px;
}

.nav-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: var(--container-max);
  margin: 0 auto;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
  min-width: 100px;
}

.nav-btn:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.2);
  border-color: var(--electric-indigo);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-arrow {
  font-size: 1.25rem;
}

.nav-btn--prev .nav-label {
  margin-left: 4px;
}

.nav-btn--next .nav-label {
  margin-right: 4px;
}

.nav-center {
  flex: 1;
  text-align: center;
}

.page-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.page-indicators {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
}

.indicator {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 16px;
  color: var(--text-muted);
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.indicator:hover {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
}

.indicator--active {
  color: var(--electric-indigo);
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
}

.indicator--active::before {
  content: '●';
  margin-right: 4px;
}

.indicator:not(.indicator--active)::before {
  content: '○';
  margin-right: 4px;
}

.indicator--guided-tour {
  margin-left: 16px;
  padding-left: 16px;
  border-left: 1px solid var(--border-subtle);
  position: relative;
}

.indicator--guided-tour .indicator-label {
  margin-right: 8px;
}

.guided-tour-status {
  font-size: 0.65rem;
  color: var(--abs-orange);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.indicator--guided-tour.indicator--active {
  background: rgba(255, 107, 0, 0.15);
  border-color: rgba(255, 107, 0, 0.3);
  color: var(--abs-orange);
}

.indicator--guided-tour.indicator--active::before {
  content: '●';
  color: var(--abs-orange);
}

.indicator--attract-mode {
  margin-left: 16px;
  padding-left: 16px;
  border-left: 1px solid var(--border-subtle);
  position: relative;
}

.indicator--attract-mode .indicator-label {
  margin-right: 8px;
}

.attract-mode-status {
  font-size: 0.65rem;
  color: var(--electric-indigo);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.indicator--attract-mode.indicator--active {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
  color: var(--electric-indigo);
}

.indicator--attract-mode.indicator--active::before {
  content: '●';
  color: var(--electric-indigo);
}
</style>
