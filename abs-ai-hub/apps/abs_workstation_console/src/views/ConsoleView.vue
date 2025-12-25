<script setup lang="ts">
import { onMounted, onUnmounted, provide, watch, computed } from 'vue'
import PageNavigation from '@/components/navigation/PageNavigation.vue'
import Page1Overview from '@/pages/Page1Overview.vue'
import Page2Performance from '@/pages/Page2Performance.vue'
import Page3Workloads from '@/pages/Page3Workloads.vue'
import Page4Models from '@/pages/Page4Models.vue'
import Page5Explore from '@/pages/Page5Explore.vue'
import Page6ModelOrchestration from '@/pages/Page6ModelOrchestration.vue'
import { usePageNavigation } from '@/navigation/usePageNavigation'
import { useMetricsStore } from '@/stores/metricsStore'
import { useWorkloadsStore } from '@/stores/workloadsStore'
import { useModelsStore } from '@/stores/modelsStore'
import { useAttractModeStore } from '@/stores/attractModeStore'
import { useAllInOneDemoStore } from '@/stores/allInOneDemoStore'
import { useCESMode } from '@/composables/useCESMode'
import AllInOneTagline from '@/components/common/AllInOneTagline.vue'
import AllInOneDemoOverlay from '@/components/demo/AllInOneDemoOverlay.vue'
import DemoControlPanel from '@/components/demo/DemoControlPanel.vue'
import GuidedPromptKiosk from '@/components/demo/GuidedPromptKiosk.vue'
import DualModelOutput from '@/components/demo/DualModelOutput.vue'
import { useDemoControlStore } from '@/stores/demoControlStore'

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
const allInOneDemoStore = useAllInOneDemoStore()
const demoControlStore = useDemoControlStore()
const { isCESMode } = useCESMode()

// Show demo control panel on Performance, Orchestration, and Models pages
const showDemoControl = computed(() => {
  const demoPages = [1, 3, 4] // Performance (1), Models (3), Orchestration (4)
  return demoPages.includes(currentIndex.value)
})

// Provide navigation to child components if needed
provide('pageNavigation', { currentIndex, goToPage, goNext, goPrev })

function triggerAttractMode() {
  attractStore.activate()
}

function toggleAllInOneDemo(event?: Event) {
  if (event) {
    event.stopPropagation()
    event.preventDefault()
  }
  
  console.log('[ConsoleView] Toggle clicked, current state:', {
    isActive: allInOneDemoStore.isActive,
    isEnabled: allInOneDemoStore.isEnabled
  })
  
  if (allInOneDemoStore.isActive) {
    console.log('[ConsoleView] Deactivating demo...')
    allInOneDemoStore.deactivate()
  } else {
    console.log('[ConsoleView] Activating demo...')
    // Temporarily disable activity detection to prevent immediate stop
    const wasEnabled = allInOneDemoStore.isEnabled
    allInOneDemoStore.isEnabled = true
    allInOneDemoStore.activate()
    console.log('[ConsoleView] Starting demo sequence...')
    allInOneDemoStore.startDemo(goToPage)
    console.log('[ConsoleView] Demo started, isActive:', allInOneDemoStore.isActive)
    
    // Re-enable after a short delay
    setTimeout(() => {
      allInOneDemoStore.isEnabled = wasEnabled
    }, 1000)
  }
}

function recordActivity(event?: Event) {
  // Don't record activity if clicking the guided tour or showcase mode buttons
  if (event && (event.target as HTMLElement)?.closest('.indicator--guided-tour, .indicator--attract-mode')) {
    return
  }
  allInOneDemoStore.recordActivity()
  attractStore.recordActivity()
}

function handleNavigateToPage(e: Event) {
  const pageIndex = (e as CustomEvent).detail
  if (typeof pageIndex === 'number') {
    goToPage(pageIndex)
  }
}

