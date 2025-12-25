<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useGPUParticleField } from '@/attract/engine/legacy/useGPUParticleField'
import { useBloomEffect } from '@/composables/useBloomEffect'

const containerRef = ref<HTMLElement | null>(null)
const { getElementGlow } = useBloomEffect()

// Initialize particle field (reacts to cursor)
let particleField: ReturnType<typeof useGPUParticleField> | null = null

onMounted(() => {
  if (containerRef.value) {
    particleField = useGPUParticleField({
      container: containerRef.value,
      particleCount: 60000
    })
  }
})

const visibleLines = ref<string[]>([])
const allLines = [
  'Touch any key to explore',
  'Run a 70B model live',
  'Guided Tour Available'
]

// Button positions (drift apart and back together)
const buttonPositions = ref<Array<{ x: number; y: number; scale: number }>>([])
const mousePosition = ref({ x: 0, y: 0 })
let buttonAnimationFrame: ReturnType<typeof requestAnimationFrame> | null = null

let lineTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // Initialize button positions
  allLines.forEach((_, index) => {
    buttonPositions.value.push({ x: 0, y: 0, scale: 1 })
  })
  
  // Reveal lines one by one
  let lineIndex = 0
  lineTimer = setInterval(() => {
    if (lineIndex < allLines.length) {
      visibleLines.value.push(allLines[lineIndex])
      lineIndex++
    } else {
      if (lineTimer) {
        clearInterval(lineTimer)
        lineTimer = null
      }
    }
  }, 800)
  
  // Animate buttons (drift apart and back together)
  const animateButtons = () => {
    const time = Date.now() / 1000
    buttonPositions.value.forEach((pos, index) => {
      const drift = Math.sin(time * 0.3 + index) * 15
      pos.x = drift
      pos.y = Math.sin(time * 0.4 + index) * 5
      pos.scale = 1 + Math.sin(time * 0.5 + index) * 0.05
    })
    buttonAnimationFrame = requestAnimationFrame(animateButtons)
  }
  animateButtons()
  
  // Track mouse for proximity effects
  const handleMouseMove = (e: MouseEvent) => {
    mousePosition.value = { x: e.clientX, y: e.clientY }
  }
  window.addEventListener('mousemove', handleMouseMove)
  
  return () => {
    window.removeEventListener('mousemove', handleMouseMove)
  }
})

onUnmounted(() => {
  if (lineTimer) {
    clearInterval(lineTimer)
    lineTimer = null
  }
  if (buttonAnimationFrame !== null) {
    cancelAnimationFrame(buttonAnimationFrame)
    buttonAnimationFrame = null
  }
})

// Get button transform
function getButtonTransform(index: number) {
  const pos = buttonPositions.value[index]
  if (!pos) return ''
  return `translate(${pos.x}px, ${pos.y}px) scale(${pos.scale})`
}
</script>

<template>
  <div ref="containerRef" class="scene-e">
    <!-- Cursor ripple effect background -->
    <div class="cursor-ripple" :style="{ left: `${mousePosition.x}px`, top: `${mousePosition.y}px` }"></div>
    
    <!-- Subtle UI overlay -->
    <div class="scene-e__invitation">
      <TransitionGroup name="line-fade" tag="div" class="invitation-lines">
        <div
          v-for="(line, index) in visibleLines"
          :key="line"
          class="invitation-line"
          :style="{ 
            animationDelay: `${index * 0.1}s`,
            transform: getButtonTransform(index),
            ...getElementGlow('var(--text-secondary)', 0.2)
          }"
        >
          {{ line }}
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.scene-e {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--abs-black);
  overflow: hidden;
}

.cursor-ripple {
  position: absolute;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.1) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  pointer-events: none;
  animation: ripple-expand 2s ease-out infinite;
  z-index: 1;
}

@keyframes ripple-expand {
  0% {
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 0.5;
  }
  100% {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
  }
}

.scene-e__invitation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.invitation-lines {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.invitation-line {
  font-family: var(--font-label);
  font-size: 2.5rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-align: center;
  padding: 20px 40px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  animation: fade-in-gentle 0.8s var(--ease-smooth);
  transition: all 0.3s var(--ease-smooth);
  cursor: default;
  z-index: 10;
  position: relative;
}

.invitation-line:hover {
  color: var(--abs-orange);
  border-color: var(--abs-orange);
  background: rgba(249, 115, 22, 0.05);
}

/* Line transition */
.line-fade-enter-active {
  transition: opacity 0.6s var(--ease-smooth), transform 0.6s var(--ease-smooth);
}

.line-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

@keyframes fade-in-gentle {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

