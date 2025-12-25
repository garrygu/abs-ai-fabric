/**
 * WebGPU Renderer - Full implementation with compute and render pipelines
 * 
 * Implements particle system, bloom, and post-processing
 */

import { GPUDeviceContext, RenderState, SceneParams, createUniformBuffer, createParticleBuffers, createFlowFieldTexture, createRenderTargets, initializeParticles, updateUniformBuffer } from './engine'
import { particleComputeShader, particleRenderShader, bloomBrightPassShader, bloomBlurShader, bloomCompositeShader, tonemapGrainShader } from './shaders'
import { WebGPURenderer } from './runtime'

export function createWebGPURenderer(deviceContext: GPUDeviceContext): WebGPURenderer {
  const { device, context, format } = deviceContext

  // Configuration
  const particleCount = 100000
  let viewport: [number, number] = [1920, 1080]
  let center: [number, number] = [960, 540]

  // Update viewport from canvas
  const canvas = context.canvas
  if (canvas) {
    viewport = [canvas.width, canvas.height]
    center = [canvas.width / 2, canvas.height / 2]
  }

  // Buffers
  const uniformBuffer = createUniformBuffer(device, 12 * 4) // 12 floats
  const { bufferA, bufferB } = createParticleBuffers(device, particleCount)

  // Initialize particles
  initializeParticles(device, bufferA, particleCount, viewport)
  initializeParticles(device, bufferB, particleCount, viewport)

  let currentParticleBuffer = bufferA
  let nextParticleBuffer = bufferB

  // Flow field texture
  const flowFieldSize = 256
  const flowFieldTexture = createFlowFieldTexture(device, flowFieldSize, flowFieldSize)
  const flowFieldSampler = device.createSampler({
    magFilter: 'linear',
    minFilter: 'linear',
    addressModeU: 'repeat',
    addressModeV: 'repeat'
  })

  // Render targets
  let renderTargets = createRenderTargets(device, viewport[0], viewport[1])

  // Samplers
  const linearSampler = device.createSampler({
    magFilter: 'linear',
    minFilter: 'linear',
    addressModeU: 'clamp-to-edge',
    addressModeV: 'clamp-to-edge'
  })

  // ============================================================================
  // COMPUTE PIPELINES
  // ============================================================================

  // Particle compute pipeline
  const particleComputeModule = device.createShaderModule({
    code: particleComputeShader
  })

  const particleComputePipeline = device.createComputePipeline({
    layout: 'auto',
    compute: {
      module: particleComputeModule,
      entryPoint: 'main'
    }
  })

  let particleComputeBindGroup = device.createBindGroup({
    layout: particleComputePipeline.getBindGroupLayout(0),
    entries: [
      { binding: 0, resource: { buffer: uniformBuffer } },
      { binding: 1, resource: currentParticleBuffer },
      { binding: 2, resource: nextParticleBuffer },
      { binding: 3, resource: flowFieldTexture.createView() },
      { binding: 4, resource: flowFieldSampler }
    ]
  })


  // Flow field compute pipeline (optional - can use analytic curl noise)
  const flowFieldComputeModule = device.createShaderModule({
    code: `
      struct Uniforms {
        timeSec: f32,
        dtSec: f32,
        gpuUtil01: f32,
        vramUtil01: f32,
        sceneId: u32,
        sceneT01: f32,
        transitionT01: f32,
        accent01: f32,
        viewport: vec2<f32>,
        center: vec2<f32>,
      };
      
      @group(0) @binding(0) var<uniform> U: Uniforms;
      @group(0) @binding(1) var flowField: texture_storage_2d<rg16float, write>;
      
      @compute @workgroup_size(16, 16)
      fn main(@builtin(global_invocation_id) id: vec3<u32>) {
        let uv = vec2<f32>(id.xy) / 256.0;
        let time = U.timeSec;
        let gpuUtil = U.gpuUtil01;
        
        // Curl noise / vortex field
        let angle = sin(uv.x * 10.0 + time) * cos(uv.y * 10.0 + time) * 3.14159;
        let strength = 0.1 * (1.0 + gpuUtil * 0.5);
        
        let vel = vec2<f32>(
          cos(angle) * strength,
          sin(angle) * strength
        );
        
        textureStore(flowField, vec2<i32>(id.xy), vec4<f32>(vel, 0.0, 1.0));
      }
    `
  })

  const flowFieldComputePipeline = device.createComputePipeline({
    layout: 'auto',
    compute: {
      module: flowFieldComputeModule,
      entryPoint: 'main'
    }
  })

  const flowFieldBindGroup = device.createBindGroup({
    layout: flowFieldComputePipeline.getBindGroupLayout(0),
    entries: [
      { binding: 0, resource: { buffer: uniformBuffer } },
      { binding: 1, resource: flowFieldTexture.createView() }
    ]
  })

  // ============================================================================
  // RENDER PIPELINES
  // ============================================================================

  // Particle render pipeline
  const particleRenderModule = device.createShaderModule({
    code: particleRenderShader
  })

  // Create quad vertex buffer for instanced rendering
  const quadVertexBuffer = device.createBuffer({
    size: 6 * 2 * 4, // 6 vertices * 2 floats * 4 bytes
    usage: GPUBufferUsage.VERTEX,
    mappedAtCreation: true
  })
  const quadVertices = new Float32Array([
    -1, -1, 1, -1, -1, 1,
    -1, 1, 1, -1, 1, 1
  ])
  new Float32Array(quadVertexBuffer.getMappedRange()).set(quadVertices)
  quadVertexBuffer.unmap()

  const particleRenderPipeline = device.createRenderPipeline({
    layout: 'auto',
    vertex: {
      module: particleRenderModule,
      entryPoint: 'vsMain',
      buffers: [{
        arrayStride: 2 * 4,
        stepMode: 'vertex',
        attributes: [{ shaderLocation: 0, offset: 0, format: 'float32x2' }]
      }]
    },
    fragment: {
      module: particleRenderModule,
      entryPoint: 'fsMain',
      targets: [{
        format: 'rgba16float',
        blend: {
          color: {
            srcFactor: 'src-alpha',
            dstFactor: 'one',
            operation: 'add'
          },
          alpha: {
            srcFactor: 'one',
            dstFactor: 'one-minus-src-alpha',
            operation: 'add'
          }
        }
      }]
    },
    primitive: {
      topology: 'triangle-list',
      cullMode: 'none'
    }
  })


  // Particle render bind group
  let particleRenderBindGroup = device.createBindGroup({
    layout: particleRenderPipeline.getBindGroupLayout(0),
    entries: [
      { binding: 0, resource: { buffer: uniformBuffer } },
      { binding: 1, resource: currentParticleBuffer }
    ]
  })

  // ============================================================================
  // POST-PROCESSING PIPELINES
  // ============================================================================

  // Full-screen quad for post-processing
  const fullscreenQuadBuffer = device.createBuffer({
    size: 6 * 2 * 4, // 6 vertices * 2 floats * 4 bytes
    usage: GPUBufferUsage.VERTEX,
    mappedAtCreation: true
  })
  const quadData = new Float32Array([
    -1, -1, 1, -1, -1, 1,
    -1, 1, 1, -1, 1, 1
  ])
  new Float32Array(fullscreenQuadBuffer.getMappedRange()).set(quadData)
  fullscreenQuadBuffer.unmap()

  // Bright-pass pipeline
  const brightPassModule = device.createShaderModule({
    code: bloomBrightPassShader
  })

  const brightPassPipeline = device.createRenderPipeline({
    layout: 'auto',
    vertex: {
      module: device.createShaderModule({
        code: `
          @vertex
          fn main(@location(0) pos: vec2<f32>) -> @builtin(position) vec4<f32> {
            return vec4<f32>(pos, 0.0, 1.0);
          }
        `
      }),
      entryPoint: 'main',
      buffers: [{
        arrayStride: 2 * 4,
        attributes: [{ shaderLocation: 0, offset: 0, format: 'float32x2' }]
      }]
    },
    fragment: {
      module: brightPassModule,
      entryPoint: 'brightPassFS',
      targets: [{
        format: 'rgba16float'
      }]
    },
    primitive: {
      topology: 'triangle-list'
    }
  })

  // Blur pipeline
  const blurModule = device.createShaderModule({
    code: bloomBlurShader
  })

  // Extended uniform buffer for blur (includes blurWidth, blurHeight, blurDir)
  const blurUniformBuffer = device.createBuffer({
    size: 16 * 4, // 16 floats (12 base + 4 blur params)
    usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST
  })

  const blurPipeline = device.createRenderPipeline({
    layout: 'auto',
    vertex: {
      module: device.createShaderModule({
        code: `
          @vertex
          fn main(@location(0) pos: vec2<f32>) -> @builtin(position) vec4<f32> {
            return vec4<f32>(pos, 0.0, 1.0);
          }
        `
      }),
      entryPoint: 'main',
      buffers: [{
        arrayStride: 2 * 4,
        attributes: [{ shaderLocation: 0, offset: 0, format: 'float32x2' }]
      }]
    },
    fragment: {
      module: blurModule,
      entryPoint: 'blurFS',
      targets: [{
        format: 'rgba16float'
      }]
    },
    primitive: {
      topology: 'triangle-list'
    }
  })

  // Composite pipeline
  const compositeModule = device.createShaderModule({
    code: bloomCompositeShader
  })

  const compositePipeline = device.createRenderPipeline({
    layout: 'auto',
    vertex: {
      module: device.createShaderModule({
        code: `
          @vertex
          fn main(@location(0) pos: vec2<f32>) -> @builtin(position) vec4<f32> {
            return vec4<f32>(pos, 0.0, 1.0);
          }
        `
      }),
      entryPoint: 'main',
      buffers: [{
        arrayStride: 2 * 4,
        attributes: [{ shaderLocation: 0, offset: 0, format: 'float32x2' }]
      }]
    },
    fragment: {
      module: compositeModule,
      entryPoint: 'compositeFS',
      targets: [{
        format: format
      }]
    },
    primitive: {
      topology: 'triangle-list'
    }
  })

  // Tonemap + grain pipeline
  const tonemapModule = device.createShaderModule({
    code: tonemapGrainShader
  })

  const tonemapPipeline = device.createRenderPipeline({
    layout: 'auto',
    vertex: {
      module: device.createShaderModule({
        code: `
          @vertex
          fn main(@location(0) pos: vec2<f32>) -> @builtin(position) vec4<f32> {
            return vec4<f32>(pos, 0.0, 1.0);
          }
        `
      }),
      entryPoint: 'main',
      buffers: [{
        arrayStride: 2 * 4,
        attributes: [{ shaderLocation: 0, offset: 0, format: 'float32x2' }]
      }]
    },
    fragment: {
      module: tonemapModule,
      entryPoint: 'fs',
      targets: [{
        format: format
      }]
    },
    primitive: {
      topology: 'triangle-list'
    }
  })

  // ============================================================================
  // RENDER FUNCTION
  // ============================================================================

  let flowFieldUpdateCounter = 0

  function frame(
    encoder: GPUCommandEncoder,
    view: GPUTextureView,
    state: {
      renderState: RenderState
      sceneParams: SceneParams
      dt: number
      now: number
    }
  ) {
    // Update uniform buffer
    updateUniformBuffer(device, uniformBuffer, state.renderState, state.sceneParams, viewport, center)

    // Update flow field every 2-4 frames (performance optimization)
    flowFieldUpdateCounter++
    if (flowFieldUpdateCounter % 3 === 0) {
      const flowFieldPass = encoder.beginComputePass()
      flowFieldPass.setPipeline(flowFieldComputePipeline)
      flowFieldPass.setBindGroup(0, flowFieldBindGroup)
      flowFieldPass.dispatchWorkgroups(
        Math.ceil(flowFieldSize / 16),
        Math.ceil(flowFieldSize / 16)
      )
      flowFieldPass.end()
    }

    // Particle compute pass
    const computePass = encoder.beginComputePass()
    computePass.setPipeline(particleComputePipeline)
    computePass.setBindGroup(0, particleComputeBindGroup)
    computePass.dispatchWorkgroups(Math.ceil(particleCount / 256))
    computePass.end()

    // Swap particle buffers
    const temp = currentParticleBuffer
    currentParticleBuffer = nextParticleBuffer
    nextParticleBuffer = temp

    // Recreate bind groups with swapped buffers (ping-pong)
    particleComputeBindGroup = device.createBindGroup({
      layout: particleComputePipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: uniformBuffer } },
        { binding: 1, resource: currentParticleBuffer },
        { binding: 2, resource: nextParticleBuffer },
        { binding: 3, resource: flowFieldTexture.createView() },
        { binding: 4, resource: flowFieldSampler }
      ]
    })

    particleRenderBindGroup = device.createBindGroup({
      layout: particleRenderPipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: uniformBuffer } },
        { binding: 1, resource: currentParticleBuffer }
      ]
    })

    // Render particles to scene color target
    const scenePass = encoder.beginRenderPass({
      colorAttachments: [{
        view: renderTargets.sceneColor.createView(),
        clearValue: { r: 0, g: 0, b: 0, a: 1 },
        loadOp: 'clear',
        storeOp: 'store'
      }]
    })
    scenePass.setPipeline(particleRenderPipeline)
    scenePass.setBindGroup(0, particleRenderBindGroup)
    scenePass.setVertexBuffer(0, quadVertexBuffer)
    scenePass.draw(6, particleCount, 0, 0) // 6 vertices per quad, particleCount instances
    scenePass.end()

    // Bright-pass (half-res)
    const brightPassView = renderTargets.brightPass.createView()
    const brightPassBindGroup = device.createBindGroup({
      layout: brightPassPipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: uniformBuffer } },
        { binding: 1, resource: renderTargets.sceneColor.createView() },
        { binding: 2, resource: linearSampler }
      ]
    })

    const brightPass = encoder.beginRenderPass({
      colorAttachments: [{
        view: brightPassView,
        clearValue: { r: 0, g: 0, b: 0, a: 1 },
        loadOp: 'clear',
        storeOp: 'store'
      }]
    })
    brightPass.setPipeline(brightPassPipeline)
    brightPass.setBindGroup(0, brightPassBindGroup)
    brightPass.setVertexBuffer(0, fullscreenQuadBuffer)
    brightPass.draw(6)
    brightPass.end()

    // Update blur uniform buffer
    const blurWidth = Math.floor(viewport[0] / 2)
    const blurHeight = Math.floor(viewport[1] / 2)
    const blurData = new Float32Array(16)
    // Copy base uniform values (reconstruct from state)
    blurData[0] = state.renderState.timeSec
    blurData[1] = state.renderState.dtSec
    blurData[2] = state.renderState.gpuUtil01
    blurData[3] = state.renderState.vramUtil01
    blurData[4] = state.sceneParams.sceneId === 'A' ? 0 : state.sceneParams.sceneId === 'B' ? 1 : state.sceneParams.sceneId === 'C' ? 2 : state.sceneParams.sceneId === 'D' ? 3 : 4
    blurData[5] = state.sceneParams.sceneT01
    blurData[6] = state.sceneParams.transitionT01
    blurData[7] = state.sceneParams.accent01
    blurData[8] = viewport[0]
    blurData[9] = viewport[1]
    blurData[10] = center[0]
    blurData[11] = center[1]
    // Add blur params
    blurData[12] = blurWidth
    blurData[13] = blurHeight
    blurData[14] = 1.0 // blurDir X
    blurData[15] = 0.0 // blurDir Y
    device.queue.writeBuffer(blurUniformBuffer, 0, blurData)

    // Blur X (half-res)
    const blurXBindGroup = device.createBindGroup({
      layout: blurPipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: blurUniformBuffer } },
        { binding: 1, resource: renderTargets.brightPass.createView() },
        { binding: 2, resource: linearSampler }
      ]
    })

    const blurX = encoder.beginRenderPass({
      colorAttachments: [{
        view: renderTargets.blur1.createView(),
        clearValue: { r: 0, g: 0, b: 0, a: 1 },
        loadOp: 'clear',
        storeOp: 'store'
      }]
    })
    blurX.setPipeline(blurPipeline)
    blurX.setBindGroup(0, blurXBindGroup)
    blurX.setVertexBuffer(0, fullscreenQuadBuffer)
    blurX.draw(6)
    blurX.end()

    // Update blur uniform for Y direction (reuse same data, just change direction)
    const blurDataY = new Float32Array(blurData)
    blurDataY[14] = 0.0 // blurDir X
    blurDataY[15] = 1.0 // blurDir Y
    device.queue.writeBuffer(blurUniformBuffer, 0, blurDataY)

    // Blur Y (half-res)
    const blurYBindGroup = device.createBindGroup({
      layout: blurPipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: blurUniformBuffer } },
        { binding: 1, resource: renderTargets.blur1.createView() },
        { binding: 2, resource: linearSampler }
      ]
    })

    const blurY = encoder.beginRenderPass({
      colorAttachments: [{
        view: renderTargets.blur2.createView(),
        clearValue: { r: 0, g: 0, b: 0, a: 1 },
        loadOp: 'clear',
        storeOp: 'store'
      }]
    })
    blurY.setPipeline(blurPipeline)
    blurY.setBindGroup(0, blurYBindGroup)
    blurY.setVertexBuffer(0, fullscreenQuadBuffer)
    blurY.draw(6)
    blurY.end()

    // Composite (full-res to final view)
    const compositeBindGroup = device.createBindGroup({
      layout: compositePipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: uniformBuffer } },
        { binding: 1, resource: renderTargets.sceneColor.createView() },
        { binding: 2, resource: renderTargets.blur2.createView() },
        { binding: 3, resource: linearSampler }
      ]
    })

    const composite = encoder.beginRenderPass({
      colorAttachments: [{
        view: renderTargets.sceneColor.createView(),
        loadOp: 'load',
        storeOp: 'store'
      }]
    })
    composite.setPipeline(compositePipeline)
    composite.setBindGroup(0, compositeBindGroup)
    composite.setVertexBuffer(0, fullscreenQuadBuffer)
    composite.draw(6)
    composite.end()

    // Tonemap + grain (final output)
    const tonemapBindGroup = device.createBindGroup({
      layout: tonemapPipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: uniformBuffer } },
        { binding: 1, resource: renderTargets.sceneColor.createView() },
        { binding: 2, resource: linearSampler }
      ]
    })

    const tonemap = encoder.beginRenderPass({
      colorAttachments: [{
        view,
        clearValue: { r: 0, g: 0, b: 0, a: 1 },
        loadOp: 'clear',
        storeOp: 'store'
      }]
    })
    tonemap.setPipeline(tonemapPipeline)
    tonemap.setBindGroup(0, tonemapBindGroup)
    tonemap.setVertexBuffer(0, fullscreenQuadBuffer)
    tonemap.draw(6)
    tonemap.end()
  }

  function resize(width: number, height: number) {
    viewport = [width, height]
    center = [width / 2, height / 2]
    renderTargets = createRenderTargets(device, width, height)

    // Reinitialize particles for new viewport
    initializeParticles(device, bufferA, particleCount, viewport)
    initializeParticles(device, bufferB, particleCount, viewport)
  }

  function destroy() {
    // Cleanup handled by device context
  }

  return {
    frame,
    resize,
    destroy
  }
}

