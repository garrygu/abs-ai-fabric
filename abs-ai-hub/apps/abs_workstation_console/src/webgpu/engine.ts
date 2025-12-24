/**
 * WebGPU Engine - Core infrastructure for Attract Mode visual fabric
 * 
 * Provides device initialization, buffer management, and render loop orchestration
 */

export interface GPUDeviceContext {
  device: GPUDevice
  context: GPUCanvasContext
  format: GPUTextureFormat
  adapter: GPUAdapter
}

export interface RenderState {
  // Telemetry (normalized 0..1)
  gpuUtil01: number
  vramUtil01: number
  ramUtil01: number
  modelState: 'idle' | 'warming' | 'running' | 'error'
  coldStartProgress01: number
  timeSec: number
  dtSec: number
}

export interface SceneParams {
  sceneId: 'A' | 'B' | 'C' | 'D' | 'E'
  sceneT01: number // 0..1 within scene
  transitionT01: number // 0..1 crossfade
  accent01: number // How "hot" visuals should be
  cameraJitter01: number // Subtle jitter for load events
}

/**
 * Initialize WebGPU device and canvas context
 */
export async function initWebGPU(canvas: HTMLCanvasElement): Promise<GPUDeviceContext> {
  if (!navigator.gpu) {
    throw new Error('WebGPU not supported')
  }

  const adapter = await navigator.gpu.requestAdapter({
    powerPreference: 'high-performance',
    forceFallbackAdapter: false
  })

  if (!adapter) {
    throw new Error('No GPU adapter available')
  }

  const device = await adapter.requestDevice({
    requiredFeatures: [],
    requiredLimits: {
      maxComputeWorkgroupStorageSize: adapter.limits.maxComputeWorkgroupStorageSize,
      maxComputeInvocationsPerWorkgroup: adapter.limits.maxComputeInvocationsPerWorkgroup
    }
  })

  const context = canvas.getContext('webgpu') as GPUCanvasContext | null
  if (!context) {
    throw new Error('Failed to get WebGPU canvas context')
  }

  const format = navigator.gpu.getPreferredCanvasFormat()

  context.configure({
    device,
    format,
    alphaMode: 'premultiplied',
    usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.COPY_SRC
  })

  return { device, context, format, adapter }
}

/**
 * Create uniform buffer for render state and scene params
 */
export function createUniformBuffer(device: GPUDevice, size: number): GPUBuffer {
  return device.createBuffer({
    size: size,
    usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
    mappedAtCreation: false
  })
}

/**
 * Uniform buffer layout matching WGSL struct
 * struct Uniforms {
 *   timeSec: f32,        // 0
 *   dtSec: f32,          // 1
 *   gpuUtil01: f32,      // 2
 *   vramUtil01: f32,     // 3
 *   sceneId: u32,        // 4
 *   sceneT01: f32,       // 5
 *   transitionT01: f32,  // 6
 *   accent01: f32,       // 7
 *   viewport: vec2<f32>, // 8, 9
 *   center: vec2<f32>,   // 10, 11
 * };
 */
export function updateUniformBuffer(
  device: GPUDevice,
  buffer: GPUBuffer,
  renderState: RenderState,
  sceneParams: SceneParams,
  viewport: [number, number],
  center: [number, number] = [0, 0]
) {
  const data = new Float32Array(12)
  data[0] = renderState.timeSec
  data[1] = renderState.dtSec
  data[2] = renderState.gpuUtil01
  data[3] = renderState.vramUtil01
  data[4] = sceneParams.sceneId === 'A' ? 0 : sceneParams.sceneId === 'B' ? 1 : sceneParams.sceneId === 'C' ? 2 : sceneParams.sceneId === 'D' ? 3 : 4
  data[5] = sceneParams.sceneT01
  data[6] = sceneParams.transitionT01
  data[7] = sceneParams.accent01
  data[8] = viewport[0]
  data[9] = viewport[1]
  data[10] = center[0]
  data[11] = center[1]

  device.queue.writeBuffer(buffer, 0, data)
}

