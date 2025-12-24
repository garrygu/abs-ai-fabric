<script setup lang="ts">
import { onMounted, onUnmounted, provide, watch, computed } from 'vue'
import PageNavigation from '@/components/navigation/PageNavigation.vue'
import Page1Overview from '@/pages/Page1Overview.vue'
import Page2Performance from '@/pages/Page2Performance.vue'
import Page3Workloads from '@/pages/Page3Workloads.vue'
import Page4Models from '@/pages/Page4Models.vue'
import Page5Explore from '@/pages/Page5Explore.vue'
import Page6ModelOrchestration from '@/pages/Page6ModelOrchestration.vue'
import { usePageNavigation } from '@/composables/usePageNavigation'
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
  // Don't record activity if clicking the guided tour button
  if (event && (event.target as HTMLElement)?.closest('.indicator--guided-tour')) {
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
  Page5Explore,
  Page6ModelOrchestration
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
      @toggle-guided-tour="toggleAllInOneDemo"
    />

    <!-- Page Content with Transitions -->
    <main class="page-container">
      <Transition :name="transitionDirection === 'right' ? 'slide-left' : 'slide-right'" mode="out-in">
        <component :is="pageComponents[currentIndex]" :key="currentIndex" />
      </Transition>
    </main>
    
    <!-- All-In-One Tagline (CES Only) -->
    <AllInOneTagline />
    
    <!-- All-In-One Demo Overlay (shows step info and progress) -->
    <AllInOneDemoOverlay />
    
    <!-- Demo Control Panel (on Performance, Models, Orchestration pages) -->
    <DemoControlPanel v-if="showDemoControl" />
    
    <!-- Guided Prompt Kiosk (appears when demo is active) -->
    <GuidedPromptKiosk />
    
    <!-- Dual Model Output Display (for "Decide + Explain" flow) -->
    <DualModelOutput />
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
