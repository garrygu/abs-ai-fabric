<script setup lang="ts">
import { computed, watch, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AttractModeOverlay from '@/components/attract/AttractModeOverlay.vue'
import { useAttractModeStore } from '@/stores/attractModeStore'
import { useCESMode } from '@/composables/useCESMode'

const attractStore = useAttractModeStore()
const { isCESMode } = useCESMode()

const appClasses = computed(() => ({
  'ces-mode': isCESMode.value
}))

// Hide unified header when attract mode is active
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
})
</script>

<template>
  <div id="console-app" :class="appClasses">
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