/**
 * Particle data structure (32 bytes per particle)
 */
export interface ParticleData {
  pos: [number, number]      // vec2<f32> - 8 bytes
  vel: [number, number]      // vec2<f32> - 8 bytes
  life: number               // f32 - 4 bytes
  seed: number               // f32 - 4 bytes
  size: number               // f32 - 4 bytes
  _pad: number               // f32 - 4 bytes (alignment)
}

/**
 * Create storage buffer for particles (ping-pong pattern)
 * Particle layout: pos(vec2), vel(vec2), life(f32), seed(f32), size(f32), pad(f32)
 */
export function createParticleBuffers(
  device: GPUDevice,
  particleCount: number
): { bufferA: GPUBuffer; bufferB: GPUBuffer } {
  // Each particle: 6 floats * 4 bytes = 24 bytes (but WGSL struct aligns to 32 bytes)
  const stride = 32 // 8 floats aligned to 32 bytes
  const size = particleCount * stride

  const bufferA = device.createBuffer({
    size,
    usage: GPUBufferUsage.STORAGE | GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST
  })

  const bufferB = device.createBuffer({
    size,
    usage: GPUBufferUsage.STORAGE | GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST
  })

  return { bufferA, bufferB }
}

/**
 * Initialize particle buffer with random data
 */
export function initializeParticles(
  device: GPUDevice,
  buffer: GPUBuffer,
  particleCount: number,
  viewport: [number, number]
): void {
  const stride = 32
  const data = new Float32Array(particleCount * 8) // 8 floats per particle

  for (let i = 0; i < particleCount; i++) {
    const base = i * 8
    const seed = Math.random()
    
    // pos
    data[base + 0] = Math.random() * viewport[0]
    data[base + 1] = Math.random() * viewport[1]
    
    // vel
    data[base + 2] = (Math.random() - 0.5) * 0.5
    data[base + 3] = (Math.random() - 0.5) * 0.5
    
    // life
    data[base + 4] = Math.random()
    
    // seed
    data[base + 5] = seed
    
    // size
    data[base + 6] = 1.0 + Math.random() * 1.5
    
    // pad
    data[base + 7] = 0.0
  }

  device.queue.writeBuffer(buffer, 0, data)
}

/**
 * Create flow field texture (2D velocity vectors)
 */
export function createFlowFieldTexture(
  device: GPUDevice,
  width: number,
  height: number
): GPUTexture {
  return device.createTexture({
    size: [width, height],
    format: 'rg16float', // 2D velocity vectors
    usage: GPUTextureUsage.TEXTURE_BINDING | GPUTextureUsage.STORAGE_BINDING | GPUTextureUsage.COPY_DST
  })
}

/**
 * Create offscreen render targets for post-processing
 */
export function createRenderTargets(
  device: GPUDevice,
  width: number,
  height: number
): {
  sceneColor: GPUTexture
  brightPass: GPUTexture
  blur1: GPUTexture
  blur2: GPUTexture
} {
  const format: GPUTextureFormat = 'rgba16float' // HDR-capable

  const sceneColor = device.createTexture({
    size: [width, height],
    format,
    usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING
  })

  const brightPass = device.createTexture({
    size: [width, height],
    format,
    usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING
  })

  // Bloom blur targets (half-res for performance)
  const blurWidth = Math.floor(width / 2)
  const blurHeight = Math.floor(height / 2)

  const blur1 = device.createTexture({
    size: [blurWidth, blurHeight],
    format,
    usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING
  })

  const blur2 = device.createTexture({
    size: [blurWidth, blurHeight],
    format,
    usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING
  })

  return { sceneColor, brightPass, blur1, blur2 }
}

/**
 * Check WebGPU availability
 */
export function isWebGPUSupported(): boolean {
  return typeof navigator !== 'undefined' && 'gpu' in navigator
}

