<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useMetricsStore } from '@/stores/metricsStore'

const metricsStore = useMetricsStore()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let animationId: number | null = null
let ctx: CanvasRenderingContext2D | null = null

// Particle system for GPU memory visualization
interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  alpha: number
  hue: number
}

const particles = ref<Particle[]>([])
const maxParticles = 150

// Colors based on GPU utilization
const baseHue = computed(() => {
  const util = metricsStore.gpuUtilization
  // Orange (30) at high utilization, Indigo (240) at low
  return util > 50 ? 30 : 240
})

function createParticle(): Particle {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0, vx: 0, vy: 0, size: 2, alpha: 0.5, hue: 240 }
  
  return {
    x: Math.random() * canvas.width,
    y: canvas.height + 10,
    vx: (Math.random() - 0.5) * 0.5,
    vy: -Math.random() * 2 - 0.5,
    size: Math.random() * 3 + 1,
    alpha: Math.random() * 0.5 + 0.3,
    hue: baseHue.value + (Math.random() * 40 - 20)
  }
}

function initParticles() {
  particles.value = []
  for (let i = 0; i < maxParticles / 2; i++) {
    const p = createParticle()
    p.y = Math.random() * (canvasRef.value?.height || 600)
    particles.value.push(p)
  }
}

function updateParticles() {
  const canvas = canvasRef.value
  if (!canvas) return
  
  // Add new particles based on GPU utilization
  const particlesToAdd = Math.floor(metricsStore.gpuUtilization / 10)
  for (let i = 0; i < particlesToAdd && particles.value.length < maxParticles; i++) {
    particles.value.push(createParticle())
  }
  
  // Update existing particles
  particles.value = particles.value.filter(p => {
    p.x += p.vx
    p.y += p.vy
    p.alpha -= 0.002
    
    // Wave motion
    p.x += Math.sin(p.y * 0.02) * 0.5
    
    // Remove if off screen or faded
    return p.y > -10 && p.alpha > 0
  })
}

function drawParticles() {
  const canvas = canvasRef.value
  if (!canvas || !ctx) return
  
  // Clear with fade effect
  ctx.fillStyle = 'rgba(10, 10, 15, 0.1)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // Draw particles
  particles.value.forEach(p => {
    ctx!.beginPath()
    ctx!.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx!.fillStyle = `hsla(${p.hue}, 80%, 60%, ${p.alpha})`
    ctx!.fill()
    
    // Glow effect
    ctx!.shadowBlur = 10
    ctx!.shadowColor = `hsla(${p.hue}, 90%, 50%, ${p.alpha * 0.5})`
  })
  ctx.shadowBlur = 0
  
  // Draw connecting lines between nearby particles
  particles.value.forEach((p1, i) => {
    particles.value.slice(i + 1).forEach(p2 => {
      const dx = p1.x - p2.x
      const dy = p1.y - p2.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      
      if (dist < 100) {
        ctx!.beginPath()
        ctx!.moveTo(p1.x, p1.y)
        ctx!.lineTo(p2.x, p2.y)
        ctx!.strokeStyle = `rgba(99, 102, 241, ${0.15 * (1 - dist / 100)})`
        ctx!.lineWidth = 0.5
        ctx!.stroke()
      }
    })
  })
}

function drawCenterGraphic() {
  const canvas = canvasRef.value
  if (!canvas || !ctx) return
  
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const util = metricsStore.gpuUtilization
  
  // Outer ring
  const radius = 120 + Math.sin(Date.now() * 0.001) * 10
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
  ctx.strokeStyle = 'rgba(99, 102, 241, 0.2)'
  ctx.lineWidth = 2
  ctx.stroke()
  
  // Utilization arc
  const arcAngle = (util / 100) * Math.PI * 2
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + arcAngle)
  const gradient = ctx.createLinearGradient(
    centerX - radius, centerY,
    centerX + radius, centerY
  )
  gradient.addColorStop(0, 'rgba(99, 102, 241, 0.8)')
  gradient.addColorStop(1, 'rgba(249, 115, 22, 0.8)')
  ctx.strokeStyle = util > 50 ? 'rgba(249, 115, 22, 0.8)' : 'rgba(99, 102, 241, 0.8)'
  ctx.lineWidth = 4
  ctx.lineCap = 'round'
  ctx.stroke()
  
  // Inner rings
  for (let i = 1; i <= 3; i++) {
    const innerRadius = radius - (i * 25)
    ctx.beginPath()
    ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(99, 102, 241, ${0.1 / i})`
    ctx.lineWidth = 1
    ctx.stroke()
  }
  
  // Center text
  ctx.font = 'bold 48px "JetBrains Mono", monospace'
  ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(`${Math.round(util)}%`, centerX, centerY - 10)
  
  ctx.font = '14px "Rajdhani", sans-serif'
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
  ctx.fillText('GPU UTILIZATION', centerX, centerY + 30)
}

function animate() {
  updateParticles()
  drawParticles()
  drawCenterGraphic()
  animationId = requestAnimationFrame(animate)
}

function resizeCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  ctx = canvas.getContext('2d')
  if (!ctx) return
  
  resizeCanvas()
  initParticles()
  animate()
  
  window.addEventListener('resize', resizeCanvas)
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<template>
  <canvas ref="canvasRef" class="system-visualization"></canvas>
</template>

<style scoped>
.system-visualization {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
</style>
