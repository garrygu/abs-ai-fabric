<script setup lang="ts">
import { onMounted, onUnmounted, provide } from 'vue'
import PageNavigation from '@/components/navigation/PageNavigation.vue'
import Page1Overview from '@/pages/Page1Overview.vue'
import Page2Performance from '@/pages/Page2Performance.vue'
import Page3Workloads from '@/pages/Page3Workloads.vue'
import Page4Models from '@/pages/Page4Models.vue'
import Page5Explore from '@/pages/Page5Explore.vue'
import { usePageNavigation } from '@/composables/usePageNavigation'
import { useMetricsStore } from '@/stores/metricsStore'
import { useWorkloadsStore } from '@/stores/workloadsStore'
import { useModelsStore } from '@/stores/modelsStore'
import { useAttractModeStore } from '@/stores/attractModeStore'

const {
  currentIndex,
  currentPage,
  canGoNext,
  canGoPrev,
  transitionDirection,
  goToPage,
  goNext,
  goPrev
} = usePageNavigation()

const metricsStore = useMetricsStore()
const workloadsStore = useWorkloadsStore()
const modelsStore = useModelsStore()
const attractStore = useAttractModeStore()

// Provide navigation to child components if needed
provide('pageNavigation', { currentIndex, goToPage, goNext, goPrev })

function triggerAttractMode() {
  attractStore.activate()
}

function handleNavigateToPage(e: Event) {
  const pageIndex = (e as CustomEvent).detail
  if (typeof pageIndex === 'number') {
    goToPage(pageIndex)
  }
}

onMounted(() => {
  metricsStore.startPolling(2000)
  workloadsStore.fetchWorkloads()
  modelsStore.fetchModels()
  attractStore.startIdleDetection()
  window.addEventListener('navigate-to-page', handleNavigateToPage)
})

onUnmounted(() => {
  metricsStore.stopPolling()
  attractStore.stopIdleDetection()
  window.removeEventListener('navigate-to-page', handleNavigateToPage)
})

const pageComponents = [
  Page1Overview,
  Page2Performance,
  Page3Workloads,
  Page4Models,
  Page5Explore
]
</script>

<template>
  <div class="console-view">
    <!-- Demo Mode Trigger -->
    <button class="demo-trigger" @click="triggerAttractMode" title="Launch Demo Mode">
      ✨ Demo
    </button>

    <!-- Page Navigation -->
    <PageNavigation
      :current-index="currentIndex"
      :current-page="currentPage"
      :can-go-prev="canGoPrev"
      :can-go-next="canGoNext"
      @prev="goPrev"
      @next="goNext"
      @go-to="goToPage"
    />

    <!-- Page Content with Transitions -->
    <main class="page-container">
      <Transition :name="transitionDirection === 'right' ? 'slide-left' : 'slide-right'" mode="out-in">
        <component :is="pageComponents[currentIndex]" :key="currentIndex" />
      </Transition>
    </main>
  </div>
</template>

<style scoped>
.console-view {
  min-height: 100vh;
  background: var(--abs-black);
}

.demo-trigger {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--electric-indigo), #4f46e5);
  border: none;
  border-radius: 24px;
  color: white;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-md), var(--shadow-glow-indigo);
  transition: all var(--duration-normal) var(--ease-smooth);
}

.demo-trigger:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg), 0 0 30px var(--electric-indigo-glow);
}

.page-container {
  min-height: calc(100vh - 120px);
  overflow: hidden;
}

/* Page Transitions */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease-out;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
