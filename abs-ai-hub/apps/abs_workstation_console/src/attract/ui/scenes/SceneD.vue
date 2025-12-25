<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// Rotating platform messages
const messages = [
  'ONE WORKSTATION',
  'MULTIPLE AI MINDS',
  'ZERO CLOUD DEPENDENCY'
]

const currentMessageIndex = ref(0)
const currentMessage = ref(messages[0])
let messageInterval: ReturnType<typeof setInterval> | null = null

// Cloud destruction effect (for "ZERO CLOUD DEPENDENCY")
const showCloudDestruction = ref(false)
const cloudParticles = ref<Array<{ x: number; y: number; vx: number; vy: number; opacity: number }>>([])
let cloudAnimationFrame: ReturnType<typeof requestAnimationFrame> | null = null

// Subtext line-by-line reveal
const visibleSubtextLines = ref<string[]>([])
const subtextLines = ['ASSET-BASED', 'AUTO-WAKE', 'GOVERNED']

onMounted(() => {
  // Rotate messages every 2.5 seconds (3 messages over ~7 seconds)
  messageInterval = setInterval(() => {
    const prevIndex = currentMessageIndex.value
    currentMessageIndex.value = (currentMessageIndex.value + 1) % messages.length
    currentMessage.value = messages[currentMessageIndex.value]
    
    // Trigger cloud destruction for "ZERO CLOUD DEPENDENCY"
    if (currentMessageIndex.value === 2 && prevIndex !== 2) {
      triggerCloudDestruction()
    }
    
    // Reveal subtext lines when showing "ZERO CLOUD DEPENDENCY"
    if (currentMessageIndex.value === 2) {
      visibleSubtextLines.value = []
      subtextLines.forEach((line, index) => {
        setTimeout(() => {
          visibleSubtextLines.value.push(line)
        }, 1000 + index * 400)
      })
    } else {
      visibleSubtextLines.value = []
    }
  }, 2500)
})

function triggerCloudDestruction() {
  showCloudDestruction.value = true
  
  // Create cloud particles
  cloudParticles.value = []
  for (let i = 0; i < 50; i++) {
    cloudParticles.value.push({
      x: 50 + Math.random() * 20 - 10, // Center area
      y: 40 + Math.random() * 20 - 10,
      vx: (Math.random() - 0.5) * 2,
      vy: Math.random() * 1 + 0.5, // Downward flow
      opacity: 0.6 + Math.random() * 0.4
    })
  }
  
  // Animate particles
  const animate = () => {
    cloudParticles.value = cloudParticles.value.map(particle => ({
      ...particle,
      x: particle.x + particle.vx * 0.5,
      y: particle.y + particle.vy * 0.5,
      opacity: particle.opacity * 0.98,
      vy: particle.vy + 0.1 // Gravity
    })).filter(p => p.opacity > 0.05 && p.y < 100)
    
    if (cloudParticles.value.length > 0) {
      cloudAnimationFrame = requestAnimationFrame(animate)
    } else {
      showCloudDestruction.value = false
    }
  }
  animate()
}

onUnmounted(() => {
  if (messageInterval) {
    clearInterval(messageInterval)
    messageInterval = null
  }
  if (cloudAnimationFrame !== null) {
    cancelAnimationFrame(cloudAnimationFrame)
    cloudAnimationFrame = null
  }
})
</script>

<template>
  <div class="scene-d">
    <!-- Dark background -->
    <div class="scene-d__background"></div>
    
    <!-- Cloud destruction particles -->
    <svg v-if="showCloudDestruction" class="cloud-particles" viewBox="0 0 100 100" preserveAspectRatio="none">
      <circle
        v-for="(particle, index) in cloudParticles"
        :key="index"
        :cx="particle.x"
        :cy="particle.y"
        r="1.5"
        :fill="`rgba(255, 255, 255, ${particle.opacity})`"
        class="cloud-particle"
      />
    </svg>
    
    <!-- Centered statements -->
    <div class="scene-d__content">
      <Transition name="message-fade" mode="out-in">
        <div :key="currentMessage" class="main-statement">
          {{ currentMessage }}
        </div>
      </Transition>
      
      <!-- Subtext (line-by-line) -->
      <div class="subtext-container">
        <TransitionGroup name="subtext-fade" tag="div" class="subtext">
          <div
            v-for="(line, index) in visibleSubtextLines"
            :key="line"
            class="subtext-line"
          >
            {{ line }}
          </div>
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scene-d {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--abs-black);
}

.scene-d__background {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(249, 115, 22, 0.05) 0%, transparent 70%);
}

.scene-d__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  z-index: 1;
}

.main-statement {
  font-family: var(--font-label);
  font-size: 7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-primary);
  text-align: center;
  text-shadow: 0 0 50px rgba(255, 255, 255, 0.15);
  line-height: 1.1;
}

.subtext-container {
  min-height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.subtext {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.subtext-line {
  font-family: var(--font-label);
  font-size: 1.5rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.cloud-particles {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 5;
}

.cloud-particle {
  transition: all 0.1s linear;
}

/* Message transition */
.message-fade-enter-active,
.message-fade-leave-active {
  transition: opacity 0.6s var(--ease-smooth), transform 0.6s var(--ease-smooth);
}

.message-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.message-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>

