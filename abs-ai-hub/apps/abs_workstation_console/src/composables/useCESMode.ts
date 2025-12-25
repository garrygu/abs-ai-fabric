/**
 * useCESMode.ts
 * 
 * Small reactive hook for CES configuration.
 * 
 * Provides reactive access to CES feature flag and computed config values.
 * The actual config is defined in src/config/ces.ts
 */

import { ref, computed } from 'vue'
import { getCESModeFlag, cesConfig, defaultConfig } from '@/config/ces'

export function useCESMode() {
  // Initialize reactive flag from build-time config
  const isCESMode = ref(getCESModeFlag())
  
  // Debug log (only in development)
  if (import.meta.env.DEV) {
    console.log('[CESMode] Initialized:', { 
      isCESMode: isCESMode.value,
      buildTimeFlag: getCESModeFlag()
    })
  }

  // CES-specific computed values
  const cesOverlayText = computed(() =>
    isCESMode.value ? cesConfig.overlayText : defaultConfig.overlayText
  )

  const fontScale = computed(() => 
    isCESMode.value ? cesConfig.fontScale : defaultConfig.fontScale
  )

  // Toggle for development/testing (runtime override)
  function toggleCESMode() {
    isCESMode.value = !isCESMode.value
    if (import.meta.env.DEV) {
      console.log('[CESMode] CES Mode toggled:', isCESMode.value)
    }
  }

  return {
    isCESMode,
    cesOverlayText,
    fontScale,
    toggleCESMode
  }
}
