/**
 * ⚠️ LEGACY: Canvas 2D Particle Field ⚠️
 * 
 * This is a legacy Canvas 2D-based particle field implementation.
 * 
 * PRIMARY PATH:
 * - WebGPU particle field via useWebGPUAttractMode (AttractModeOverlay.vue)
 * - 100k+ particles, bloom effects, flow fields
 * - Real-time telemetry-driven visuals
 * 
 * THIS COMPONENT (Legacy):
 * - Canvas 2D/WebGL fallback
 * - Simpler implementation
 * - Used in SceneA-E scenes (may be redundant with WebGPU path)
 * 
 * STATUS:
 * - WebGPU particles are shipping as primary path
 * - This may be removed if WebGPU path is stable
 * - Kept for fallback/compatibility if needed
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'
import { useDemoControlStore } from '@/stores/demoControlStore'

export interface ParticleFieldConfig {
  particleCount?: number
  container: HTMLElement
}

export function useGPUParticleField(config: ParticleFieldConfig) {
  const metricsStore = useMetricsStore()
  const demoControlStore = useDemoControlStore()

  const particleCount = config.particleCount || 100000
  const canvas = ref<HTMLCanvasElement | null>(null)
  const gl = ref<WebGLRenderingContext | null>(null)
  const animationFrame = ref<number | null>(null)

  // Particle state
  const particles = ref<Float32Array | null>(null)
  const velocities = ref<Float32Array | null>(null)

  // System state
  const isInitialized = ref(false)

  // Velocity field modulation based on GPU state
  const getVelocityModulation = () => {
    const gpuUtil = metricsStore.gpuUtilization / 100
    const vramPressure = metricsStore.vramUsed / metricsStore.vramTotal

    // Model state affects flow
    let _modelStateMod = 1.0
    if (demoControlStore.isWarming) {
      _modelStateMod = 0.3 // Converge inward
    } else if (demoControlStore.isRunning) {
      _modelStateMod = 2.0 // Turbulent flow
    }

    return {
      baseSpeed: 0.0002 * (1 + gpuUtil * 0.5),
      turbulence: gpuUtil * 0.001,
      convergence: demoControlStore.isWarming ? 0.0005 : 0,
      vramPressure: vramPressure * 0.0003
    }
  }

  function initWebGL() {
    if (!canvas.value) return

    const context = canvas.value.getContext('webgl', {
      alpha: true,
      antialias: true,
      premultipliedAlpha: false
    })

    if (!context) {
      console.warn('[ParticleField] WebGL not available, falling back to Canvas 2D')
      initCanvas2D()
      return
    }

    gl.value = context

    // Set up viewport
    const resize = () => {
      if (!canvas.value || !gl.value) return
      const rect = config.container.getBoundingClientRect()
      canvas.value.width = rect.width * window.devicePixelRatio
      canvas.value.height = rect.height * window.devicePixelRatio
      canvas.value.style.width = `${rect.width}px`
      canvas.value.style.height = `${rect.height}px`
      gl.value.viewport(0, 0, canvas.value.width, canvas.value.height)
    }

    resize()
    window.addEventListener('resize', resize)

    // Initialize particle data
    particles.value = new Float32Array(particleCount * 2)
    velocities.value = new Float32Array(particleCount * 2)

    // Initialize positions (random across canvas)
    for (let i = 0; i < particleCount; i++) {
      particles.value[i * 2] = Math.random() * 2 - 1 // x: -1 to 1
      particles.value[i * 2 + 1] = Math.random() * 2 - 1 // y: -1 to 1

      // Initial velocities (slow drift)
      velocities.value[i * 2] = (Math.random() - 0.5) * 0.0001
      velocities.value[i * 2 + 1] = (Math.random() - 0.5) * 0.0001
    }

    // Simple WebGL shader-based rendering
    // For now, use point sprites
    const _vertexShader = `
      attribute vec2 a_position;
      uniform vec2 u_resolution;
      uniform float u_pointSize;
      
      void main() {
        vec2 clipSpace = ((a_position / u_resolution) * 2.0) - 1.0;
        gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
        gl_PointSize = u_pointSize;
      }
    `

    const _fragmentShader = `
      precision mediump float;
      uniform vec3 u_color;
      uniform float u_alpha;
      
      void main() {
        float dist = distance(gl_PointCoord, vec2(0.5));
        float alpha = u_alpha * (1.0 - smoothstep(0.0, 0.5, dist));
        gl_FragColor = vec4(u_color, alpha);
      }
    `

    // Compile shaders (simplified - would need full WebGL setup)
    // For performance, we'll use Canvas 2D with optimizations

    isInitialized.value = true
    animate()
  }

  function initCanvas2D() {
    if (!canvas.value) return

    const ctx = canvas.value.getContext('2d')
    if (!ctx) return

    const resize = () => {
      if (!canvas.value) return
      const rect = config.container.getBoundingClientRect()
      canvas.value.width = rect.width * window.devicePixelRatio
      canvas.value.height = rect.height * window.devicePixelRatio
      canvas.value.style.width = `${rect.width}px`
      canvas.value.style.height = `${rect.height}px`
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }

    resize()
    window.addEventListener('resize', resize)

    // Initialize particle data
    particles.value = new Float32Array(particleCount * 2)
    velocities.value = new Float32Array(particleCount * 2)

    // Initialize positions
    for (let i = 0; i < particleCount; i++) {
      const rect = config.container.getBoundingClientRect()
      particles.value[i * 2] = Math.random() * rect.width
      particles.value[i * 2 + 1] = Math.random() * rect.height

      velocities.value[i * 2] = (Math.random() - 0.5) * 0.5
      velocities.value[i * 2 + 1] = (Math.random() - 0.5) * 0.5
    }

    isInitialized.value = true
    animateCanvas2D(ctx)
  }

  function animateCanvas2D(ctx: CanvasRenderingContext2D) {
    if (!particles.value || !velocities.value || !canvas.value) return

    const mod = getVelocityModulation()
    const rect = config.container.getBoundingClientRect()
    const centerX = rect.width / 2
    const centerY = rect.height / 2

    // Clear with fade trail effect
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'
    ctx.fillRect(0, 0, rect.width, rect.height)

    // Update and draw particles
    ctx.fillStyle = 'rgba(249, 115, 22, 0.15)'

    for (let i = 0; i < particleCount; i++) {
      const idx = i * 2
      let x = particles.value[idx]
      let y = particles.value[idx + 1]

      // Apply velocity field modulation
      const dx = x - centerX
      const dy = y - centerY
      const dist = Math.sqrt(dx * dx + dy * dy)

      // Convergence effect (when warming)
      if (mod.convergence > 0) {
        velocities.value[idx] -= (dx / dist) * mod.convergence
        velocities.value[idx + 1] -= (dy / dist) * mod.convergence
      }

      // Turbulence
      velocities.value[idx] += (Math.random() - 0.5) * mod.turbulence
      velocities.value[idx + 1] += (Math.random() - 0.5) * mod.turbulence

      // Apply velocity
      x += velocities.value[idx] * mod.baseSpeed * 1000
      y += velocities.value[idx + 1] * mod.baseSpeed * 1000

      // Wrap around edges
      if (x < 0) x = rect.width
      if (x > rect.width) x = 0
      if (y < 0) y = rect.height
      if (y > rect.height) y = 0

      particles.value[idx] = x
      particles.value[idx + 1] = y

      // Draw particle (small point)
      ctx.beginPath()
      ctx.arc(x, y, 0.5, 0, Math.PI * 2)
      ctx.fill()
    }

    animationFrame.value = requestAnimationFrame(() => animateCanvas2D(ctx))
  }

  function animate() {
    // WebGL animation would go here
    // For now, Canvas 2D handles it
  }

  function stop() {
    if (animationFrame.value !== null) {
      cancelAnimationFrame(animationFrame.value)
      animationFrame.value = null
    }
  }

  onMounted(() => {
    if (!config.container) return

    // Create canvas element
    const canvasEl = document.createElement('canvas')
    canvasEl.style.position = 'absolute'
    canvasEl.style.inset = '0'
    canvasEl.style.pointerEvents = 'none'
    canvasEl.style.zIndex = '1'
    config.container.appendChild(canvasEl)
    canvas.value = canvasEl

    // Initialize based on WebGL availability
    initWebGL()
  })

  onUnmounted(() => {
    stop()
    if (canvas.value && canvas.value.parentNode) {
      canvas.value.parentNode.removeChild(canvas.value)
    }
  })

  return {
    canvas,
    isInitialized
  }
}

