<script setup lang="ts">
import { computed, watch, onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'
import AttractModeOverlay from '@/attract/ui/visuals/layers/AttractModeOverlay.vue'
import NetworkStatusBanner from '@/components/NetworkStatusBanner.vue'
import { useAttractModeStore } from '@/stores/attractModeStore'
import { useNetworkStore } from '@/stores/networkStore'
import { useCESMode } from '@/composables/useCESMode'

const attractStore = useAttractModeStore()
const networkStore = useNetworkStore()
const { isCESMode } = useCESMode()

const appClasses = computed(() => ({
  'ces-mode': isCESMode.value
}))

// Hide unified header when showcase mode is active
function toggleUnifiedHeader(hide: boolean) {
  const header = document.querySelector('abs-unified-header') as HTMLElement | null
  if (header) {
    header.style.display = hide ? 'none' : 'block'
  }
}

watch(() => attractStore.isActive, (isActive) => {
  toggleUnifiedHeader(isActive)
})

onMounted(() => {
  // Ensure header is visible on mount
  toggleUnifiedHeader(false)
  
  // Initialize network monitoring
  networkStore.startPeriodicCheck(30000) // Check every 30 seconds
})

onUnmounted(() => {
  // Clean up network monitoring
  networkStore.stopPeriodicCheck()
})
</script>

<template>
  <div id="console-app" :class="appClasses">
    <NetworkStatusBanner />
    <RouterView />
    <Transition name="fade">
      <AttractModeOverlay v-if="attractStore.isActive" />
    </Transition>
  </div>
</template>

<style scoped>
#console-app {
  min-height: 100vh;
  background: var(--abs-black);
}
</style>

