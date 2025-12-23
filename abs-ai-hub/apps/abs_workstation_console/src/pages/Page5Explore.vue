<script setup lang="ts">
import { ref } from 'vue'
import HeroContextLayer from '@/components/explore/HeroContextLayer.vue'

const activeTab = ref<'models' | 'solutions'>('models')

const workstationModels = [
  {
    id: 'zaurion-aqua',
    name: 'Zaurion Aqua',
    tier: 'Professional',
    gpu: '1x RTX Pro 6000 Blackwell',
    gpuDetails: '96GB GDDR7',
    cpu: 'Intel Xeon W5-2455X / W7-2495X',
    ram: 'Up to 128GB DDR5',
    storage: '2TB NVMe SSD + 4TB SSD',
    bestFor: 'AI workloads, engineering simulation (CFD, FEA), high-end 3D rendering, scientific research',
    neweggUrl: 'https://www.newegg.com/abs-zaurion-aqua-zaw5-2455x-rp6000-tower/p/N82E16859991004',
    featured: false
  },
  {
    id: 'zaurion-duo-aqua',
    name: 'Zaurion Duo Aqua',
    tier: 'Professional',
    gpu: '2x RTX Pro 6000 Blackwell MaxQ',
    gpuDetails: '96GB each',
    cpu: 'Intel Xeon W5/W7 series',
    ram: '64GB–128GB DDR5',
    storage: '1TB–2TB NVMe + 2–4TB SSD',
    bestFor: 'Extreme scale AI training, multi-GPU rendering (film/VFX), engineering simulation',
    neweggUrl: 'https://www.newegg.com/abs-zaurion-duo-aqua-zaw5-2455x-rp6000mq-tower/p/N82E16859991008',
    featured: false
  },
  {
    id: 'zaurion-ruby',
    name: 'Zaurion Ruby',
    tier: 'Professional',
    gpu: '1x RTX Pro 6000 Blackwell',
    gpuDetails: '96GB GDDR7',
    cpu: 'AMD Threadripper Pro 7975WX',
    ram: 'Up to 128GB DDR5',
    storage: '2TB NVMe + 4TB SSD',
    bestFor: 'HPC applications, scientific computing, engineering, AI research with high parallelism',
    neweggUrl: 'https://www.newegg.com/p/59-991-006',
    featured: false
  },
  {
    id: 'zaurion-duo-ruby',
    name: 'Zaurion Duo Ruby',
    tier: 'Professional',
    gpu: '2x RTX Pro 6000 Blackwell MaxQ',
    gpuDetails: '96GB each',
    cpu: 'AMD Threadripper Pro 7975WX',
    ram: 'Up to 128GB DDR5',
    storage: '2TB NVMe + 4TB SSD',
    bestFor: 'Dual-GPU deep learning, real-time production, rendering, high-throughput simulations',
    neweggUrl: 'https://www.newegg.com/p/59-991-010',
    featured: false
  },
  {
    id: 'zaurion-pro',
    name: 'Zaurion Pro',
    tier: 'Enterprise',
    gpu: '4x NVIDIA RTX 6000 Ada Generation',
    gpuDetails: '48GB each',
    cpu: 'Intel Xeon W5-3535X (20 cores)',
    ram: '512GB DDR5 ECC',
    storage: '2TB NVMe + 2TB AI Acceleration (aiDAPTIVCache) + 4x 2TB SATA SSD',
    bestFor: 'Enterprise AI/ML, LLM training, generative AI, big data analytics, studio pipeline',
    specialFeature: 'PHISON aiDAPTIV+ AI optimization software',
    neweggUrl: 'https://www.newegg.com/p/83-367-003',
    featured: true
  }
]

