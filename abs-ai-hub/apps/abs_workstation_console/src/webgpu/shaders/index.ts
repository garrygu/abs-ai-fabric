/**
 * WebGPU Shaders Index
 * 
 * Exports all shader source strings for the Attract Mode visual fabric.
 * Shaders are imported from .wgsl files and re-exported.
 * 
 * Note: Vite's ?raw import requires the vite-plugin-raw or similar setup.
 * For now, we re-export from the original shaders.ts for compatibility.
 */

// Import shader sources
// When your build supports ?raw imports, use:
// import particleIntegrateWGSL from './particles/integrate.wgsl?raw'
// import particleRenderWGSL from './particles/render.wgsl?raw'
// etc.

// For now, re-export the original shaders for backward compatibility
export {
    particleComputeShader,
    flowFieldComputeShader,
    particleRenderShader,
    bloomBrightPassShader,
    bloomBlurShader,
    bloomCompositeShader,
    tonemapGrainShader
} from '../shaders'

// Future: When ?raw imports work, replace with:
/*
export const particleComputeShader = particleIntegrateWGSL
export const particleRenderShader = particleRenderWGSL
export const bloomBrightPassShader = bloomThresholdWGSL
export const bloomBlurShader = blurWGSL
export const bloomCompositeShader = compositeWGSL
export const tonemapGrainShader = tonemapWGSL
*/