// Watch for manual navigation - stop demo if user navigates manually
watch(currentIndex, (newIndex, oldIndex) => {
  console.log('[ConsoleView] Page changed:', {
    newIndex,
    oldIndex,
    isActive: allInOneDemoStore.isActive,
    isProgrammatic: allInOneDemoStore.isProgrammaticNavigation(),
    expectedIndex: allInOneDemoStore.getCurrentPageIndex()
  })
  
  if (allInOneDemoStore.isActive && !allInOneDemoStore.isProgrammaticNavigation()) {
    const expectedIndex = allInOneDemoStore.getCurrentPageIndex()
    // If user navigated to a different page than expected, stop demo
    if (newIndex !== expectedIndex && oldIndex !== undefined) {
      console.log('[ConsoleView] Manual navigation detected, stopping demo')
      allInOneDemoStore.deactivate()
    } else {
      console.log('[ConsoleView] Navigation matches expected, allowing demo to continue')
    }
  } else if (allInOneDemoStore.isActive && allInOneDemoStore.isProgrammaticNavigation()) {
    console.log('[ConsoleView] Programmatic navigation, ignoring')
  }
})

onMounted(() => {
  metricsStore.startPolling(2000)
  workloadsStore.fetchWorkloads()
  modelsStore.fetchModels()
  attractStore.startIdleDetection()
  window.addEventListener('navigate-to-page', handleNavigateToPage)
  
  // Set up activity detection for All-In-One Demo
  const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'wheel', 'click']
  events.forEach(eventName => {
    window.addEventListener(eventName, (e) => recordActivity(e), { passive: true })
  })
  
  // Enable All-In-One Demo (always enabled for CES app)
  allInOneDemoStore.isEnabled = true
})

onUnmounted(() => {
  metricsStore.stopPolling()
  attractStore.stopIdleDetection()
  allInOneDemoStore.stopDemo()
  window.removeEventListener('navigate-to-page', handleNavigateToPage)
  
  // Remove activity detection listeners
  const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'wheel', 'click']
  events.forEach(event => {
    window.removeEventListener(event, recordActivity)
  })
})

const pageComponents = [
  Page1Overview,
  Page2Performance,
  Page3Workloads,
  Page4Models,
  Page6ModelOrchestration,
  Page5Explore
]
</script>

<template>
  <div class="console-view">

    <!-- Page Navigation (hidden in attract mode) -->
    <PageNavigation
      v-if="!attractStore.isActive"
      :current-index="currentIndex"
      :current-page="currentPage"
      :can-go-prev="canGoPrev"
      :can-go-next="canGoNext"
      @prev="goPrev"
      @next="goNext"
      @go-to="goToPage"
      @toggle-guided-tour="toggleAllInOneDemo"
      @trigger-attract-mode="triggerAttractMode"
    />

    <!-- Page Content with Transitions -->
    <main class="page-container">
      <Transition :name="transitionDirection === 'right' ? 'slide-left' : 'slide-right'" mode="out-in">
        <component :is="pageComponents[currentIndex]" :key="currentIndex" />
      </Transition>
    </main>
    
    <!-- All-In-One Tagline (CES Only, hidden in attract mode) -->
    <AllInOneTagline v-if="!attractStore.isActive" />
    
    <!-- All-In-One Demo Overlay (shows step info and progress, hidden in attract mode) -->
    <AllInOneDemoOverlay v-if="!attractStore.isActive" />
    
    <!-- Demo Control Panel (on Performance, Models, Orchestration pages, hidden in attract mode) -->
    <DemoControlPanel v-if="showDemoControl && !attractStore.isActive" />
    
    <!-- Guided Prompt Kiosk (appears when demo is active, hidden in attract mode) -->
    <GuidedPromptKiosk v-if="!attractStore.isActive" />
    
    <!-- Dual Model Output Display (for "Decide + Explain" flow, hidden in attract mode) -->
    <DualModelOutput v-if="!attractStore.isActive" />
  </div>
</template>

<style scoped>
.console-view {
  min-height: 100vh;
  background: var(--abs-black);
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
