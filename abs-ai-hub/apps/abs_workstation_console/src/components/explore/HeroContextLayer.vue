<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animationFrame: number | null = null
let particles: Particle[] = []
let circuitNodes: CircuitNode[] = []
let time = 0

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
  life: number
  maxLife: number
}

interface CircuitNode {
  x: number
  y: number
  connections: number[]
  pulse: number
}

const particleCount = 30
const nodeCount = 15
const maxConnectionDistance = 200

function initParticles(width: number, height: number) {
  particles = []
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.15, // Very slow movement
      vy: (Math.random() - 0.5) * 0.15, // Very slow movement
      size: Math.random() * 2 + 1,
      opacity: Math.random() * 0.05 + 0.08, // 8-13% opacity for better visibility (temporarily higher)
      life: Math.random(),
      maxLife: 1
    })
  }
}

function initCircuitNodes(width: number, height: number) {
  circuitNodes = []
  for (let i = 0; i < nodeCount; i++) {
    circuitNodes.push({
      x: Math.random() * width,
      y: Math.random() * height,
      connections: [],
      pulse: Math.random() * Math.PI * 2
    })
  }
  
  // Create connections between nearby nodes
  for (let i = 0; i < circuitNodes.length; i++) {
    for (let j = i + 1; j < circuitNodes.length; j++) {
      const dx = circuitNodes[i].x - circuitNodes[j].x
      const dy = circuitNodes[i].y - circuitNodes[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      
      if (dist < maxConnectionDistance) {
        circuitNodes[i].connections.push(j)
        circuitNodes[j].connections.push(i)
      }
    }
  }
}

function draw(ctx: CanvasRenderingContext2D, width: number, height: number) {
  // Clear with slight fade for trails
  ctx.fillStyle = 'rgba(10, 10, 15, 0.02)'
  ctx.fillRect(0, 0, width, height)
  
  // Draw circuit lines (very subtle - 6-8% opacity for visibility)
  ctx.strokeStyle = 'rgba(99, 102, 241, 0.08)'
  ctx.lineWidth = 1
  
  for (let i = 0; i < circuitNodes.length; i++) {
    const node = circuitNodes[i]
    const pulse = Math.sin(time * 0.0003 + node.pulse) * 0.5 + 0.5 // Very slow movement
    
    for (const connIdx of node.connections) {
      const conn = circuitNodes[connIdx]
      const dist = Math.sqrt(
        Math.pow(node.x - conn.x, 2) + Math.pow(node.y - conn.y, 2)
      )
      const opacity = (1 - dist / maxConnectionDistance) * 0.08 * pulse
      
      ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`
      ctx.beginPath()
      ctx.moveTo(node.x, node.y)
      ctx.lineTo(conn.x, conn.y)
      ctx.stroke()
    }
  }
  
  // Draw circuit nodes (very subtle)
  for (const node of circuitNodes) {
    const pulse = Math.sin(time * 0.0005 + node.pulse) * 0.5 + 0.5
    const opacity = 0.06 * pulse
    
    ctx.fillStyle = `rgba(99, 102, 241, ${opacity})`
    ctx.beginPath()
    ctx.arc(node.x, node.y, 2, 0, Math.PI * 2)
    ctx.fill()
  }
  
  // Draw flowing data particles
  for (const particle of particles) {
    particle.x += particle.vx
    particle.y += particle.vy
    particle.life += 0.002
    
    // Wrap around edges
    if (particle.x < 0) particle.x = width
    if (particle.x > width) particle.x = 0
    if (particle.y < 0) particle.y = height
    if (particle.y > height) particle.y = 0
    
    // Reset if life cycle complete
    if (particle.life > particle.maxLife) {
      particle.x = Math.random() * width
      particle.y = Math.random() * height
      particle.life = 0
    }
    
    // Draw particle with pulsing opacity
    const lifeFactor = Math.sin(particle.life * Math.PI)
    const opacity = particle.opacity * lifeFactor
    
    ctx.fillStyle = `rgba(249, 115, 22, ${opacity})`
    ctx.beginPath()
    ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
    ctx.fill()
  }
  
  // Draw abstract compute waves (subtle gradients)
  const waveCount = 3
  for (let i = 0; i < waveCount; i++) {
    const waveTime = time * 0.0002 + i * Math.PI * 2 / waveCount // Very slow movement
    const waveX = width / 2 + Math.cos(waveTime) * width * 0.3
    const waveY = height / 2 + Math.sin(waveTime) * height * 0.3
    const radius = 150 + Math.sin(waveTime * 2) * 50
    
    const gradient = ctx.createRadialGradient(waveX, waveY, 0, waveX, waveY, radius)
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.06)') // 6% opacity for visibility
    gradient.addColorStop(0.5, 'rgba(99, 102, 241, 0.03)')
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0)')
    
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(waveX, waveY, radius, 0, Math.PI * 2)
    ctx.fill()
  }
}

function animate() {
  if (!canvasRef.value) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d', { alpha: true })
  if (!ctx) {
    console.warn('[HeroContextLayer] Could not get 2D context')
    return
  }
  
  const width = canvas.offsetWidth || window.innerWidth
  const height = canvas.offsetHeight || window.innerHeight
  
  // Set canvas size
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width
    canvas.height = height
  }
  
  time += 16 // ~60fps
  
  draw(ctx, width, height)
  
  animationFrame = requestAnimationFrame(animate)
}

function handleResize() {
  if (!canvasRef.value) return
  
  const canvas = canvasRef.value
  const width = canvas.offsetWidth
  const height = canvas.offsetHeight
  
  initParticles(width, height)
  initCircuitNodes(width, height)
}

onMounted(() => {
  // Wait for next tick to ensure canvas is mounted
  setTimeout(() => {
    if (!canvasRef.value) {
      console.warn('[HeroContextLayer] Canvas ref not available')
      return
    }
    
    const canvas = canvasRef.value
    const width = canvas.offsetWidth || window.innerWidth
    const height = canvas.offsetHeight || window.innerHeight
    
    if (width === 0 || height === 0) {
      console.warn('[HeroContextLayer] Canvas dimensions are zero', { width, height })
    }
    
    initParticles(width, height)
    initCircuitNodes(width, height)
    
    animate()
    
    window.addEventListener('resize', handleResize)
  }, 100)
})

onUnmounted(() => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <canvas 
    ref="canvasRef"
    class="hero-context-layer"
  />
</template>

<style scoped>
.hero-context-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  opacity: 1;
  background: transparent;
}
</style>