const solutions = [
  {
    id: 'ai-deep-learning',
    title: 'AI & Deep Learning',
    description: 'Train and deploy large models with multi-GPU performance',
    features: [
      'Multi-GPU configurations for parallel training',
      'CUDA-optimized software stacks',
      'Large memory capacity for big models',
      'Distributed training across GPUs',
      'Local LLM deployment and inference'
    ],
    useCases: [
      'Large language model training and fine-tuning',
      'Computer vision and image recognition',
      'Reinforcement learning experiments',
      'Deep learning research and development',
      'AI model inference at scale'
    ],
    recommendedModels: ['zaurion-pro', 'zaurion-duo-aqua', 'zaurion-duo-ruby']
  },
  {
    id: 'engineering-cad',
    title: 'Engineering / CAD / Simulation',
    description: 'High-performance workstations for design and simulation',
    features: [
      'Professional GPU acceleration for CAD workflows',
      'High core-count CPUs for simulation',
      'Optimized for SOLIDWORKS, AutoCAD, ANSYS',
      'Real-time visualization and rendering',
      'Stable performance for long-running simulations'
    ],
    useCases: [
      'CAD design and modeling',
      'CFD and FEA simulation',
      'Engineering visualization',
      'Product design and prototyping',
      'Technical computing and analysis'
    ],
    recommendedModels: ['zaurion-aqua', 'zaurion-ruby']
  },
  {
    id: 'content-creation',
    title: 'Content Creation / Media',
    description: 'Professional workstations for creative production',
    features: [
      'Multi-GPU configurations for concurrent rendering',
      'Real-time rendering and preview',
      'High-resolution video processing',
      'Studio pipeline acceleration',
      'Optimized storage for media workflows'
    ],
    useCases: [
      'VFX and animation production',
      'Multi-stream video editing',
      'Complex motion graphics',
      'Professional photo editing',
      'Virtual production and real-time rendering'
    ],
    recommendedModels: ['zaurion-pro', 'zaurion-duo-aqua', 'zaurion-duo-ruby', 'zaurion-aqua', 'zaurion-ruby']
  },
  {
    id: 'scientific-research',
    title: 'Scientific Research / Big Data',
    description: 'High-performance computing for research and analytics',
    features: [
      'High memory capacity (up to 512GB ECC)',
      'Multi-GPU configurations for parallel computing',
      'High thread/core count for data processing',
      'Optimized for scientific workloads',
      'Scalable GPU compute for large datasets'
    ],
    useCases: [
      'Genomics and bioinformatics',
      'Big data analytics and visualization',
      'Scientific simulations',
      'Data exploration and analysis',
      'HPC and research computing'
    ],
    recommendedModels: ['zaurion-pro', 'zaurion-ruby', 'zaurion-duo-ruby']
  }
]

function openNewegg(modelId: string) {
  const model = workstationModels.find(m => m.id === modelId)
  if (model?.neweggUrl) {
    window.open(model.neweggUrl + '?utm_source=console&utm_campaign=explore', '_blank')
  }
}

function openContact() {
  window.open('https://absworkstation.com/contact?utm_source=console&utm_campaign=explore', '_blank')
}

function getModelById(id: string) {
  return workstationModels.find(m => m.id === id)
}
</script>

