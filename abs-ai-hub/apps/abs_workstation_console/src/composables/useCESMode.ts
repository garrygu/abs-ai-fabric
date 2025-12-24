import { ref, computed } from 'vue'

// CES Mode composable - reads from build-time flag
declare const __CES_MODE__: boolean

export function useCESMode() {
    // Default to true (CES app) - can be overridden by build-time flag
    // Try to read the build-time constant, with fallback to true
    let cesModeValue = true
    try {
        // @ts-ignore - __CES_MODE__ is defined at build time by Vite
        if (typeof __CES_MODE__ !== 'undefined') {
            // @ts-ignore
            cesModeValue = __CES_MODE__
        }
    } catch (e) {
        // If not defined, default to true
        cesModeValue = true
    }
    
    const isCESMode = ref(cesModeValue)
    
    // Debug log
    console.log('[CESMode] Initialized:', { isCESMode: isCESMode.value, __CES_MODE__: typeof __CES_MODE__ !== 'undefined' ? __CES_MODE__ : 'undefined' })

    // CES-specific text overlays
    const cesOverlayText = computed(() =>
        isCESMode.value ? 'LIVE AI • NO CLOUD • RTX PRO 6000' : ''
    )

    // CES-specific font scale
    const fontScale = computed(() => isCESMode.value ? 1.15 : 1)

    // Toggle for development/testing
    function toggleCESMode() {
        isCESMode.value = !isCESMode.value
    }

    return {
        isCESMode,
        cesOverlayText,
        fontScale,
        toggleCESMode
    }
}
