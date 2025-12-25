/**
 * CES Configuration
 * 
 * Build-time feature flag and CES-specific configuration values.
 * Flags are injected at build time via Vite's `define` option.
 * 
 * Usage:
 *   CES_MODE=true npm run build  // Enable CES mode
 *   CES_MODE=false npm run build // Disable CES mode (default: true)
 */

// Build-time constant injected by Vite
declare const __CES_MODE__: boolean

/**
 * Reads the CES mode flag from build-time constant
 * Defaults to true if not defined (CES app is the default)
 */
export function getCESModeFlag(): boolean {
  try {
    // @ts-ignore - __CES_MODE__ is defined at build time by Vite
    if (typeof __CES_MODE__ !== 'undefined') {
      // @ts-ignore
      return __CES_MODE__
    }
  } catch (e) {
    // If not defined, default to true (CES app)
  }
  return true
}

/**
 * CES-specific configuration values
 */
export const cesConfig = {
  overlayText: 'LIVE AI • NO CLOUD • RTX PRO 6000',
  fontScale: 1.15,
} as const

/**
 * Default (non-CES) configuration values
 */
export const defaultConfig = {
  overlayText: '',
  fontScale: 1,
} as const