<template>
  <div class="page page-explore">
    <!-- Hero Context Layer - Animated Background -->
    <HeroContextLayer />
    
    <div class="page-content">
    <div class="page-header">
      <h1 class="page-title">EXPLORE ABS</h1>
      <p class="page-subtitle">Explore the ABS Workstation lineup</p>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button 
        class="tab-button"
        :class="{ 'tab-button--active': activeTab === 'models' }"
        @click="activeTab = 'models'"
      >
        Workstation Models
      </button>
      <button 
        class="tab-button"
        :class="{ 'tab-button--active': activeTab === 'solutions' }"
        @click="activeTab = 'solutions'"
      >
        Solutions by Workload
      </button>
    </div>

    <!-- Models Tab -->
    <div v-if="activeTab === 'models'" class="tab-content">
      <div class="models-grid">
        <div 
          v-for="model in workstationModels" 
          :key="model.id"
          :data-model-id="model.id"
          class="model-card"
          :class="{ 'model-card--featured': model.featured }"
        >
          <div v-if="model.featured" class="featured-badge">ENTERPRISE</div>
          <div class="model-header">
            <div class="model-tier">{{ model.tier }}</div>
            <div class="gpu-icon">⚡</div>
          </div>
          <h3 class="model-name">{{ model.name }}</h3>
          
          <!-- Orange accent bar -->
          <div class="model-accent-bar"></div>
          
          <div class="model-specs">
            <div class="spec-row spec-row--gpu">
              <span class="spec-label">GPU</span>
              <div class="spec-value-group">
                <span class="spec-value">{{ model.gpu }}</span>
                <span class="spec-detail">{{ model.gpuDetails }}</span>
              </div>
            </div>
            <div class="spec-row spec-row--cpu">
              <span class="spec-label">CPU</span>
              <span class="spec-value">{{ model.cpu }}</span>
            </div>
            <div class="spec-row spec-row--ram">
              <span class="spec-label">RAM</span>
              <span class="spec-value">{{ model.ram }}</span>
            </div>
            <div class="spec-row spec-row--storage">
              <span class="spec-label">Storage</span>
              <span class="spec-value">{{ model.storage }}</span>
            </div>
            <div v-if="model.specialFeature" class="spec-row spec-row--special">
              <span class="spec-label">Special</span>
              <span class="spec-value spec-value--special">{{ model.specialFeature }}</span>
            </div>
          </div>

          <div class="model-best-for">
            <span class="best-for-label">Best For:</span>
            <span class="best-for-text">{{ model.bestFor }}</span>
          </div>

          <div class="model-actions">
            <button 
              class="action-button action-button--primary"
              @click="openNewegg(model.id)"
            >
              View on Newegg
            </button>
            <button 
              class="action-button action-button--secondary"
              @click="openContact"
            >
              Get Quote
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Solutions Tab -->
    <div v-if="activeTab === 'solutions'" class="tab-content">
      <div class="solutions-grid">
        <div 
          v-for="solution in solutions" 
          :key="solution.id"
          class="solution-card"
        >
          <h3 class="solution-title">{{ solution.title }}</h3>
          <p class="solution-description">{{ solution.description }}</p>
          
          <div class="solution-section">
            <h4 class="solution-section-title">Key Features</h4>
            <ul class="solution-list">
              <li v-for="feature in solution.features" :key="feature">{{ feature }}</li>
            </ul>
          </div>

          <div class="solution-section">
            <h4 class="solution-section-title">Use Cases</h4>
            <ul class="solution-list">
              <li v-for="useCase in solution.useCases" :key="useCase">{{ useCase }}</li>
            </ul>
          </div>

          <div class="solution-section">
            <h4 class="solution-section-title">Recommended Models</h4>
            <div class="recommended-models">
              <button
                v-for="modelId in solution.recommendedModels"
                :key="modelId"
                class="model-chip"
                @click="activeTab = 'models'; setTimeout(() => document.querySelector(`[data-model-id='${modelId}']`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100)"
              >
                {{ getModelById(modelId)?.name }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CTA Section -->
    <div class="cta-section">
      <button class="cta-button" @click="openContact">
        Contact Our Team for Custom Configuration
        <span class="cta-arrow">→</span>
      </button>
    </div>
    </div>
  </div>
</template>

<style scoped>
.page-explore {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  background: var(--abs-black);
}

.page-content {
  position: relative;
  z-index: 1;
  padding: 40px 24px;
  max-width: var(--container-max);
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}

.page-title {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle {
  font-family: var(--font-label);
  font-size: 0.875rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Tabs */
.tabs {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 40px;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0;
  position: relative;
  z-index: 1;
}

.tab-button {
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
  margin-bottom: -1px;
}

.tab-button:hover {
  color: var(--text-primary);
}

.tab-button--active {
  color: var(--electric-indigo);
  border-bottom-color: var(--electric-indigo);
}

/* Models Grid */
.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
  position: relative;
  z-index: 1;
}

.model-card {
  padding: 32px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  position: relative;
  transition: all var(--duration-normal) var(--ease-smooth);
  display: flex;
  flex-direction: column;
  z-index: 1;
  backdrop-filter: blur(1px);
  overflow: hidden;
}

.model-card:hover {
  border-color: var(--border-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.model-card:hover .gpu-icon {
  animation: gpu-pulse 1.5s ease-in-out infinite;
}

.model-card:hover .model-accent-bar {
  animation: accent-slide-up 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* On hover/focus, hide all specs first, then reveal them one by one */
.model-card:hover .spec-row,
.model-card:focus-within .spec-row {
  opacity: 0;
  transform: translateX(-10px) scale(2);
  animation: spec-slide-in 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.model-card:hover .spec-row--gpu,
.model-card:focus-within .spec-row--gpu {
  animation-delay: 0.2s;
}

.model-card:hover .spec-row--cpu,
.model-card:focus-within .spec-row--cpu {
  animation-delay: 0.6s;
}

.model-card:hover .spec-row--ram,
.model-card:focus-within .spec-row--ram {
  animation-delay: 1.0s;
}

.model-card:hover .spec-row--storage,
.model-card:focus-within .spec-row--storage {
  animation-delay: 1.4s;
}

.model-card:hover .spec-row--special,
.model-card:focus-within .spec-row--special {
  animation-delay: 1.8s;
}

.model-card--featured {
  border-color: var(--abs-orange);
  box-shadow: 0 0 30px rgba(249, 115, 22, 0.15);
}

.featured-badge {
  position: absolute;
  top: -12px;
  right: 24px;
  padding: 6px 14px;
  background: var(--abs-orange);
  color: white;
  font-family: var(--font-label);
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-radius: 12px;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.model-tier {
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.gpu-icon {
  font-size: 1.5rem;
  opacity: 0.6;
  transition: opacity var(--duration-normal) var(--ease-smooth);
  filter: drop-shadow(0 0 4px rgba(249, 115, 22, 0.3));
}

.model-card:hover .gpu-icon {
  opacity: 1;
  filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.6));
}

.model-accent-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--abs-orange), transparent);
  transform: translateY(100%);
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-smooth);
}

.model-card--featured .model-tier {
  color: var(--abs-orange);
}

.model-name {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 24px;
}

.model-specs {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  flex: 1;
}

.spec-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
  /* Default: fully visible */
  opacity: 1;
  transform: translateX(0) scale(1);
  transition: none; /* No transition - animation handles it */
  transform-origin: left center;
  will-change: transform, opacity; /* Optimize for animation */
}

.spec-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.spec-row--special {
  background: rgba(249, 115, 22, 0.1);
  padding: 12px;
  border-radius: 8px;
  border-bottom: none;
  margin-top: 8px;
}

.spec-label {
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.spec-value {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--text-primary);
  line-height: 1.4;
}

.spec-value-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.spec-detail {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.spec-value--special {
  color: var(--abs-orange);
  font-weight: 600;
}

.model-best-for {
  margin-bottom: 24px;
  padding: 12px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  border-left: 3px solid var(--electric-indigo);
}

.best-for-label {
  display: block;
  font-family: var(--font-label);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}

.best-for-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.model-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.action-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.action-button--primary {
  background: var(--electric-indigo);
  color: white;
}

.action-button--primary:hover {
  background: var(--electric-indigo-hover);
  transform: translateY(-1px);
}

.action-button--secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.action-button--secondary:hover {
  border-color: var(--electric-indigo);
  color: var(--electric-indigo);
}

/* Solutions Grid */
.solutions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 32px;
  margin-bottom: 48px;
  position: relative;
  z-index: 1;
}

.solution-card {
  padding: 32px;
  background: var(--abs-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  transition: all var(--duration-normal) var(--ease-smooth);
  z-index: 1;
  backdrop-filter: blur(1px);
  position: relative;
}

.solution-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-md);
}

