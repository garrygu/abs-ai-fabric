<template>
  <div class="powered-by-banner" @click="openSite">
    <div class="banner-content">
      <span class="banner-icon">⚡</span>
      <span class="banner-text">Powered by ABS Workstation</span>
    </div>
    
    <!-- Tooltip on hover -->
    <div class="banner-tooltip">
      <div class="tooltip-specs">
        <div class="spec-row"><span class="spec-icon">🎮</span> RTX Pro 6000</div>
        <div class="spec-row"><span class="spec-icon">💾</span> 128GB RAM</div>
        <div class="spec-row"><span class="spec-icon">🧠</span> Local AI Processing</div>
      </div>
      <div class="tooltip-cta">View Hardware →</div>
    </div>
  </div>
</template>

<script setup lang="ts">
function openSite() {
  window.open('https://absworkstation.com', '_blank')
}
</script>

<style scoped>
.powered-by-banner {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  padding: 0.4rem 0.75rem;
  background: linear-gradient(135deg, rgba(255, 107, 0, 0.08) 0%, rgba(255, 107, 0, 0.03) 100%);
  border: 1px solid rgba(255, 107, 0, 0.2);
  border-radius: 6px;
  
  cursor: pointer;
  transition: all 0.2s ease;
}

.powered-by-banner:hover {
  background: linear-gradient(135deg, rgba(255, 107, 0, 0.15) 0%, rgba(255, 107, 0, 0.08) 100%);
  border-color: rgba(255, 107, 0, 0.4);
  box-shadow: 0 2px 8px rgba(255, 107, 0, 0.15);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.banner-icon {
  font-size: 0.9rem;
}

.banner-text {
  font-size: 0.7rem;
  font-weight: 600;
  color: #FF6B00;
  letter-spacing: 0.2px;
  white-space: nowrap;
}

/* Tooltip */
.banner-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  
  min-width: 180px;
  padding: 0.75rem;
  
  background: var(--bg-primary, #fff);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: all 0.2s ease;
  z-index: 1000;
}

.powered-by-banner:hover .banner-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.tooltip-specs {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}

.spec-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: var(--text-secondary, #6b7280);
}

.spec-icon {
  font-size: 0.8rem;
}

.tooltip-cta {
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-color, #e5e7eb);
  font-size: 0.7rem;
  font-weight: 600;
  color: #FF6B00;
  text-align: center;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .powered-by-banner {
    background: linear-gradient(135deg, rgba(255, 107, 0, 0.12) 0%, rgba(255, 107, 0, 0.05) 100%);
  }
  
  .banner-tooltip {
    background: #1f2937;
    border-color: #374151;
  }
}
</style>
