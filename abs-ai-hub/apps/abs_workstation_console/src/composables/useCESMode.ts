import { ref, computed } from 'vue'

// CES Mode composable - reads from build-time flag
declare const __CES_MODE__: boolean

export function useCESMode() {
    // Default to false if not defined
    const isCESMode = ref(typeof __CES_MODE__ !== 'undefined' ? __CES_MODE__ : false)

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
