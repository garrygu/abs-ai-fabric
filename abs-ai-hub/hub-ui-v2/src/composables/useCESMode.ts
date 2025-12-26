/**
 * useCESMode.ts
 * 
 * Provides reactive access to CES mode configuration for hub-ui-v2.
 * CES mode can be enabled via environment variable or runtime config.
 */

import { ref } from 'vue'

// Build-time constant injected by Vite (if defined)
declare const __CES_MODE__: boolean | undefined

/**
 * Reads the CES mode flag from build-time constant or environment
 * Defaults to false if not defined
 */
function getCESModeFlag(): boolean {
  // Priority 1: Check runtime environment variable (for development/testing)
  // This takes precedence so .env changes work without rebuild
  const envValue = import.meta.env.VITE_CES_MODE
  if (envValue === 'true' || envValue === '1' || envValue === true) {
    return true
  }
  
  // Priority 2: Check build-time constant (for production builds)
  try {
    // @ts-ignore - __CES_MODE__ is defined at build time by Vite
    if (typeof __CES_MODE__ !== 'undefined') {
      // @ts-ignore
      const buildTimeValue = __CES_MODE__
      if (buildTimeValue === true || String(buildTimeValue) === 'true') {
        return true
      }
    }
  } catch (e) {
    // If not defined, continue to default
  }
  
  return false
}

export function useCESMode() {
  // Initialize reactive flag
  const flagValue = getCESModeFlag()
  const isCESMode = ref(flagValue)
  
  // Debug log (only in development, can be removed in production)
  if (import.meta.env.DEV && import.meta.env.VITE_DEBUG_CES_MODE === 'true') {
    const envValue = import.meta.env.VITE_CES_MODE
    console.log('[CESMode] Composable initialized:', { 
      isCESMode: isCESMode.value,
      viteEnvValue: envValue
    })
  }

  return {
    isCESMode
  }
}

