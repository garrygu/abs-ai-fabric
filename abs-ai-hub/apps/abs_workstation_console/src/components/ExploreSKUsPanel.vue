<script setup lang="ts">
import { ref } from 'vue'

interface WorkstationSKU {
  sku_id: string
  tier: 'entry' | 'creator' | 'enterprise'
  name: string
  gpu: string
  ram: string
  target_use_case: string
  highlight?: boolean
  cta_url: string
}

// Static workstation data - could be loaded from JSON in production
const workstations = ref<WorkstationSKU[]>([
  {
    sku_id: 'abs-entry-4070',
    tier: 'entry',
    name: 'ABS Entry',
    gpu: 'RTX 4070 Super',
    ram: '64GB DDR5',
    target_use_case: 'Small team AI development',
    cta_url: 'https://absworkstation.com/entry?utm_source=console&utm_campaign=ces2025'
  },
  {
    sku_id: 'abs-creator-4090',
    tier: 'creator',
    name: 'ABS Creator',
    gpu: 'RTX 4090',
    ram: '128GB DDR5',
    target_use_case: 'Content creation & inference',
    cta_url: 'https://absworkstation.com/creator?utm_source=console&utm_campaign=ces2025'
  },
  {
    sku_id: 'abs-enterprise-6000',
    tier: 'enterprise',
    name: 'ABS Enterprise',
    gpu: 'RTX Pro 6000',
    ram: '256GB DDR5',
    target_use_case: 'Enterprise AI deployment',
    highlight: true,
    cta_url: 'https://absworkstation.com/enterprise?utm_source=console&utm_campaign=ces2025'
  }
])

const tierLabels: Record<string, { label: string; class: string }> = {
  entry: { label: 'Entry', class: 'tier--entry' },
  creator: { label: 'Creator', class: 'tier--creator' },
  enterprise: { label: 'Enterprise', class: 'tier--enterprise' }
}

function openWorkstationPage(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <div class="explore-panel">
    <div class="section-header">
      <h2 class="section-title">Explore ABS Workstations</h2>
    </div>
    
    <p class="section-description text-secondary">
      Purpose-built hardware for local AI. No cloud required.
    </p>
    
    <div class="workstations-grid">
      <div 
        v-for="ws in workstations" 
        :key="ws.sku_id"
        class="workstation-card card"
        :class="{ 'workstation-card--highlight': ws.highlight }"
        @click="openWorkstationPage(ws.cta_url)"
      >
        <div class="workstation-header">
          <span class="tier-badge" :class="tierLabels[ws.tier].class">
            {{ tierLabels[ws.tier].label }}
          </span>
          <span v-if="ws.highlight" class="current-badge">This Workstation</span>
        </div>
        
        <h3 class="workstation-name">{{ ws.name }}</h3>
        
        <div class="workstation-specs">
          <div class="spec-row">
            <span class="spec-icon">⚡</span>
            <span class="spec-value">{{ ws.gpu }}</span>
          </div>
          <div class="spec-row">
            <span class="spec-icon">💾</span>
            <span class="spec-value">{{ ws.ram }}</span>
          </div>
        </div>
        
        <p class="workstation-use-case">{{ ws.target_use_case }}</p>
        
        <div class="workstation-cta">
          <span class="cta-text">Learn More</span>
          <span class="cta-arrow">→</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.explore-panel {
  width: 100%;
}

.section-header {
  margin-bottom: 8px;
}

.section-title {
  font-size: 1.375rem;
  margin: 0;
}

.section-description {
  font-size: 0.875rem;
  margin: 0 0 24px 0;
}

.workstations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.workstation-card {
  padding: 24px;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.workstation-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.workstation-card--highlight {
  border-color: var(--abs-orange);
  background: rgba(249, 115, 22, 0.05);
}

.workstation-card--highlight:hover {
  border-color: var(--abs-orange);
  box-shadow: var(--shadow-glow-orange);
}

.workstation-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.tier-badge {
  padding: 4px 10px;
  font-family: var(--font-display);
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-radius: 4px;
}

.tier--entry {
  background: rgba(99, 102, 241, 0.15);
  color: var(--electric-indigo);
}

.tier--creator {
  background: rgba(34, 197, 94, 0.15);
  color: var(--status-success);
}

.tier--enterprise {
  background: rgba(249, 115, 22, 0.15);
  color: var(--abs-orange);
}

.current-badge {
  font-family: var(--font-label);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--abs-orange);
}

.workstation-name {
  font-family: var(--font-display);
  font-size: 1.375rem;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: var(--text-primary);
}

.workstation-specs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.spec-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spec-icon {
  font-size: 1rem;
  width: 20px;
  text-align: center;
}

.spec-value {
  font-family: var(--font-label);
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.workstation-use-case {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.workstation-cta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--electric-indigo);
  transition: gap var(--duration-normal) var(--ease-smooth);
}

.workstation-card:hover .workstation-cta {
  gap: 10px;
}

.cta-arrow {
  transition: transform var(--duration-normal) var(--ease-smooth);
}

.workstation-card:hover .cta-arrow {
  transform: translateX(2px);
}
</style>