.solution-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.solution-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0 0 24px;
  line-height: 1.5;
}

.solution-section {
  margin-bottom: 24px;
}

.solution-section:last-child {
  margin-bottom: 0;
}

.solution-section-title {
  font-family: var(--font-label);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--electric-indigo);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 12px;
}

.solution-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.solution-list li {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}

.solution-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--electric-indigo);
  font-weight: bold;
}

.recommended-models {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.model-chip {
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 6px;
  color: var(--electric-indigo);
  font-family: var(--font-label);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}

.model-chip:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: var(--electric-indigo);
  transform: translateY(-1px);
}

/* CTA Section */
.cta-section {
  text-align: center;
  margin-top: 48px;
  position: relative;
  z-index: 1;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(135deg, var(--abs-orange), #ff9f43);
  border: none;
  border-radius: 12px;
  color: white;
  font-family: var(--font-label);
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
  box-shadow: var(--shadow-md), 0 0 30px var(--abs-orange-glow);
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg), 0 0 40px var(--abs-orange-glow);
}

.cta-arrow {
  font-size: 1.25rem;
}

/* Responsive */
@media (min-width: 768px) {
  .models-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .solutions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .page-explore {
    padding: 48px 32px;
  }
  
  .page-title {
    font-size: 2.5rem;
  }
  
  .models-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .solutions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1400px) {
  .models-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* GPU-Powered Micro-Animations */
@keyframes gpu-pulse {
  0%, 100% {
    transform: scale(1);
    filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.6));
  }
  50% {
    transform: scale(1.1);
    filter: drop-shadow(0 0 12px rgba(249, 115, 22, 0.8));
  }
}

@keyframes accent-slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes spec-slide-in {
  0% {
    opacity: 0;
    transform: translateX(-10px) scale(2);
  }
  40% {
    opacity: 0.9;
    transform: translateX(-4px) scale(1.15);
  }
  100% {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* Reset to visible state when not hovering */
.model-card:not(:hover):not(:focus-within) .spec-row {
  animation: none;
  opacity: 1;
  transform: translateX(0) scale(1);
  will-change: auto;
}

/* Reset accent bar when not hovering */
.model-card:not(:hover) .model-accent-bar {
  animation: none;
  transform: translateY(100%);
  opacity: 0;
}
</style>
